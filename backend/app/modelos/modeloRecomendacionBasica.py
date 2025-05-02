# archivo: modelos/modeloRecomendacionBasica.py

from pydantic import BaseModel

class SolicitudRecomendacionBasica(BaseModel):
    descripcionUsuario: str
