# archivo: modelos/modeloUsuario.py

from pydantic import BaseModel
from typing import List, Optional, Literal


class ConfiguracionPc(BaseModel):
    so: Optional[str] = None
    procesador: Optional[str] = None
    memoria: Optional[str] = None
    tarjetaGrafica: Optional[str] = None


class JuegoPoseido(BaseModel):
    nombre: str
    consolasDisponibles: List[str]


class Usuario(BaseModel):
    nombre: str
    correo: str
    rol: Literal["usuario", "administrador"]

    consolas: Optional[List[str]] = None
    configuracionPc: Optional[ConfiguracionPc] = None

    necesidadesEspeciales: Optional[List[str]] = None
    juegosGustados: Optional[List[str]] = None
    juegosNoGustados: Optional[List[str]] = None
    juegosJugados: Optional[List[str]] = None
    suscripciones: Optional[List[str]] = None
    idiomas: Optional[List[str]] = None

    juegosPoseidos: Optional[List[JuegoPoseido]] = None


class UsuarioEnBaseDeDatos(Usuario):
    id: str



