# archivo: app/rutas/rutaHello.py


from fastapi import APIRouter, HTTPException
from app.servicios.servicioProximosLanzamientos import obtenerProximosLanzamientosServicio
from app.modelos.modeloProximosLanzamientos import ProximoLanzamiento
from app.servicios.serviciosUsuario import obtenerUsuarioPorCorreoServicio
from app.modelos.modeloUsuario import UsuarioOpcionalSinHistorial
from typing import List

router = APIRouter(prefix="/lanzamientos", tags=["lanzamientos"])

@router.get("/proximos/{correo}", response_model=List[ProximoLanzamiento])
def obtenerProximosLanzamientos(correo: str):
    try:
        # Obtener datos del usuario
        usuario = obtenerUsuarioPorCorreoServicio(correo)
        if not usuario:
            raise ValueError("Usuario no encontrado")
        
        # Extraer datos opcionales (sin historial)
        datos_usuario = {k: usuario.get(k) for k in UsuarioOpcionalSinHistorial.__fields__}
        
        # Llamar al servicio
        recomendaciones = obtenerProximosLanzamientosServicio(datos_usuario)
        return recomendaciones
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")