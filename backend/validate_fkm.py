"""
Validação de qualidade dos dados FKM.

Cruza a planilha FKM com:
  - torre.fkm_reconciliacao (reconciliação TruckPag)
  - config.py (grupos esperados por grupo de veículo)

Execução:
  cd backend && python validate_fkm.py               # último mês
  cd backend && python validate_fkm.py 2026-02       # mês específico
  cd backend && python validate_fkm.py todos         # todos os meses
"""
import logging
import sys
from collections import defaultdict

import pandas as pd
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.WARNING, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# Limites de referência por grupo (min_kml, max_kml, max_preco_litro, min_preco_litro)
_KML_LIMITES = {
    "Leve":    (6.0,  25.0),
    "Médio":   (5.0,  18.0),
    "Pesado":  (4.0,  14.0),
    "3/4":     (3.0,  10.0),
    "Toco":    (2.5,   7.0),
    "Truck":   (2.0,   6.0),
    "Bitruck": (1.5,   5.0),
    "Moto":    (15.0, 60.0),
}
_PRECO_MIN = 4.0
_PRECO_MAX = 18.0
_KM_MIN_MES = 100  # abaixo disso → provável parado/manutenção


def _load_fkm(ano_mes: str | None) -> pd.DataFrame:
    from db_fkm import get_fkm_df
    df = get_fkm_df()
    if df.empty:
        print("ERRO: FKM vazio — verifique o arquivo xlsb")
        sys.exit(1)
    if ano_mes and ano_mes != "todos":
        df = df[df["ano_mes"] == ano_mes]
        if df.empty:
            print(f"ERRO: Nenhuma linha FKM para {ano_mes}")
            sys.exit(1)
    return df


def _load_reconciliacao(meses: list[str]) -> pd.DataFrame:
    """Carrega torre.fkm_reconciliacao para os meses informados."""
    try:
        from sqlalchemy import text
        from db_dw import get_dw_engine
        engine = get_dw_engine()
        placeholders = ", ".join(f"'{m}'" for m in meses)
        sql = f"""
            SELECT placa, ano_mes, litros_fkm, valor_fkm,
                   litros_truckpag, valor_truckpag, qtd_transacoes,
                   litros_efetivo, valor_efetivo,
                   litros_direto, valor_direto,
                   pct_truckpag, preco_litro_implicito,
                   corrigido_por_truckpag, flags, tem_alerta
            FROM torre.fkm_reconciliacao
            WHERE ano_mes IN ({placeholders})
        """
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn)
    except Exception as e:
        logger.warning(f"fkm_reconciliacao não acessível: {e}")
        return pd.DataFrame()


def _sep(titulo: str):
    print(f"\n{'═' * 70}")
    print(f"  {titulo}")
    print('═' * 70)


def _sub(titulo: str):
    print(f"\n── {titulo} {'─' * max(0, 60 - len(titulo))}")


def validate(ano_mes_arg: str | None):
    ano_mes = None if (ano_mes_arg == "todos" or not ano_mes_arg) else ano_mes_arg

    df = _load_fkm(ano_mes)

    meses = sorted(df["ano_mes"].dropna().unique().tolist())
    if not ano_mes:
        # Usa último mês por padrão
        if ano_mes_arg != "todos":
            ano_mes = meses[-1]
            df = df[df["ano_mes"] == ano_mes]
            meses = [ano_mes]

    recon = _load_reconciliacao(meses)
    tem_recon = not recon.empty

    _sep(f"VALIDAÇÃO FKM — {'todos os meses' if ano_mes_arg == 'todos' else meses}")
    print(f"  Linhas: {len(df):,}  |  Placas: {df['placa'].nunique()}  |  Meses: {len(meses)}")
    print(f"  Reconciliação DW: {'✓ disponível' if tem_recon else '✗ não disponível (rode etl_fkm_reconcilia.py)'}")

    problemas: dict[str, list[dict]] = defaultdict(list)

    # ── 1. Grupos não mapeados / inesperados ─────────────────────────────────
    from config import FKM_GRUPO_MAP, VEICULO_GROUPS
    grupos_validos = set(VEICULO_GROUPS)
    grupos_no_fkm = df["grupo_veiculo"].dropna().unique()
    grupos_desconhecidos = [g for g in grupos_no_fkm if g and g not in grupos_validos]

    _sub("1. GRUPOS NÃO MAPEADOS")
    if grupos_desconhecidos:
        for g in sorted(grupos_desconhecidos):
            qtd = int((df["grupo_veiculo"] == g).sum())
            print(f"  ⚠  '{g}'  →  {qtd} veículo(s) — adicionar ao FKM_GRUPO_MAP")
            problemas["grupo_nao_mapeado"].append({"grupo": g, "qtd": qtd})
    else:
        print("  ✓ Todos os grupos mapeados corretamente")

    # ── 2. KM/L fora dos limites esperados por grupo ──────────────────────────
    _sub("2. KM/L FORA DO LIMITE POR GRUPO")
    df_kml = df[df["total_km"] > _KM_MIN_MES].copy()
    df_kml = df_kml[df_kml["media_kml"] > 0]
    # Motos classificadas como Leve têm km/L naturalmente alto — excluir
    df_kml = df_kml[~df_kml["modelo"].str.lower().str.contains("moto|cg 160|cg160", na=False)]

    kml_problemas = []
    for _, row in df_kml.iterrows():
        grp = row["grupo_veiculo"]
        if grp not in _KML_LIMITES:
            continue
        kmin, kmax = _KML_LIMITES[grp]
        kml = row["media_kml"]
        if kml < kmin or kml > kmax:
            kml_problemas.append({
                "placa": row["placa"], "grupo": grp, "mes": row["ano_mes"],
                "km_l": round(kml, 2), "limite": f"{kmin}–{kmax}",
                "filial": row.get("filial", ""),
            })

    if kml_problemas:
        print(f"  {len(kml_problemas)} linha(s) com km/L suspeito:")
        for p in sorted(kml_problemas, key=lambda x: abs(x["km_l"]), reverse=True)[:20]:
            print(f"  ⚠  {p['placa']} | {p['grupo']} | {p['mes']} | {p['km_l']} km/L (esperado {p['limite']}) | {p['filial']}")
        problemas["kml_suspeito"].extend(kml_problemas)
    else:
        print("  ✓ Todos os km/L dentro dos limites esperados")

    # ── 3. Preço/L implícito suspeito ────────────────────────────────────────
    _sub("3. PREÇO/LITRO SUSPEITO (fora de R$ 4–18)")
    df_preco = df[(df["litros_comb"] > 0) & (df["valor_comb"] > 0)].copy()
    df_preco["preco_impl"] = df_preco["valor_comb"] / df_preco["litros_comb"]
    preco_ruim = df_preco[(df_preco["preco_impl"] < _PRECO_MIN) | (df_preco["preco_impl"] > _PRECO_MAX)]

    if not preco_ruim.empty:
        print(f"  {len(preco_ruim)} linha(s) com preço/L suspeito:")
        for _, row in preco_ruim.head(20).iterrows():
            print(f"  ⚠  {row['placa']} | {row['grupo_veiculo']} | {row['ano_mes']} "
                  f"| R$ {row['preco_impl']:.2f}/L "
                  f"| {row['litros_comb']:.0f}L / R$ {row['valor_comb']:.0f}")
            problemas["preco_suspeito"].append({
                "placa": row["placa"], "mes": row["ano_mes"],
                "preco_impl": round(row["preco_impl"], 2),
            })
    else:
        print("  ✓ Todos os preços dentro do intervalo esperado")

    # ── 4. Km zerado ou muito baixo ──────────────────────────────────────────
    _sub(f"4. VEÍCULOS COM KM ≤ {_KM_MIN_MES} km NO MÊS (parado / manutenção)")
    df_km0 = df[df["total_km"] <= _KM_MIN_MES]
    if not df_km0.empty:
        por_mes = df_km0.groupby("ano_mes").size()
        for mes, qtd in por_mes.items():
            print(f"  ⚠  {mes}: {qtd} veículo(s) com km ≤ {_KM_MIN_MES}")
        print(f"  Total: {len(df_km0)} linhas — estes veículos são excluídos do ranking de eficiência")
        problemas["km_baixo"].append({"total": len(df_km0)})
    else:
        print(f"  ✓ Nenhum veículo com km ≤ {_KM_MIN_MES} km")

    # ── 5. Veículos sem combustível informado ────────────────────────────────
    _sub("5. SEM COMBUSTÍVEL INFORMADO (litros = 0 e valor = 0)")
    sem_comb = df[(df["litros_comb"] == 0) & (df["valor_comb"] == 0)]
    if not sem_comb.empty:
        print(f"  {len(sem_comb)} linha(s) sem consumo de combustível registrado:")
        for _, row in sem_comb.head(10).iterrows():
            print(f"  ⚠  {row['placa']} | {row['grupo_veiculo']} | {row['ano_mes']} | {row.get('filial', '')}")
        problemas["sem_combustivel"].append({"total": len(sem_comb)})
    else:
        print("  ✓ Todos os veículos têm consumo registrado")

    # ── 6. Reconciliação TruckPag (só se disponível) ─────────────────────────
    if tem_recon:
        _sub("6. RECONCILIAÇÃO FKM × TRUCKPAG")

        corrigidos = recon[recon["corrigido_por_truckpag"] == True]
        direto = recon[recon["valor_direto"] > 100]
        sem_tp = recon[(recon["qtd_transacoes"] == 0) & (recon["valor_fkm"] > 0)]
        alertas = recon[recon["tem_alerta"] == True]

        print(f"  Corrigidos pelo TruckPag (FKM < TruckPag): {len(corrigidos)}")
        print(f"  Com faturamento direto (FKM > TruckPag > 0): {len(direto)}")
        print(f"  Sem nenhuma transação TruckPag: {len(sem_tp)}")
        print(f"  Com algum alerta de qualidade: {len(alertas)}")

        if not alertas.empty:
            from collections import Counter
            todas_flags = [f for flags in alertas["flags"] for f in (flags or [])]
            contagem = Counter(todas_flags)
            print(f"\n  Alertas por tipo:")
            for flag, n in contagem.most_common():
                print(f"    {flag}: {n}")

        # Veículos com discrepância grave (> 50% entre FKM e TruckPag)
        recon_disc = recon[recon["valor_fkm"] > 0].copy()
        recon_disc["disc_pct"] = abs(recon_disc["valor_fkm"] - recon_disc["valor_truckpag"]) / recon_disc["valor_fkm"] * 100
        graves = recon_disc[recon_disc["disc_pct"] > 50].sort_values("disc_pct", ascending=False)

        if not graves.empty:
            print(f"\n  {len(graves)} veículo(s) com discrepância > 50% entre FKM e TruckPag:")
            for _, row in graves.head(15).iterrows():
                print(f"  ⚠  {row['placa']} | {row['ano_mes']} "
                      f"| FKM R$ {row['valor_fkm']:.0f} "
                      f"| TruckPag R$ {row['valor_truckpag']:.0f} "
                      f"| disc {row['disc_pct']:.0f}%"
                      f"{'  [corrigido]' if row['corrigido_por_truckpag'] else ''}")
            problemas["discrepancia_grave"].append({"total": len(graves)})
    else:
        _sub("6. RECONCILIAÇÃO FKM × TRUCKPAG")
        print("  ✗ Dados de reconciliação não disponíveis.")
        print("    Rode: cd backend && python etl_fkm_reconcilia.py")

    # ── 7. Filiais não reconhecidas ──────────────────────────────────────────
    _sub("7. FILIAIS NÃO RECONHECIDAS NO CADASTRO")
    from config import FILIAIS_MAP, PALMAS_FILIAL
    # FKM usa nomes por extenso; FILIAIS_MAP usa siglas do SQL Server como chave.
    # Monta conjunto de nomes de exibição válidos, normalizando acentos para comparação.
    import unicodedata
    def _strip_accents(s):
        return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()
    nomes_validos_norm = {_strip_accents(v["nome"]) for v in FILIAIS_MAP.values()} | {_strip_accents(PALMAS_FILIAL["nome"])}
    filiais_fkm = df["filial"].dropna().unique()
    filiais_desconhecidas = [f for f in filiais_fkm if f and _strip_accents(f) not in nomes_validos_norm]
    if filiais_desconhecidas:
        for f in sorted(filiais_desconhecidas):
            qtd = int((df["filial"] == f).sum())
            print(f"  ⚠  '{f}' — {qtd} linha(s) — não reconhecida (verificar config.py)")
            problemas["filial_desconhecida"].append({"filial": f, "qtd": qtd})
    else:
        print("  ✓ Todas as filiais reconhecidas")

    # ── 8. Veículos duplicados no mesmo mês ──────────────────────────────────
    _sub("8. LINHAS DUPLICADAS (mesma placa+mês+filial+contrato)")
    dupl = df[df.duplicated(subset=["placa", "ano_mes", "filial", "contrato"], keep=False)]
    if not dupl.empty:
        print(f"  {len(dupl)} linhas duplicadas:")
        for (p, m, f, c), g in dupl.groupby(["placa", "ano_mes", "filial", "contrato"]):
            print(f"  ⚠  {p} | {m} | {f} | contrato={c} — {len(g)}x")
        problemas["duplicado"].append({"total": len(dupl)})
    else:
        print("  ✓ Nenhuma duplicata encontrada")

    # ── 9. Contratos ─────────────────────────────────────────────────────────
    _sub("9. CONTRATOS")
    contratos = df["contrato"].dropna().unique()
    sem_contrato = df[df["contrato"].isin(["", "nan", "None"]) | df["contrato"].isna()]
    print(f"  {len(contratos)} contrato(s) distintos: {sorted(contratos)[:10]}")
    if not sem_contrato.empty:
        print(f"  ⚠  {len(sem_contrato)} veículo(s) sem contrato informado")
        problemas["sem_contrato"].append({"total": len(sem_contrato)})
    else:
        print("  ✓ Todos os veículos têm contrato")

    # ── RESUMO FINAL ─────────────────────────────────────────────────────────
    _sep("RESUMO")
    total_problemas = sum(len(v) for v in problemas.values())
    if total_problemas == 0:
        print("  ✓ Nenhum problema encontrado nos dados FKM")
    else:
        print(f"  {total_problemas} categorias de problema encontradas:")
        labels = {
            "grupo_nao_mapeado":  "Grupos não mapeados",
            "kml_suspeito":       "km/L fora do limite",
            "preco_suspeito":     "Preço/L suspeito",
            "km_baixo":           "Veículos com km baixo",
            "sem_combustivel":    "Sem combustível registrado",
            "discrepancia_grave": "Discrepância > 50% vs TruckPag",
            "filial_desconhecida":"Filiais não reconhecidas",
            "duplicado":          "Linhas duplicadas",
            "sem_contrato":       "Sem contrato",
        }
        for chave, itens in problemas.items():
            n = sum(i.get("total", 1) if "total" in i else 1 for i in itens)
            print(f"  • {labels.get(chave, chave)}: {n}")
    print()


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    validate(arg)
