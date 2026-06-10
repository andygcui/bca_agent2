"""Orchestrate production → review → revision loops."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from src.claude_client import CALL_NAMES, ClaudeBCAClient, ClaudeRunState
from src.config import settings
from src.claude_reviewer import ClaudeReviewer

logger = logging.getLogger(__name__)


class RunStatus(str, Enum):
    IDLE = "idle"
    PRODUCTION = "production"
    REVIEW = "review"
    REVISION = "revision"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class RunRecord:
    run_id: str
    run_dir: Path
    status: RunStatus = RunStatus.IDLE
    project_name: str = ""
    project_text: str = ""
    project_files: list[str] = field(default_factory=list)
    current_version: int = 0
    max_iterations: int = 1
    reviews_completed: int = 0
    error: str = ""
    last_artifacts: dict[str, Any] = field(default_factory=dict)
    last_review: dict[str, Any] = field(default_factory=dict)
    log: list[str] = field(default_factory=list)

    def append_log(self, msg: str) -> None:
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        self.log.append(entry)
        logger.info(entry)


class BCARunManager:
    def __init__(
        self,
        on_status: Callable[[RunRecord], None] | None = None,
    ) -> None:
        self.claude = ClaudeBCAClient()
        self.reviewer = ClaudeReviewer()
        self.on_status = on_status
        self.record: RunRecord | None = None
        self.claude_state: ClaudeRunState | None = None

    def _notify(self) -> None:
        if self.on_status and self.record:
            self.on_status(self.record)

    def create_run(
        self,
        project_name: str,
        project_text: str,
        project_files: list[str],
        project_file_bytes: list[tuple[str, bytes]] | None = None,
        *,
        max_iterations: int = 1,
    ) -> RunRecord:
        run_id = self.claude.new_run_id()
        run_dir = settings.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        uploads_dir = run_dir / "project_uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        file_bytes = project_file_bytes or []
        for name, data in file_bytes:
            (uploads_dir / name).write_bytes(data)

        self.record = RunRecord(
            run_id=run_id,
            run_dir=run_dir,
            project_name=project_name,
            project_text=project_text,
            project_files=project_files,
            max_iterations=max_iterations,
        )
        self.claude_state = self.claude.start_production(
            run_dir,
            file_bytes,
            project_file_names=project_files,
        )
        self.record.append_log(f"Created run {run_id} ({len(file_bytes)} project file(s) uploaded to Anthropic)")
        self._notify()
        return self.record

    def resume_run(self, run_dir: Path) -> RunRecord:
        self.claude_state = ClaudeRunState.load(run_dir)
        self.record = RunRecord(
            run_id=self.claude_state.run_id,
            run_dir=run_dir,
            current_version=self.claude_state.iteration,
            status=RunStatus.IDLE,
        )
        self.record.append_log(f"Resumed run {self.claude_state.run_id}")
        self._notify()
        return self.record

    def run_production(self) -> dict[str, Any]:
        if not self.record or not self.claude_state:
            raise RuntimeError("No active run")

        self.record.status = RunStatus.PRODUCTION
        self.record.append_log("Starting Claude production (3 focused API calls)")
        self._notify()

        try:
            self.record.append_log(f"Call 1/3 — {CALL_NAMES[0]}")
            self._notify()
            self.claude_state, _ = self.claude.run_assessment(self.claude_state)

            self.record.append_log(f"Call 2/3 — {CALL_NAMES[1]}")
            self._notify()
            self.claude_state, _ = self.claude.run_workbook_build(self.claude_state)

            self.record.append_log(f"Call 3/3 — {CALL_NAMES[2]}")
            self._notify()
            self.claude_state, memo_response = self.claude.run_memo_write(self.claude_state)

            artifacts = self.claude.export_artifacts(
                self.claude_state,
                memo_response,
                workbook_file_ids=self.claude_state.workbook_output_file_ids,
            )
            self.record.current_version = self.claude_state.iteration
            self.record.last_artifacts = artifacts
            self.record.status = RunStatus.COMPLETE
            self.record.append_log(
                f"Production complete — v{artifacts['version']}: "
                f"memo={'yes' if artifacts.get('memo_path') else 'no'}, "
                f"workbook={'yes' if artifacts.get('workbook_path') else 'no'}"
            )
            if artifacts.get("warnings"):
                for w in artifacts["warnings"]:
                    self.record.append_log(f"Warning: {w}")
        except Exception as exc:
            self.record.status = RunStatus.ERROR
            self.record.error = str(exc)
            self.record.append_log(f"Production error: {exc}")
            raise
        finally:
            self._notify()

        return self.record.last_artifacts

    def run_review(self) -> dict[str, Any]:
        if not self.record or not self.claude_state:
            raise RuntimeError("No active run")

        version = self.record.current_version or self.claude_state.iteration
        if version < 1:
            raise RuntimeError("No artifacts to review — run production first")

        self.record.status = RunStatus.REVIEW
        self.record.append_log(f"Starting Claude review of v{version}")
        self._notify()

        try:
            review = self.reviewer.review(
                self.record.run_dir,
                version,
                self.record.project_text,
                self.record.project_files,
            )
            self.record.last_review = review
            self.record.reviews_completed += 1
            self.record.status = RunStatus.COMPLETE
            score = review.get("scores", {}).get("overall")
            self.record.append_log(
                f"Review v{version} saved — overall score: {score if score else 'n/a'}"
            )
        except Exception as exc:
            self.record.status = RunStatus.ERROR
            self.record.error = str(exc)
            self.record.append_log(f"Review error: {exc}")
            raise
        finally:
            self._notify()

        return self.record.last_review

    def run_revision(self) -> dict[str, Any]:
        if not self.record or not self.claude_state:
            raise RuntimeError("No active run")
        if not self.record.last_review.get("review_text"):
            raise RuntimeError("No review text — run review first")

        self.record.status = RunStatus.REVISION
        self.record.append_log("Starting Claude revision from review feedback")
        self._notify()

        try:
            self.claude_state, response = self.claude.revise_from_review(
                self.claude_state,
                self.record.last_review["review_text"],
            )
            artifacts = self.claude.export_artifacts(
                self.claude_state,
                response,
                workbook_file_ids=self.claude_state.workbook_output_file_ids,
            )
            self.record.current_version = self.claude_state.iteration
            self.record.last_artifacts = artifacts
            self.record.status = RunStatus.COMPLETE
            self.record.append_log(
                f"Revision complete — v{artifacts['version']}: "
                f"patches applied={artifacts.get('patches_applied', 0)}"
            )
        except Exception as exc:
            self.record.status = RunStatus.ERROR
            self.record.error = str(exc)
            self.record.append_log(f"Revision error: {exc}")
            raise
        finally:
            self._notify()

        return self.record.last_artifacts

    def can_review_again(self) -> bool:
        if not self.record:
            return False
        return self.record.reviews_completed < self.record.max_iterations

    def run_full_loop(self) -> RunRecord:
        """Production → (review → revision) × max_iterations."""
        self.run_production()
        while self.record and self.record.reviews_completed < self.record.max_iterations:
            self.run_review()
            if self.record.reviews_completed < self.record.max_iterations:
                self.run_revision()
        return self.record  # type: ignore[return-value]
