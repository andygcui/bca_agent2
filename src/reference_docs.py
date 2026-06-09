"""USDOT reference document loading with disk cache."""

from __future__ import annotations

import logging
from pathlib import Path

from src.config import settings
from src.document_ingest import DocumentIngestError, extract_text
from src.workbook_export import workbook_context_for_prompt

logger = logging.getLogger(__name__)

REFERENCE_ROLES = {
    "guide_memo.pdf": "USDOT Benefit-Cost Analysis Guidance (authoritative methodology)",
    "guide_workbook.xlsm": "USDOT BCA Spreadsheet Template (authoritative workbook design)",
    "example_memo.pdf": "Example BCA Technical Memorandum (structure/style only)",
    "example_workbook.xlsx": "Example BCA Workbook (structure/style only)",
}

_CACHE_DIR = settings.data_dir / ".reference_cache"


def list_reference_documents() -> list[dict[str, str]]:
    docs: list[dict[str, str]] = []
    for name in settings.reference_filenames:
        path = settings.data_dir / name
        docs.append(
            {
                "filename": name,
                "path": str(path),
                "present": str(path.exists()).lower(),
                "role": REFERENCE_ROLES.get(name, ""),
            }
        )
    return docs


def references_ready() -> bool:
    return all((settings.data_dir / name).exists() for name in settings.reference_filenames[:2])


def _cache_path(source: Path, mode: str) -> Path:
    return _CACHE_DIR / f"{source.name}.{mode}.txt"


def _read_cache(source: Path, mode: str) -> str | None:
    cache = _cache_path(source, mode)
    if not cache.exists():
        return None
    try:
        if cache.stat().st_mtime >= source.stat().st_mtime:
            return cache.read_text(encoding="utf-8")
    except OSError:
        return None
    return None


def _write_cache(source: Path, mode: str, text: str) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(source, mode).write_text(text, encoding="utf-8")


def extract_reference_text(name: str, path: Path) -> str:
    suffix = path.suffix.lower()
    mode = settings.reference_workbook_mode

    if suffix in (".xlsx", ".xlsm"):
        cache_mode = f"workbook_{mode}"
        cached = _read_cache(path, cache_mode)
        if cached is not None:
            return cached
        text = workbook_context_for_prompt(path, mode=mode)
        _write_cache(path, cache_mode, text)
        return text

    cache_mode = "pdf"
    cached = _read_cache(path, cache_mode)
    if cached is not None:
        return cached
    text = extract_text(name, path.read_bytes())
    _write_cache(path, cache_mode, text)
    return text


def load_reference_bundle() -> tuple[str, list[str], list[str]]:
    """Return combined reference text, loaded filenames, warnings."""
    warnings: list[str] = []
    loaded: list[str] = []
    parts: list[str] = []

    for name in settings.reference_filenames:
        path = settings.data_dir / name
        if not path.exists():
            warnings.append(f"Missing reference: {name}")
            continue
        try:
            text = extract_reference_text(name, path)
            parts.append(f"--- FILE: {name} ({REFERENCE_ROLES[name]}) ---\n{text}")
            loaded.append(name)
        except (DocumentIngestError, OSError, RuntimeError, ValueError) as exc:
            warnings.append(f"{name}: {exc}")

    return "\n\n".join(parts), loaded, warnings


def get_guide_workbook_tabs() -> list[str]:
    from src.workbook_export import get_workbook_tab_names

    path = settings.data_dir / "guide_workbook.xlsm"
    if not path.exists():
        return []
    return get_workbook_tab_names(path)
