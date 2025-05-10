# archivo: app/rutas/rutaRecomendacionBasica.py


from fastapi import APIRouter
from app.modelos.modeloRecomendacionBasica import SolicitudRecomendacionBasica
from app.servicios.servicioRecomendacionBasica import generarRecomendacionesBasicas

router = APIRouter(prefix="/recomendar", tags=["recomendacion"])

@router.post("/")
def recomendarBasico(solicitud: SolicitudRecomendacionBasica):
    resultado = generarRecomendacionesBasicas(solicitud.descripcionUsuario)
    return {"recomendaciones": resultado}