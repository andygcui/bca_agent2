I have uploaded several documents for a USDOT discretionary grant Benefit-Cost Analysis (BCA). The reference PDFs, template workbooks, and project application files are **attached to this message** — open and read them directly.

Please work through the following phases **in order** in this conversation. Complete each phase before moving to the next.

## Attached files

**USDOT references (authoritative):**
- `guide_memo.pdf` — USDOT BCA Guidance (December 2025)
- `guide_workbook.xlsm` — USDOT BCA Excel template (formulas and structure)

**Style references only (do NOT copy values):**
- `example_memo.pdf` — memo structure and narrative depth
- `example_workbook.xlsx` — highway workbook layout (use as base for highway/capacity projects)

**Project application materials** — authoritative source of project facts. Do not invent facts absent from these documents.

---

## Governing rules

- Follow `guide_memo.pdf` for methodology, benefit/cost categories, discounting, and reporting.
- **Workbook:** Use **code execution** to open the attached template files. For highway/capacity projects (like bridge/road widening), start from `example_workbook.xlsx` as the base and align methodology with `guide_memo.pdf`. For rail/freight projects, start from `guide_workbook.xlsm`.
- **Preserve formulas.** Only write to input cells. Do not overwrite cells that contain formulas unless you are intentionally replacing a formula with a new formula.
- Use `example_memo.pdf` for memo structure only.
- Do **not** monetize CO₂ per current USDOT/EO guidance.
- Real discount rate: 7.0% unless project documents specify otherwise.
- Base year: 2024 constant dollars unless project documents specify otherwise.

**If using guide_workbook.xlsm, tab names (exact spelling only):**
{valid_tabs}

---

## Phase 1 — Project Assessment

Assess the project from the attached application files:
- Project scope, sponsor, location, grant program
- Baseline vs. build alternative
- Applicable benefit and cost categories
- Critical missing information and key assumptions
- Which workbook template applies (highway vs. rail)

---

## Phase 2 — Design Complete BCA Workbook

Using code execution, open the appropriate template workbook and plan:
- Which tabs apply to this project
- Input cells to populate (do not break existing formulas)
- Assumptions and data sources for each input
- Target: >80% of relevant input cells populated or documented

---

## Phase 3 — Prepare BCA Technical Memorandum

Draft the full BCA Technical Memorandum following `example_memo.pdf` structure.

---

## Phase 4 — Perform Benefit-Cost Analysis

Populate the workbook via code execution. Ensure memo numbers match workbook results.

---

## Phase 5 — Sensitivity Analysis

Test influential assumptions. Report BCR/NPV under alternative scenarios.

---

## Phase 6 — Quality Review (self-review)

Internal quality check: methodology compliance, memo-workbook consistency, auditability.

---

## Final deliverables

### 1. BCA Workbook (via code execution — PRIMARY)

Use code execution to save the completed workbook file:
- Filename: `workbook_v1.xlsx` (or `.xlsm` if macros required)
- Copy from the appropriate template; preserve all formulas
- Populate input cells only
- The harness will download this file from your code execution output

### 2. BCA Technical Memorandum (in your text response)

Place the **complete memo** between:

--- MEMO START ---
[full memo in markdown]
--- MEMO END ---

### 3. Brief completion summary

BCR, NPV, key assumptions, and items needing human follow-up.

**Do NOT** output a giant TSV or hundreds of `Sheet!Cell=value` patch lines unless code execution fails and you cannot save a file.
