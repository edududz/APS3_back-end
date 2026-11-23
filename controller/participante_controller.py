from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schema.participante_schema import ParticipanteCreate, ParticipanteUpdate, ParticipanteResponse
from service.participante_service import ParticipanteService

router = APIRouter(prefix="/participantes", tags=["Participantes"])

@router.post("/", response_model=ParticipanteResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_participante(participante_in: ParticipanteCreate, db: Session = Depends(get_db)):
    return ParticipanteService.cadastrar_participante(db, participante_in)

@router.get("/", response_model=List[ParticipanteResponse])
def listar_participantes(db: Session = Depends(get_db)):
    return ParticipanteService.listar_participantes(db)

@router.get("/{id}", response_model=ParticipanteResponse)
def consultar_participante(id: int, db: Session = Depends(get_db)):
    return ParticipanteService.consultar_participante(db, id)

@router.put("/{id}", response_model=ParticipanteResponse)
def atualizar_participante(id: int, participante_in: ParticipanteUpdate, db: Session = Depends(get_db)):
    return ParticipanteService.atualizar_participante(db, id, participante_in)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_participante(id: int, db: Session = Depends(get_db)):
    ParticipanteService.excluir_participante(db, id)
