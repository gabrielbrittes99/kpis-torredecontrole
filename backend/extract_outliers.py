import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from data_cache import cache
import pandas as pd

try:
    print("Carregando dados do cache...")
    df = cache.get_df()
    
    if df.empty:
        print("Aviso: Cache vazio.")
        sys.exit(0)

    print(f"Total de registros: {len(df)}")

    # 1. Outliers de Combustível (Pesado + Leve)
    df_comb = df[df["flag_combustivel_indevido"] == True].copy()
    if not df_comb.empty:
        print("\n=== OUTLIERS: COMBUSTÍVEL INDEVIDO (PESADO + GASOLINA/ÁLCOOL) ===")
        print(df_comb[["placa", "modelo_veiculo", "grupo_veiculo", "nome_combustivel", "valor"]].drop_duplicates("placa").to_string(index=False))
    else:
        print("\nNenhum outlier de combustível encontrado.")

    # 2. Outliers de Status (Venda/Vendido)
    df_venda = df[df["flag_venda"] == True].copy()
    if not df_venda.empty:
        print("\n=== OUTLIERS: VEÍCULOS EM VENDA/VENDIDO ===")
        print(df_venda[["placa", "modelo_veiculo", "filial_nome"]].drop_duplicates("placa").to_string(index=False))
    else:
        print("\nNenhum veículo em 'Venda' encontrado.")

    # 3. Placas sem Filial (Potencialmente novos ou problemas de cadastro)
    sem_filial = df[df["filial_nome"] == ""][["placa", "modelo_veiculo"]].drop_duplicates("placa")
    if not sem_filial.empty:
        print("\n=== AVISO: PLACAS SEM FILIAL IDENTIFICADA ===")
        print(sem_filial.to_string(index=False))

except Exception as e:
    print(f"Erro ao processar outliers: {e}")
