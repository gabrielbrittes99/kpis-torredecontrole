import data_cache
df = data_cache.cache.get_df()
print("--- COLUMNS ---")
for col in df.columns:
    print(col)
print("--- SAMPLE ---")
print(df.head(1).to_dict(orient='records'))
