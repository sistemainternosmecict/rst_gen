from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from service.orquestrador import Orquestrador

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/validar_documento_por_hash/{hash}", response_class=HTMLResponse)
def validar_doc_por_hash(request: Request, hash:str):
    orq = Orquestrador()
    doc_dict = orq.validar_documento_por_hash(hash)
    if not doc_dict:
        return HTMLResponse(content="<h1>Documento não encontrado!</h1>")

    return templates.TemplateResponse(name="pagina_validacao.html",context={"documento":doc_dict}, request=request)
