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
from routers import combustivel, precos, frota, diretoria, veiculos, operacional, alertas, visao_geral, sistema, benchmark, fkm, manutencao, gestao_transacoes, pedagios, contratos, estornos, tco, pneus, gestao_pneus


def _warmup_all():
    """Carrega TODOS os caches externos em background para que as abas abram instantaneamente."""
    import threading
    from market_client import get_brent, get_cambio, get_noticias
    from anp_client import get_anp_df

    # 1. Dados de transações (PostgreSQL) — bloqueante, mais importante
    try:
        cache.get_df("transacoes")
        cache.get_df("pedagios")
        cache.get_df("estornos")
        logger.info("✓ Caches de transações, pedágios e estornos carregados.")
    except Exception as e:
        logger.error(f"✗ Falha ao carregar caches de transações/pedágios/estornos: {e}")

    # 2. Veículos + Manutenção (SQL Server / BlueFleet) — paralelo
    def _sqlserver():
        try:
            from db_sqlserver import get_veiculos_df, get_manutencao_df
            get_veiculos_df()
            logger.info("✓ Cache de veículos (SQL Server) carregado.")
            get_manutencao_df()
            logger.info("✓ Cache de manutenção (SQL Server) carregado.")
        except Exception as e:
            logger.warning(f"✗ Warmup SQL Server: {e}")

    # 3. FKM (planilha Excel)
    def _fkm():
        try:
            from db_fkm import get_fkm_df
            get_fkm_df()
            logger.info("✓ Cache FKM carregado.")
        except Exception as e:
            logger.warning(f"✗ Warmup FKM: {e}")

    # 4. ANP (downloads CSV)
    def _anp():
        try:
            get_anp_df()
            logger.info("✓ Cache ANP carregado.")
        except Exception as e:
            logger.warning(f"✗ Warmup ANP: {e}")

    # 5. Mercado externo (Brent + câmbio + notícias)
    def _mercado():
        try:
            get_brent()
            get_cambio()
            get_noticias()
            logger.info("✓ Cache de mercado carregado.")
        except Exception as e:
            logger.warning(f"✗ Warmup mercado: {e}")

    # Dispara tudo em paralelo
    threads = [
        threading.Thread(target=_sqlserver, daemon=True, name="warmup-sqlserver"),
        threading.Thread(target=_fkm, daemon=True, name="warmup-fkm"),
        threading.Thread(target=_anp, daemon=True, name="warmup-anp"),
        threading.Thread(target=_mercado, daemon=True, name="warmup-mercado"),
    ]
    for t in threads:
        t.start()
    # Aguarda todos terminarem para que o servidor esteja pronto antes de atender requests
    for t in threads:
        t.join(timeout=60)
    logger.info("✓ Warmup completo — todos os caches inicializados.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando servidor — aquecendo TODOS os caches...")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _warmup_all)
    logger.info("Servidor pronto para receber requests.")
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
app.include_router(gestao_transacoes.router)
app.include_router(pedagios.router)
app.include_router(contratos.router)
app.include_router(estornos.router)
app.include_router(tco.router)
app.include_router(pneus.router)
app.include_router(gestao_pneus.router)


@app.get("/health", tags=["sistema"])
def health():
    return {
        "status": "ok",
        "data_source": cache.data_source,
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
