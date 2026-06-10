# BCA Agent

Local harness that replicates a manual USDOT BUILD Benefit-Cost Analysis workflow:

1. **Claude** — single conversation thread, Phases 1–6, produces memo + workbook
2. **Claude (review model)** — independent review on exported files
3. **Claude (production thread)** — revision from pasted review feedback

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add ANTHROPIC_API_KEY to .env
```

Reference files must be in `data/`:

- `guide_memo.pdf`
- `guide_workbook.xlsm`
- `example_memo.pdf`
- `example_workbook.xlsx`

## Run

```bash
streamlit run app.py
```

## Workflow

| Step | Action | Output |
|------|--------|--------|
| 1 | Upload project docs, click **Run Phases 1–6** | `memo_v1.docx`, `workbook_v1.xlsm` |
| 2 | Click **Run Claude Review** | `reviews/review_v1.md` |
| 3 | Click **Revise from Review** | `memo_v2.docx`, `workbook_v2.xlsm` |
| 4 | Repeat review/revise up to `MAX_REVIEW_ITERATIONS` | |

Checkpoints saved under `runs/{run_id}/`:

- `conversation.json` — full message history (resumable)
- `phase_*_response.md` — phase outputs
- `memo_v{n}.docx`, `workbook_v{n}.xlsm`

## Configuration

See `.env.example`. Key settings:

- `MAX_REVIEW_ITERATIONS=1` — first draft only (default)
- `REFERENCE_WORKBOOK_MODE=compact_extract` — labels + formulas, not full TSV dump
- `CLAUDE_MODEL=claude-sonnet-4-6`
- `CLAUDE_REVIEW_MODEL=claude-opus-4-6` (defaults to Opus; production uses `CLAUDE_MODEL`)

## Architecture

- **Files API** — reference PDFs + workbooks + project docs uploaded to Anthropic (not text dumps)
- **Code execution** — Claude opens/edits real spreadsheets in a sandbox (like claude.ai)
- **Workbook output** — downloaded from Claude's code execution output; patch-list is fallback only
- **Claude review** uses a separate model on exported files (not the production thread)
- **Human-in-the-loop** — review and revise are separate button clicks by default
