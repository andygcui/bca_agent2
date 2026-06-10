Read all attached USDOT reference files and project application documents carefully.

Your task is to extract a structured JSON specification for this BCA project. This JSON will be used by a separate workbook-building step and a memo-writing step — they will NOT have access to the original files, so the spec must be complete enough that those steps can work from it alone.

## Output format

First, output the JSON inside a ```json code fence. Then write a plain-text summary (3–5 sentences covering project type, key benefit categories, template choice, and estimated cost range).

## JSON schema (use exactly this structure)

```json
{
  "project": {
    "name": "string",
    "sponsor": "string — agency or applicant name",
    "location": "string — city, state",
    "grant_program": "BUILD | RAISE | INFRA | MEGA | CRISI | BIP | other",
    "grant_amount_requested_M": 0.0,
    "total_project_cost_M": 0.0,
    "project_type": "highway | bridge | rail | transit | port | other",
    "workbook_template": "example_workbook.xlsx | guide_workbook.xlsm",
    "description": "2–3 sentence project description",
    "baseline_description": "what exists today and its deficiencies",
    "build_description": "what the project builds and how it addresses deficiencies"
  },
  "economics": {
    "base_year": 2024,
    "analysis_period_years": 20,
    "discount_rate": 0.07,
    "construction_start_year": 2025,
    "construction_schedule": {"2025": 0.0, "2026": 0.0},
    "annual_om_cost_M": 0.0
  },
  "traffic": {
    "base_year_aadt": 0,
    "growth_rate_pct": 0.0,
    "truck_pct": 0.0,
    "peak_hour_factor": 0.0,
    "detour_miles_baseline": 0.0,
    "detour_miles_build": 0.0,
    "travel_time_savings_min_per_trip": 0.0,
    "vehicles_per_day_affected": 0
  },
  "benefits": [
    {
      "category": "Travel Time Savings | Vehicle Operating Cost | Safety | Emissions | Freight Reliability | Noise | other",
      "applicable": true,
      "methodology": "brief description of how to calculate this benefit",
      "key_inputs": {"input_name": "value with units"},
      "data_source": "which document or section",
      "estimated_annual_benefit_M": 0.0,
      "notes": "any caveats, assumptions, or missing data"
    }
  ],
  "costs": {
    "capital_cost_total_M": 0.0,
    "federal_share_M": 0.0,
    "non_federal_share_M": 0.0,
    "annual_om_M": 0.0,
    "residual_value_M": 0.0
  },
  "safety": {
    "current_crash_rate_per_mvmt": 0.0,
    "expected_reduction_pct": 0.0,
    "fatal_crashes_per_year": 0.0,
    "injury_crashes_per_year": 0.0,
    "pdo_crashes_per_year": 0.0
  },
  "key_assumptions": [
    {"assumption": "string", "value": "string with units", "source": "document and section"}
  ],
  "data_gaps": ["list of data items not found in the application that will require assumptions"]
}
```

## Rules

- Use 0.0 for any numeric field where data is unavailable — do not omit fields.
- Set `"applicable": false` for benefit categories not relevant to this project.
- `"workbook_template"`: highway/bridge/road projects → `"example_workbook.xlsx"`; rail/transit/freight projects → `"guide_workbook.xlsm"`.
- Do NOT monetize CO₂ per current USDOT/EO guidance — set applicable to false for CO₂ emissions benefits.
- Real discount rate: 7.0% unless project documents specify otherwise.
- Base year: 2024 constant dollars unless project documents specify otherwise.
- All dollar values in millions (M), rates as decimals (e.g. 0.07 not 7%), percentages as decimals.
