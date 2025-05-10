# archivo: app/rutas/rutaRecomendacionesJuegosFuturos.py

from fastapi import APIRouter, HTTPException, Depends
from app.servicios.serviciosUsuario import obtenerRecomendacionesJuegosFuturosServicio
from app.rutas.rutaAuth import get_current_user
from typing import List, Dict

router = APIRouter(prefix="/recomendaciones", tags=["recomendaciones"])

@router.post("/juegosFuturos/{correo}", response_model=List[dict])
def recomendacionJuegosFuturos(correo: str, current_user: dict = Depends(get_current_user)):
    try:
        recomendaciones = obtenerRecomendacionesJuegosFuturosServicio(correo)
        return recomendaciones
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")