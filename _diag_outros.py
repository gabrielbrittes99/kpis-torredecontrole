#!/usr/bin/env python3
"""Diagnóstico: identifica veículos classificados como 'Outros'."""
import sys
sys.path.insert(0, '/home/gabriel/projetos/kpis-torredecontrole/backend')

from config import get_veiculo_group
from data_cache import cache

df = cache.get_df()

# Classifica cada veículo
df['grupo_calc'] = [
    get_veiculo_group(str(m or ''), str(b or ''))
    for m, b in zip(df['modelo_veiculo'], df['marca_veiculo'])
]

# Filtra os que caem em "Outros"
outros = df[df['grupo_calc'] == 'Outros'][['placa', 'modelo_veiculo', 'marca_veiculo']].drop_duplicates()

if outros.empty:
    print("Nenhum veículo classificado como 'Outros'!")
else:
    print(f"=== {len(outros)} veículos classificados como 'Outros' ===\n")
    for _, r in outros.iterrows():
        print(f"  Placa={r['placa']:10s}  Modelo={str(r['modelo_veiculo']):50s}  Marca={r['marca_veiculo']}")

print("\n\n=== Distribuição dos grupos ===")
counts = df.groupby('grupo_calc')['placa'].nunique().sort_values(ascending=False)
for g, c in counts.items():
    print(f"  {g:25s} → {c} veículos")
