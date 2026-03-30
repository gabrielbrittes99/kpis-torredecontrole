import sys
import logging
from pprint import pprint

# Configura logs
logging.basicConfig(level=logging.DEBUG)

from data_cache import DataCache, get_fkm_df

def test():
    try:
        cache = DataCache()
        print("Buscando pedagios...")
        df = cache.get_df("pedagios")
        print("TIPO:", type(df))
        if df is not None and not df.empty:
            print("Sucesso! Linhas:", len(df))
            print("Colunas:", df.columns.tolist())
            print(df.head())
        else:
            print("DataFrame vazio ou None!")
    except Exception as e:
        print("EXCEPTION FATAL:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
