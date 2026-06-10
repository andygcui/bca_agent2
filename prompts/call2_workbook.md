**IMPORTANT: The openpyxl SKILL reference has been prepended above. Read it completely before writing any code.**

Build the BCA workbook using code execution (openpyxl).

The project specification JSON below is your authoritative source for all inputs and assumptions. The appropriate template workbook is attached — open it as your base.

## Build sequence (follow in order)

1. **Open the template** using the correct `keep_vba` parameter (see SKILL.md §7).
2. **Plan before writing**: identify all input cells to populate. Print their addresses before writing.
3. **Write inputs** using `safe_write()` (see SKILL.md §6) — never overwrite a formula cell.
4. **Apply formatting** per SKILL.md §§1–5: fill colors, font colors, alignment, column widths, freeze panes.
5. **Save** as `workbook_v1.xlsx`.
6. **Run verification** (see SKILL.md §8). If errors are found, fix them and verify again.
7. **Output results** only after verification passes.

## Data integrity rules

- Only write to input cells. Never overwrite a formula cell with a hardcoded value.
- All monetary inputs must be in the units the workbook expects — check the template headers (usually $, not $M).
- Use the `safe_write()` helper from SKILL.md on every cell write.

## Output required

After verification passes, output the key computed results between these exact markers:

--- WORKBOOK RESULTS START ---
BCR (7%): [value]
NPV at 7% ($M): [value]
Total Benefits PV ($M): [value]
Total Costs PV ($M): [value]
BCR (3%): [value, if computed]
NPV at 3% ($M): [value, if computed]
Analysis period (years): [value]
Base year: [value]
Key benefit categories included: [comma-separated list]
Verification status: PASSED / FAILED [n errors]
--- WORKBOOK RESULTS END ---

If code execution fails to save the file, output a patch list as a last resort:
`Sheet!CellRef=value` (one per line, no other formatting).

## Valid tab names for guide_workbook.xlsm (use exact spelling only)

{valid_tabs}

## Project specification

```json
{project_spec}
```
