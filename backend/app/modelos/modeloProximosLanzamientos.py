# archivo: app/modelos/modeloProximosLanzamientos.py


from pydantic import BaseModel
from typing import List

class ProximoLanzamiento(BaseModel):
    titulo: str
    plataformas: str
    fecha_lanzamiento: str
    imagen: str