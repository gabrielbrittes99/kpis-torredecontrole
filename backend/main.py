import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from data_cache import cache
from routers import combustivel, precos, frota, diretoria, veiculos, benchmark, operacional, alertas, torre


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando servidor — carregando cache de dados...")
    try:
        cache.get_df()
        logger.info("Cache carregado com sucesso.")
    except Exception as e:
        logger.error(f"Falha ao carregar cache na inicialização: {e}")
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
app.include_router(benchmark.router)
app.include_router(operacional.router)
app.include_router(alertas.router)
app.include_router(torre.router)


@app.get("/health", tags=["sistema"])
def health():
    return {
        "status": "ok",
        "cache_ultima_atualizacao": (
            cache.last_updated.isoformat() if cache.last_updated else None
        ),
    }
