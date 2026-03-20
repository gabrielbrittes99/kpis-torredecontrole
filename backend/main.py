import asyncio
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from data_cache import cache
from routers import combustivel, precos, frota, diretoria, veiculos, operacional, alertas, visao_geral, sistema, benchmark, fkm, manutencao


def _warmup_all():
    """Carrega todos os caches externos em background (DB + ANP + mercado)."""
    import threading
    from market_client import get_brent, get_cambio, get_noticias
    from anp_client import get_anp_df

    # 1. Dados de transações (PostgreSQL)
    try:
        cache.get_df()
        logger.info("Cache de transações carregado.")
    except Exception as e:
        logger.error(f"Falha ao carregar cache de transações: {e}")

    # 2. ANP (downloads CSV — paralelos internamente)
    def _anp():
        try:
            get_anp_df()
            logger.info("Cache ANP carregado.")
        except Exception as e:
            logger.warning(f"Warmup ANP: {e}")

    # 3. Mercado externo (Brent + câmbio + notícias)
    def _mercado():
        try:
            get_brent()
            get_cambio()
            get_noticias()
            logger.info("Cache de mercado carregado.")
        except Exception as e:
            logger.warning(f"Warmup mercado: {e}")

    threading.Thread(target=_anp, daemon=True).start()
    threading.Thread(target=_mercado, daemon=True).start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando servidor — aquecendo caches em background...")
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _warmup_all)
    yield


app = FastAPI(
    title="KPIs Torre de Controle — Gritsch",
    description="API de análise de combustível integrada com TruckPag",
    version="1.0.0",
    lifespan=lifespan,
)

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(combustivel.router)
app.include_router(precos.router)
app.include_router(frota.router)
app.include_router(diretoria.router)
app.include_router(veiculos.router)
app.include_router(operacional.router)
app.include_router(benchmark.router)
app.include_router(alertas.router)
app.include_router(visao_geral.router)
app.include_router(sistema.router)
app.include_router(fkm.router)
app.include_router(manutencao.router)


@app.get("/health", tags=["sistema"])
def health():
    return {
        "status": "ok",
        "cache_ultima_atualizacao": (
            cache.last_updated.isoformat() if cache.last_updated else None
        ),
    }


# ── Serve frontend (Vue SPA) ─────────────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
_dist = os.path.join(_here, "..", "frontend", "dist")

if os.path.isdir(_dist):
    _assets = os.path.join(_dist, "assets")
    if os.path.isdir(_assets):
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_catch_all(full_path: str):
        # Serve arquivos estáticos da raiz do dist (favicon, etc.)
        candidate = os.path.join(_dist, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(_dist, "index.html"))
