# archivo: app/modelos/modeloUsuario.py

from pydantic import BaseModel
from typing import List, Optional, Literal

class ConfiguracionPc(BaseModel):
    so: Optional[str] = None
    procesador: Optional[str] = None
    memoria: Optional[str] = None
    tarjetaGrafica: Optional[str] = None

class JuegoPoseido(BaseModel):
    nombre: str = None
    consolasDisponibles: List[str] = None

class JuegoRecomendado(BaseModel):  # Nueva clase para los juegos en el historial
    nombre: str
    imagen: str

class Conversacion(BaseModel):
    pregunta: Optional[str] = None
    juegos: Optional[List[JuegoRecomendado]] = None  # Reemplaza respuesta, fecha y contexto

class Usuario(BaseModel):
    nombre: str = None
    correo: str = None
    contrasena: str = None
    rol: Literal["usuario", "administrador"] = None
    consolas: Optional[List[str]] = None
    configuracionPc: Optional[ConfiguracionPc] = None
    necesidadesEspeciales: Optional[List[str]] = None
    juegosGustados: Optional[List[str]] = None
    juegosNoGustados: Optional[List[str]] = None
    juegosJugados: Optional[List[str]] = None
    suscripciones: Optional[List[str]] = None
    idiomas: Optional[List[str]] = None
    juegosPoseidos: Optional[List[JuegoPoseido]] = None
    historialConversaciones: Optional[List[Conversacion]] = None

class UsuarioEnBaseDeDatos(Usuario):
    id: str = None

class UsuarioObligatorio(BaseModel):
    nombre: str = None
    correo: str = None
    contrasena: str = None
    rol: Literal["usuario", "administrador"] = None

class UsuarioOpcionalSinHistorial(BaseModel):
    consolas: Optional[List[str]] = None
    configuracionPc: Optional[ConfiguracionPc] = None
    necesidadesEspeciales: Optional[List[str]] = None
    juegosGustados: Optional[List[str]] = None
    juegosNoGustados: Optional[List[str]] = None
    juegosJugados: Optional[List[str]] = None
    suscripciones: Optional[List[str]] = None
    idiomas: Optional[List[str]] = None
    juegosPoseidos: Optional[List[JuegoPoseido]] = None

class UsuarioOpcionalConHistorial(BaseModel):
    consolas: Optional[List[str]] = None
    configuracionPc: Optional[ConfiguracionPc] = None
    necesidadesEspeciales: Optional[List[str]] = None
    juegosGustados: Optional[List[str]] = None
    juegosNoGustados: Optional[List[str]] = None
    juegosJugados: Optional[List[str]] = None
    suscripciones: Optional[List[str]] = None
    idiomas: Optional[List[str]] = None
    juegosPoseidos: Optional[List[JuegoPoseido]] = None
    historialConversaciones: Optional[List[Conversacion]] = None