from fastapi import APIRouter, BackgroundTasks
from service.orquestrador import Orquestrador
from datetime import datetime
from schemas.rst_schemas import RSTCreate

router = APIRouter()


@router.post("/assinar_documento")
async def assinar_documento(dados_doc: RSTCreate, bg_tasks: BackgroundTasks):
    orq = Orquestrador()

    bg_tasks.add_task(orq.gerar_documento_assinado, dados_doc)
    rsp_orquestrador = {
        "status": "success",
        "msg": "Processando RST. Um comentário será inserido!",
    }
    return rsp_orquestrador
