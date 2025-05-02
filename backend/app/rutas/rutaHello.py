# archivo: routes/rutaHello.py

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def readRoot():
    return {"message": "¡Hola desde FastAPI!"}
