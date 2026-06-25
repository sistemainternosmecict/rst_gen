from fastapi import APIRouter

router = APIRouter()

@router.get("/validar_documento_por_hash/")
def validar_doc_por_hash():
    return "Validar documento por hash! Rota ok"
