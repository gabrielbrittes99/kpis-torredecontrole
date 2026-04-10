import sys
sys.path.append("/home/gabriel/projetos/kpis-torredecontrole/backend")
from dotenv import load_dotenv
load_dotenv("/home/gabriel/projetos/kpis-torredecontrole/backend/.env")

from backend.data_cache import cache

print('Carregando dados...')
df = cache.get_df()

if df.empty:
    print('Tentando carregar DW...')
    cache._load_from_dw()
    df = cache.get_df()

if df.empty:
    print('DataFrame vazio, listando fallback...')
    cache._load_fallback()
    df = cache.get_df()

if df.empty:
    print('Ainda vazio.')
else:
    # Filtra pesados abastecendo gasolina
    pesados = df[
        (df['grupo_veiculo'].isin(['Pesado', 'Caminhão', 'Cavalo Mecânico', 'Utilitário VUC', 'Semi Pesado', 'Onibus'])) & 
        (df['grupo_combustivel'].str.contains('Gasolina', case=False, na=False))
    ]
    if pesados.empty:
        print('Nenhum veiculo pesado abastecido com gasolina encontrado.')
    else:
        print(f"Encontrados {len(pesados)} registros:")
        pd.set_option('display.max_columns', None)
        print(pesados[['placa', 'modelo_veiculo', 'grupo_veiculo', 'grupo_combustivel', 'filial_nome', 'data_transacao', 'litragem', 'valor']].drop_duplicates().to_string())

