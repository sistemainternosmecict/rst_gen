from fastapi import APIRouter
from service.orquestrador import Orquestrador
from datetime import datetime
from schemas.rst_schemas import RSTCreate

router = APIRouter()


@router.post("/assinar_documento")
def assinar_documento(dados_doc: RSTCreate):
    orq = Orquestrador()
    orq.gerar_documento_assinado(dados_doc)
    return "assinar_documento! Rota ok"
