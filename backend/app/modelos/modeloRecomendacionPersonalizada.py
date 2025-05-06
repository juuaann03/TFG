# archivo: modelos/modeloRecomendacionPersonalizada.py


from pydantic import BaseModel

class SolicitudRecomendacionPersonalizada(BaseModel):
    correo: str
    peticion: str