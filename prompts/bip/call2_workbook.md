**IMPORTANT: The openpyxl SKILL reference has been prepended above. Read it completely before writing any code.**

You are filling the FHWA BIP BCA Tool workbook — a pre-built Excel template with formulas, NBI data, and NBIAS condition forecasts already embedded. Your job is to write values into the input cells only. Do NOT modify formula cells, gray cells, or the structure of the workbook.

## Engineer-provided inputs (use these — they override null values in the spec)

{engineer_inputs}

## Project specification

```json
{project_spec}
```

## Bridge tab name

The bridge tab to fill is named: `{bridge_tab}`

---

## Fill sequence (follow in order)

### Step 1 — Open the template
```python
import openpyxl
wb = openpyxl.load_workbook("bip_workbook_example.xlsm", keep_vba=True, data_only=False)
ws = wb["{bridge_tab}"]
```

### Step 2 — Write values to input cells

Use this exact cell map. Only write to cells listed here. Never overwrite a formula cell.

**TABLE 1 — Bridge Identification**
```
B11 = state (string, e.g. "Maryland")
B12 = county (string)
B13 = structure_number (string)
```

**TABLE 2 — Project Timeline**
```
B39 = first_year_construction_costs (integer)
B40 = last_year_construction_costs (integer)
B41 = project_opens (integer)
B42 = years_of_benefits (integer, 20 or 30)
```

**TABLE 3 — AADT by Year and Mode**
The calendar year rows start at row 54 for the first construction year.
Row for a given calendar year = 54 + (calendar_year - first_year_construction_costs)
Maximum row available is 98 (45 years total). Do not write past row 98.

For each calendar year in spec["aadt"]["by_year"]:
```
E{row} = no_build passenger AADT
F{row} = no_build trucks AADT
G{row} = no_build bus AADT
H{row} = no_build pedestrian AADT
I{row} = no_build cyclist AADT
J{row} = build passenger AADT
K{row} = build trucks AADT
L{row} = build bus AADT
M{row} = build pedestrian AADT
N{row} = build cyclist AADT
```

**TABLE 4 — Detour Information**
```
C108 = bridge_length_mi (float)
C109 = avg_speed_on_bridge_mph (float)
C110 = passenger_detour_road_type (string: "Rural" or "Urban")
C111 = truck_detour_road_type (string)
C112 = bus_detour_road_type (string)
C113 = passenger_net_detour_length_mi (float)
C114 = truck_net_detour_length_mi (float)
C115 = bus_net_detour_length_mi (float)
C116 = pedestrian_net_detour_length_mi (float)
C117 = cyclist_net_detour_length_mi (float)
C118 = passenger_detour_avg_speed_mph (float)
C119 = truck_detour_avg_speed_mph (float)
C120 = bus_detour_avg_speed_mph (float)
D110 = explanation for detour road type (string)
```

**TABLE 5 — Travel Assumptions (USDOT Dec 2025 defaults)**
```
C134 = 1.52   (avg car occupancy)
C135 = 0.00   (share long-distance personal travel)
C136 = 28.20  (value of time — long-distance personal, $/hr)
C137 = 0.118  (share business travel)
C138 = 34.60  (value of time — business, $/hr)
C139 = 20.10  (value of time — personal, $/hr)
C141 = 40.20  (walking/cycling/waiting time, $/hr)
C142 = 37.20  (truck driver, $/hr)
C143 = 40.30  (bus driver, $/hr)
C144 = bus_occupancy (from spec or 15 if null — note source)
```

**TABLE 6 — Expenditure Dollar Option**
```
B148 = "YES" if costs_in_nominal_dollars else "NO"
B149 = inflation_rate (float, e.g. 0.025)
```

**TABLE 7 — Already Incurred Costs** (if any in spec["costs"]["already_incurred"])
```
A154 = year, B154 = cost  (first entry)
A155 = year, B155 = cost  (second entry)
... up to A164/B164
Leave remaining rows as "-"
```

**TABLE 8 — Capital Costs**
Column A (years) is formula-driven — do NOT write to column A.
```
B168 = cost for first_year_construction_costs
B169 = cost for first_year+1 (0 if none)
B170 = cost for first_year+2 (0 if none)
... continue for each construction year through B182
```

**TABLE 10 — Residual Value**
```
A191 = share_of_costs_pct / 100  (as decimal, e.g. 1.0 for 100%)
B191 = asset_life_years
A192-B192, A193-B193, A194-B194 for additional components (0 if not used)
```

**TABLE 11 — O&M Year of Dollar**
```
B201 = om_year_of_dollar (integer year)
```

**TABLE 12 — O&M Costs by Year**
Row for a given calendar year = 207 + (calendar_year - first_year_construction_costs)
```
C{row} = no_build_annual_cost
D{row} = build_annual_cost
```

**TABLE 13 — Construction Traffic Management Description**
```
B255 = traffic_management_description (string)
```

**BRIDGE CONDITION (Table 17)**
```
B319 = "YES" if bridge_condition["include"] else "NO"
```
If YES, also write:
```
C340 = anticipated_load_posting_level1_year (or 2070 if null)
D340 = anticipated_load_posting_level1_pct_trucks (or 0)
E340 = anticipated_load_posting_level1_pct_buses (or 0)
C341 = level2_year (or 2070), D341 = level2_pct_trucks, E341 = level2_pct_buses
C342 = level3_year (or 2070), D342 = level3_pct_trucks, E342 = level3_pct_buses
C346 = anticipated_closure_year (or 2070 if null)
D346 = anticipated_closure_pct_capacity_reduction (or 0)
```

**RESILIENCE (Table 23)**
```
B385 = "YES" if resilience["include"] else "NO"
```
If YES and method == "probability":
```
B389 = "YES"
E396 = annual_prob_volume_capacity_reduction (or 0)
E397 = annual_prob_level1_structural_damage (or 0)
E398 = annual_prob_level2_structural_damage (or 0)
```
If YES and method == "other":
```
B389 = "NO"
B434 = "YES"
B440 = explanation text
```

**SAFETY (Tables 31–35)**
```
B444 = crash_cost_type ("KABCO" or "General")
```
For KABCO crash data: refer to the uploaded BIP guide for the exact row addresses of Tables 32–33 (historical crash data by severity). Write annual average crashes to those cells.
```
B462 = "YES" if safety["include_cmf"] else "NO"
```
If YES:
```
C467 = cmf_start_year
C468 = cmf_end_year
```
For CMF value and crash type, refer to the guide for the exact cells in Table 33.

**TRAVEL TIME (Table 36)**
```
B489 = "YES" if travel_time["include"] else "NO"
```

**ENVIRONMENTAL (Table 39)**
```
B508 = "YES" if environmental["include"] else "NO"
```

**PEDESTRIAN/CYCLIST (Table 41)**
```
B519 = "YES" if pedestrian_cyclist["include"] else "NO"
C547 = pct_trips_induced_from_non_active_modes (or 0 if null)
```

**OTHER BENEFITS (Table 44)**
```
B553 = "YES" if other_benefits["include"] else "NO"
```

### Step 3 — Clean up stale tabs and save
```python
# Remove any stale tabs that should not appear in the output
for stale in ["example", "example_sns"]:
    if stale in wb.sheetnames:
        del wb[stale]
wb.save("bip_workbook_v1.xlsm")
print("Saved: bip_workbook_v1.xlsm")
```

### Step 4 — Verify key cells were written
Print a verification table confirming the key input cells have been written correctly.

### Step 5 — Calculate approximate BCR
Using the inputs you just wrote, calculate an approximate BCR using the BIP methodology:

1. **Total discounted capital costs**: Sum capital costs discounted at 7% to 2024 dollars
2. **Total discounted O&M cost difference**: Sum (no_build_om - build_om) × discount factor for each year
3. **Construction disbenefits**: Estimate delay costs during construction (AADT × detour_time × value_of_time × construction_days)
4. **Bridge condition/closure benefits** (if applicable): Annual vehicle-hours lost to closure/load posting × value of time, discounted
5. **Safety benefits** (if applicable): Crash reduction × USDOT unit crash costs, discounted
6. Apply discount rate 7%, base year 2024

Note: This is an approximation. The definitive BCR comes from the Excel workbook when opened in Excel.

---

## Output required

After verification, output the key inputs and approximate results between these exact markers:

--- WORKBOOK RESULTS START ---
Bridge: [state] / [county] / [structure_number]
First Year Construction: [value]
Project Opens: [value]
Years of Benefits: [value]
Total Capital Cost ($): [value]
Benefit Categories Included: [comma-separated list]
BCR (7%, approximate): [value or "pending Excel verification"]
NPV at 7% ($M, approximate): [value or "pending Excel verification"]
Discount Rate: 7%
Base Year: 2024
Verification status: PASSED / FAILED [n errors]
--- WORKBOOK RESULTS END ---

If code execution fails to save the file, output a cell patch list as last resort:
`{bridge_tab}!CellRef=value` (one per line)

## Data integrity rules
- Only write to input cells listed in the cell map above.
- Never overwrite a cell that contains a formula (check with `isinstance(ws[addr].value, str) and ws[addr].value.startswith("=")`).
- For null values in the spec where a 0 is required (the BIP tool rejects blank inputs), write 0 and note it.
- AADT values must be non-negative integers.
- All costs in dollars (not millions).
