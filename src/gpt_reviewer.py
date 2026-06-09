"""OpenAI GPT reviewer — separate vendor from Claude production."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from openai import OpenAI

from src.config import settings
from src.document_ingest import extract_text
from src.reference_docs import load_reference_bundle
from src.workbook_export import workbook_context_for_prompt

logger = logging.getLogger(__name__)


class GPTReviewer:
    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or settings.openai_api_key
        if not key:
            raise ValueError("OPENAI_API_KEY is required")
        self.client = OpenAI(api_key=key)
        self.model = settings.gpt_review_model

    def _load_system_prompt(self) -> str:
        return (settings.prompts_dir / "review_gpt.md").read_text(encoding="utf-8")

    def _extract_artifact_text(self, path: Path, max_chars: int = 120_000) -> str:
        if not path.exists():
            return f"[File not found: {path}]"
        suffix = path.suffix.lower()
        if suffix == ".md":
            text = path.read_text(encoding="utf-8")
        elif suffix in (".docx",):
            text = extract_text(path.name, path.read_bytes())
        elif suffix in (".xlsx", ".xlsm"):
            text = workbook_context_for_prompt(path, mode="compact_extract")
        elif suffix == ".pdf":
            text = extract_text(path.name, path.read_bytes())
        else:
            text = path.read_text(encoding="utf-8", errors="replace")

        if len(text) > max_chars:
            return text[:max_chars] + f"\n\n[... truncated to {max_chars:,} chars ...]"
        return text

    def review(
        self,
        run_dir: Path,
        version: int,
        project_text: str,
        project_files: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run GPT review on exported memo + workbook + original docs."""
        reviews_dir = run_dir / "reviews"
        reviews_dir.mkdir(parents=True, exist_ok=True)

        memo_path = self._find_memo(run_dir, version)
        workbook_path = self._find_workbook(run_dir, version)

        ref_text, loaded_refs, ref_warnings = load_reference_bundle()

        user_parts = [
            self._load_system_prompt(),
            "",
            "## Reference documents",
            ref_text or "(no reference text loaded)",
            "",
            "## Project application materials",
            f"Files: {', '.join(project_files or [])}",
            "",
            project_text or "(no project text)",
            "",
            "## Draft BCA Technical Memorandum",
            self._extract_artifact_text(memo_path) if memo_path else "(memo not found)",
            "",
            "## Draft BCA Excel Workbook",
            self._extract_artifact_text(workbook_path) if workbook_path else "(workbook not found)",
        ]

        if ref_warnings:
            user_parts.extend(["", "## Warnings", *[f"- {w}" for w in ref_warnings]])

        user_content = "\n".join(user_parts)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an independent USDOT BCA reviewer. Output plain text only.",
                },
                {"role": "user", "content": user_content},
            ],
            max_tokens=16000,
        )

        review_text = response.choices[0].message.content or ""
        review_path = reviews_dir / f"review_v{version}.md"
        review_path.write_text(review_text, encoding="utf-8")

        scores = _extract_scores(review_text)

        usage = response.usage
        return {
            "version": version,
            "review_path": str(review_path),
            "review_text": review_text,
            "scores": scores,
            "memo_path": str(memo_path) if memo_path else None,
            "workbook_path": str(workbook_path) if workbook_path else None,
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
        }

    def _find_memo(self, run_dir: Path, version: int) -> Path | None:
        for candidate in (
            run_dir / f"memo_v{version}.md",
            run_dir / f"memo_v{version}.docx",
        ):
            if candidate.exists():
                return candidate
        return None

    def _find_workbook(self, run_dir: Path, version: int) -> Path | None:
        for ext in (".xlsm", ".xlsx"):
            candidate = run_dir / f"workbook_v{version}{ext}"
            if candidate.exists():
                return candidate
        return None


def _extract_scores(review_text: str) -> dict[str, float | None]:
    """Best-effort parse of overall quality score from plain text."""
    import re

    scores: dict[str, float | None] = {"overall": None}
    patterns = [
        r"overall\s+quality[^0-9]*(\d+(?:\.\d+)?)\s*/\s*10",
        r"overall[^0-9]*(\d+(?:\.\d+)?)\s*/\s*10",
        r"overall\s+quality[^0-9]*(\d+(?:\.\d+)?)",
    ]
    for pat in patterns:
        m = re.search(pat, review_text, re.IGNORECASE)
        if m:
            scores["overall"] = float(m.group(1))
            break
    return scores
