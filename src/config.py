"""Application configuration from environment."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")


class Settings:
    root_dir: Path = _ROOT
    data_dir: Path = Path(os.getenv("DATA_DIR", _ROOT / "data"))
    runs_dir: Path = Path(os.getenv("RUNS_DIR", _ROOT / "runs"))
    prompts_dir: Path = _ROOT / "prompts"

    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
    gpt_review_model: str = os.getenv("GPT_REVIEW_MODEL", "gpt-4.1")
    max_review_iterations: int = int(os.getenv("MAX_REVIEW_ITERATIONS", "3"))

    # compact_extract = labels + formulas only (default)
    # full = row-grouped TSV from source workbook
    # files_api = attach workbook file, minimal text extract
    reference_workbook_mode: str = os.getenv(
        "REFERENCE_WORKBOOK_MODE", "compact_extract"
    ).lower()

    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    claude_max_tokens: int = int(os.getenv("CLAUDE_MAX_TOKENS", "64000"))
    anthropic_timeout: float = float(os.getenv("ANTHROPIC_TIMEOUT", "3600"))

    reference_filenames: tuple[str, ...] = (
        "guide_memo.pdf",
        "guide_workbook.xlsm",
        "example_memo.pdf",
        "example_workbook.xlsx",
    )


settings = Settings()
