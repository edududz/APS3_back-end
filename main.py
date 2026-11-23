from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from database import init_db
from controller.evento_controller import router as evento_router
from controller.participante_controller import router as participante_router
from controller.inscricao_controller import router as inscricao_router
from controller.relatorio_controller import router as relatorio_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa as tabelas do banco de dados na inicialização
    init_db()
    yield

app = FastAPI(
    title="API de Gerenciamento de Eventos Acadêmicos",
    description="API RESTful para gerenciar eventos, participantes e inscrições com persistência em SQLite e relatórios consolidados em SQLAlchemy.",
    version="2.0.0",
    lifespan=lifespan
)

# Inclusão dos roteadores por módulo/domínio
app.include_router(evento_router)
app.include_router(participante_router)
app.include_router(inscricao_router)
app.include_router(relatorio_router)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")
