Read all attached USDOT reference files and project application documents carefully and thoroughly.

Your task is to produce a structured BCA specification by reasoning from the project's characteristics — not by filling in a generic template. The workbook-building step and memo-writing step work entirely from this JSON, so extract every number and never invent a value.

**Read every page of every document.** Look for:
- Traffic counts (AADT, peak hour, seasonal, by direction, by year)
- Crash histories (every year reported, by severity, by location)
- Cost breakdowns (by category, by year, federal vs. non-federal)
- Engineering estimates (dimensions, capacities, design-life years)
- Risk/resilience data (flood return periods, closure frequencies, detour distances)
- Any quantitative table in any appendix or exhibit

---

## CRITICAL RULE — Never invent project-specific values

**Do NOT estimate, assume, or invent any value not found in the uploaded documents.**

If a required variable is missing, set it to `null` and add it to `data_gaps`. A `null` is honest and defensible. An invented number looks plausible but will be challenged by a USDOT reviewer and can invalidate the BCA.

Source classification — label every extracted value with exactly one:
- `"Project Data"` — found explicitly in the uploaded project documents
- `"Engineering Analysis"` — from a model output (HCM, Synchro, VISSIM, travel demand model) cited in the documents
- `"Literature Source"` — from CMF Clearinghouse, USDOT BCA guidance, FHWA unit cost tables, EPA MOVES, or another named external database
- `"Analyst Judgment"` — Claude is inferring this; not found in documents

Minimize `"Analyst Judgment"`. Flag every one explicitly.

---

## Reasoning framework

For each benefit and cost category that could apply to this project, reason through the following steps before writing a single number:

**Step 1 — Does this category apply?**
Based on the project description, decide whether this category is relevant. Be conservative — only claim a category if the project characteristics clearly support it. A bridge rehabilitation without load-posting history probably has no VOC detour benefit. An intersection capacity project likely has travel time savings but not resilience benefits unless flooding is mentioned.

**Step 2 — What methodology fits this project?**
Select the specific calculation approach appropriate for this project type and the evidence likely available:
- Travel Time: Rule-of-half from capacity model delay outputs? Direct speed/distance from a traffic study? Pick the method that matches what engineering analysis was done for this project.
- Safety: CMF method (treatment applied to a segment or intersection, CMF from CMF Clearinghouse)? Before/after if a completed project? What crash types and facility type does the CMF need to match?
- VOC: Avoided load-posting truck detour? Reduced idling from congestion? Reduced grade/curvature? Pick the mechanism the project description actually supports.
- Resilience: Expected annual avoided closures × detour cost? Return-period event framework? Only if the project addresses a documented vulnerability.

**Step 3 — What variables does that methodology require?**
List every input variable needed to perform the calculation. Be specific — not "traffic data" but "annual AADT by year 2025–2047" or "no-build average intersection delay (sec/vehicle) for the design year from the capacity analysis."

**Step 4 — Extract from documents**
Search every uploaded file for each required variable. Record the exact value, source document, and page/table/exhibit number.

**Step 5 — Flag every missing variable**
Any required variable not found in the documents goes into `data_gaps` with the preferred source for an engineer to consult. Do not substitute an assumption. If you cannot calculate a category because of missing variables, say so explicitly.

**Step 6 — Can this category be calculated?**
Set `"can_calculate": true` only if every required variable is found with `Project Data`, `Engineering Analysis`, or `Literature Source` classification. If any required variable is `null`, set `"can_calculate": false` and `"estimated_annual_benefit_M": 0.0`.

---

## Output format

1. Output the JSON inside a ```json code fence.
2. Write a plain-text summary (3–5 sentences: project type, applicable benefit categories, template choice, estimated BCR range only if any categories are fully calculable).
3. Output the Data Request Sheet between these exact markers:

--- DATA REQUEST SHEET START ---
[markdown table]
--- DATA REQUEST SHEET END ---

---

## JSON schema

```json
{
  "project": {
    "name": "string",
    "sponsor": "string",
    "location": "string — city, county, state",
    "grant_program": "BUILD | RAISE | INFRA | MEGA | CRISI | BIP | other",
    "grant_amount_requested_M": 0.0,
    "total_project_cost_M": 0.0,
    "project_type": "highway | bridge | rail | transit | port | other",
    "workbook_template": "example_workbook.xlsx | guide_workbook.xlsm",
    "description": "2–3 sentence project description",
    "baseline_description": "what exists today — include condition ratings, deficiency details",
    "build_description": "what the project builds and why it solves each deficiency"
  },
  "economics": {
    "base_year": 2024,
    "analysis_period_years": 20,
    "discount_rate": 0.07,
    "construction_start_year": 2025,
    "construction_schedule": {"2025": 0.0, "2026": 0.0},
    "annual_om_cost_M": 0.0,
    "om_cost_notes": "string"
  },
  "costs": {
    "capital_cost_total_M": 0.0,
    "capital_cost_breakdown": {"category": 0.0},
    "federal_share_M": 0.0,
    "non_federal_share_M": 0.0,
    "annual_om_M": 0.0,
    "om_escalation_pct": 0.0,
    "residual_value_M": 0.0,
    "residual_value_basis": "string"
  },
  "baseline_traffic": {
    "aadt": null,
    "aadt_source": "string or null",
    "aadt_classification": "Project Data | Engineering Analysis | Literature Source | Analyst Judgment",
    "aadt_by_year": {},
    "growth_rate_pct": null,
    "growth_rate_source": "string or null",
    "truck_pct": null,
    "truck_pct_source": "string or null"
  },
  "benefit_analyses": [
    {
      "category": "Travel Time Savings | Vehicle Operating Cost | Safety | Emissions | Freight Reliability | Resilience | Noise | other",
      "applicable": true,
      "rationale": "why this category applies to this specific project",
      "methodology": "the specific calculation methodology selected for this project type and why",
      "required_variables": [
        {
          "variable": "human-readable variable name",
          "description": "what this is and why the methodology needs it",
          "found": false,
          "value": null,
          "source_citation": "document name and section/page/exhibit, or null",
          "classification": "Project Data | Engineering Analysis | Literature Source | Analyst Judgment"
        }
      ],
      "can_calculate": false,
      "estimated_annual_benefit_M": 0.0,
      "calculation_sketch": "formula with actual values substituted if can_calculate=true, otherwise null"
    }
  ],
  "raw_quantitative_data": {
    "description": "All quantitative data from the documents that does not fit the schema above. Include exact figures with units and source.",
    "items": [
      {"field": "string", "value": "exact value with units", "source": "document and page/exhibit"}
    ]
  },
  "data_gaps": [
    {
      "item": "exact variable name, e.g. 'No-build average intersection delay (sec/vehicle), design year 2028'",
      "category": "which benefit category this blocks",
      "why_needed": "its specific role in the calculation — e.g. 'denominator in rule-of-half travel time calculation'",
      "preferred_source": "where an engineer should obtain this — e.g. 'Synchro/HCM intersection analysis output for no-build scenario', 'CMF Clearinghouse search by treatment type and facility type', 'FEMA 100-year flood frequency data'",
      "required": true,
      "input_type": "number | text | percent | years | table"
    }
  ]
}
```

---

## Data Request Sheet format

After the JSON, output a markdown table between the markers. List only variables that are `null` — things the engineer must look up from a model, database, or field study. Required items first.

| # | Input Needed | Benefit Category | Why Needed | Where to Get It | Required? |
|---|-------------|-----------------|-----------|----------------|-----------|

---

## Rules

- **Never invent a project-specific value.** Missing → `null` + row in `data_gaps` + row in Data Request Sheet.
- Classify every `required_variables[].classification`.
- Set `can_calculate: false` and `estimated_annual_benefit_M: 0.0` for any category with null required variables.
- Only include benefit categories this project's characteristics actually support.
- `"workbook_template"`: highway/bridge/road/capacity → `"example_workbook.xlsx"`; rail/transit/freight → `"guide_workbook.xlsm"`.
- Do NOT monetize CO₂ per current USDOT/EO guidance.
- Discount rate: 7.0% unless project documents specify otherwise.
- Base year: 2024 constant dollars unless project documents specify otherwise.
- All dollar values in millions (M). Rates as decimals (0.07 = 7%).
- Capture everything in `raw_quantitative_data` that doesn't fit the schema above.
