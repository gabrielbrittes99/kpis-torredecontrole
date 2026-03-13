import data_cache
df = data_cache.cache.get_df()
print(f"Total rows: {len(df)}")
print(f"Min date: {df['data_transacao'].min()}")
print(f"Max date: {df['data_transacao'].max()}")
# check if there's data for current month (March 2026)
import datetime
now = datetime.datetime.now()
df_mes = df[(df['data_transacao'].dt.month == now.month) & (df['data_transacao'].dt.year == now.year)]
print(f"Rows for current month ({now.month}/{now.year}): {len(df_mes)}")
