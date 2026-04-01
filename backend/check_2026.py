import os
from db_pneus import get_pneus_df
import pandas as pd

try:
    df = get_pneus_df()
    if df.empty:
        print("Planilha vazia!")
    else:
        df_26 = df[df['ano'] == '2026']
        total = len(df_26)
        unitarias = len(df_26[df_26['quan'] == 1])
        pct = (unitarias / total * 100) if total > 0 else 0
        
        print("-" * 30)
        print(f"RESUMO AUDITORIA 2026")
        print(f"Total de Lançamentos: {total}")
        print(f"Linhas com Quan=1: {unitarias}")
        print(f"Percentual Emergência: {pct:.1f}%")
        print("-" * 30)
        print("OS PRIMEIROS 10 LANÇAMENTOS DE 2026:")
        print(df_26[['data', 'filial', 'quan', 'total', 'placa']].head(10).to_string())
except Exception as e:
    print(f"Erro na auditoria: {e}")
