# archivo: app/rutas/rutaAuth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from app.gestores.gestorUsuario import verificarContrasena
import os

router = APIRouter(prefix="/auth", tags=["auth"])

# Configuración de OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Clave secreta para JWT (debería estar en .env)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "tu_clave_secreta")
ALGORITHM = "HS256"

class LoginRequest(BaseModel):
    correo: str
    contrasena: str

@router.post("/login")
def login(datos: LoginRequest):
    usuario = verificarContrasena(datos.correo, datos.contrasena)
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    # Crear token JWT
    token_data = {"sub": datos.correo}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return {
        "token": token,
        "correo": datos.correo,
        "nombre": usuario.get("nombre")
    }

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        correo: str = payload.get("sub")
        if correo is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    from app.servicios.serviciosUsuario import obtenerUsuarioPorCorreoServicio
    usuario = obtenerUsuarioPorCorreoServicio(correo)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario