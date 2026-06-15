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
        "guideline": "build",
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
    guideline = st.session_state.get("guideline", "build")
    st.subheader("Reference Files")
    docs = list_reference_documents(guideline=guideline)
    cols = st.columns(2)
    for i, doc in enumerate(docs):
        present = doc["present"] == "true"
        cols[i % 2].markdown(
            f"{'✅' if present else '❌'} **{doc['filename']}**  \n"
            f"<small>{doc['role']}</small>",
            unsafe_allow_html=True,
        )

    tabs = get_guide_workbook_tabs(guideline=guideline)
    if tabs:
        with st.expander(f"Guide workbook tabs ({len(tabs)})"):
            st.code(", ".join(tabs), language=None)

    if not references_ready(guideline=guideline):
        if guideline == "bip":
            st.error("Missing BIP reference files in data/bip/. Copy bip_guide.pdf and bip_workbook_example.xlsm.")
        else:
            st.error("Missing core reference files in data/. Copy guide_memo.pdf and guide_workbook.xlsm.")


def render_run_controls() -> None:
    record = st.session_state.run_record
    manager: BCARunManager = st.session_state.manager

    st.subheader("Step 1 — Extract Evidence from Documents")
    st.caption(
        "Claude reads your project documents, extracts every number it can find, "
        "and identifies what data is missing. No assumptions are invented."
    )

    has_files = bool(st.session_state.get("project_file_bytes"))
    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Extract & Identify Gaps",
            type="primary",
            disabled=not has_files,
            help="Run Call 1: extract data from documents and generate the Data Request Sheet",
        ):
            manager.create_run(
                st.session_state.project_name,
                st.session_state.project_text,
                st.session_state.project_files,
                st.session_state.get("project_file_bytes", []),
                max_iterations=st.session_state.max_iterations,
                guideline=st.session_state.get("guideline", "build"),
            )
            with st.spinner("Claude reading documents and identifying missing data…"):
                try:
                    manager.run_assessment()
                    rec = st.session_state.run_record
                    if rec and rec.status == RunStatus.AWAITING_INPUT:
                        st.success("Extraction complete — review the Data Request Sheet below")
                    else:
                        st.success("Extraction complete — no missing data detected")
                except Exception as exc:
                    st.error(str(exc))

    with col2:
        if st.button(
            "Skip Gap-Fill (bypass mode)",
            disabled=not has_files,
            help="Run all 3 calls without pausing for engineer input. Less reliable for USDOT review.",
        ):
            manager.create_run(
                st.session_state.project_name,
                st.session_state.project_text,
                st.session_state.project_files,
                st.session_state.get("project_file_bytes", []),
                max_iterations=st.session_state.max_iterations,
                guideline=st.session_state.get("guideline", "build"),
            )
            with st.spinner("Claude running all 3 phases (bypass mode)…"):
                try:
                    manager.run_production()
                    st.success("Production complete")
                except Exception as exc:
                    st.error(str(exc))

    # Step 2 gap-fill form (shown when assessment is awaiting engineer input)
    record = st.session_state.run_record
    if record and record.status == RunStatus.AWAITING_INPUT:
        render_gap_fill_form(record, manager)
    elif record and record.data_gaps and record.status != RunStatus.AWAITING_INPUT:
        with st.expander("Data Request Sheet (submitted)", expanded=False):
            if record.data_request_sheet:
                st.markdown(record.data_request_sheet)

    # Step 3 review / revision controls
    record = st.session_state.run_record
    if record and record.current_version >= 1:
        st.divider()
        st.subheader("Step 3 — Review & Revision")
        col3, col4 = st.columns(2)

        with col3:
            if st.button("Run Claude Review"):
                with st.spinner("Claude reviewing artifacts…"):
                    try:
                        manager.run_review()
                        st.success("Review complete")
                    except Exception as exc:
                        st.error(str(exc))

        with col4:
            can_revise = record and record.last_review.get("review_text")
            if st.button("Revise from Review (Claude)", disabled=not can_revise):
                with st.spinner("Claude revising…"):
                    try:
                        manager.run_revision()
                        st.success("Revision complete")
                    except Exception as exc:
                        st.error(str(exc))


def render_gap_fill_form(record, manager: BCARunManager) -> None:
    st.divider()
    st.subheader("Step 2 — Engineer Inputs Required")
    st.info(
        "Claude identified the following missing data points. Provide values "
        "from your traffic model outputs, crash database, CMF Clearinghouse, or engineering analysis. "
        "Leave blank if a value is unavailable — it will be noted as missing in the BCA."
    )

    if record.data_request_sheet:
        with st.expander("Data Request Sheet", expanded=True):
            st.markdown(record.data_request_sheet)

    st.markdown("**Enter values below:**")
    engineer_inputs: dict[str, str] = {}

    gaps = record.data_gaps or []
    if not gaps:
        st.warning("No structured gap data — enter values as free text.")
        free_text = st.text_area(
            "Engineer inputs (one per line: 'Input name: value')",
            height=200,
            placeholder="No-build delay (sec/vehicle): 33.8\nBuild delay (sec/vehicle): 33.1\nCMF ID: 7569\nCMF value: 0.712",
        )
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Submit Inputs & Build BCA", type="primary"):
                parsed: dict[str, str] = {}
                for line in free_text.strip().splitlines():
                    if ":" in line:
                        k, _, v = line.partition(":")
                        parsed[k.strip()] = v.strip()
                with st.spinner("Building workbook and writing memo…"):
                    try:
                        manager.submit_engineer_inputs(parsed)
                        st.success("BCA complete")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
        with col_b:
            if st.button("Build BCA Without These Inputs"):
                with st.spinner("Building BCA — missing inputs noted as unavailable…"):
                    try:
                        manager.submit_engineer_inputs({})
                        st.success("BCA complete")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
        return

    RISK_COLORS = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}

    # Sort: Critical driver gaps first, then Critical, then Optional
    def gap_sort_key(g):
        is_driver = g.get("is_benefit_driver", False)
        crit = g.get("criticality", "Critical")
        return (0 if crit == "Critical" and is_driver else 1 if crit == "Critical" else 2)

    sorted_gaps = sorted(gaps, key=gap_sort_key)
    critical_gaps = [g for g in sorted_gaps if g.get("criticality", "Critical") == "Critical"]
    optional_gaps = [g for g in sorted_gaps if g.get("criticality", "Critical") != "Critical"]

    def render_gap_input(gap: dict, key_prefix: str) -> tuple[str, str] | None:
        label = gap.get("item", "Unknown input")
        category = gap.get("category", "")
        risk = gap.get("reviewer_risk", "")
        risk_icon = RISK_COLORS.get(risk, "")
        preferred = gap.get("preferred_for_review", "")
        minimum = gap.get("minimum_acceptable", "")
        source = gap.get("preferred_source", "")

        caption_parts = []
        if category:
            caption_parts.append(f"**{category}**")
        if risk:
            caption_parts.append(f"{risk_icon} Reviewer risk: {risk}")
        if caption_parts:
            st.caption(" · ".join(caption_parts))

        help_lines = []
        if preferred:
            help_lines.append(f"Preferred: {preferred}")
        if minimum and minimum != preferred:
            help_lines.append(f"Minimum acceptable: {minimum}")
        if source:
            help_lines.append(f"Source: {source}")
        help_text = "\n".join(help_lines)

        key = f"{key_prefix}_{label}"
        val = st.text_input(label, key=key, help=help_text or None, placeholder="e.g. 33.8")
        return (label, val.strip()) if val.strip() else None

    if critical_gaps:
        st.markdown("**Critical inputs** — required for the BCA to be calculable")
        for gap in critical_gaps:
            result = render_gap_input(gap, "gap_crit")
            if result:
                engineer_inputs[result[0]] = result[1]

    if optional_gaps:
        with st.expander(f"Optional inputs ({len(optional_gaps)}) — BCA is viable without these"):
            for gap in optional_gaps:
                result = render_gap_input(gap, "gap_opt")
                if result:
                    engineer_inputs[result[0]] = result[1]

    provided = len(engineer_inputs)
    needed = len(critical_gaps)
    if provided < needed:
        st.caption(f"{provided} of {needed} critical inputs filled in")

    col_submit, col_skip = st.columns(2)
    with col_submit:
        if st.button("Submit Inputs & Build BCA", type="primary"):
            with st.spinner("Building workbook and writing memo with your inputs…"):
                try:
                    manager.submit_engineer_inputs(engineer_inputs)
                    st.success("BCA complete")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    with col_skip:
        if st.button("Build BCA Without These Inputs"):
            with st.spinner("Building BCA — missing inputs noted as unavailable…"):
                try:
                    manager.submit_engineer_inputs({})
                    st.success("BCA complete")
                    st.rerun()
                except Exception as exc:
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

    guideline = st.session_state.get("guideline", "build")
    if guideline == "bip":
        st.title("BCA Agent — BIP Bridge Project")
        st.caption("Evidence-first FHWA BIP BCA — Claude extracts data, engineer fills gaps, Claude fills the BIP BCA Tool workbook")
    else:
        st.title("BCA Agent")
        st.caption("Evidence-first USDOT BUILD BCA — Claude extracts data, engineer fills gaps, Claude builds the BCA")

    with st.sidebar:
        st.header("Settings")

        guideline_options = {
            "USDOT BUILD / RAISE / INFRA / MEGA / CRISI": "build",
            "BIP — Bridge Investment Program": "bip",
        }
        selected_label = st.radio(
            "BCA Guideline",
            options=list(guideline_options.keys()),
            index=0 if st.session_state.get("guideline", "build") == "build" else 1,
            help="SELECT before uploading files. Determines which prompts, reference files, and workbook template are used.",
        )
        st.session_state.guideline = guideline_options[selected_label]

        st.divider()

        st.session_state.max_iterations = st.number_input(
            "Max review iterations",
            min_value=1,
            max_value=5,
            value=st.session_state.max_iterations,
            help="1 = first draft only (+ optional single review). 3 = production + 3 review loops.",
        )
        st.text_input("Claude model", value=settings.claude_model, disabled=True)
        st.text_input("Claude review model", value=settings.claude_review_model, disabled=True)
        if st.session_state.guideline == "build":
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
