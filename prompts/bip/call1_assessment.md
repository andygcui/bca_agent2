Read all attached BIP reference files and project application documents carefully and thoroughly.

Your task is to produce a structured BCA specification formatted for the FHWA Bridge Investment Program (BIP) BCA Tool v1.1.2. The workbook-filling step works entirely from this JSON, so extract every number precisely and never invent a value.

**Read every page of every document before doing anything else.** This is not optional. Look in every appendix, exhibit, attachment, and supplemental file for:
- Bridge identification: State, County, NBI Structure Number
- Traffic counts: AADT by vehicle type (passenger, truck, bus, pedestrian, cyclist), by direction, by year
- Construction schedule and phasing
- Cost breakdowns by year (capital costs, O&M costs)
- Bridge inspection reports, NBI data, condition ratings, load posting history, closure history
- Detour route information: distance, road type, speed
- Crash history: by severity (fatal, serious injury, minor injury, property damage only), by year
- CMF references or safety improvement details
- Resilience data: flood records, seismic zone, closure history from extreme events
- Pedestrian/cyclist counts if applicable
- Any prior BCA or feasibility studies

**Do not flag a variable as missing until you have confirmed it is absent from ALL uploaded materials.**

---

## CRITICAL RULE — Never invent project-specific values

**Do NOT estimate, assume, or invent any value not found in the uploaded documents.**

If a required variable is missing, set it to `null` and add it to `data_gaps`. A `null` is honest and defensible.

Source classification — label every value with exactly one:
- `"Project Data"` — found explicitly in the uploaded project documents
- `"Engineering Analysis"` — from a model output cited in the documents
- `"NBI Default"` — from National Bridge Inventory data (acceptable when project data unavailable)
- `"USDOT Default"` — from USDOT BCA Guidance default values (Dec 2025) — always available
- `"Analyst Judgment"` — Claude is inferring this; flag every one explicitly

Minimize `"Analyst Judgment"`. Flag every one explicitly.

---

## Reasoning framework

**Step 1 — Identify the bridge**
Find the NBI Structure Number, State, and County. This is required to populate the BIP tool. If the structure number is not in the documents, flag it as a Critical gap — nothing else in the BIP tool can proceed without it.

**Step 2 — Establish the project timeline**
Identify: first year of construction costs, last year of construction costs, first full year open to traffic (project_opens), and the appropriate years of benefits (20 for rehabilitation/preservation; 30 for full reconstruction per USDOT BCA Guidance).

**Step 3 — Extract AADT by mode**
The BIP tool needs AADT separately for: passenger vehicles, trucks, buses, pedestrians, and cyclists — for BOTH no-build and build scenarios, for EVERY year in the analysis period.

If only total AADT is available, note the source and use NBI mode splits as a fallback (flag as NBI Default).
If build scenario AADT differs from no-build (e.g., induced demand, mode shift), document the basis.
If no project-specific AADT is available, use NBI AADT and flag as NBI Default.

**Step 4 — Extract costs**
Capital costs by year, O&M costs by year for both no-build and build scenarios, already-incurred costs (if any), residual value components.

**Step 5 — Identify which benefit categories apply**
For each BIP benefit category, determine YES/NO and extract the specific inputs:
- **Bridge Condition/Closures**: Does the project improve or preserve bridge condition to avoid load posting or closure? Extract NBIAS-based or engineer-estimated years of load posting and closure.
- **Resilience**: Does the project improve resistance to weather, seismic, or extreme events? Extract annual probabilities and damage scenarios.
- **Safety**: Does the project include crash cost improvements (historical crash data required) and/or a CMF-based safety countermeasure?
- **Travel Time**: Does the project improve travel time separate from closure avoidance (e.g., adds shoulder, removes bottleneck)?
- **Environmental/Noise**: Does the project reduce noise or improve water runoff?
- **Pedestrian/Cyclist**: Does the project improve pedestrian or cycling facilities?
- **Other Benefits**: Are there other quantifiable monetized benefits?

**Step 6 — Identify gaps**
For each null value, create a data_gap entry specifying exactly what is needed, where to get it, and whether it is Critical (blocks a key benefit category) or Optional.

---

## Output format

1. Output the JSON inside a ```json code fence.
2. Write a plain-text summary (3–5 sentences: bridge condition, key benefit drivers, data quality, gaps summary).
3. Output the Data Request Sheet between these exact markers:

--- DATA REQUEST SHEET START ---
[markdown table]
--- DATA REQUEST SHEET END ---

---

## JSON schema

```json
{
  "bridge": {
    "state": "full state name as it appears in NBI (e.g. 'Maryland')",
    "county": "county name",
    "structure_number": "NBI structure number string",
    "bridge_name": "descriptive name",
    "owner": "bridge owner",
    "location_description": "route carried over feature intersected, city/county/state",
    "grant_program": "BIP Bridge | BIP Large Bridge",
    "grant_amount_requested_M": 0.0,
    "total_project_cost_M": 0.0,
    "project_description": "2-3 sentence project description",
    "baseline_description": "current bridge condition, NBI rating, deficiencies, any existing load posting or closure history",
    "build_description": "what the project physically does and what deficiencies it resolves"
  },
  "timeline": {
    "first_year_construction_costs": 2026,
    "last_year_construction_costs": 2028,
    "project_opens": 2029,
    "years_of_benefits": 20,
    "costs_in_nominal_dollars": true,
    "inflation_rate": 0.025
  },
  "aadt": {
    "notes": "explanation of AADT sources and any growth rate assumptions",
    "by_year": [
      {
        "calendar_year": 2026,
        "no_build": {
          "passenger": 0,
          "trucks": 0,
          "bus": 0,
          "pedestrian": 0,
          "cyclist": 0
        },
        "build": {
          "passenger": 0,
          "trucks": 0,
          "bus": 0,
          "pedestrian": 0,
          "cyclist": 0
        }
      }
    ]
  },
  "detour": {
    "bridge_length_mi": null,
    "avg_speed_on_bridge_mph": null,
    "passenger_detour_road_type": "Rural | Urban",
    "truck_detour_road_type": "Rural | Urban",
    "bus_detour_road_type": "Rural | Urban",
    "passenger_net_detour_length_mi": null,
    "truck_net_detour_length_mi": null,
    "bus_net_detour_length_mi": null,
    "pedestrian_net_detour_length_mi": null,
    "cyclist_net_detour_length_mi": null,
    "passenger_detour_avg_speed_mph": null,
    "truck_detour_avg_speed_mph": null,
    "bus_detour_avg_speed_mph": null,
    "explanation": "source and basis for detour values"
  },
  "costs": {
    "already_incurred": [],
    "capital_by_year": [
      {"year": 2026, "cost": 0.0}
    ],
    "residual_value_components": [
      {"share_of_costs_pct": 100.0, "asset_life_years": 75}
    ],
    "om_year_of_dollar": 2024,
    "om_by_year": [
      {"calendar_year": 2026, "no_build_annual_cost": 0.0, "build_annual_cost": 0.0}
    ]
  },
  "construction_disbenefits": {
    "traffic_management_description": "specific description of traffic management plan during construction and expected impacts on users",
    "partial_capacity_days_per_year": null,
    "partial_capacity_pct_reduction": null,
    "full_detour_days_per_year": null
  },
  "bridge_condition": {
    "include": false,
    "anticipated_load_posting_level1_year": null,
    "anticipated_load_posting_level1_pct_trucks": null,
    "anticipated_load_posting_level1_pct_buses": null,
    "anticipated_load_posting_level2_year": null,
    "anticipated_load_posting_level2_pct_trucks": null,
    "anticipated_load_posting_level2_pct_buses": null,
    "anticipated_load_posting_level3_year": null,
    "anticipated_load_posting_level3_pct_trucks": null,
    "anticipated_load_posting_level3_pct_buses": null,
    "anticipated_closure_year": null,
    "anticipated_closure_pct_capacity_reduction": null,
    "condition_notes": "basis for closure/load posting forecasts — NBIAS model, engineer estimate, etc."
  },
  "resilience": {
    "include": false,
    "method": "probability | other | null",
    "annual_prob_volume_capacity_reduction": null,
    "annual_prob_level1_structural_damage": null,
    "annual_prob_level2_structural_damage": null,
    "resilience_notes": "description of extreme events considered and basis for probabilities"
  },
  "safety": {
    "include_crash_costs": false,
    "crash_cost_type": "KABCO | General",
    "historical_crashes_annual_avg": {
      "fatal": null,
      "serious_injury": null,
      "minor_injury": null,
      "property_damage_only": null,
      "years_of_data": null,
      "source": null
    },
    "include_cmf": false,
    "cmf_value": null,
    "cmf_source": null,
    "cmf_start_year": null,
    "cmf_end_year": null,
    "safety_notes": "basis for crash data and CMF selection"
  },
  "travel_time": {
    "include": false,
    "improvement_description": null,
    "notes": "basis for travel time improvement claim"
  },
  "environmental": {
    "include": false,
    "description": null
  },
  "pedestrian_cyclist": {
    "include": false,
    "pct_trips_induced_from_non_active_modes": null,
    "notes": null
  },
  "other_benefits": {
    "include": false,
    "description": null
  },
  "data_gaps": [
    {
      "item": "exact variable name",
      "section": "bridge_id | aadt | detour | costs | condition | safety | resilience | travel_time | ped_cyclist",
      "criticality": "Critical | Optional",
      "why_needed": "specific role in BIP tool calculation",
      "preferred_source": "where the engineer should get this — be specific",
      "input_type": "number | text | year | percent | table"
    }
  ]
}
```

---

## Data Request Sheet format

Output a markdown table after the JSON, between the markers. List only project-specific variables that are null. USDOT defaults do not belong here.

| # | Input Needed | BIP Section | Critical? | Where to Get It |
|---|-------------|-------------|-----------|----------------|

---

## Rules

- **Never invent a project-specific value.** Missing → `null` + `data_gaps` entry + Data Request Sheet row.
- **Confirm a variable is absent from ALL uploaded materials before flagging it missing.**
- NBI defaults are acceptable for AADT if no better source exists — flag as `"NBI Default"`.
- USDOT BCA Guidance Dec 2025 defaults are acceptable for travel assumptions (value of time, occupancy).
- Use `years_of_benefits: 20` for rehabilitation/preservation projects; 30 for full reconstruction.
- Set `include: false` for any benefit category where the project's physical scope does not clearly support that benefit.
- For bridge condition, use NBIAS-based forecasts from the guide as a fallback if no engineer estimate is available — note this explicitly.
- Discount rate: 7.0% (USDOT default). Dollar year: 2024 (per Dec 2025 USDOT BCA Guidance).
