# archivo: app/utils/jwt.py


from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables del .env
dotenv_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=dotenv_path)

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

def crear_token_jwt(data: dict) -> str:
    a_codificar = data.copy()
    expira = datetime.utcnow() + timedelta(hours=24)  # Token válido por 24 horas
    a_codificar.update({"exp": expira})
    token = jwt.encode(a_codificar, SECRET_KEY, algorithm=ALGORITHM)
    return token