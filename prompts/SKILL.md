# openpyxl BCA Workbook Build Patterns

**Read this entire file before writing any workbook code.** These patterns encode hard-won fixes — skipping them produces workbooks that open correctly but have broken formatting or hardcoded numbers.

---

## 1. Fill colors — use full ARGB with both fgColor and bgColor

The most common mistake: setting only `fgColor` causes `bgColor` to default to `"00000000"` (black), which produces black cell backgrounds.

```python
# CORRECT — always set both fgColor and bgColor with full 8-char ARGB
from openpyxl.styles import PatternFill
cell.fill = PatternFill(patternType="solid", fgColor="FFD9E1F2", bgColor="FFD9E1F2")

# WRONG — missing FF prefix and bgColor defaults to black
cell.fill = PatternFill(fill_type="solid", fgColor="D9E1F2")
```

Standard fills for this project:
- Input cells (light blue): `fgColor="FFD9E1F2", bgColor="FFD9E1F2"`
- Section headers (dark blue): `fgColor="FF1F3864", bgColor="FF1F3864"` with white font
- Result cells (light green): `fgColor="FFE2EFDA", bgColor="FFE2EFDA"`

---

## 2. Alignment — always explicit on every styled cell

Never apply font or fill styling without also setting Alignment. Without it, styled cells inherit unpredictable defaults from the template.

```python
from openpyxl.styles import Alignment
cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=False)
```

---

## 3. Column widths AND cell number formats — always both

```python
ws.column_dimensions['B'].width = 32          # set column width
cell.number_format = '#,##0.00'               # set cell number format
```

Never set one without the other on data columns.

---

## 4. Freeze panes — every data sheet

```python
ws.freeze_panes = "B2"   # freeze row 1 (header) and column A (labels)
```

Apply to every sheet that has a data table.

---

## 5. Color convention (USDOT standard — apply consistently)

```python
from openpyxl.styles import Font

# Blue — hardcoded input values (what the user provides)
cell.font = Font(color="FF0070C0")

# Black — formula result cells (NEVER overwrite these)
cell.font = Font(color="FF000000")

# Green — cross-sheet reference inputs
cell.font = Font(color="FF00B050")
```

---

## 6. Formula preservation — check before writing

Before writing to ANY cell, check if it contains a formula:

```python
def safe_write(cell, value):
    """Only write if cell does not contain a formula."""
    if cell.value and str(cell.value).startswith('='):
        print(f"SKIPPED formula cell {cell.coordinate}: {cell.value}")
        return False
    cell.value = value
    return True
```

---

## 7. Loading templates

```python
import openpyxl

# For .xlsm (guide workbook with VBA)
wb = openpyxl.load_workbook("guide_workbook.xlsm", keep_vba=True)

# For .xlsx (example workbook, no VBA)
wb = openpyxl.load_workbook("example_workbook.xlsx", keep_vba=False)
```

Always specify `keep_vba` explicitly.

---

## 8. Post-build verification — run after saving

After saving, always re-open the file and verify:

```python
from openpyxl import load_workbook

wb_check = load_workbook("workbook_v1.xlsx")
issues = []

for sheet_name in wb_check.sheetnames:
    ws_check = wb_check[sheet_name]
    for row in ws_check.iter_rows():
        for cell in row:
            if cell.value is None:
                continue
            val_str = str(cell.value)
            # Flag cells whose display value is an error string
            if val_str.startswith('#') and any(
                val_str.startswith(e) for e in ('#REF', '#VALUE', '#NAME', '#DIV', '#NUM', '#N/A')
            ):
                issues.append(f"{sheet_name}!{cell.coordinate}: {val_str}")

if issues:
    print(f"VERIFICATION FAILED — {len(issues)} error(s):")
    for issue in issues:
        print(f"  {issue}")
    print("\nFix these errors and re-save before outputting results.")
else:
    print(f"VERIFICATION PASSED — 0 errors across {len(wb_check.sheetnames)} sheets")
```

**If verification fails: fix the errors and run verification again. Do not output results until verification passes.**
