Read all attached USDOT reference files and project application documents carefully and thoroughly.

Your task is to extract a complete structured JSON specification for this BCA project. The workbook-building step and the memo-writing step will NOT have access to the original files — they work entirely from this JSON. Extract every number. Do not summarize. Capture exact figures.

**Read every page of every document.** Look specifically for:
- Traffic counts (AADT, peak hour, seasonal, by direction, by year)
- Crash histories (every year reported, by severity, by location if given)
- Cost breakdowns (by category, by year, federal vs. non-federal)
- Engineering estimates (dimensions, capacities, design-life years)
- Risk/resilience data (flood return periods, closure frequencies, detour distances)
- Any quantitative data table in any appendix or exhibit

## CRITICAL RULE — Never invent project-specific values

**Do NOT estimate, assume, or invent any project-specific numerical input that is not found in the uploaded documents.**

If a value is not in the documents, set the field to `null`. A null value is honest. An invented number looks plausible but will be challenged by a USDOT reviewer and will embarrass the project team.

Examples of values you must NOT invent:
- No-build or build speed / delay / LOS (requires a traffic model or field study)
- Crash reduction percentage or CMF (requires CMF Clearinghouse lookup by an engineer)
- Detour distance or truck percentage (requires a traffic classification count)
- Flood closure frequency (requires FEMA, NOAA, or roadway closure records)

For each key input in every benefit category, classify the source using exactly one label:
- `"Project Data"` — found explicitly in the uploaded project documents
- `"Engineering Analysis"` — derived from a model output (HCM, Synchro, VISSIM, travel demand model) referenced in the documents
- `"Literature Source"` — from CMF Clearinghouse, USDOT BCA guidance, FHWA unit cost tables, EPA MOVES, or another named external database
- `"Analyst Judgment"` — Claude is inferring or assuming this; not found in documents

Minimize "Analyst Judgment" inputs. Flag every one explicitly in `notes`.

## Output format

1. Output the JSON inside a ```json code fence.
2. Write a plain-text summary (3–5 sentences: project type, key benefit categories, template choice, estimated BCR range if calculable).
3. Output a Data Request Sheet between these exact markers:

--- DATA REQUEST SHEET START ---
[markdown table of missing inputs — see instructions below]
--- DATA REQUEST SHEET END ---

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
    "om_cost_notes": "string — source and any escalation assumptions"
  },
  "traffic": {
    "base_year_aadt": 0,
    "base_year_label": "string — e.g. '2023 count'",
    "aadt_by_year": {"2023": 0, "2030": 0, "2040": 0},
    "growth_rate_pct": 0.0,
    "growth_rate_source": "string",
    "truck_pct": null,
    "peak_hour_factor": 0.0,
    "detour_miles_baseline": 0.0,
    "detour_miles_build": 0.0,
    "nobuild_delay_sec_per_vehicle": null,
    "build_delay_sec_per_vehicle": null,
    "delay_source": "string — HCM/Synchro/VISSIM/model name and scenario, or null",
    "travel_time_savings_min_per_trip": null,
    "travel_time_basis": "string — how this was calculated or sourced, or 'MISSING — requires capacity analysis output'",
    "vehicles_per_day_affected": 0,
    "freight_trucks_per_day": 0
  },
  "safety": {
    "crash_history_years": 0,
    "crash_history_note": "string — data source and period",
    "fatal_crashes_per_year": 0.0,
    "injury_crashes_per_year": 0.0,
    "pdo_crashes_per_year": 0.0,
    "total_crashes_per_year": 0.0,
    "crash_rate_per_mvmt": 0.0,
    "statewide_avg_crash_rate": 0.0,
    "crash_rate_ratio_vs_state": 0.0,
    "expected_crash_reduction_pct": null,
    "cmf_id": null,
    "cmf_value": null,
    "cmf_source": "string — CMF Clearinghouse entry ID and study, or null",
    "cmf_applies_to": "string — total crashes / injury crashes / intersection only, or null",
    "annual_crash_costs_M": 0.0,
    "crash_cost_notes": "string — unit costs used"
  },
  "benefits": [
    {
      "category": "Travel Time Savings | Vehicle Operating Cost | Safety | Emissions | Freight Reliability | Resilience | Noise | other",
      "applicable": true,
      "methodology": "step-by-step description of how to calculate this benefit",
      "key_inputs": {
        "input_name": {
          "value": "exact value with units from documents, or null if missing",
          "source_classification": "Project Data | Engineering Analysis | Literature Source | Analyst Judgment",
          "source_citation": "document name and section/page, or null"
        }
      },
      "data_source": "exact document name and section/page",
      "estimated_annual_benefit_M": 0.0,
      "calculation_sketch": "brief formula or logic — only if all inputs have non-null values",
      "notes": "list any null inputs and any Analyst Judgment inputs explicitly"
    }
  ],
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
  "resilience": {
    "applicable": false,
    "event_type": "flood | storm | seismic | other",
    "closure_days_per_year_baseline": 0.0,
    "closure_days_per_year_build": 0.0,
    "detour_length_miles": 0.0,
    "annual_detour_cost_M": 0.0,
    "return_period_events": [
      {"return_period_years": 0, "closure_days": 0.0, "probability": 0.0}
    ],
    "source": "string"
  },
  "key_assumptions": [
    {
      "assumption": "string",
      "value": "exact value with units",
      "source": "document name and section/page",
      "classification": "Project Data | Engineering Analysis | Literature Source | Analyst Judgment"
    }
  ],
  "raw_quantitative_data": {
    "description": "Any quantitative data from the documents that does not fit the schema above. Include exact figures with their units and source. Do not summarize.",
    "items": [
      {"field": "string description", "value": "exact value with units", "source": "document and page"}
    ]
  },
  "data_gaps": [
    {
      "item": "string — what is missing, e.g. 'No-build average delay (sec/vehicle)'",
      "impact": "which benefit category this blocks or weakens",
      "preferred_source": "where an engineer should obtain this — e.g. 'Synchro/HCM output', 'CMF Clearinghouse', 'State crash database'",
      "required": true,
      "input_type": "number | text | percent | years",
      "json_path": "dot-notation path in this spec, e.g. 'traffic.nobuild_delay_sec_per_vehicle'"
    }
  ]
}
```

## Data Request Sheet instructions

After the JSON, output a markdown table between the markers `--- DATA REQUEST SHEET START ---` and `--- DATA REQUEST SHEET END ---`.

List ONLY inputs that are null in the JSON — values that require an engineer, a traffic model output, a crash database, or the CMF Clearinghouse. Order: required inputs first, then optional.

Format:

| # | Input Needed | Why Needed | Preferred Source | Required? |
|---|-------------|-----------|-----------------|-----------|
| 1 | No-build average delay (sec/vehicle) | Travel Time Savings — rule-of-half calculation | Synchro/HCM/VISSIM capacity analysis output | Yes |
| 2 | CMF ID and value | Safety — crash reduction calculation | CMF Clearinghouse (cmfclearinghouse.com) | Yes |

## Rules

- **Never invent a project-specific value.** Missing → `null` in JSON + row in data_gaps + row in Data Request Sheet.
- Classify every key input in `benefits[].key_inputs` with `source_classification`.
- Set `estimated_annual_benefit_M` to `0.0` for any category where key inputs are null — do not estimate.
- Set `"applicable": false` for benefit categories not relevant to this project.
- `"workbook_template"`: highway/bridge/road/capacity projects → `"example_workbook.xlsx"`; rail/transit/freight projects → `"guide_workbook.xlsm"`.
- Do NOT set applicable=true for CO₂ monetization per current USDOT/EO guidance.
- Discount rate: 7.0% unless project documents specify otherwise.
- Base year: 2024 constant dollars unless project documents specify otherwise.
- All dollar values in millions (M). Rates as decimals (0.07 = 7%). Percentages as decimals.
- For `raw_quantitative_data`, capture EVERYTHING that doesn't fit the schema — tables, exhibits, appendix figures.
- For `key_assumptions`, flag every Analyst Judgment item. These are the values a USDOT reviewer will question.
