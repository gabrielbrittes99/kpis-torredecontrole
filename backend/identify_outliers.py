from backend.data_cache import cache
from backend.config import get_fuel_group
import pandas as pd

try:
    df = cache.get_df()
    print(f"Total transações: {len(df)}")
    
    # 1. Fuel Outliers (Heavy/Caminhão + Gasolina/Álcool)
    heavy_groups = [
        "Caminhão17Ton", "Caminhão12Ton", "Caminhão10.5Ton", "Caminhão9Ton", 
        "Caminhão7.5Ton", "Caminhão6Ton", "Caminhão5.5Ton", "Caminhão5Ton", 
        "Caminhão4.2Ton", "Pesado"
    ]
    
    # Flag fuel mismatches
    df["abastecimento_indevido"] = False
    mask_heavy = df["grupo_veiculo"].isin(heavy_groups)
    mask_light_fuel = df["grupo_combustivel"].isin(["Gasolina", "Álcool"])
    df.loc[mask_heavy & mask_light_fuel, "abastecimento_indevido"] = True
    
    outliers = df[df["abastecimento_indevido"] == True][
        ["id", "data_transacao", "placa", "modelo_veiculo", "grupo_veiculo", "nome_combustivel", "litragem"]
    ]
    
    if outliers.empty:
        print("Nenhum outlier de combustível encontrado!")
    else:
        print(f"\n=== {len(outliers)} Outliers de Combustível Encontrados (Pesado+Leve) ===\n")
        print(outliers.head(20).to_string())
        if len(outliers) > 20:
            print(f"... e mais {len(outliers)-20} registros.")

    # 2. Outliers de Filial (Sem Filial - Venda?)
    # (Sem Movimentos por enquanto, vamos apenas ver os que estão com filial_nome vazio)
    sem_filial = df[df["filial_nome"] == ""][["placa", "modelo_veiculo"]].drop_duplicates()
    print(f"\n=== {len(sem_filial)} Placas sem Filial identificada (Possíveis Vendas/Novos) ===\n")
    print(sem_filial.head(20).to_string())

except Exception as e:
    print(f"Erro: {e}")
