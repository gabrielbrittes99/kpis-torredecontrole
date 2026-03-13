import data_cache
df = data_cache.cache.get_df()
import datetime
now = datetime.datetime.now()
df_mes = df[(df['data_transacao'].dt.month == now.month) & (df['data_transacao'].dt.year == now.year)]
print(f"March 2026 rows: {len(df_mes)}")
print(f"Total value (sum): {df_mes['valor'].sum()}")
print(f"Max value: {df_mes['valor'].max()}")
print(f"Min value: {df_mes['valor'].min()}")
print(df_mes[['data_transacao', 'valor']].head(5))
print("---")
# Check if current day has data
hoje = now.date()
df_hoje = df_mes[df_mes['data_transacao'].dt.date == hoje]
print(f"Today's rows: {len(df_hoje)}")
print(f"Today's total: {df_hoje['valor'].sum()}")
