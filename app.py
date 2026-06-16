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

_CSS = """
<style>
/* ── Layout ── */
.main .block-container { padding-top: 2rem; padding-bottom: 3rem; }

/* ── Typography ── */
h1 { font-size: 1.75rem !important; font-weight: 700 !important; letter-spacing: -0.02em !important; }
h2 { font-size: 1.15rem !important; font-weight: 600 !important; margin-top: 0 !important; }
h3 { font-size: 1rem !important; font-weight: 600 !important; }

/* ── Divider ── */
hr { margin: 1.5rem 0 !important; border-color: #E5E9F0 !important; }

/* ── Workflow tracker ── */
.wf-tracker {
    display: flex;
    align-items: center;
    background: #F4F6F9;
    border: 1px solid #E5E9F0;
    border-radius: 10px;
    padding: 1.1rem 2rem;
    margin-bottom: 2rem;
    gap: 0;
}
.wf-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    gap: 0.4rem;
}
.wf-icon {
    width: 38px; height: 38px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; font-weight: 700;
    border: 2px solid;
}
.wf-icon.pending  { background:#EEF1F5; border-color:#CBD5E1; color:#94A3B8; }
.wf-icon.active   { background:#1A56A0; border-color:#1A56A0; color:#fff; }
.wf-icon.done     { background:#DCFCE7; border-color:#16A34A; color:#16A34A; }
.wf-label {
    font-size: 0.72rem; font-weight: 600; text-align: center;
    line-height: 1.3; color: #64748B;
}
.wf-label.active { color: #1A56A0; }
.wf-label.done   { color: #16A34A; }
.wf-connector { flex: 0.3; height: 2px; background: #CBD5E1; margin-bottom: 1.4rem; }
.wf-connector.done { background: #16A34A; }

/* ── Section card ── */
.section-card {
    background: #F8FAFC;
    border: 1px solid #E5E9F0;
    border-radius: 10px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1.5rem;
}

/* ── Landing ── */
.landing-hero {
    background: linear-gradient(135deg, #EEF4FF 0%, #F8FAFC 100%);
    border: 1px solid #C7D9F5;
    border-radius: 12px;
    padding: 3rem 2.5rem;
    text-align: center;
    margin: 1.5rem 0 2rem 0;
}
.landing-hero h2 { font-size: 1.4rem !important; color: #1A1F36 !important; margin-bottom: 0.5rem !important; }
.landing-hero p  { color: #4A5568; font-size: 0.95rem; max-width: 560px; margin: 0 auto 1.5rem; }

/* ── Step badge ── */
.step-badge {
    display: inline-flex; align-items: center; justify-content: center;
    width: 24px; height: 24px; border-radius: 50%;
    background: #1A56A0; color: #fff;
    font-size: 0.75rem; font-weight: 700;
    margin-right: 0.5rem; vertical-align: middle;
}
.step-badge.done { background: #16A34A; }

/* ── How-it-works steps (landing) ── */
.how-step {
    background: #fff;
    border: 1px solid #E5E9F0;
    border-radius: 8px;
    padding: 1rem 1.25rem;
}
.how-step-num {
    font-size: 1.5rem; font-weight: 800; color: #1A56A0;
    line-height: 1; margin-bottom: 0.3rem;
}
.how-step-title { font-size: 0.85rem; font-weight: 700; color: #1A1F36; margin-bottom: 0.2rem; }
.how-step-desc  { font-size: 0.78rem; color: #64748B; line-height: 1.4; }

/* ── Artifact cards ── */
.artifact-card {
    background: #F8FAFC;
    border: 1px solid #E5E9F0;
    border-radius: 8px;
    padding: 1.1rem 1.25rem;
}

/* ── Sidebar section labels ── */
.sidebar-label {
    font-size: 0.65rem; font-weight: 700;
    letter-spacing: 0.09em; text-transform: uppercase;
    color: #94A3B8; margin: 1rem 0 0.35rem 0;
}

/* ── Status pill ── */
.status-pill {
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 99px;
    font-size: 0.7rem; font-weight: 600;
    letter-spacing: 0.03em;
}
.status-pill.running  { background:#DBEAFE; color:#1D4ED8; }
.status-pill.done     { background:#DCFCE7; color:#15803D; }
.status-pill.waiting  { background:#FEF9C3; color:#854D0E; }
.status-pill.error    { background:#FEE2E2; color:#B91C1C; }
</style>
"""

GUIDELINE_LABELS = {
    "USDOT BUILD / RAISE / INFRA / MEGA / CRISI": "build",
    "BIP — Bridge Investment Program": "bip",
}


# ── Session ────────────────────────────────────────────────────────────────

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


# ── File helpers ────────────────────────────────────────────────────────────

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


# ── Sidebar ─────────────────────────────────────────────────────────────────

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## BCA builder")
        st.caption("USDOT Grant Benefit-Cost Analysis")

        st.divider()

        # ── Project files ──
        st.markdown('<div class="sidebar-label">Project Documents</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Upload files",
            type=UPLOAD_TYPES,
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        if uploaded:
            _process_uploads(uploaded)

        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.text_input("Project name", key="project_name", label_visibility="collapsed",
                          placeholder="Project name")
        with col_b:
            if st.button("Sample", help="Load Howard County BUILD 2026 sample project", use_container_width=True):
                _load_howard_county_sample()
                st.rerun()

        if st.session_state.ingest_warnings:
            st.warning("\n".join(st.session_state.ingest_warnings))

        n_files = len(st.session_state.get("project_file_bytes", []))
        if n_files:
            n_chars = len(st.session_state.project_text)
            st.success(f"{n_files} file{'s' if n_files != 1 else ''} loaded · {n_chars:,} chars")

        st.divider()

        # ── BCA Guideline ──
        st.markdown('<div class="sidebar-label">BCA Guideline</div>', unsafe_allow_html=True)
        selected_label = st.radio(
            "BCA Guideline",
            options=list(GUIDELINE_LABELS.keys()),
            index=0 if st.session_state.get("guideline", "build") == "build" else 1,
            help="Select before uploading files. Determines prompts, reference files, and workbook template.",
            label_visibility="collapsed",
        )
        st.session_state.guideline = GUIDELINE_LABELS[selected_label]

        # ── Advanced settings ──
        with st.expander("Advanced settings"):
            st.session_state.max_iterations = st.number_input(
                "Max review iterations",
                min_value=1, max_value=5,
                value=st.session_state.max_iterations,
                help="1 = first draft only. 3 = production + 3 review loops.",
            )
            st.text_input("Claude model", value=settings.claude_model, disabled=True)
            st.text_input("Review model", value=settings.claude_review_model, disabled=True)
            if st.session_state.guideline == "build":
                st.text_input("Workbook mode", value=settings.reference_workbook_mode, disabled=True)

        # ── Reference files ──
        guideline = st.session_state.get("guideline", "build")
        docs = list_reference_documents(guideline=guideline)
        ready = references_ready(guideline=guideline)
        tabs = get_guide_workbook_tabs(guideline=guideline)

        with st.expander(f"{'✓' if ready else '☐'} Reference files", expanded=not ready):
            cols = st.columns(2)
            for i, doc in enumerate(docs):
                present = doc["present"] == "true"
                cols[i % 2].markdown(
                    f"{'✓' if present else '✗'} **{doc['filename']}**  \n"
                    f"<small>{doc['role']}</small>",
                    unsafe_allow_html=True,
                )
            if tabs:
                st.caption(f"Tabs: {', '.join(tabs[:4])}{'…' if len(tabs) > 4 else ''}")
            if not ready:
                if guideline == "bip":
                    st.error("Add bip_guide.pdf and bip_workbook_example.xlsm to data/bip/")
                else:
                    st.error("Add guide_memo.pdf and guide_workbook.xlsm to data/")


# ── Workflow tracker ─────────────────────────────────────────────────────────

def render_workflow_tracker() -> None:
    record = st.session_state.run_record

    step1_done = bool(record and record.data_gaps is not None)
    step2_active = bool(record and record.status == RunStatus.AWAITING_INPUT)
    step2_done = bool(record and record.status != RunStatus.AWAITING_INPUT and record.current_version >= 1)
    step3_done = bool(record and record.last_artifacts)
    step3_active = bool(record and record.current_version >= 1 and not step3_done)

    def cls(done: bool, active: bool) -> str:
        if done: return "done"
        if active: return "active"
        return "pending"

    s1 = cls(step1_done, not step1_done)
    s2 = cls(step2_done, step2_active)
    s3 = cls(step3_done, step3_active)
    c1 = "done" if step1_done else ""
    c2 = "done" if step2_done else ""

    icons = {"done": "✓", "active": "●", "pending": "○"}

    st.markdown(f"""
<div class="wf-tracker">
  <div class="wf-step">
    <div class="wf-icon {s1}">{icons[s1]}</div>
    <div class="wf-label {s1}">Extract<br>Evidence</div>
  </div>
  <div class="wf-connector {c1}"></div>
  <div class="wf-step">
    <div class="wf-icon {s2}">{icons[s2]}</div>
    <div class="wf-label {s2}">Engineer<br>Inputs</div>
  </div>
  <div class="wf-connector {c2}"></div>
  <div class="wf-step">
    <div class="wf-icon {s3}">{icons[s3]}</div>
    <div class="wf-label {s3}">Build<br>BCA</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Landing (no project loaded) ──────────────────────────────────────────────

def render_landing() -> None:
    st.markdown("""
<div class="landing-hero">
  <h2>Evidence-First Benefit-Cost Analysis</h2>
  <p>Upload your project application documents and our agent will extract every data point,
  identify what's missing, collect engineer inputs, and produce a USDOT-ready BCA memo
  and workbook — without inventing numbers.</p>
</div>
""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
<div class="how-step">
  <div class="how-step-num">01</div>
  <div class="how-step-title">Extract Evidence</div>
  <div class="how-step-desc">Claude reads your documents and extracts every number it finds.
  No assumptions are made for missing data.</div>
</div>
""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
<div class="how-step">
  <div class="how-step-num">02</div>
  <div class="how-step-title">Fill Data Gaps</div>
  <div class="how-step-desc">A structured Data Request Sheet lists what's missing.
  You supply values from your traffic model, crash database, or CMF Clearinghouse.</div>
</div>
""", unsafe_allow_html=True)
    with c3:
        st.markdown("""
<div class="how-step">
  <div class="how-step-num">03</div>
  <div class="how-step-title">Build the BCA</div>
  <div class="how-step-desc">Claude populates the official workbook and writes a
  USDOT-formatted BCA memo ready for grant submission.</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.info("Upload your project documents in the sidebar to get started, or click **Sample** to try a demo project.")


# ── Step 1 / 2 controls ──────────────────────────────────────────────────────

def render_run_controls() -> None:
    record = st.session_state.run_record
    manager: BCARunManager = st.session_state.manager

    # ── Step 1 ──
    st.markdown("#### Step 1 — Extract Evidence from Documents")
    st.caption(
        "Claude reads your project documents, extracts every number it can find, "
        "and identifies what data is missing. No assumptions are invented."
    )

    has_files = bool(st.session_state.get("project_file_bytes"))
    col1, col2 = st.columns([2, 1])

    with col1:
        if st.button(
            "Extract & Identify Gaps",
            type="primary",
            disabled=not has_files,
            help="Run Call 1: extract data from documents and generate the Data Request Sheet",
            use_container_width=True,
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
            "Bypass (skip gap-fill)",
            disabled=not has_files,
            help="Run all 3 calls without pausing for engineer input. Less reliable for USDOT review.",
            use_container_width=True,
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

    # ── Step 2 gap-fill (shown when assessment is awaiting engineer input) ──
    record = st.session_state.run_record
    if record and record.status == RunStatus.AWAITING_INPUT:
        render_gap_fill_form(record, manager)
    elif record and record.data_gaps and record.status != RunStatus.AWAITING_INPUT:
        with st.expander("Data Request Sheet (submitted)", expanded=False):
            if record.data_request_sheet:
                st.markdown(record.data_request_sheet)

    # ── Step 3 review / revision ──
    record = st.session_state.run_record
    if record and record.current_version >= 1:
        st.divider()
        st.markdown("#### Step 3 — Review & Revision")
        col3, col4 = st.columns(2)

        with col3:
            if st.button("Run Claude Review", use_container_width=True):
                with st.spinner("Claude reviewing artifacts…"):
                    try:
                        manager.run_review()
                        st.success("Review complete")
                    except Exception as exc:
                        st.error(str(exc))

        with col4:
            can_revise = record and record.last_review.get("review_text")
            if st.button("Revise from Review", disabled=not can_revise, use_container_width=True):
                with st.spinner("Claude revising…"):
                    try:
                        manager.run_revision()
                        st.success("Revision complete")
                    except Exception as exc:
                        st.error(str(exc))


# ── Step 2 gap-fill form ─────────────────────────────────────────────────────

def render_gap_fill_form(record, manager: BCARunManager) -> None:
    st.divider()
    st.markdown("#### Step 2 — Engineer Inputs Required")
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
            if st.button("Submit Inputs & Build BCA", type="primary", use_container_width=True):
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
            if st.button("Build BCA Without These Inputs", use_container_width=True):
                with st.spinner("Building BCA — missing inputs noted as unavailable…"):
                    try:
                        manager.submit_engineer_inputs({})
                        st.success("BCA complete")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
        return

    RISK_COLORS = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}

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

        key = f"{key_prefix}_{label}"
        val = st.text_input(label, key=key, help="\n".join(help_lines) or None, placeholder="e.g. 33.8")
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
        if st.button("Submit Inputs & Build BCA", type="primary", use_container_width=True):
            with st.spinner("Building workbook and writing memo with your inputs…"):
                try:
                    manager.submit_engineer_inputs(engineer_inputs)
                    st.success("BCA complete")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    with col_skip:
        if st.button("Build BCA Without These Inputs", use_container_width=True):
            with st.spinner("Building BCA — missing inputs noted as unavailable…"):
                try:
                    manager.submit_engineer_inputs({})
                    st.success("BCA complete")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


# ── Artifacts ────────────────────────────────────────────────────────────────

def render_artifacts() -> None:
    record = st.session_state.run_record
    if not record:
        return

    artifacts = record.last_artifacts
    if not artifacts:
        return

    st.divider()
    st.markdown("#### Deliverables")

    cols = st.columns(2)

    with cols[0]:
        st.markdown('<div class="artifact-card">', unsafe_allow_html=True)
        st.markdown(f"**BCA Memo** · v{artifacts.get('version', '—')}")
        if artifacts.get("memo_path"):
            memo_path = Path(artifacts["memo_path"])
            if memo_path.exists():
                st.download_button(
                    "Download memo (.docx)",
                    memo_path.read_bytes(),
                    file_name=memo_path.name,
                    key=f"dl_memo_{artifacts['version']}",
                    use_container_width=True,
                )
            else:
                st.caption("File not found on disk")
        st.markdown("</div>", unsafe_allow_html=True)

    with cols[1]:
        st.markdown('<div class="artifact-card">', unsafe_allow_html=True)
        st.markdown(f"**BCA Workbook** · v{artifacts.get('version', '—')}")
        if artifacts.get("workbook_path"):
            wb_path = Path(artifacts["workbook_path"])
            if wb_path.exists():
                st.download_button(
                    "Download workbook (.xlsm)",
                    wb_path.read_bytes(),
                    file_name=wb_path.name,
                    key=f"dl_wb_{artifacts['version']}",
                    use_container_width=True,
                )
            else:
                st.caption("File not found on disk")
        st.markdown("</div>", unsafe_allow_html=True)

    if artifacts.get("workbook_source"):
        st.caption(f"Workbook source: {artifacts['workbook_source']}")
    if artifacts.get("patches_submitted"):
        st.caption(
            f"Patches: {artifacts.get('patches_applied', 0)} applied / "
            f"{artifacts.get('patches_submitted', 0)} submitted"
        )
    if artifacts.get("warnings"):
        for w in artifacts["warnings"]:
            st.warning(w)
    if artifacts.get("rejection_details"):
        with st.expander("Rejected patches"):
            st.code("\n".join(artifacts["rejection_details"][:30]))


# ── Review ───────────────────────────────────────────────────────────────────

def render_review() -> None:
    record = st.session_state.run_record
    if not record or not record.last_review:
        return

    review = record.last_review
    review_text = review.get("review_text", "")
    if not review_text:
        return

    st.divider()
    st.markdown("#### Claude Review")

    score = review.get("scores", {}).get("overall")
    if score is not None:
        st.metric("Overall quality score", f"{score} / 10")

    st.text_area("Review memo", review_text, height=400, disabled=True)

    if review.get("review_path"):
        st.caption(f"Saved: `{review['review_path']}`")


# ── Run log ──────────────────────────────────────────────────────────────────

def render_logs() -> None:
    record = st.session_state.run_record
    if not record:
        return

    status_class = {
        RunStatus.RUNNING: "running",
        RunStatus.AWAITING_INPUT: "waiting",
        RunStatus.COMPLETE: "done",
        RunStatus.ERROR: "error",
    }.get(record.status, "done")

    with st.expander("Run log", expanded=bool(record.error)):
        st.markdown(
            f'<span class="status-pill {status_class}">{record.status.value}</span>'
            f'&nbsp; Run ID: <code>{record.run_id}</code>',
            unsafe_allow_html=True,
        )
        if record.run_dir:
            st.caption(f"Checkpoint: `{record.run_dir}`")
        if record.log:
            st.code("\n".join(record.log[-50:]), language=None)
        if record.error:
            st.error(record.error)


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    guideline_key = "guideline"

    st.set_page_config(
        page_title="BCA Agent — USDOT Grant BCA Tool",
        page_icon="📊",
        layout="wide",
    )
    st.markdown(_CSS, unsafe_allow_html=True)
    init_session()

    render_sidebar()

    guideline = st.session_state.get(guideline_key, "build")
    if guideline == "bip":
        st.title("Benefit Cost Analysis Builder")
        st.caption("Evidence-first FHWA BIP Bridge Investment Program BCA")
    else:
        st.title("Benefit Cost Analysis Builder")
        st.caption("Evidence-first USDOT BUILD / RAISE / INFRA / MEGA / CRISI Benefit-Cost Analysis")

    has_files = bool(st.session_state.get("project_file_bytes"))

    if not has_files:
        render_landing()
    else:
        render_workflow_tracker()
        render_run_controls()
        render_artifacts()
        render_review()
        render_logs()


if __name__ == "__main__":
    main()
