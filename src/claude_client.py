"""Anthropic Claude 3-call BCA pipeline — Files API + code execution."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import anthropic

from src.anthropic_files import (
    UploadedFile,
    anthropic_betas,
    build_file_attachment_blocks,
    code_execution_tools,
    download_file,
    extract_output_file_ids,
    extract_text_from_message,
    guess_mime,
    pick_workbook_file_id,
    save_upload_manifest,
    serialize_content_blocks,
    upload_path,
    upload_project_files,
    upload_reference_files,
)
from src.config import settings
from src.memo_export import extract_memo_from_text, markdown_to_docx
from src.reference_docs import get_guide_workbook_tabs
from src.workbook_export import apply_patches_to_workbook, extract_patches_from_text

logger = logging.getLogger(__name__)

PHASE_NAMES = [
    "Project Assessment",
    "Design Complete BCA Workbook",
    "Prepare BCA Technical Memorandum",
    "Perform Benefit-Cost Analysis",
    "Sensitivity Analysis",
    "Quality Review",
]

CALL_NAMES = [
    "Project Assessment & Spec",
    "Build BCA Workbook",
    "Write BCA Technical Memorandum",
]


def _extract_json_spec(text: str) -> str:
    m = re.search(r"```json\s*([\s\S]*?)\s*```", text)
    return m.group(1).strip() if m else ""


def _extract_workbook_results(text: str) -> str:
    m = re.search(
        r"---\s*WORKBOOK RESULTS START\s*---\s*([\s\S]*?)\s*---\s*WORKBOOK RESULTS END\s*---",
        text,
        re.IGNORECASE,
    )
    return m.group(1).strip() if m else ""


@dataclass
class ClaudeRunState:
    run_id: str
    run_dir: Path
    messages: list[dict[str, Any]] = field(default_factory=list)
    phases_completed: int = 0
    iteration: int = 1
    model: str = settings.claude_model
    input_tokens: int = 0
    output_tokens: int = 0
    uploaded_files: list[dict[str, str]] = field(default_factory=list)
    input_file_ids: list[str] = field(default_factory=list)
    last_output_file_ids: list[str] = field(default_factory=list)
    # 3-call pipeline state
    project_spec: str = ""
    workbook_results: str = ""
    workbook_output_file_ids: list[str] = field(default_factory=list)

    def save(self) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        path = self.run_dir / "conversation.json"
        path.write_text(
            json.dumps(
                {
                    "run_id": self.run_id,
                    "phases_completed": self.phases_completed,
                    "iteration": self.iteration,
                    "model": self.model,
                    "input_tokens": self.input_tokens,
                    "output_tokens": self.output_tokens,
                    "uploaded_files": self.uploaded_files,
                    "input_file_ids": self.input_file_ids,
                    "last_output_file_ids": self.last_output_file_ids,
                    "project_spec": self.project_spec,
                    "workbook_results": self.workbook_results,
                    "workbook_output_file_ids": self.workbook_output_file_ids,
                    "messages": self.messages,
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, run_dir: Path) -> ClaudeRunState:
        path = run_dir / "conversation.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            run_id=data["run_id"],
            run_dir=run_dir,
            messages=data.get("messages", []),
            phases_completed=data.get("phases_completed", 0),
            iteration=data.get("iteration", 1),
            model=data.get("model", settings.claude_model),
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
            uploaded_files=data.get("uploaded_files", []),
            input_file_ids=data.get("input_file_ids", []),
            last_output_file_ids=data.get("last_output_file_ids", []),
            project_spec=data.get("project_spec", ""),
            workbook_results=data.get("workbook_results", ""),
            workbook_output_file_ids=data.get("workbook_output_file_ids", []),
        )


class ClaudeBCAClient:
    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or settings.anthropic_api_key
        if not key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        self.client = anthropic.Anthropic(
            api_key=key,
            timeout=settings.anthropic_timeout,
        )

    def new_run_id(self) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"run_{ts}"

    def _get_uploaded_files(self, state: ClaudeRunState) -> list[UploadedFile]:
        result = []
        for f in state.uploaded_files:
            name = f["name"]
            uf = UploadedFile(
                name=name,
                path="",
                file_id=f["file_id"],
                mime_type=guess_mime(Path(name)),
                role=f.get("role", ""),
            )
            result.append(uf)
        return result

    def _upload_run_files(
        self,
        run_dir: Path,
        project_files: list[tuple[str, bytes]],
    ) -> list[UploadedFile]:
        refs = upload_reference_files(self.client)
        projects = upload_project_files(self.client, project_files) if project_files else []
        all_uploaded = refs + projects
        save_upload_manifest(run_dir, all_uploaded)
        return all_uploaded

    def _api_messages(self, state: ClaudeRunState) -> list[dict[str, Any]]:
        return [{"role": m["role"], "content": m["content"]} for m in state.messages]

    _SYSTEM_PROMPT = (
        "You are a senior transportation economist and infrastructure finance consultant "
        "with extensive experience preparing USDOT BUILD, RAISE, INFRA, MEGA, CRISI, BIP, "
        "and other discretionary grant benefit-cost analyses. "
        "Your work is reviewed by USDOT economists and must be technically rigorous, "
        "transparent, and fully traceable. "
        "Every formula in the workbook must be live and reference the inputs tab — "
        "never hardcode a number that derives from an input."
    )

    def _call_claude(
        self,
        state: ClaudeRunState,
        *,
        on_text_delta: Callable[[str], None] | None = None,
    ) -> tuple[str, list[dict[str, Any]], list[str]]:
        logger.info(
            "Claude API call (model=%s, max_tokens=%s)",
            state.model,
            settings.claude_max_tokens,
        )
        chars = 0
        with self.client.beta.messages.stream(
            model=state.model,
            max_tokens=settings.claude_max_tokens,
            system=self._SYSTEM_PROMPT,
            messages=self._api_messages(state),
            tools=code_execution_tools(),
            betas=anthropic_betas(),
        ) as stream:
            for text in stream.text_stream:
                chars += len(text)
                if on_text_delta:
                    on_text_delta(text)
            final = stream.get_final_message()

        if final.usage:
            state.input_tokens += final.usage.input_tokens
            state.output_tokens += final.usage.output_tokens

        assistant_content = serialize_content_blocks(final.content)
        if not isinstance(assistant_content, list):
            assistant_content = [{"type": "text", "text": str(assistant_content)}]

        output_file_ids = extract_output_file_ids(final)
        state.last_output_file_ids = output_file_ids
        response_text = extract_text_from_message(final)

        logger.info(
            "Call complete (%d chars, %d output files, %s out tokens)",
            chars,
            len(output_file_ids),
            final.usage.output_tokens if final.usage else "?",
        )
        return response_text, assistant_content, output_file_ids

    def _fresh_call(
        self,
        state: ClaudeRunState,
        content: list[dict[str, Any]],
    ) -> tuple[str, list[dict[str, Any]], list[str]]:
        """Make a single API call with a fresh (one-message) conversation."""
        temp = ClaudeRunState(
            run_id=state.run_id,
            run_dir=state.run_dir,
            model=state.model,
            messages=[{"role": "user", "content": content}],
            input_file_ids=state.input_file_ids,
        )
        response_text, assistant_content, output_file_ids = self._call_claude(temp)
        state.input_tokens += temp.input_tokens
        state.output_tokens += temp.output_tokens
        return response_text, assistant_content, output_file_ids

    # -------------------------------------------------------------------------
    # Pipeline entry point
    # -------------------------------------------------------------------------

    def start_production(
        self,
        run_dir: Path,
        project_files: list[tuple[str, bytes]],
        project_file_names: list[str] | None = None,
    ) -> ClaudeRunState:
        run_id = run_dir.name
        state = ClaudeRunState(run_id=run_id, run_dir=run_dir, iteration=1)

        uploaded = self._upload_run_files(run_dir, project_files)
        state.uploaded_files = [
            {"name": u.name, "file_id": u.file_id, "role": u.role} for u in uploaded
        ]
        state.input_file_ids = [u.file_id for u in uploaded]
        state.save()
        return state

    # -------------------------------------------------------------------------
    # 3-call production pipeline
    # -------------------------------------------------------------------------

    def run_assessment(self, state: ClaudeRunState) -> tuple[ClaudeRunState, str]:
        """Call 1: read all files → structured JSON project spec."""
        prompt = (settings.prompts_dir / "call1_assessment.md").read_text(encoding="utf-8")
        all_files = self._get_uploaded_files(state)

        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        content.extend(build_file_attachment_blocks(all_files))

        response_text, _, _ = self._fresh_call(state, content)

        state.project_spec = _extract_json_spec(response_text)
        if not state.project_spec:
            logger.warning("Call 1 response contained no JSON spec — raw text saved")
        state.phases_completed = max(state.phases_completed, 1)
        self._save_phase_response(state, 1, response_text)
        state.save()
        return state, response_text

    def run_workbook_build(self, state: ClaudeRunState) -> tuple[ClaudeRunState, str]:
        """Call 2: spec + template workbook → build workbook via code execution."""
        spec_dict: dict[str, Any] = {}
        if state.project_spec:
            try:
                spec_dict = json.loads(state.project_spec)
            except json.JSONDecodeError:
                logger.warning("Could not parse project_spec JSON")

        template_name = spec_dict.get("project", {}).get(
            "workbook_template", "example_workbook.xlsx"
        )

        all_files = self._get_uploaded_files(state)
        template_files = [f for f in all_files if f.name == template_name]
        if not template_files:
            logger.warning(
                "Template %s not found in uploaded files; attaching all reference workbooks",
                template_name,
            )
            template_files = [
                f for f in all_files
                if Path(f.name).suffix.lower() in {".xlsx", ".xlsm"}
                and f.role != "Project application material"
            ]

        valid_tabs = "\n".join(get_guide_workbook_tabs())
        prompt_template = (settings.prompts_dir / "call2_workbook.md").read_text(encoding="utf-8")
        prompt = prompt_template.format(
            project_spec=state.project_spec or "(no spec available)",
            valid_tabs=valid_tabs or "(see workbook)",
        )

        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        content.extend(build_file_attachment_blocks(template_files))

        response_text, _, output_file_ids = self._fresh_call(state, content)

        state.workbook_output_file_ids = output_file_ids
        state.last_output_file_ids = output_file_ids
        state.workbook_results = _extract_workbook_results(response_text)
        state.phases_completed = max(state.phases_completed, 4)
        self._save_phase_response(state, 4, response_text)
        state.save()
        return state, response_text

    def run_memo_write(self, state: ClaudeRunState) -> tuple[ClaudeRunState, str]:
        """Call 3: spec + workbook results → write BCA memo."""
        all_files = self._get_uploaded_files(state)
        style_files = [f for f in all_files if f.name in {"example_memo.pdf", "guide_memo.pdf"}]

        prompt_template = (settings.prompts_dir / "call3_memo.md").read_text(encoding="utf-8")
        prompt = prompt_template.format(
            project_spec=state.project_spec or "(no spec available)",
            workbook_results=state.workbook_results
            or "(workbook results not captured — use project spec estimates)",
        )

        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        content.extend(build_file_attachment_blocks(style_files))

        response_text, _, _ = self._fresh_call(state, content)

        state.phases_completed = 6
        self._save_phase_response(state, 6, response_text)
        state.save()
        return state, response_text

    # -------------------------------------------------------------------------
    # Revision (fresh call with spec + prior workbook + review feedback)
    # -------------------------------------------------------------------------

    def revise_from_review(
        self,
        state: ClaudeRunState,
        review_text: str,
    ) -> tuple[ClaudeRunState, str]:
        template = (settings.prompts_dir / "revision_user.md").read_text(encoding="utf-8")
        next_version = state.iteration + 1
        valid_tabs = "\n".join(get_guide_workbook_tabs())
        user_msg = template.format(
            review_text=review_text,
            version=next_version,
            valid_tabs=valid_tabs or "(see workbook)",
        )

        content: list[dict[str, Any]] = [{"type": "text", "text": user_msg}]

        for ext in (".xlsm", ".xlsx"):
            prior_wb = state.run_dir / f"workbook_v{state.iteration}{ext}"
            if prior_wb.exists():
                attached = upload_path(self.client, prior_wb)
                attached.role = f"Prior workbook v{state.iteration} to revise"
                content.extend(build_file_attachment_blocks([attached]))
                state.input_file_ids.append(attached.file_id)
                break

        state.iteration = next_version
        response_text, _, output_file_ids = self._fresh_call(state, content)

        state.workbook_output_file_ids = output_file_ids
        state.last_output_file_ids = output_file_ids
        state.workbook_results = _extract_workbook_results(response_text) or state.workbook_results
        self._save_phase_response(state, 6, response_text, suffix=f"_rev{state.iteration}")
        state.save()
        return state, response_text

    # -------------------------------------------------------------------------
    # Artifact export
    # -------------------------------------------------------------------------

    def _save_phase_response(
        self,
        state: ClaudeRunState,
        phase_num: int,
        text: str,
        suffix: str = "",
    ) -> Path:
        path = state.run_dir / f"phase_{phase_num}_response{suffix}.md"
        path.write_text(text, encoding="utf-8")
        return path

    def export_artifacts(
        self,
        state: ClaudeRunState,
        response_text: str,
        *,
        workbook_file_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        version = state.iteration
        memo_md = extract_memo_from_text(response_text)
        patches = extract_patches_from_text(response_text)
        valid_tabs = get_guide_workbook_tabs()

        result: dict[str, Any] = {
            "version": version,
            "memo_path": None,
            "workbook_path": None,
            "workbook_source": None,
            "patches_submitted": len(patches),
            "patches_applied": 0,
            "warnings": [],
        }

        if not memo_md:
            result["warnings"].append("No memo found in response (expected --- MEMO START --- markers)")
        else:
            memo_path = state.run_dir / f"memo_v{version}.docx"
            memo_md_path = state.run_dir / f"memo_v{version}.md"
            memo_md_path.write_text(memo_md, encoding="utf-8")
            markdown_to_docx(memo_md, memo_path)
            result["memo_path"] = str(memo_path)
            result["memo_md_path"] = str(memo_md_path)

        wb_file_ids = workbook_file_ids if workbook_file_ids is not None else state.last_output_file_ids
        wb_path = self._export_workbook_from_code_execution(state, version, file_ids=wb_file_ids)
        if wb_path:
            result["workbook_path"] = str(wb_path)
            result["workbook_source"] = "code_execution"
        elif patches:
            ext = ".xlsm"
            fallback = state.run_dir / f"workbook_v{version}{ext}"
            wb_result = apply_patches_to_workbook(
                patches,
                fallback,
                valid_sheets=valid_tabs,
            )
            result["workbook_path"] = wb_result["output_path"]
            result["workbook_source"] = "patches_fallback"
            result["patches_applied"] = wb_result["patches_applied"]
            result["patches_rejected"] = wb_result["patches_rejected"]
            result["rejection_details"] = wb_result.get("rejection_details", [])
            if wb_result["patches_rejected"]:
                result["warnings"].append(
                    f"{wb_result['patches_rejected']} patches rejected (fallback mode)"
                )
        else:
            result["warnings"].append(
                "No workbook from code execution and no patches in response"
            )

        patches_path = state.run_dir / f"workbook_patches_v{version}.txt"
        patches_path.write_text("\n".join(patches), encoding="utf-8")
        result["patches_path"] = str(patches_path)
        return result

    def _export_workbook_from_code_execution(
        self,
        state: ClaudeRunState,
        version: int,
        *,
        file_ids: list[str] | None = None,
    ) -> Path | None:
        output_ids = file_ids if file_ids is not None else state.last_output_file_ids
        input_ids = set(state.input_file_ids)
        file_id = pick_workbook_file_id(self.client, output_ids, input_file_ids=input_ids)
        if not file_id:
            return None

        try:
            meta = self.client.beta.files.retrieve_metadata(file_id)
            suffix = Path(meta.filename).suffix if meta.filename else ".xlsx"
            if suffix.lower() not in {".xlsx", ".xlsm", ".xls"}:
                suffix = ".xlsx"
            dest = state.run_dir / f"workbook_v{version}{suffix}"
            download_file(self.client, file_id, dest)
            return dest
        except Exception as exc:
            logger.error("Failed to download workbook %s: %s", file_id, exc)
            return None
