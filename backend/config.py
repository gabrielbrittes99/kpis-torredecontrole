"""
Configurações centrais do sistema Torre de Controle.

Este arquivo é a fonte de verdade para:
- Agrupamento de combustíveis (4 grupos)
- Mapeamento de filiais (sigla SQL Server → nome + estado + região)
- Placas hardcoded da Gritsch Palmas (ainda sem sigla no SQL Server)
"""

# ---------------------------------------------------------------------------
# GRUPOS DE COMBUSTÍVEL
# ---------------------------------------------------------------------------

# De → Para (nome_combustivel no banco → grupo)
FUEL_GROUP_MAP: dict[str, str] = {
    # Diesel
    "diesel s10":           "Diesel",
    "diesel s10 aditivado": "Diesel",
    "diesel aditivado":     "Diesel",
    "biodiesel":            "Diesel",
    # Gasolina
    "gasolina comum":       "Gasolina",
    "gasolina aditivada":   "Gasolina",
    # Álcool
    "alcool comum":         "Álcool",
    "alcool aditivado":     "Álcool",
    # Arla
    "arla 32":              "Arla",
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


def get_filial_info(sigla_sqlserver: str) -> dict:
    """Retorna nome, estado e região da filial pelo código do SQL Server."""
    return FILIAIS_MAP.get(sigla_sqlserver, {
        "nome": sigla_sqlserver or "Sem filial",
        "estado": "?",
        "regiao": "?",
    })


def get_filial_by_placa(placa: str) -> dict | None:
    """Retorna os dados de Palmas se a placa for uma das hardcoded."""
    if placa.upper().strip() in PALMAS_PLACAS:
        return PALMAS_FILIAL
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
    # ── Kombi ────────────────────────────────────────────────────────────────
    ("kombi",           None,       "Kombi"),

    # ══════════════════════════════════════════════════════════════════════════
    # CAMINHÕES — por tonelagem (ordem do mais pesado para o mais leve)
    # ══════════════════════════════════════════════════════════════════════════

    # ── Caminhão 17 Ton (Bitruck e pesados 6x4) ──────────────────────────────
    ("30-330",          None,       "Caminhão17Ton"),
    ("30.330",          None,       "Caminhão17Ton"),
    ("30-280",          None,       "Caminhão17Ton"),
    ("30.280",          None,       "Caminhão17Ton"),
    ("vm 330",          None,       "Caminhão17Ton"),
    ("26-260",          None,       "Caminhão17Ton"),   # 26-260 Constellation 6X2
    ("24.260",          None,       "Caminhão17Ton"),   # 24.260 CNM 6X4
    ("24-260",          None,       "Caminhão17Ton"),

    # ── Caminhão 12 Ton (Truck) ──────────────────────────────────────────────
    ("cargo 2423",      None,       "Caminhão12Ton"),
    ("2423",            "ford",     "Caminhão12Ton"),
    ("24-280",          None,       "Caminhão12Ton"),
    ("24.280",          None,       "Caminhão12Ton"),
    ("vm 290",          None,       "Caminhão12Ton"),
    ("atego 2429",      None,       "Caminhão12Ton"),
    ("atego 2430",      None,       "Caminhão12Ton"),
    ("15.190",          None,       "Caminhão12Ton"),
    ("15-190",          None,       "Caminhão12Ton"),

    # ── Caminhão 10.5 Ton (Toco) ─────────────────────────────────────────────
    ("17-230",          None,       "Caminhão10.5Ton"),
    ("17.230",          None,       "Caminhão10.5Ton"),
    ("17-210",          None,       "Caminhão10.5Ton"),
    ("17.210",          None,       "Caminhão10.5Ton"),
    ("atego 1719",      None,       "Caminhão10.5Ton"),

    # ── Caminhão 9 Ton (Toco) ────────────────────────────────────────────────
    ("13-180",          None,       "Caminhão9Ton"),
    ("13.180",          None,       "Caminhão9Ton"),
    ("atego 1419",      None,       "Caminhão9Ton"),

    # ── Caminhão 7.5 Ton (Toco) ──────────────────────────────────────────────
    ("14-190",          None,       "Caminhão7.5Ton"),
    ("14.190",          None,       "Caminhão7.5Ton"),
    ("14-210",          None,       "Caminhão7.5Ton"),
    ("14.210",          None,       "Caminhão7.5Ton"),

    # ── Caminhão 6 Ton (3/4) ─────────────────────────────────────────────────
    ("11-180",          None,       "Caminhão6Ton"),
    ("11.180",          None,       "Caminhão6Ton"),

    # ── Caminhão 5.5 Ton (3/4) ───────────────────────────────────────────────
    ("accelo 1016",     None,       "Caminhão5.5Ton"),
    ("accelo 1017",     None,       "Caminhão5.5Ton"),
    ("10.160",          None,       "Caminhão5.5Ton"),
    ("10-160",          None,       "Caminhão5.5Ton"),

    # ── Caminhão 5 Ton (3/4) ────────────────────────────────────────────────
    ("9-170",           None,       "Caminhão5Ton"),
    ("9.170",           None,       "Caminhão5Ton"),

    # ── Caminhão 4.2 Ton (3/4) ──────────────────────────────────────────────
    ("8-160",           None,       "Caminhão4.2Ton"),
    ("8.160",           None,       "Caminhão4.2Ton"),
    ("cargo 816",       None,       "Caminhão4.2Ton"),
    ("816",             "ford",     "Caminhão4.2Ton"),
    ("hd80",            None,       "Caminhão4.2Ton"),
    ("hd 80",           None,       "Caminhão4.2Ton"),
    ("accelo 815",      None,       "Caminhão4.2Ton"),
    ("accelo 817",      None,       "Caminhão4.2Ton"),

    # Fallbacks genéricos para caminhões (se não bateu acima)
    ("accelo",          None,       "Caminhão5.5Ton"),  # Accelo genérico → 5.5T
    ("atego",           None,       "Caminhão10.5Ton"), # Atego genérico → 10.5T
    ("constellation",   None,       "Caminhão12Ton"),   # Constellation genérico → 12T
    ("constelation",    None,       "Caminhão12Ton"),
    ("vm",              "volvo",    "Caminhão12Ton"),    # Volvo VM genérico → 12T

    # ══════════════════════════════════════════════════════════════════════════
    # PESADO — vans e furgões grandes (diesel)
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
    "Caminhão17Ton",
    "Caminhão12Ton",
    "Caminhão10.5Ton",
    "Caminhão9Ton",
    "Caminhão7.5Ton",
    "Caminhão6Ton",
    "Caminhão5.5Ton",
    "Caminhão5Ton",
    "Caminhão4.2Ton",
    "Pesado",
    "Médio",
    "Leve",
    "Kombi",
    "Moto",
]


# ---------------------------------------------------------------------------
# KM/L DE REFERÊNCIA POR GRUPO DE VEÍCULO
# ---------------------------------------------------------------------------
# Fonte: tabela de referência Gritsch (Mar/2026)
# Estrutura: grupo → combustível → (kml_rodoviario, kml_urbano)
# None = não aplicável para aquela combinação.
# Para comparação usamos a média simples (rodo + urbano) / 2 quando ambos disponíveis.

KML_REFERENCIA: dict[str, dict[str, tuple]] = {
    "Leve": {
        "Gasolina": (15.70, 12.43),
        "Álcool":   (11.40,  9.60),
    },
    "Médio": {
        "Gasolina": (11.80, 10.43),
        "Álcool":   ( 9.58,  7.80),
    },
    "Kombi": {
        "Gasolina": (None,   9.60),
        "Álcool":   ( 8.95,  8.90),
    },
    "Moto": {
        "Gasolina": (None,  31.00),
    },
    "Pesado": {              # Sprinter / Master / Transit / Ducato
        "Diesel": (10.01,  8.50),
    },
    "Caminhão4.2Ton": {      # Cargo 816, Accelo 815, HD80, 8-160
        "Diesel":  ( 5.90,  5.69),
    },
    "Caminhão5Ton": {        # VW 9-170
        "Diesel":  ( 5.50,  5.30),
    },
    "Caminhão5.5Ton": {      # Accelo 1016/1017
        "Diesel":  ( 5.50,  5.20),
    },
    "Caminhão6Ton": {        # VW 11-180
        "Diesel":  ( 5.11,  4.80),
    },
    "Caminhão7.5Ton": {      # VW 14-190/14-210
        "Diesel":  ( 4.80,  4.40),
    },
    "Caminhão9Ton": {        # Atego 1419, 13-180
        "Diesel":  ( 4.50,  4.10),
    },
    "Caminhão10.5Ton": {     # VW 17-230/17-210, Atego 1719
        "Diesel":  ( 4.20,  3.80),
    },
    "Caminhão12Ton": {       # Cargo 2423, 24-280, VM 290, Atego 2429
        "Diesel":  ( 3.80,  3.50),
    },
    "Caminhão17Ton": {       # 30-330, 30-280, VM 330
        "Diesel":  ( 3.60,  3.30),
    },
}


def get_kml_referencia(grupo: str, combustivel: str) -> float | None:
    """Retorna km/L de referência médio (rodo + urbano) para o grupo/combustível.

    Retorna None se não houver referência definida.
    """
    ref = KML_REFERENCIA.get(grupo, {}).get(combustivel)
    if ref is None:
        return None
    rodo, urb = ref
    valores = [v for v in (rodo, urb) if v is not None]
    return round(sum(valores) / len(valores), 2) if valores else None


def get_veiculo_group(modelo: str, marca: str = "") -> str:
    """Retorna o grupo do veículo baseado em modelo e marca.

    Aplica as regras VEICULO_RULES em ordem; retorna 'Outros' se nenhuma bater.
    """
    m = (modelo or "").lower().strip()
    b = (marca or "").lower().strip()
    for keyword_modelo, keyword_marca, grupo in VEICULO_RULES:
        if keyword_modelo not in m:
            continue
        if keyword_marca is not None and keyword_marca not in b:
            continue
        return grupo
    return "Outros"
