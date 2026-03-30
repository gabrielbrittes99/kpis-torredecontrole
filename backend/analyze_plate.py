import pandas as pd
from data_cache import cache

df = cache.get_df()
v = df[df['placa'] == 'SFG3J43'].sort_values('data_transacao').copy()
v['has_hodo'] = v['hodometro'].notna() & (v['hodometro'] > 0)
pd.set_option('display.max_rows', None)
print("--- TRANSAÇÕES SFG3J43 ---")
print(v[['data_transacao', 'hodometro', 'litragem', 'valor', 'has_hodo']])
print("\n--- RESUMO ---")
print(f"Total Transações: {len(v)}")
print(f"Com Hodômetro: {v['has_hodo'].sum()}")
print(f"Valor Total: {v['valor'].sum():.2f}")
print(f"Valor com Hodômetro: {v[v['has_hodo']]['valor'].sum():.2f}")
print(f"Litragem Total: {v['litragem'].sum():.2f}")
print(f"Litragem com Hodômetro: {v[v['has_hodo']]['litragem'].sum():.2f}")

hodo = v[v['has_hodo']]
if len(hodo) >= 2:
    km_range = hodo['hodometro'].max() - hodo['hodometro'].min()
    val_hodo = hodo['valor'].sum()
    print(f"Range KM: {km_range}")
    print(f"Custo/KM (Lógica atual): {val_hodo / km_range if km_range > 0 else 0:.4f}")

