Write the complete BCA Technical Memorandum for this BIP Bridge Project grant application.

## Engineer-provided inputs

{engineer_inputs}

Use the project specification JSON, engineer-provided inputs, and workbook results below as your data sources. The BIP guide is attached for methodology reference.

## Memo requirements

- Match ALL numbers precisely to the workbook results (or the spec if workbook results are pending).
- Follow USDOT BCA Guidance (December 2025) methodology for discounting, benefit categories, and reporting.
- Report BCR and NPV at 7% discount rate. Include 3% if computed.
- Sensitivity analysis section must test the top 2–3 most influential assumptions.
- Discount rate: 7.0%. Base year: 2024 constant dollars.
- If BCR is listed as "pending Excel verification" in the workbook results, use the approximate value and note that it should be verified in the BIP BCA Tool workbook.

## Required sections

1. **Executive Summary** — BCR, NPV, bridge identification (State/County/Structure #), key findings, benefit categories included (1 page max)
2. **Project Description** — baseline bridge condition (NBI rating, deficiencies, load posting/closure history), build scenario, location, sponsor, grant program (BIP Bridge or Large Bridge)
3. **Methodology** — BIP BCA Tool v1.1.2, USDOT BCA Guidance Dec 2025, discount rate, analysis period, base year, benefit categories included/excluded with justification for each
4. **Benefit Quantification** — one subsection per applicable benefit category:
   - Bridge Condition & Closure Avoidance (if applicable): NBIAS forecast basis, load posting restrictions, closure year, annual vehicle-hours saved
   - Safety (if applicable): historical crash data, crash reduction methodology, CMF applied (if any), annual crash cost savings
   - Travel Time (if applicable): improvement description, methodology, annual time savings
   - Resilience (if applicable): event type, annual probability, damage avoided
   - Construction Disbenefits: traffic management plan, delay costs during construction (these are costs, not benefits — subtract from benefits)
   - Any other applicable categories
5. **Cost Estimation** — capital costs by year (discounted to 2024$), O&M cost difference, already-incurred costs (if any), residual value
6. **Benefit-Cost Results** — BCR and NPV table; note that definitive BCR comes from BIP BCA Tool workbook
7. **Sensitivity Analysis** — BCR/NPV under alternative assumptions for top 2–3 variables (table format)
8. **Conclusion** — summary of findings, confidence in results, items requiring follow-up or engineer verification

## Output

Place the COMPLETE memo between these exact markers (do not truncate):

--- MEMO START ---
[full memo in markdown — include all sections, tables, and numbers]
--- MEMO END ---

Then output a brief completion summary:
- BCR (7%): [value or "pending Excel verification"]
- NPV (7%, $M): [value]
- Top 3 assumptions the BCR is sensitive to
- Any data gaps or items requiring human follow-up
- Reminder: open the BIP BCA Tool workbook in Excel to obtain the definitive BCR from the Results tab

## Project specification

```json
{project_spec}
```

## Workbook results

{workbook_results}
