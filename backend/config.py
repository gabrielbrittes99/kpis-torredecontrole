from typing import Optional

# ---------------------------------------------------------------------------
# GRUPOS DE COMBUSTÍVEL
# ---------------------------------------------------------------------------

# De → Para (nome_combustivel no banco → grupo)
FUEL_GROUP_MAP: dict[str, str] = {
    # Diesel — todas as variantes
    "diesel":                    "Diesel",
    "diesel s10":                "Diesel",
    "diesel s-10":               "Diesel",
    "diesel s500":               "Diesel",
    "diesel s-500":              "Diesel",
    "diesel s10 aditivado":      "Diesel",
    "diesel s500 aditivado":     "Diesel",
    "diesel aditivado":          "Diesel",
    "diesel comum":              "Diesel",
    "oleo diesel":               "Diesel",
    "óleo diesel":               "Diesel",
    "biodiesel":                 "Diesel",
    "b10":                       "Diesel",
    "b12":                       "Diesel",
    "b13":                       "Diesel",
    # Gasolina — todas as variantes
    "gasolina":                  "Gasolina",
    "gasolina c":                "Gasolina",
    "gasolina comum":            "Gasolina",
    "gasolina aditivada":        "Gasolina",
    "gasolina premium":          "Gasolina",
    "gasolina podium":           "Gasolina",
    "gasolina v-power":          "Gasolina",
    "gasolina select":           "Gasolina",
    "gasolina boa":              "Gasolina",
    "gasolina super":            "Gasolina",
    "gasolina aditivada premium": "Gasolina",
    # Álcool / Etanol — todas as variantes
    "alcool":                    "Álcool",
    "álcool":                    "Álcool",
    "etanol":                    "Álcool",
    "etanol hidratado":          "Álcool",
    "alcool comum":              "Álcool",
    "alcool aditivado":          "Álcool",
    "álcool comum":              "Álcool",
    "álcool aditivado":          "Álcool",
    "etanol aditivado":          "Álcool",
    # Arla
    "arla":                      "Arla",
    "arla 32":                   "Arla",
    "arla32":                    "Arla",
}

FUEL_GROUPS = ["Diesel", "Gasolina", "Álcool", "Arla"]


def get_fuel_group(nome_combustivel: str) -> str:
    """Retorna o grupo do combustível ou 'Outros' se não mapeado."""
    return FUEL_GROUP_MAP.get(nome_combustivel.lower().strip(), "Outros")


# ---------------------------------------------------------------------------
# FILIAIS GRITSCH
# ---------------------------------------------------------------------------

# Sigla SQL Server → (nome_exibicao, estado, regiao)
FILIAIS_MAP: dict[str, dict] = {
    # ── Referências (veículos de uso interno / base) ───────────────────────
    "REFERÊNCIA CURITIBA":       {"nome": "Referência Curitiba",       "estado": "PR", "regiao": "Sul"},
    "REFERÊNCIA BRASILIA":       {"nome": "Referência Brasília",       "estado": "DF", "regiao": "Centro-Oeste"},
    "REFERÊNCIA SÃO PAULO":      {"nome": "Referência São Paulo",      "estado": "SP", "regiao": "Sudeste"},
    "REFERÊNCIA SINOP":          {"nome": "Referência Sinop",          "estado": "MT", "regiao": "Centro-Oeste"},
    # ── Sul / PR ──────────────────────────────────────────────────────────
    "GRITSCH - CWB (BASE)":      {"nome": "Gritsch Curitiba",         "estado": "PR", "regiao": "Sul"},
    "GRITSCH - CWB (DIR)":       {"nome": "Gritsch Curitiba",         "estado": "PR", "regiao": "Sul"},
    "GRITSCH - CWB (ECT)":       {"nome": "Gritsch Curitiba",         "estado": "PR", "regiao": "Sul"},
    "GRITSCH - MATRIZ":          {"nome": "Gritsch Curitiba",         "estado": "PR", "regiao": "Sul"},
    "GRITSCH - LDB":             {"nome": "Gritsch Londrina",         "estado": "PR", "regiao": "Sul"},
    "GRITSCH - MGA":             {"nome": "Gritsch Maringá",          "estado": "PR", "regiao": "Sul"},
    "GRITSCH - PGR":             {"nome": "Gritsch Ponta Grossa",     "estado": "PR", "regiao": "Sul"},
    "GRITSCH - PBC":             {"nome": "Gritsch Pato Branco",      "estado": "PR", "regiao": "Sul"},
    "GRITSCH - GPA":             {"nome": "Gritsch Guarapuava",       "estado": "PR", "regiao": "Sul"},
    "GRITSCH - CSC":             {"nome": "Gritsch Cascavel",         "estado": "PR", "regiao": "Sul"},
    "GRITSCH - UMU":             {"nome": "Gritsch Umuarama",         "estado": "PR", "regiao": "Sul"},
    # ── Sul / SC ──────────────────────────────────────────────────────────
    "GRITSCH - FLN":             {"nome": "Gritsch Florianópolis",    "estado": "SC", "regiao": "Sul"},
    "GRITSCH - JOI":             {"nome": "Gritsch Joinville",        "estado": "SC", "regiao": "Sul"},
    "GRITSCH - BLN":             {"nome": "Gritsch Blumenau",         "estado": "SC", "regiao": "Sul"},
    "GRITSCH - CHA":             {"nome": "Gritsch Chapecó",          "estado": "SC", "regiao": "Sul"},
    "GRITSCH - CRI":             {"nome": "Gritsch Criciúma",         "estado": "SC", "regiao": "Sul"},
    "GRITSCH - CTB":             {"nome": "Gritsch Curitibanos",      "estado": "SC", "regiao": "Sul"},
    # ── Sul / RS ──────────────────────────────────────────────────────────
    "GRITSCH - POA":             {"nome": "Gritsch Porto Alegre",     "estado": "RS", "regiao": "Sul"},
    "GRITSCH - CXJ":             {"nome": "Gritsch Caxias do Sul",    "estado": "RS", "regiao": "Sul"},
    # ── Centro-Oeste / GO ─────────────────────────────────────────────────
    "GRITSCH - GOI":             {"nome": "Gritsch Goiânia",          "estado": "GO", "regiao": "Centro-Oeste"},
    "GRITSCH - RVD":             {"nome": "Gritsch Rio Verde",        "estado": "GO", "regiao": "Centro-Oeste"},
    "GRITSCH - ITR":             {"nome": "Gritsch Itumbiara",        "estado": "GO", "regiao": "Centro-Oeste"},
    # ── Centro-Oeste / MT ─────────────────────────────────────────────────
    "GRITSCH - SNO":             {"nome": "Gritsch Sinop",            "estado": "MT", "regiao": "Centro-Oeste"},
    "GRITSCH - RDN":             {"nome": "Gritsch Rondonópolis",     "estado": "MT", "regiao": "Centro-Oeste"},
    "GRITSCH - CGB":             {"nome": "Gritsch Cuiabá",           "estado": "MT", "regiao": "Centro-Oeste"},
    # ── Centro-Oeste / MS + DF ────────────────────────────────────────────
    "GRITSCH - CGR":             {"nome": "Gritsch Campo Grande",     "estado": "MS", "regiao": "Centro-Oeste"},
    "GRITSCH - BSB":             {"nome": "Gritsch Brasília",         "estado": "DF", "regiao": "Centro-Oeste"},
    # ── Sudeste / SP ──────────────────────────────────────────────────────
    "GRITSCH - SAO (FREGUESIA)": {"nome": "Gritsch São Paulo",        "estado": "SP", "regiao": "Sudeste"},
    "GRITSCH - SAO (PERUS)":     {"nome": "Gritsch São Paulo (Perus)","estado": "SP", "regiao": "Sudeste"},
    # ── Nordeste / BA ─────────────────────────────────────────────────────
    "GRITSCH - SSA":             {"nome": "Gritsch Salvador",         "estado": "BA", "regiao": "Nordeste"},
}

# Filial Palmas — sem sigla no SQL Server ainda, identificada por placa
PALMAS_FILIAL = {"nome": "Gritsch Palmas", "estado": "TO", "regiao": "Norte"}
PALMAS_PLACAS: set[str] = {
    "RHS8D34", "SDR4D98", "SDR8E04", "SDR8E58",
    "SDX2J14", "SEN1C55", "SEN1C56", "SFL1E46", "UAV5J75",
}

# TBU9D20 agora está em "REFERÊNCIA CURITIBA" no SQL Server — removida do hardcode
# CWB_BASE_PLACAS mantido como set vazio para compatibilidade com data_cache.py
CWB_BASE_FILIAL = {"nome": "Referência Curitiba", "estado": "PR", "regiao": "Sul"}
CWB_BASE_PLACAS: set[str] = set()

# Placas renomeadas: placa antiga → placa nova
# As transações históricas da placa antiga são reindexadas para a nova,
# permitindo lookup de filial e continuidade dos dados.
PLACAS_RENOMEADAS: dict[str, str] = {
    "TBI2068": "UBO0E91",  # Placa trocada — nova: UBO-0E91 (GRITSCH - MATRIZ)
}

IGNORAR_PLACAS: set[str] = set()


def get_filial_info(sigla_sqlserver: str) -> dict:
    """Retorna nome, estado e região da filial pelo código do SQL Server."""
    return FILIAIS_MAP.get(sigla_sqlserver, {
        "nome": sigla_sqlserver or "Sem filial",
        "estado": "?",
        "regiao": "?",
    })


def get_filial_by_placa(placa: str) -> dict | None:
    """Retorna os dados de Palmas ou Curitiba se a placa for uma das hardcoded."""
    p_upper = placa.upper().strip()
    if p_upper in PALMAS_PLACAS:
        return PALMAS_FILIAL
    if p_upper in CWB_BASE_PLACAS:
        return CWB_BASE_FILIAL
    return None


REGIOES = ["Sul", "Centro-Oeste", "Sudeste", "Nordeste", "Norte"]


# ---------------------------------------------------------------------------
# GRUPOS DE VEÍCULO
# ---------------------------------------------------------------------------
# Mapeamento baseado na planilha VEÍCULOS.xlsx (fonte: TruckPag)
# Regras avaliadas em ordem; a primeira que bater é aplicada.
# Cada regra: (substring_no_modelo, substring_na_marca_ou_None, grupo)
# Comparação feita em lowercase; marca None = qualquer marca.

VEICULO_RULES: list[tuple[str, str | None, str]] = [
    # ── Moto ─────────────────────────────────────────────────────────────────
    ("cg 160",          None,       "Moto"),
    ("cg160",           None,       "Moto"),

    # ══════════════════════════════════════════════════════════════════════════
    # BITRUCK / 6x4 (Antigo Caminhão 17 Ton)
    # ══════════════════════════════════════════════════════════════════════════
    ("30-330",          None,       "Bitruck"),
    ("30.330",          None,       "Bitruck"),
    ("30-280",          None,       "Bitruck"),
    ("30.280",          None,       "Bitruck"),
    ("vm 330",          None,       "Bitruck"),
    ("26-260",          None,       "Bitruck"),
    ("24.260",          None,       "Bitruck"),
    ("24-260",          None,       "Bitruck"),

    # ══════════════════════════════════════════════════════════════════════════
    # TRUCK (Antigo Caminhão 12 Ton)
    # ══════════════════════════════════════════════════════════════════════════
    ("cargo 2423",      None,       "Truck"),
    ("2423",            "ford",     "Truck"),
    ("24-280",          None,       "Truck"),
    ("24.280",          None,       "Truck"),
    ("vm 290",          None,       "Truck"),
    ("atego 2429",      None,       "Truck"),
    ("atego 2430",      None,       "Truck"),
    ("15.190",          None,       "Truck"),
    ("15-190",          None,       "Truck"),
    ("20.480",          None,       "Truck"),
    ("constellation",   None,       "Truck"),
    ("constelation",    None,       "Truck"),
    ("costellation",    None,       "Truck"),
    ("vm",              "volvo",    "Truck"),

    # ══════════════════════════════════════════════════════════════════════════
    # TOCO (Antigos 10.5, 9, 7.5 Ton)
    # ══════════════════════════════════════════════════════════════════════════
    ("17-230",          None,       "Toco"),
    ("17.230",          None,       "Toco"),
    ("17-210",          None,       "Toco"),
    ("17.210",          None,       "Toco"),
    ("atego 1719",      None,       "Toco"),
    ("13-180",          None,       "Toco"),
    ("13.180",          None,       "Toco"),
    ("atego 1419",      None,       "Toco"),
    ("14-190",          None,       "Toco"),
    ("14.190",          None,       "Toco"),
    ("14-210",          None,       "Toco"),
    ("14.210",          None,       "Toco"),
    ("atego",           None,       "Toco"),

    # ══════════════════════════════════════════════════════════════════════════
    # 3/4 (Antigos 6, 5.5, 5, 4.2 Ton)
    # ══════════════════════════════════════════════════════════════════════════
    ("11-180",          None,       "3/4"),
    ("11.180",          None,       "3/4"),
    ("accelo 1016",     None,       "3/4"),
    ("accelo 1017",     None,       "3/4"),
    ("10.160",          None,       "3/4"),
    ("10-160",          None,       "3/4"),
    ("9-170",           None,       "3/4"),
    ("9.170",           None,       "3/4"),
    ("8-160",           None,       "3/4"),
    ("8.160",           None,       "3/4"),
    ("cargo 816",       None,       "3/4"),
    ("816",             "ford",     "3/4"),
    ("hd80",            None,       "3/4"),
    ("hd 80",           None,       "3/4"),
    ("accelo 815",      None,       "3/4"),
    ("accelo 817",      None,       "3/4"),
    ("accelo",          None,       "3/4"),

    # ══════════════════════════════════════════════════════════════════════════
    # PESADO — vans, kombi e furgões grandes (diesel e gasolina)
    # ══════════════════════════════════════════════════════════════════════════
    ("master",          None,       "Pesado"),
    ("sprinter",        None,       "Pesado"),
    ("mb 311",          None,       "Pesado"),
    ("transit",         None,       "Pesado"),
    ("ducato",          None,       "Pesado"),
    ("hr",              "hy",       "Pesado"),
    ("hr",              "kia",      "Pesado"),
    ("furgão",          None,       "Pesado"),
    ("furgao",          None,       "Pesado"),
    ("s10",             None,       "Pesado"),
    ("kombi",           None,       "Pesado"),

    # ══════════════════════════════════════════════════════════════════════════
    # MÉDIO — pickups, utilitários leves, furgonetas
    # ══════════════════════════════════════════════════════════════════════════
    ("strada",          None,       "Médio"),
    ("saveiro",         None,       "Médio"),
    ("fiorino",         None,       "Médio"),
    ("partner",         None,       "Médio"),
    ("oroch",           None,       "Médio"),
    ("duster",          None,       "Médio"),

    # ══════════════════════════════════════════════════════════════════════════
    # LEVE — passeio, hatches, sedãs
    # ══════════════════════════════════════════════════════════════════════════
    ("gol",             None,       "Leve"),
    ("polo",            None,       "Leve"),
    ("virtus",          None,       "Leve"),
    ("voyage",          None,       "Leve"),
    ("argo",            None,       "Leve"),
    ("cronos",          None,       "Leve"),
    ("uno",             None,       "Leve"),
    ("208",             None,       "Leve"),
    ("onix",            None,       "Leve"),
    ("spin",            None,       "Leve"),
]

VEICULO_GROUPS = [
    "Bitruck",
    "Truck",
    "Toco",
    "3/4",
    "Pesado",
    "Médio",
    "Leve",
    "Moto",
]

# Grupos que operam obrigatoriamente a Diesel
HEAVY_GROUPS = [
    "Bitruck",
    "Truck",
    "Toco",
    "3/4",
]

# Exceções manuais por placa (Placa -> Grupo)
# Útil quando o modelo no cadastro está incorreto ou é genérico demais.
VEICULO_PLATE_OVERRIDES: dict[str, str] = {
    "SEN1C55": "Leve",  # Cadastrado como Master, mas é um Polo (confirmado pelo usuário)
}

# Exceções manuais de combustível por placa — removidas.
# Todos os veículos afetados (Sprinter, Master, caminhões VW) são confirmados como Diesel
# no SQL Server. Qualquer registro com combustível errado será capturado automaticamente
# pelo flag_combustivel_indevido (is_fuel_incompatible) e nos abastecimentos suspeitos.
FUEL_PLATE_OVERRIDES: dict[str, str] = {}

# Exceções manuais de filial por placa (Placa -> Sigla Filial BlueFleet)
FILIAL_PLATE_OVERRIDES: dict[str, str] = {
    "RHF1B45": "REFERÊNCIA SINOP",
    "SDX2A65": "Gritsch Brasília",
}


# ---------------------------------------------------------------------------
# KM/L DE REFERÊNCIA POR GRUPO DE VEÍCULO
# ---------------------------------------------------------------------------
# Fonte: calculado a partir dos dados reais da frota Gritsch (TruckPag, Mar/2026).
# Meta = percentil 75 da frota atual (o que um veículo bem mantido consegue).
# Estrutura: grupo → combustível → (kml_meta, kml_alerta)
#   kml_meta    = p75 da frota (meta de eficiência)
#   kml_alerta  = p25 da frota (abaixo disso = preocupante)
# Grupos sem dados reais suficientes mantêm estimativas de mercado.

KML_REFERENCIA: dict[str, dict[str, tuple]] = {
    "Leve": {
        "Gasolina": (13.69, 10.83),
        "Álcool":   (11.14,  7.86),
    },
    "Médio": {
        "Gasolina": (11.72,  9.23),
        "Álcool":   ( 8.44,  6.99),
    },
    "Pesado": {
        "Diesel":   (10.18,  8.14),
        "Gasolina": (None,   9.60),
        "Álcool":   ( 8.95,  8.90),
    },
    "Moto": {
        "Gasolina": (None,  31.00),
    },
    "3/4": {
        "Diesel":  ( 6.18,  5.06),
    },
    "Toco": {
        "Diesel":  ( 4.65,  4.18),
    },
    "Truck": {
        "Diesel":  ( 3.77,  3.23),
    },
    "Bitruck": {
        "Diesel":  ( 3.21,  2.91),
    },
}


def is_fuel_incompatible(grupo_veiculo: str, grupo_combustivel: str) -> bool:
    """Retorna True se houver uma incompatibilidade lógica (ex: Caminhão com Gasolina)."""
    if grupo_veiculo in HEAVY_GROUPS:
        # Pesados/Caminhões não devem abastecer Gasolina ou Álcool
        if grupo_combustivel and grupo_combustivel.lower() in ["gasolina", "álcool", "etanol"]:
            return True
    return False


def get_veiculo_group(modelo: str, marca: str = "", placa: str = "") -> str:
    """Retorna o grupo do veículo baseado em modelo, marca e placa.

    Aplica as regras VEICULO_RULES em ordem; retorna 'Outros' se nenhuma bater.
    """
    p_upper = placa.upper().replace("-", "").strip()
    if p_upper in VEICULO_PLATE_OVERRIDES:
        return VEICULO_PLATE_OVERRIDES[p_upper]

    m = (modelo or "").lower().strip()
    b = (marca or "").lower().strip()
    for keyword_modelo, keyword_marca, grupo in VEICULO_RULES:
        if keyword_modelo not in m:
            continue
        if keyword_marca is not None and keyword_marca not in b:
            continue
        return grupo
    return "Outros"


def get_kml_referencia(grupo_veiculo: str, grupo_combustivel: str) -> Optional[float]:
    """Retorna o KM/L meta (p75 da frota) para o par grupo/combustível."""
    grupo_data = KML_REFERENCIA.get(grupo_veiculo)
    if not grupo_data:
        return None

    fuel_norm = (grupo_combustivel or "").capitalize().strip()
    if fuel_norm in ["Etanol", "Alcool"]:
        fuel_norm = "Álcool"

    ref_tuple = grupo_data.get(fuel_norm)
    if not ref_tuple:
        return None

    # Retorna a meta (primeiro valor = p75); ignora None
    meta = ref_tuple[0]
    return round(float(meta), 2) if meta is not None else None


def get_kml_alerta(grupo_veiculo: str, grupo_combustivel: str) -> Optional[float]:
    """Retorna o KM/L de alerta (p25 da frota) — abaixo disso é preocupante."""
    grupo_data = KML_REFERENCIA.get(grupo_veiculo)
    if not grupo_data:
        return None

    fuel_norm = (grupo_combustivel or "").capitalize().strip()
    if fuel_norm in ["Etanol", "Alcool"]:
        fuel_norm = "Álcool"

    ref_tuple = grupo_data.get(fuel_norm)
    if not ref_tuple:
        return None

    # Alerta = segundo valor (p25)
    alerta = ref_tuple[1]
    return round(float(alerta), 2) if alerta is not None else None
