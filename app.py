"""
BCA Agent — Streamlit UI for conversation-first USDOT BCA workflow.

Run from project root: streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from src.config import settings
from src.document_ingest import ingest_uploaded_files
from src.reference_docs import get_guide_workbook_tabs, list_reference_documents, references_ready
from src.run_manager import BCARunManager, RunStatus

UPLOAD_TYPES = ["pdf", "docx", "doc", "txt", "md", "csv", "xlsx", "xlsm"]


def init_session() -> None:
    defaults = {
        "manager": BCARunManager(on_status=_on_status),
        "run_record": None,
        "project_name": "Unnamed Project",
        "project_text": "",
        "project_files": [],
        "project_file_bytes": [],
        "ingest_warnings": [],
        "max_iterations": 1,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _on_status(record) -> None:
    st.session_state.run_record = record


def _process_uploads(uploaded_files) -> None:
    if not uploaded_files:
        return
    files = [(f.name, f.getvalue()) for f in uploaded_files]
    combined, _records, warnings = ingest_uploaded_files(files)
    if combined:
        st.session_state.project_text = combined
        st.session_state.project_files = [f.name for f in uploaded_files]
        st.session_state.project_file_bytes = files
        if st.session_state.project_name == "Unnamed Project":
            stem = Path(uploaded_files[0].name).stem.replace("_", " ").replace("-", " ")
            st.session_state.project_name = stem.title()
    st.session_state.ingest_warnings = warnings


def _load_howard_county_sample() -> None:
    sample_dir = settings.data_dir / "uploads" / "howard_county_build_application_2026"
    if not sample_dir.exists():
        st.warning(f"Sample not found: {sample_dir}")
        return
    files: list[tuple[str, bytes]] = []
    for path in sorted(sample_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in {f".{t}" for t in UPLOAD_TYPES}:
            files.append((path.name, path.read_bytes()))
    if not files:
        st.warning("No sample files found")
        return
    combined, _, warnings = ingest_uploaded_files(files, max_chars_per_file=200_000, max_chars_total=400_000)
    st.session_state.project_text = combined
    st.session_state.project_files = [n for n, _ in files]
    st.session_state.project_file_bytes = files
    st.session_state.project_name = "Howard County Marriottsville BUILD 2026"
    st.session_state.ingest_warnings = warnings


def render_reference_status() -> None:
    st.subheader("Reference Files")
    docs = list_reference_documents()
    cols = st.columns(2)
    for i, doc in enumerate(docs):
        present = doc["present"] == "true"
        cols[i % 2].markdown(
            f"{'✅' if present else '❌'} **{doc['filename']}**  \n"
            f"<small>{doc['role']}</small>",
            unsafe_allow_html=True,
        )

    tabs = get_guide_workbook_tabs()
    if tabs:
        with st.expander(f"Guide workbook tabs ({len(tabs)})"):
            st.code(", ".join(tabs), language=None)

    if not references_ready():
        st.error("Missing core reference files in data/. Copy guide_memo.pdf and guide_workbook.xlsm.")


def render_run_controls() -> None:
    record = st.session_state.run_record
    manager: BCARunManager = st.session_state.manager

    col1, col2, col3 = st.columns(3)

    with col1:
        has_files = bool(st.session_state.get("project_file_bytes"))
        if st.button("Run Phases 1–6 (Claude)", type="primary", disabled=not has_files):
            manager.create_run(
                st.session_state.project_name,
                st.session_state.project_text,
                st.session_state.project_files,
                st.session_state.get("project_file_bytes", []),
                max_iterations=st.session_state.max_iterations,
            )
            with st.spinner("Claude running Phases 1–6…"):
                try:
                    manager.run_production()
                    st.success("Production complete")
                except Exception as exc:
                    st.error(str(exc))

    with col2:
        can_review = record and record.current_version >= 1
        if st.button("Run Claude Review", disabled=not can_review):
            with st.spinner("Claude reviewing artifacts…"):
                try:
                    manager.run_review()
                    st.success("Review complete")
                except Exception as exc:
                    st.error(str(exc))

    with col3:
        can_revise = record and record.last_review.get("review_text")
        if st.button("Revise from Review (Claude)", disabled=not can_revise):
            with st.spinner("Claude revising…"):
                try:
                    manager.run_revision()
                    st.success("Revision complete")
                except Exception as exc:
                    st.error(str(exc))

    stepped = st.checkbox("Step through phases one at a time", value=False)
    if stepped and st.button("Run next phase only"):
        if not record:
            manager.create_run(
                st.session_state.project_name,
                st.session_state.project_text,
                st.session_state.project_files,
                st.session_state.get("project_file_bytes", []),
                max_iterations=st.session_state.max_iterations,
            )
            record = st.session_state.run_record
        with st.spinner("Running next phase…"):
            try:
                phase = (manager.claude_state.phases_completed if manager.claude_state else 0) + 1
                if phase > 6:
                    st.info("All 6 phases complete")
                else:
                    manager.record.status = RunStatus.PRODUCTION
                    manager.claude_state, response = manager.claude.run_phase_step(
                        manager.claude_state, phase
                    )
                    if phase == 6:
                        manager.record.last_artifacts = manager.claude.export_artifacts(
                            manager.claude_state, response
                        )
                        manager.record.current_version = manager.claude_state.iteration
                        manager.record.status = RunStatus.COMPLETE
                    manager.record.append_log(f"Phase {phase}/6 complete")
                    st.session_state.run_record = manager.record
                    st.success(f"Phase {phase} complete")
            except Exception as exc:
                if manager.record:
                    manager.record.status = RunStatus.ERROR
                    manager.record.error = str(exc)
                st.error(str(exc))


def render_artifacts() -> None:
    record = st.session_state.run_record
    if not record:
        return

    st.subheader("Artifacts")
    artifacts = record.last_artifacts
    if not artifacts:
        st.info("No artifacts yet.")
        return

    cols = st.columns(2)
    if artifacts.get("memo_path"):
        memo_path = Path(artifacts["memo_path"])
        cols[0].markdown(f"**Memo v{artifacts['version']}**")
        if memo_path.exists():
            cols[0].download_button(
                "Download memo (.docx)",
                memo_path.read_bytes(),
                file_name=memo_path.name,
                key=f"dl_memo_{artifacts['version']}",
            )
    if artifacts.get("workbook_path"):
        wb_path = Path(artifacts["workbook_path"])
        cols[1].markdown(f"**Workbook v{artifacts['version']}**")
        if wb_path.exists():
            cols[1].download_button(
                "Download workbook",
                wb_path.read_bytes(),
                file_name=wb_path.name,
                key=f"dl_wb_{artifacts['version']}",
            )

    if artifacts.get("workbook_source"):
        st.caption(f"Workbook source: {artifacts['workbook_source']}")
    if artifacts.get("patches_submitted"):
        st.caption(
            f"Patches (fallback): {artifacts.get('patches_applied', 0)} applied / "
            f"{artifacts.get('patches_submitted', 0)} submitted"
        )
    if artifacts.get("warnings"):
        for w in artifacts["warnings"]:
            st.warning(w)

    if artifacts.get("rejection_details"):
        with st.expander("Rejected patches"):
            st.code("\n".join(artifacts["rejection_details"][:30]))


def render_review() -> None:
    record = st.session_state.run_record
    if not record or not record.last_review:
        return

    st.subheader("Claude Review")
    review = record.last_review
    score = review.get("scores", {}).get("overall")
    if score is not None:
        st.metric("Overall quality", f"{score}/10")

    review_text = review.get("review_text", "")
    st.text_area("Review memo", review_text, height=400, disabled=True)

    if review.get("review_path"):
        st.caption(f"Saved: `{review['review_path']}`")


def render_logs() -> None:
    record = st.session_state.run_record
    if not record:
        return

    st.subheader("Run Log")
    st.caption(f"Run ID: `{record.run_id}` | Status: {record.status.value}")
    if record.run_dir:
        st.caption(f"Checkpoint dir: `{record.run_dir}`")
    if record.log:
        st.code("\n".join(record.log[-50:]), language=None)
    if record.error:
        st.error(record.error)


def main() -> None:
    st.set_page_config(page_title="BCA Agent", layout="wide")
    init_session()

    st.title("BCA Agent")
    st.caption("Conversation-first USDOT BUILD BCA — Claude production, review, and revision")

    with st.sidebar:
        st.header("Settings")
        st.session_state.max_iterations = st.number_input(
            "Max review iterations",
            min_value=1,
            max_value=5,
            value=st.session_state.max_iterations,
            help="1 = first draft only (+ optional single review). 3 = production + 3 review loops.",
        )
        st.text_input("Claude model", value=settings.claude_model, disabled=True)
        st.text_input("Claude review model", value=settings.claude_review_model, disabled=True)
        st.text_input("Workbook mode", value=settings.reference_workbook_mode, disabled=True)

        st.divider()

        uploaded = st.file_uploader(
            "Project documents",
            type=UPLOAD_TYPES,
            accept_multiple_files=True,
        )
        if uploaded:
            _process_uploads(uploaded)

        if st.button("Load Howard County sample"):
            _load_howard_county_sample()

        # After uploads (may auto-set project_name) — widget must come last
        st.text_input("Project name", key="project_name")

        if st.session_state.ingest_warnings:
            st.warning("\n".join(st.session_state.ingest_warnings))

        n_bytes = len(st.session_state.get("project_file_bytes", []))
        if n_bytes:
            st.success(
                f"{n_bytes} file(s) ready for upload "
                f"({len(st.session_state.project_text):,} chars extracted for review context)"
            )

    render_reference_status()
    st.divider()
    render_run_controls()
    st.divider()
    render_artifacts()
    render_review()
    render_logs()


if __name__ == "__main__":
    main()
