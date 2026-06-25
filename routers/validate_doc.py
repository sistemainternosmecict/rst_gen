from fastapi import APIRouter

router = APIRouter()

@router.get("/validar_documento_por_hash/{hash}")
def validar_doc_por_hash(hash:str):
    return f"Validar documento por hash! Hash: {hash}"
