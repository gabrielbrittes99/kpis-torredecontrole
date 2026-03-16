"""
Dados de mercado externos — sem dependência de API key proprietária.

Fontes:
  - Brent:   EIA (US Energy Information Administration) — gratuito, key via .env
  - Câmbio:  AwesomeAPI (dados BCB) — 100% gratuito, sem key
  - Notícias: RSS Reuters (energia + commodities + negócios) — gratuito, sem key
"""
import logging
import os
import threading
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

EIA_API_KEY = os.getenv("EIA_API_KEY", "DEMO_KEY")

# Cache em memória — evita chamadas repetidas
_brent_cache:    dict = {"data": None, "ts": None}
_cambio_cache:   dict = {"data": None, "ts": None}
_noticias_cache: dict = {"data": None, "ts": None}

_TTL_BRENT    = timedelta(hours=4)
_TTL_CAMBIO   = timedelta(minutes=30)
_TTL_NOTICIAS = timedelta(hours=2)

# Flags para evitar refreshes concorrentes em background
_refreshing_brent    = False
_refreshing_cambio   = False
_refreshing_noticias = False


def _bg(target):
    """Lança target numa thread daemon em background."""
    t = threading.Thread(target=target, daemon=True)
    t.start()

# Google News RSS — sem autenticação, funciona em produção
_RSS_FEEDS = [
    "https://news.google.com/rss/search?q=petróleo+combustível+diesel&hl=pt-BR&gl=BR&ceid=BR:pt",
    "https://news.google.com/rss/search?q=brent+petrobras+frota+logística&hl=pt-BR&gl=BR&ceid=BR:pt",
]

# Palavras-chave relevantes para filtrar notícias (busca no título)
_KEYWORDS = [
    "oil", "crude", "brent", "diesel", "fuel", "petro", "energy", "energia",
    "combustivel", "combustível", "logistics", "logística", "freight", "frete",
    "anp", "petrobras", "opec", "refin",
]


def _is_stale(cache: dict, ttl: timedelta) -> bool:
    return cache["ts"] is None or (datetime.now() - cache["ts"]) > ttl


# ---------------------------------------------------------------------------
# BRENT
# ---------------------------------------------------------------------------

def _fetch_brent_sync():
    global _brent_cache, _refreshing_brent
    _refreshing_brent = True
    try:
        url = (
            "https://api.eia.gov/v2/petroleum/pri/spt/data/"
            f"?api_key={EIA_API_KEY}"
            "&frequency=daily"
            "&data[0]=value"
            "&facets[series][]=RBRTE"
            "&sort[0][column]=period"
            "&sort[0][direction]=desc"
            "&length=2"
        )
        r = httpx.get(url, timeout=10)
        r.raise_for_status()
        items = r.json()["response"]["data"]
        atual = items[0]
        ontem = items[1] if len(items) > 1 else None
        valor = float(atual["value"])
        variacao = round(
            ((valor - float(ontem["value"])) / float(ontem["value"])) * 100, 2
        ) if ontem else None
        resultado = {"valor_usd": round(valor, 2), "data": atual["period"], "variacao_pct": variacao, "fonte": "EIA"}
        _brent_cache = {"data": resultado, "ts": datetime.now()}
        logger.info(f"Brent: USD {valor:.2f}/barril")
    except Exception as e:
        logger.warning(f"Brent: falha EIA: {e}")
    finally:
        _refreshing_brent = False


def get_brent() -> dict:
    """Retorna Brent spot. Se cache venceu, retorna dado antigo e atualiza em background."""
    global _brent_cache, _refreshing_brent
    if not _is_stale(_brent_cache, _TTL_BRENT) and _brent_cache["data"]:
        return _brent_cache["data"]
    if _brent_cache["data"]:
        # Cache vencido mas há dado antigo — retorna imediatamente e atualiza em bg
        if not _refreshing_brent:
            _bg(_fetch_brent_sync)
        return _brent_cache["data"]
    # Primeira vez — busca síncrona (só ocorre uma vez na vida do servidor)
    _fetch_brent_sync()
    return _brent_cache.get("data") or {"valor_usd": None, "data": None, "variacao_pct": None, "fonte": "EIA"}


# ---------------------------------------------------------------------------
# CÂMBIO
# ---------------------------------------------------------------------------

def _fetch_cambio_sync():
    global _cambio_cache, _refreshing_cambio
    _refreshing_cambio = True
    try:
        r = httpx.get("https://economia.awesomeapi.com.br/json/last/USD-BRL,EUR-BRL", timeout=8)
        r.raise_for_status()
        dados = r.json()
        usd = dados.get("USDBRL", {})
        eur = dados.get("EURBRL", {})
        resultado = {
            "usd_brl": {
                "valor": round(float(usd.get("bid", 0)), 4),
                "variacao_pct": round(float(usd.get("pctChange", 0)), 4),
                "alta": round(float(usd.get("high", 0)), 4),
                "baixa": round(float(usd.get("low", 0)), 4),
                "atualizado": usd.get("create_date"),
            },
            "eur_brl": {"valor": round(float(eur.get("bid", 0)), 4), "variacao_pct": round(float(eur.get("pctChange", 0)), 4)},
            "fonte": "AwesomeAPI/BCB",
        }
        _cambio_cache = {"data": resultado, "ts": datetime.now()}
        logger.info(f"Câmbio: USD/BRL {resultado['usd_brl']['valor']}")
    except Exception as e:
        logger.warning(f"Câmbio: falha AwesomeAPI: {e}")
    finally:
        _refreshing_cambio = False


def get_cambio() -> dict:
    """Retorna câmbio. Se cache venceu, retorna dado antigo e atualiza em background."""
    global _cambio_cache, _refreshing_cambio
    if not _is_stale(_cambio_cache, _TTL_CAMBIO) and _cambio_cache["data"]:
        return _cambio_cache["data"]
    if _cambio_cache["data"]:
        if not _refreshing_cambio:
            _bg(_fetch_cambio_sync)
        return _cambio_cache["data"]
    _fetch_cambio_sync()
    return _cambio_cache.get("data") or {"usd_brl": {"valor": None}, "eur_brl": {"valor": None}, "fonte": "AwesomeAPI/BCB"}


# ---------------------------------------------------------------------------
# NOTÍCIAS (RSS Reuters)
# ---------------------------------------------------------------------------

def _parse_rss_item(item: ET.Element, ns: dict) -> Optional[dict]:
    """Extrai campos de um <item> do RSS e filtra por relevância."""
    titulo = item.findtext("title", default="").strip()
    pubdate = item.findtext("pubDate", default="").strip()
    desc   = item.findtext("description", default="").strip()

    # Google News: <source> tag tem o nome do veículo
    source_el = item.find("source")
    fonte = source_el.text.strip() if source_el is not None and source_el.text else "Google News"

    # <link> no Google News RSS está entre <title> e <guid> (sem tag própria, usa <guid>)
    link = item.findtext("link", default="").strip()
    if not link:
        link = item.findtext("guid", default="").strip()

    # Filtra por palavra-chave (case-insensitive)
    texto_busca = (titulo + " " + desc).lower()
    if not any(kw in texto_busca for kw in _KEYWORDS):
        return None

    # Determina impacto simplificado
    impacto = "neutro"
    palavras_alta = ["surge", "spike", "rise", "alta", "sobe", "record", "high", "aumenta", "dispara"]
    palavras_baixa = ["fall", "drop", "decline", "baixa", "cai", "cut", "reduce", "reduz", "recua"]
    if any(w in texto_busca for w in palavras_alta):
        impacto = "alta"
    elif any(w in texto_busca for w in palavras_baixa):
        impacto = "baixa"

    return {
        "titulo":    titulo,
        "link":      link,
        "publicado": pubdate,
        "fonte":     fonte,
        "impacto":   impacto,
    }


def _fetch_noticias_sync():
    global _noticias_cache, _refreshing_noticias
    _refreshing_noticias = True
    try:
        noticias = []
        headers = {"User-Agent": "Mozilla/5.0 (compatible; GritschKPIs/1.0)"}
        for feed_url in _RSS_FEEDS:
            try:
                r = httpx.get(feed_url, timeout=10, follow_redirects=True, headers=headers)
                r.raise_for_status()
                root = ET.fromstring(r.content)
                for item in root.findall(".//item"):
                    noticia = _parse_rss_item(item, {})
                    if noticia:
                        noticias.append(noticia)
            except Exception as e:
                logger.warning(f"Notícias: falha {feed_url}: {e}")
        seen, unicas = set(), []
        for n in noticias:
            if n["titulo"] not in seen:
                seen.add(n["titulo"])
                unicas.append(n)
        _noticias_cache = {"data": unicas, "ts": datetime.now()}
        logger.info(f"Notícias: {len(unicas)} encontradas")
    except Exception as e:
        logger.warning(f"Notícias: erro geral: {e}")
    finally:
        _refreshing_noticias = False


def get_noticias(limite: int = 5) -> list[dict]:
    """Retorna notícias. Se cache venceu, retorna dado antigo e atualiza em background."""
    global _noticias_cache, _refreshing_noticias
    if not _is_stale(_noticias_cache, _TTL_NOTICIAS) and _noticias_cache["data"]:
        return _noticias_cache["data"][:limite]
    if _noticias_cache["data"]:
        if not _refreshing_noticias:
            _bg(_fetch_noticias_sync)
        return _noticias_cache["data"][:limite]
    _fetch_noticias_sync()
    return (_noticias_cache.get("data") or [])[:limite]


# ---------------------------------------------------------------------------
# RESUMO CONSOLIDADO (usado pela Vigilância Constante)
# ---------------------------------------------------------------------------

def get_market_summary() -> dict:
    """Retorna brent + câmbio + notícias em uma única chamada."""
    return {
        "brent":    get_brent(),
        "cambio":   get_cambio(),
        "noticias": get_noticias(limite=5),
        "atualizado_em": datetime.now().isoformat(),
    }
