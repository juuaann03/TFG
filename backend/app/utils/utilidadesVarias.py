import re
import os
import requests  # Para solicitudes HTTP
from dotenv import load_dotenv
from pathlib import Path


modelos = [
    "openai/gpt-4o-mini",
    "meta-llama/llama-3.3-70b-instruct",
    "google/gemini-2.0-flash-001"
]

# Más rápido pero consume más tokens
modelos2 = [
    "openai/gpt-4o-mini",
    "meta-ai/llama-3.1-70b-instruct",
    "google/gemini-pro-1.5"
]

# Cargar variables del .env
dotenv_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=dotenv_path)

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
if not openrouter_api_key:
    raise ValueError("OPENROUTER_API_KEY no está definido en el .env")

os.environ["OPENAI_API_KEY"] = openrouter_api_key
os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"

steam_api_key = os.getenv("STEAM_API_KEY")
if not steam_api_key:
    raise ValueError("STEAM_API_KEY no está definido en el .env")

rawg_api_key = os.getenv("RAWG_API_KEY")
if not rawg_api_key:
    raise ValueError("RAWG_API_KEY no está definido en el .env")

#Limpia la respuesta del modelo para extraer solo el JSON.
def limpiar_respuesta(respuesta: str) -> str:

    # Eliminar marcadores de markdown
    respuesta = re.sub(r'```json\s*|\s*```', '', respuesta, flags=re.IGNORECASE)
    # Eliminar espacios y saltos de línea al inicio y final
    respuesta = respuesta.strip()
    # Si no empieza con '{', intentar extraer el JSON
    if respuesta and not respuesta.startswith('{'):
        start = respuesta.find('{')
        end = respuesta.rfind('}') + 1
        if start != -1 and end != 0:
            respuesta = respuesta[start:end]
        else:
            return ""
    return respuesta

def obtener_imagen_juego(nombre_juego: str) -> str:
    """Obtiene la URL de la imagen de un juego usando la API de RAWG."""
    rawg_api_key = os.getenv("RAWG_API_KEY")
    if not rawg_api_key:
        return ""  # Devolver cadena vacía si no hay API key

    try:
        # Buscar el juego en RAWG
        url = f"https://api.rawg.io/api/games?key={rawg_api_key}&search={nombre_juego}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Obtener la primera coincidencia
        if data["results"]:
            # Usar background_image o la primera captura si está disponible
            return data["results"][0].get("background_image", "")
        return ""
    except Exception as e:
        print(f"Error al obtener imagen para {nombre_juego}: {str(e)}")
        return ""