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

If a required variable is missing from documents, set it to `null` and add it to `data_gaps`. A `null` is honest and defensible. An invented number looks plausible but will be challenged by a USDOT reviewer and can invalidate the BCA.

Source classification — label every value with exactly one:
- `"Project Data"` — found explicitly in the uploaded project documents
- `"Engineering Analysis"` — from a model output (HCM, Synchro, VISSIM, travel demand model) cited in the documents
- `"Literature Source"` — from a named standard reference: USDOT BCA guidance, FHWA crash unit costs, USDOT Value of Time tables, EPA MOVES emissions factors, CMF Clearinghouse. These are always available and do not need to come from project documents.
- `"Analyst Judgment"` — Claude is inferring this; not found in documents and not from a standard reference

Minimize `"Analyst Judgment"`. Flag every one explicitly.

---

## Reasoning framework — follow these steps in order

**Step 0 — Classify the project**
Before evaluating any benefit category, identify what this project actually does at an engineering level. Record `project_classification` with:
- `engineering_scope`: what physical work is being done (e.g. "bridge superstructure replacement and approach road widening", "signalized intersection capacity expansion", "new BRT corridor with dedicated lanes")
- `primary_mechanisms`: the specific mechanisms by which this project could generate economic benefits (e.g. "eliminates load posting restriction that currently diverts trucks 4 miles", "reduces intersection delay from Level of Service F to C", "improves drainage to prevent recurrent flooding closures")

This classification drives everything that follows. Do not skip it.

**Step 1 — Does this category apply?**
For each potential benefit category, decide whether this project's engineering scope and primary mechanisms could plausibly generate that benefit. Be conservative. Examples:
- A bridge rehab without capacity expansion: travel time savings are unlikely unless there is evidence of delay caused by weight-restricted single-lane alternating traffic.
- An at-grade crossing elimination: resilience applies if trains currently block traffic; safety applies if crashes are documented.
- A rural bridge replacement: load-posting VOC benefit applies if the current bridge is posted or will be posted without replacement.

Only include categories the project's characteristics clearly support.

**Step 2 — What methodology fits this project?**
For each applicable category, select the calculation approach that matches both the project type and the evidence likely to exist:
- Travel Time: Rule-of-half from capacity model delay outputs (requires HCM/Synchro/VISSIM)? Direct from travel time study? Speed-distance calculation (only if a speed study exists)? Do not select a methodology that requires model outputs if no traffic model was run for this project.
- Safety: CMF method (requires a CMF matched to the treatment type and facility type from CMF Clearinghouse)? Before/after count method? Identify what crash type and facility the CMF must cover.
- VOC: Avoided load-posting detour (requires detour length, truck volume, load posting year)? Reduced congestion idling (requires speed profile change)? Reduced curvature/grade? Pick the mechanism the documents describe.
- Resilience: Expected annual avoided closures × detour cost (requires closure frequency data)? Return-period event framework (requires FEMA/NOAA flood data)? Only if a specific hazard is documented.

**Step 3 — What variables does that methodology require?**
List every input variable the selected methodology needs. Be precise — "AADT by year 2025–2047 for the subject facility" not "traffic data." Include both project-specific variables (which must come from documents or the engineer) and standard values (which come from USDOT/FHWA literature).

**Step 4 — Extract from documents**
Search every uploaded file for each project-specific required variable. Record the exact value, source document, and page/table/exhibit.

**Step 5 — Flag missing project-specific variables**
Any required project-specific variable not found in documents goes into `data_gaps`. Standard literature values (Value of Time, FHWA crash unit costs, EPA factors) do not go in `data_gaps` — they are always obtainable and should be filled in with `"Literature Source"` classification.

**Step 6 — Can this category be calculated?**
Set `"can_calculate": true` only if every required variable has a non-null value from one of:
- Project documents (`"Project Data"` or `"Engineering Analysis"`)
- A standard USDOT/FHWA reference (`"Literature Source"`)
- Engineer-provided inputs listed at the top of the workbook prompt (these will be supplied after this step)

If any project-specific variable is `null`, set `"can_calculate": false` and `"estimated_annual_benefit_M": 0.0`. Do not estimate.

---

## Output format

1. Output the JSON inside a ```json code fence.
2. Write a plain-text summary (3–5 sentences: project type, applicable categories, template choice, estimated BCR range only if any categories are fully calculable from documents alone).
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
  "project_classification": {
    "engineering_scope": "what physical work is being done",
    "primary_mechanisms": ["list of specific economic benefit mechanisms this project creates"]
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
  "benefit_analyses": [
    {
      "category": "Travel Time Savings | Vehicle Operating Cost | Safety | Emissions | Freight Reliability | Resilience | Noise | other",
      "applicable": true,
      "rationale": "why this category applies to this specific project based on its engineering scope and primary mechanisms",
      "methodology": "the specific calculation methodology selected and why it fits this project type",
      "required_variables": [
        {
          "variable": "human-readable variable name",
          "description": "what this is and why the methodology needs it",
          "found": false,
          "value": null,
          "source_citation": "document name and section/page/exhibit, or USDOT/FHWA reference, or null",
          "classification": "Project Data | Engineering Analysis | Literature Source | Analyst Judgment"
        }
      ],
      "can_calculate": false,
      "estimated_annual_benefit_M": 0.0,
      "calculation_sketch": "formula with actual values substituted if can_calculate=true, otherwise null"
    }
  ],
  "raw_quantitative_data": {
    "description": "All quantitative data from the documents that does not fit the schema above.",
    "items": [
      {"field": "string", "value": "exact value with units", "source": "document and page/exhibit"}
    ]
  },
  "data_gaps": [
    {
      "item": "exact variable name, e.g. 'No-build average intersection delay (sec/vehicle), design year 2028'",
      "category": "which benefit category this blocks",
      "why_needed": "its specific role in the calculation — e.g. 'required for rule-of-half travel time calculation'",
      "preferred_source": "where an engineer should obtain this — be specific, e.g. 'Synchro/HCM output for no-build scenario at the subject intersection', 'CMF Clearinghouse — search treatment type: bridge rail upgrade, facility: rural two-lane'",
      "required": true,
      "input_type": "number | text | percent | years | table"
    }
  ]
}
```

---

## Data Request Sheet format

After the JSON, output a markdown table between the markers. List only project-specific variables that are `null` — standard USDOT/FHWA values do not belong here. Required items first.

| # | Input Needed | Benefit Category | Why Needed | Where to Get It | Required? |
|---|-------------|-----------------|-----------|----------------|-----------|

---

## Rules

- **Never invent a project-specific value.** Missing → `null` + row in `data_gaps` + row in Data Request Sheet.
- Standard USDOT/FHWA values (Value of Time, crash unit costs, emissions factors) use `"Literature Source"` and do not block `can_calculate`.
- Set `can_calculate: false` and `estimated_annual_benefit_M: 0.0` for any category missing a project-specific variable.
- Only include benefit categories this project's `primary_mechanisms` clearly support.
- `"workbook_template"`: highway/bridge/road/capacity → `"example_workbook.xlsx"`; rail/transit/freight → `"guide_workbook.xlsm"`.
- Do NOT monetize CO₂ per current USDOT/EO guidance.
- Discount rate: 7.0% unless project documents specify otherwise.
- Base year: 2024 constant dollars unless project documents specify otherwise.
- All dollar values in millions (M). Rates as decimals (0.07 = 7%).
- Capture everything in `raw_quantitative_data` that doesn't fit the schema above.
