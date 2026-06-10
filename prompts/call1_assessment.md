Read all attached USDOT reference files and project application documents carefully and thoroughly.

Your task is to extract a complete structured JSON specification for this BCA project. The workbook-building step and the memo-writing step will NOT have access to the original files — they work entirely from this JSON. Extract every number. Do not summarize. Capture exact figures.

**Read every page of every document.** Look specifically for:
- Traffic counts (AADT, peak hour, seasonal, by direction, by year)
- Crash histories (every year reported, by severity, by location if given)
- Cost breakdowns (by category, by year, federal vs. non-federal)
- Engineering estimates (dimensions, capacities, design-life years)
- Risk/resilience data (flood return periods, closure frequencies, detour distances)
- Any quantitative data table in any appendix or exhibit

## Output format

Output the JSON inside a ```json code fence. Then write a plain-text summary (3–5 sentences covering project type, key benefit categories, template choice, and estimated BCR range if calculable).

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
    "truck_pct": 0.0,
    "peak_hour_factor": 0.0,
    "detour_miles_baseline": 0.0,
    "detour_miles_build": 0.0,
    "travel_time_savings_min_per_trip": 0.0,
    "travel_time_basis": "string — how this was calculated or sourced",
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
    "expected_crash_reduction_pct": 0.0,
    "cmf_source": "string — CMF Clearinghouse entry or study cited",
    "annual_crash_costs_M": 0.0,
    "crash_cost_notes": "string — unit costs used"
  },
  "benefits": [
    {
      "category": "Travel Time Savings | Vehicle Operating Cost | Safety | Emissions | Freight Reliability | Resilience | Noise | other",
      "applicable": true,
      "methodology": "step-by-step description of how to calculate this benefit",
      "key_inputs": {"input_name": "exact value with units from documents"},
      "data_source": "exact document name and section/page",
      "estimated_annual_benefit_M": 0.0,
      "calculation_sketch": "brief formula or logic showing how the annual estimate was derived",
      "notes": "caveats, assumptions, or data gaps specific to this category"
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
    {"assumption": "string", "value": "exact value with units", "source": "document name and section/page"}
  ],
  "raw_quantitative_data": {
    "description": "Any quantitative data from the documents that does not fit the schema above. Include exact figures with their units and source. Do not summarize.",
    "items": [
      {"field": "string description", "value": "exact value with units", "source": "document and page"}
    ]
  },
  "data_gaps": [
    {"item": "string — what is missing", "impact": "which benefit category this affects", "default_assumption": "what value to use if unavailable"}
  ]
}
```

## Rules

- **Do not summarize. Capture exact figures.** If the application says "8.5× the statewide average crash rate", record that ratio exactly.
- Use `0.0` for numeric fields where data is truly unavailable — do not omit fields.
- Set `"applicable": false` for benefit categories not relevant to this project.
- `"workbook_template"`: highway/bridge/road/capacity projects → `"example_workbook.xlsx"`; rail/transit/freight projects → `"guide_workbook.xlsm"`.
- Do NOT set applicable=true for CO₂ monetization per current USDOT/EO guidance.
- Discount rate: 7.0% unless project documents specify otherwise.
- Base year: 2024 constant dollars unless project documents specify otherwise.
- All dollar values in millions (M). Rates as decimals (0.07 = 7%). Percentages as decimals.
- For `raw_quantitative_data`, capture EVERYTHING that doesn't fit the schema — tables, exhibits, appendix figures.
