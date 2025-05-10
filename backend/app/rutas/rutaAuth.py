# archivo: app/rutas/rutaAuth.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.gestores.gestorUsuario import verificarContrasena, crearUsuario
from app.utils.jwt import crear_token_jwt
from app.modelos.modeloUsuario import Usuario

router = APIRouter(prefix="/auth", tags=["autenticacion"])

class Credenciales(BaseModel):
    correo: str
    contrasena: str

@router.post("/login")
def login(credenciales: Credenciales):
    usuario = verificarContrasena(credenciales.correo, credenciales.contrasena)
    if not usuario:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    
    token = crear_token_jwt({"sub": usuario["correo"], "rol": usuario["rol"]})
    return {"token": token, "rol": usuario["rol"]}

@router.post("/register")
def register(usuario: Usuario):
    try:
        resultado = crearUsuario(usuario.dict())
        token = crear_token_jwt({"sub": usuario.correo, "rol": usuario.rol})
        return {"token": token, "rol": usuario.rol}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))