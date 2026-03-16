#!/bin/bash
cd /home/gabriel/projetos/kpis-torredecontrole
python3 -m venv .venv
source .venv/bin/activate
pip install pandas openpyxl -q
python3 -c "
import pandas as pd
df = pd.read_excel('documentacao API - Truckpag/VEÍCULOS.xlsx')
df.to_csv('veiculos_data.csv', index=False)
print(df.to_string())
"
