from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supervisorio.api.routes import router
from supervisorio.infrastructure.database.repositories import PesagemRepository, EventRepository
from supervisorio.infrastructure.database.connection import close_pool
from supervisorio.core.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Início e fechamento de recursor de api"""
    logger.info("Iniciando API e conectando ao Pool de Dados...")
    await PesagemRepository.initialize()
    await EventRepository.initialize()
    yield
    logger.info("Encerrando API e fechando conexões...")
    await close_pool()


app = FastAPI(
    title="Supervisor Modbus API",
    description="API para consulta de dados de pesagem industrial",
    version="1.0.0",
    debug=True,
    openapi_url="/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
