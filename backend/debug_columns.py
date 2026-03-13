import data_cache
df = data_cache.cache.get_df()
print("Columns:", list(df.columns))
if 'produto' in df.columns:
    print("Unique Products:", df['produto'].unique())
elif 'combustivel' in df.columns:
    print("Unique Fuels:", df['combustivel'].unique())
else:
    # Try searching for something related to fuels
    fuel_cols = [c for c in df.columns if 'comb' in c.lower() or 'prod' in c.lower()]
    print("Possible Fuel Columns:", fuel_cols)
