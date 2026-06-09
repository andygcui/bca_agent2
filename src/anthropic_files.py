"""Anthropic Files API — upload references, attach to messages, download outputs."""

from __future__ import annotations

import json
import logging
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import anthropic

from src.config import settings

logger = logging.getLogger(__name__)

FILES_BETA = "files-api-2025-04-14"
CODE_EXEC_BETA = "code-execution-2025-08-25"

MIME_OVERRIDES = {
    ".pdf": "application/pdf",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xlsm": "application/vnd.ms-excel.sheet.macroEnabled.12",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".csv": "text/csv",
}

REFERENCE_FILES = (
    ("guide_memo.pdf", "USDOT BCA Guidance (authoritative methodology)"),
    ("guide_workbook.xlsm", "USDOT BCA template workbook (authoritative structure)"),
    ("example_memo.pdf", "Example BCA memo (structure/style only)"),
    ("example_workbook.xlsx", "Example highway workbook (structure/style only)"),
)

SPREADSHEET_SUFFIXES = {".xlsx", ".xlsm", ".xls", ".csv"}


@dataclass
class UploadedFile:
    name: str
    path: str
    file_id: str
    mime_type: str
    role: str = ""


def anthropic_betas() -> list[str]:
    return [FILES_BETA, CODE_EXEC_BETA]


def code_execution_tools() -> list[dict[str, str]]:
    return [{"type": "code_execution_20250825", "name": "code_execution"}]


def guess_mime(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in MIME_OVERRIDES:
        return MIME_OVERRIDES[suffix]
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "application/octet-stream"


def upload_path(client: anthropic.Anthropic, path: Path) -> UploadedFile:
    path = Path(path)
    mime = guess_mime(path)
    logger.info("Uploading %s (%s)", path.name, mime)
    with path.open("rb") as fh:
        meta = client.beta.files.upload(file=(path.name, fh, mime))
    return UploadedFile(
        name=path.name,
        path=str(path),
        file_id=meta.id,
        mime_type=mime,
    )


def upload_bytes(client: anthropic.Anthropic, name: str, data: bytes) -> UploadedFile:
    mime = guess_mime(Path(name))
    logger.info("Uploading %s (%s, %d bytes)", name, mime, len(data))
    meta = client.beta.files.upload(file=(name, data, mime))
    return UploadedFile(
        name=name,
        path="",
        file_id=meta.id,
        mime_type=mime,
    )


def upload_reference_files(client: anthropic.Anthropic) -> list[UploadedFile]:
    uploaded: list[UploadedFile] = []
    for filename, role in REFERENCE_FILES:
        path = settings.data_dir / filename
        if not path.exists():
            logger.warning("Reference file missing: %s", path)
            continue
        item = upload_path(client, path)
        item.role = role
        uploaded.append(item)
    return uploaded


def upload_project_files(
    client: anthropic.Anthropic,
    files: list[tuple[str, bytes]],
) -> list[UploadedFile]:
    uploaded: list[UploadedFile] = []
    for name, data in files:
        item = upload_bytes(client, name, data)
        item.role = "Project application material"
        uploaded.append(item)
    return uploaded


def file_content_block(uploaded: UploadedFile) -> dict[str, Any]:
    """PDF → document block; spreadsheets/data → container_upload for code execution."""
    suffix = Path(uploaded.name).suffix.lower()
    if suffix == ".pdf":
        return {
            "type": "document",
            "source": {"type": "file", "file_id": uploaded.file_id},
            "title": uploaded.name,
            "context": uploaded.role or uploaded.name,
        }
    return {
        "type": "container_upload",
        "file_id": uploaded.file_id,
    }


def build_file_attachment_blocks(uploaded: list[UploadedFile]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for item in uploaded:
        blocks.append(
            {
                "type": "text",
                "text": f"**Attached file:** `{item.name}` — {item.role or 'uploaded file'}",
            }
        )
        blocks.append(file_content_block(item))
    return blocks


def save_upload_manifest(run_dir: Path, uploaded: list[UploadedFile]) -> None:
    manifest = [
        {
            "name": u.name,
            "file_id": u.file_id,
            "mime_type": u.mime_type,
            "role": u.role,
            "path": u.path,
        }
        for u in uploaded
    ]
    (run_dir / "uploaded_files.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


def load_upload_manifest(run_dir: Path) -> list[UploadedFile]:
    path = run_dir / "uploaded_files.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        UploadedFile(
            name=item["name"],
            path=item.get("path", ""),
            file_id=item["file_id"],
            mime_type=item.get("mime_type", ""),
            role=item.get("role", ""),
        )
        for item in data
    ]


def extract_text_from_message(message: Any) -> str:
    parts: list[str] = []
    for block in message.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "\n".join(parts)


def extract_output_file_ids(message: Any) -> list[str]:
    """Collect file_ids from code execution output blocks in the response."""
    found: list[str] = []

    def walk(obj: Any) -> None:
        if obj is None:
            return
        if isinstance(obj, list):
            for item in obj:
                walk(item)
            return
        if isinstance(obj, dict):
            if obj.get("type") in (
                "bash_code_execution_output",
                "code_execution_output",
            ) and obj.get("file_id"):
                found.append(obj["file_id"])
            for value in obj.values():
                walk(value)
            return
        if hasattr(obj, "model_dump"):
            walk(obj.model_dump())
            return
        if hasattr(obj, "__dict__"):
            for block in getattr(obj, "content", []) or []:
                walk(block)
            if hasattr(obj, "type"):
                t = getattr(obj, "type", "")
                if t in ("bash_code_execution_output", "code_execution_output"):
                    fid = getattr(obj, "file_id", None)
                    if fid:
                        found.append(fid)
                if t in ("bash_code_execution_tool_result", "code_execution_tool_result"):
                    walk(getattr(obj, "content", None))
                if t in ("bash_code_execution_result", "code_execution_result"):
                    for out in getattr(obj, "content", []) or []:
                        walk(out)

    for block in message.content:
        walk(block)

    # Preserve order, dedupe
    seen: set[str] = set()
    ordered: list[str] = []
    for fid in found:
        if fid not in seen:
            seen.add(fid)
            ordered.append(fid)
    return ordered


def pick_workbook_file_id(
    client: anthropic.Anthropic,
    file_ids: list[str],
    *,
    input_file_ids: set[str] | None = None,
) -> str | None:
    """Prefer downloadable spreadsheet outputs not in the input set."""
    input_file_ids = input_file_ids or set()
    candidates: list[tuple[int, str, str]] = []

    for fid in file_ids:
        if fid in input_file_ids:
            continue
        try:
            meta = client.beta.files.retrieve_metadata(fid)
        except Exception as exc:
            logger.warning("Could not retrieve metadata for %s: %s", fid, exc)
            continue
        if meta.downloadable is False:
            continue
        name_lower = (meta.filename or "").lower()
        mime = (meta.mime_type or "").lower()
        is_sheet = (
            any(name_lower.endswith(ext) for ext in SPREADSHEET_SUFFIXES)
            or "spreadsheet" in mime
            or "excel" in mime
        )
        if is_sheet:
            candidates.append((meta.size_bytes, fid, meta.filename))

    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def download_file(client: anthropic.Anthropic, file_id: str, dest: Path) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    response = client.beta.files.download(file_id)
    data = response.read()
    dest.write_bytes(data)
    logger.info("Downloaded file %s → %s (%d bytes)", file_id, dest, len(data))
    return dest


def serialize_content_blocks(blocks: Any) -> list[dict[str, Any]] | str:
    if isinstance(blocks, str):
        return blocks
    if isinstance(blocks, list):
        out: list[dict[str, Any]] = []
        for block in blocks:
            if hasattr(block, "model_dump"):
                out.append(block.model_dump())
            elif isinstance(block, dict):
                out.append(block)
            else:
                out.append({"type": "text", "text": str(block)})
        return out
    return str(blocks)
