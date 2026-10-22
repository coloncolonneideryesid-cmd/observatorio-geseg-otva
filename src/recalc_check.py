#!/usr/bin/env python3
"""Recalcula el Excel con una instancia propia de Excel (sobre copia temporal) y cuenta errores de fórmula."""
import shutil, sys, tempfile, os
from pathlib import Path
import win32com.client as w

src = Path(__file__).resolve().parent.parent / "dist" / "Observatorio_Violencia_Armada_Colombia_2026.xlsx"
tmp = Path(tempfile.mkdtemp()) / src.name
shutil.copy(src, tmp)
x = w.DispatchEx("Excel.Application")
x.Visible = False
x.DisplayAlerts = False
try:
    wb = x.Workbooks.Open(str(tmp))
    x.CalculateFull()
    errs = 0
    for ws in wb.Worksheets:
        ur = ws.UsedRange
        for row in ur.Rows:
            for c in row.Cells:
                if isinstance(c.Value, int) and c.Text.startswith("#") or (c.Text or "").startswith("#"):
                    errs += 1
                    print("ERROR", ws.Name, c.Address, c.Text)
    ind = wb.Worksheets("Indicadores")
    for r in range(4, 22):
        print(ind.Cells(r, 1).Value, "=", ind.Cells(r, 2).Value)
    print("Errores de fórmula:", errs)
    wb.Close(False)
finally:
    x.Quit()
sys.exit(1 if errs else 0)
