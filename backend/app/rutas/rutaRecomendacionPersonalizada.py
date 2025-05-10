# archivo: app/rutas/rutaRecomendacionPersonalizada.py


from fastapi import APIRouter, HTTPException
from app.modelos.modeloRecomendacionPersonalizada import SolicitudRecomendacionPersonalizada
from app.servicios.serviciosUsuario import obtenerRecomendacionPersonalizadaServicio
from typing import List

router = APIRouter(prefix="/recomendar/personalizada", tags=["recomendacion"])

@router.post("/", response_model=List[dict])
def recomendarPersonalizado(solicitud: SolicitudRecomendacionPersonalizada):
    try:
        resultado = obtenerRecomendacionPersonalizadaServicio(solicitud.correo, solicitud.peticion)
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")