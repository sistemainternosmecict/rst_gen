from fastapi import APIRouter

router = APIRouter()

@router.post("/assinar_documento")
def assinar_documento():
    return "assinar_documento! Rota ok"
