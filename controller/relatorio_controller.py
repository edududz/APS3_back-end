from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schema.relatorio_schema import RelatorioOcupacao, RelatorioCategoria, RelatorioCurso
from service.relatorio_service import RelatorioService

router = APIRouter(prefix="/relatorios", tags=["Relatórios e Consolidações"])

@router.get("/eventos/ocupacao", response_model=List[RelatorioOcupacao])
def relatorio_ocupacao(db: Session = Depends(get_db)):
    return RelatorioService.relatorio_ocupacao_eventos(db)

@router.get("/eventos/categorias", response_model=List[RelatorioCategoria])
def relatorio_categorias(db: Session = Depends(get_db)):
    return RelatorioService.relatorio_eventos_por_categoria(db)

@router.get("/participantes/cursos", response_model=List[RelatorioCurso])
def relatorio_cursos(db: Session = Depends(get_db)):
    return RelatorioService.relatorio_participacao_por_curso(db)

