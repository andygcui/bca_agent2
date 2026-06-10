Write the complete BCA Technical Memorandum for this project.

Use the project specification JSON and verified workbook results below as your data sources. The example memo and USDOT guidance are attached for structure and methodology reference — do NOT copy their values, only their format and narrative approach.

## Memo requirements

- Match ALL numbers precisely to the workbook results.
- Follow USDOT BCA Guidance methodology for discounting, benefit categories, and reporting.
- Do NOT monetize CO₂ per current USDOT/EO guidance.
- Report BCR and NPV at 7% discount rate. Include 3% if computed.
- Sensitivity analysis section must test the top 2–3 most influential assumptions.

## Required sections (follow example_memo.pdf structure)

1. Executive Summary — BCR, NPV, brief project description, key findings (1 page max)
2. Project Description — baseline vs. build, location, sponsor, grant program
3. Methodology — discount rate, analysis period, base year, benefit categories included/excluded with justification
4. Benefit Quantification — one subsection per applicable benefit category with formulas, inputs, and results
5. Cost Estimation — capital costs by year, O&M, present value of total costs
6. Benefit-Cost Results — BCR and NPV table, comparison summary
7. Sensitivity Analysis — BCR/NPV under alternative assumptions (table format)
8. Conclusion — summary of findings, limitations, items requiring follow-up

## Output

Place the COMPLETE memo between these exact markers (do not truncate):

--- MEMO START ---
[full memo in markdown — include all sections, tables, and numbers]
--- MEMO END ---

Then output a brief completion summary:
- BCR (7%): [value]
- NPV (7%, $M): [value]
- Top 3 assumptions the BCR is sensitive to
- Any data gaps or items requiring human follow-up

## Project specification

```json
{project_spec}
```

## Verified workbook results

{workbook_results}
