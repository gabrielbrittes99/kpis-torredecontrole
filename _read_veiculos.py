#!/usr/bin/env python3
"""Read VEÍCULOS.xlsx using ONLY Python stdlib (zipfile + xml)."""
import csv
import sys
import zipfile
import xml.etree.ElementTree as ET

XLSX = '/home/gabriel/projetos/kpis-torredecontrole/documentacao API - Truckpag/VEÍCULOS.xlsx'
OUT  = '/home/gabriel/projetos/kpis-torredecontrole/veiculos_data.csv'

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def read_xlsx(path):
    with zipfile.ZipFile(path, 'r') as z:
        # Read shared strings
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            tree = ET.parse(z.open('xl/sharedStrings.xml'))
            for si in tree.findall('.//s:si', NS):
                texts = si.findall('.//s:t', NS)
                shared.append(''.join(t.text or '' for t in texts))

        # Read sheet1
        sheet_tree = ET.parse(z.open('xl/worksheets/sheet1.xml'))
        rows = []
        for row_el in sheet_tree.findall('.//s:sheetData/s:row', NS):
            cells = []
            for c in row_el.findall('s:c', NS):
                v_el = c.find('s:v', NS)
                val = v_el.text if v_el is not None else ''
                # 's' type = shared string
                if c.get('t') == 's' and val:
                    val = shared[int(val)] if int(val) < len(shared) else val
                cells.append(val or '')
            rows.append(cells)
        return rows

rows = read_xlsx(XLSX)
if not rows:
    print("Empty sheet")
    sys.exit(1)

with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    for row in rows:
        w.writerow(row)

print(f"DONE: {len(rows)} rows (incl header) written to {OUT}")
