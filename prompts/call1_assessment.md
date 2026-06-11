Read all attached USDOT reference files and project application documents carefully and thoroughly.

Your task is to produce a structured BCA specification by reasoning from the project's characteristics — not by filling in a generic template. The workbook-building step and memo-writing step work entirely from this JSON, so extract every number and never invent a value.

**Read every page of every document before doing anything else.** This is not optional. Look in every appendix, exhibit, attachment, and supplemental file for:
- Traffic counts, AADT, peak hour volumes, seasonal factors, by direction, by year
- Traffic studies, travel demand model outputs, Synchro/HCM/VISSIM outputs
- Crash histories — every year, by severity, by location
- Bridge inspection reports, NBI data, load posting history, asset management reports
- Cost breakdowns by category, by year, federal vs. non-federal
- Engineering estimates — dimensions, capacities, design-life years
- Risk/resilience data — flood return periods, closure records, detour distances
- Environmental documents (NEPA, EA, EIS) — often contain traffic and crash data
- Prior BCAs or feasibility studies
- CMF references or safety analyses
- Any quantitative table in any appendix or exhibit

**Do not flag a variable as missing until you have confirmed it is absent from ALL uploaded materials.**

---

## CRITICAL RULE — Never invent project-specific values

**Do NOT estimate, assume, or invent any value not found in the uploaded documents.**

If a required variable is missing, set it to `null` and add it to `data_gaps`. A `null` is honest and defensible. An invented number looks plausible but will be challenged by a USDOT reviewer.

Source classification — label every value with exactly one:
- `"Project Data"` — found explicitly in the uploaded project documents
- `"Engineering Analysis"` — from a model output (HCM, Synchro, VISSIM, travel demand model) cited in the documents
- `"Literature Source"` — from a named standard reference: USDOT BCA guidance, FHWA crash unit costs, USDOT Value of Time tables, EPA MOVES, CMF Clearinghouse. These are always available without project documents.
- `"Analyst Judgment"` — Claude is inferring this; not in documents and not from a standard reference

Minimize `"Analyst Judgment"`. Flag every one explicitly.

---

## Reasoning framework — follow these steps in order

**Step 0 — Classify the project**
Identify what this project physically does at an engineering level. Record `engineering_scope` and `primary_mechanisms` (the specific ways this project generates economic benefits). This classification drives every subsequent step.

**Step 0.5 — Identify benefit drivers**
Before evaluating individual categories, estimate which benefit categories are likely to account for more than 10% of total project benefits based on the project type and scope. Mark these as `is_benefit_driver: true`. For driver categories, require higher-quality evidence and apply more conservative assumptions. This mirrors how professional BCA economists prioritize their effort.

Example reasoning: A bridge rehabilitation at a high-crash location with a load posting restriction — Safety and VOC are likely drivers. Travel time savings from 0.7 seconds of delay reduction will not be a driver.

**Step 1 — Does this category apply, and is it critical?**
For each potential benefit category:
- **Applicable?** Does this project's engineering scope and primary mechanisms plausibly generate this benefit? Be conservative.
- **Critical or Optional?** Determine whether excluding this category entirely would make the BCR fall below 1.0 based on rough orders of magnitude. If the BCA remains clearly viable without this category (BCR likely > 1.0 from other categories alone), classify it as `"Optional"`. Do not hold up the BCA for Optional categories. Critical categories must be quantified; Optional categories should be quantified if data is available but should not block production.

**Step 2 — Select methodology before requesting variables**
For each applicable category, select the specific calculation approach that fits the project type AND the evidence likely to exist for this project. Different methodologies require entirely different variables — select first, then determine what you need.

For each variable, distinguish:
- `minimum_acceptable`: the lowest-quality data that still allows a defensible calculation (e.g., a speed estimate from posted speed limits)
- `preferred_for_review`: what a USDOT reviewer would prefer to see (e.g., Synchro/HCM delay outputs by design year)

If only minimum-acceptable data is available, note the reviewer risk. If preferred data is available, use it.

**Step 3 — Determine required variables for the selected methodology**
List every input variable the selected methodology needs. Be specific: not "traffic data" but "annual AADT for Marriottsville Road at the project intersection, 2025–2047." For each variable, note evidence strength even before searching.

**Step 4 — Search exhaustively for each variable**
Search every uploaded file for each required variable. Before recording a variable as `"found": false`, confirm you checked:
- Main application narrative
- All appendices and exhibits
- Traffic studies or travel demand model outputs
- Bridge inspection or engineering reports
- Environmental documents (EA/EIS/FONSI)
- Any prior BCA or feasibility study
- Footnotes and references sections

Record the exact value, source document name, and page/table/exhibit number.

**Step 5 — Assign evidence strength and reviewer risk**
For each required variable that was found, assign evidence strength:
- `"High"` — directly stated in the document (e.g., crash count from state crash database, cost from engineer's estimate)
- `"Medium"` — derived from a documented analysis (e.g., delay calculated from a referenced Synchro run)
- `"Low"` — secondary reference or indirect (e.g., growth rate from a regional plan cited in the application)

For each benefit category, assign `reviewer_risk`:
- `"Low"` — all key variables are High or Medium evidence strength, methodology is standard
- `"Medium"` — some variables are Low strength or the methodology involves minor judgment
- `"High"` — this is a likely benefit driver but key variables are missing or methodology relies on Analyst Judgment

**Step 6 — Can this category be calculated?**
Set `"can_calculate": true` only if every required variable has a non-null value from:
- Project documents (`"Project Data"` or `"Engineering Analysis"`)
- A standard USDOT/FHWA reference (`"Literature Source"`) — Value of Time, crash unit costs, emissions factors are always available
- Engineer-provided inputs (these will be supplied via the Data Request Sheet after this step)

If any project-specific variable is `null`, set `"can_calculate": false` and `"estimated_annual_benefit_M": 0.0`. Do not estimate.

---

## Output format

1. Output the JSON inside a ```json code fence.
2. Write a plain-text summary (3–5 sentences: project type, benefit drivers, reviewer risk areas, template choice).
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
    "primary_mechanisms": ["specific economic benefit mechanisms this project creates"]
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
      "criticality": "Critical | Optional",
      "criticality_reason": "why this category is critical or optional to the BCA's viability",
      "is_benefit_driver": false,
      "rationale": "why this category applies to this specific project",
      "methodology": "the specific calculation methodology selected and why it fits this project type",
      "reviewer_risk": "Low | Medium | High",
      "reviewer_risk_reason": "what specifically creates reviewer risk — missing data, weak evidence, large benefit share, etc.",
      "required_variables": [
        {
          "variable": "human-readable variable name",
          "description": "what this is and why the methodology needs it",
          "minimum_acceptable": "lowest-quality data that still allows a defensible calculation",
          "preferred_for_review": "what a USDOT reviewer would prefer to see",
          "found": false,
          "value": null,
          "evidence_strength": "High | Medium | Low | Missing",
          "evidence_strength_reason": "why this strength rating was assigned",
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
      "item": "exact variable name",
      "category": "which benefit category this blocks",
      "criticality": "Critical | Optional",
      "why_needed": "its specific role in the calculation",
      "minimum_acceptable": "what would at least allow calculation, if less than preferred",
      "preferred_for_review": "what a USDOT reviewer would want to see",
      "preferred_source": "where an engineer should get this — be specific",
      "required": true,
      "input_type": "number | text | percent | years | table",
      "documents_searched": ["list of document types confirmed absent — e.g. 'traffic study', 'Synchro output', 'bridge inspection report'"]
    }
  ]
}
```

---

## Data Request Sheet format

Output a markdown table after the JSON, between the markers. List only project-specific variables that are `null`. Standard USDOT/FHWA values do not belong here. Sort: Critical driver categories first, then Critical non-drivers, then Optional.

| # | Input Needed | Category | Critical? | Min. Acceptable | Preferred | Where to Get It |
|---|-------------|---------|-----------|----------------|-----------|----------------|

---

## Rules

- **Never invent a project-specific value.** Missing → `null` + `data_gaps` entry + Data Request Sheet row.
- **Confirm a variable is absent from ALL uploaded materials before flagging it missing.** Note which document types were searched.
- Standard USDOT/FHWA values use `"Literature Source"` and do not block `can_calculate`.
- `can_calculate: false` and `estimated_annual_benefit_M: 0.0` for any category missing a project-specific variable.
- Only include benefit categories this project's `primary_mechanisms` clearly support.
- Do not request variables for Optional categories unless they are also benefit drivers.
- `"workbook_template"`: highway/bridge/road/capacity → `"example_workbook.xlsx"`; rail/transit/freight → `"guide_workbook.xlsm"`.
- Do NOT monetize CO₂ per current USDOT/EO guidance.
- Discount rate: 7.0% unless project documents specify otherwise.
- Base year: 2024 constant dollars unless project documents specify otherwise.
- All dollar values in millions (M). Rates as decimals (0.07 = 7%).
- Capture everything in `raw_quantitative_data` that does not fit the schema above.
