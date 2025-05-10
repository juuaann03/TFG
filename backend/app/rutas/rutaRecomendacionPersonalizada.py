# archivo: app/rutas/rutaRecomendacionPersonalizada.py


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.servicios.serviciosUsuario import obtenerRecomendacionPersonalizadaServicio

router = APIRouter(prefix="/recomendaciones", tags=["recomendaciones"])

class PeticionRecomendacion(BaseModel):
    peticion: str

@router.post("/personalizada/{correo}", response_model=list)
def recomendacionPersonalizada(correo: str, datos: PeticionRecomendacion):
    try:
        recomendaciones = obtenerRecomendacionPersonalizadaServicio(correo, datos.peticion)
        return recomendaciones
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))