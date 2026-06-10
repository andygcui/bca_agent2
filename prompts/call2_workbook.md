Build the BCA workbook using code execution (openpyxl).

The project specification JSON below is your authoritative source for all inputs and assumptions. The appropriate template workbook is attached — open it as your base.

## Workbook build rules

### Python / openpyxl patterns (follow exactly)

- Open the attached template with `openpyxl.load_workbook(filename, keep_vba=True)` (or `keep_vba=False` for .xlsx).
- Use `ShadingType.CLEAR` (NOT `ShadingType.SOLID`) for all cell fills — SOLID causes black backgrounds.
- Apply an explicit `Alignment` object on every styled cell (even if just `Alignment(wrap_text=False)`).
- Set column widths with `ws.column_dimensions['A'].width = 18` AND apply cell-level number formats.
- Freeze panes on every data sheet (e.g., `ws.freeze_panes = "A2"` or `"B2"`).
- Color coding:
  - Blue text `"FF0070C0"` for hardcoded input values
  - Black text `"FF000000"` for cells containing formulas
  - Green text `"FF00B050"` for cross-sheet reference inputs
- Use `PatternFill(fill_type="solid", fgColor="FFD9E1F2")` for input cell backgrounds (light blue).

### Data integrity

- **Preserve formulas.** Only write to input cells. Never overwrite a formula cell with a hardcoded value unless replacing it with a new formula.
- If a cell already has a formula, leave it alone.
- All monetary inputs in the workbook should be in the same units the workbook expects (check the template headers — usually $, not $M).

### Save

Save the completed workbook via code execution as `workbook_v1.xlsx`.

## Output required

After saving, output the key computed results as text between these exact markers:

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
--- WORKBOOK RESULTS END ---

If code execution fails to save the file, output a patch list as a last resort:
`Sheet!CellRef=value` (one per line, no other formatting).

## Valid tab names for guide_workbook.xlsm (use exact spelling only)

{valid_tabs}

## Project specification

```json
{project_spec}
```
