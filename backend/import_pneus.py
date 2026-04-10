# -*- coding: utf-8 -*-
import os, sys
from db_pneus import get_pneus_df
from db_gestao_pneus import _e, text

def main():
    print("Baixando planilha online...")
    df = get_pneus_df()
    if df.empty:
        print("Planilha vazia.")
        return
        
    df_clean = df.drop_duplicates(subset=["n_fogo"], keep="last")
    df_clean = df_clean[df_clean["n_fogo"].astype(str).str.strip() != ""]
    
    with _e().begin() as conn:
        filiais_db = conn.execute(text("SELECT id, nome FROM gp_filiais")).mappings().all()
        mapa_filiais = {str(f['nome']).upper(): f['id'] for f in filiais_db}
        
        veiculos_db = conn.execute(text("SELECT id, placa FROM gp_veiculos")).mappings().all()
        mapa_veiculos = {str(v['placa']).upper(): v['id'] for v in veiculos_db}
        
    criados = 0
    ignorados = 0
    with _e().begin() as conn:
        for idx, row in df_clean.iterrows():
            nfog = str(row.get("n_fogo", "")).strip().upper()
            exist = conn.execute(text("SELECT id FROM gp_pneus WHERE numero_fogo=:nf"), {"nf": nfog}).scalar()
            if exist:
                ignorados += 1
                continue
            
            # Filial
            f_nome = str(row.get("filial", "")).strip().upper()
            fid = mapa_filiais.get(f_nome)
            if not fid and f_nome:
                for n_db, id_db in mapa_filiais.items():
                    if n_db in f_nome or f_nome in n_db:
                        fid = id_db
                        break
            if not fid:
                try: 
                    conn.execute(text("INSERT INTO gp_filiais (nome) VALUES (:n)"), {"n": f_nome or "SEM FILIAL"})
                    fid = conn.execute(text("SELECT last_insert_rowid()")).scalar()
                    mapa_filiais[f_nome] = fid
                except Exception:
                    fid = 1 # fallback se existir pelo menos uma
                    
            # Veiculo e status
            status = "estoque"
            placa = str(row.get("placa", "")).strip().upper().replace("-", "")
            vid = None
            if placa:
                vid = mapa_veiculos.get(placa)
                if vid:
                   status = "em_uso"
                   
            marca = str(row.get("marca", "")).strip()[:100]
            modelo = str(row.get("modelo", "")).strip()[:100]
            medida = str(row.get("medida", "")).strip()[:50]
            dot = str(row.get("dot", "")).strip()[:50]
            valor = float(row.get("valor_un", 0) or 0)
            nf = str(row.get("nf", "")).strip()
            forn = str(row.get("fornecedor", "")).strip()
            
            if not nfog:
                continue
                
            try:
                conn.execute(text('''
                    INSERT INTO gp_pneus (numero_fogo, marca, modelo, medida, dot, valor, filial_id, nf, fornecedor, veiculo_id, status)
                    VALUES (:nfog, :ma, :mo, :med, :d, :val, :fi, :nf, :forn, :vid, :st)
                '''), {
                    "nfog": nfog, "ma": marca, "mo": modelo, "med": medida, "d": dot, "val": valor, 
                    "fi": fid, "nf": nf, "forn": forn, "vid": vid, "st": status
                })
                criados += 1
            except Exception as e:
                ignorados += 1

    print(f"Importacao de pneus da planilha online concluida!")
    print(f"Pneus criados: {criados}")
    print(f"Pneus ignorados (ja existiam): {ignorados}")

if __name__ == '__main__':
    main()
