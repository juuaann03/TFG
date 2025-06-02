# archivo: app/utils/utilidadesVarias.py

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

# Diccionario para mapear nombres de tiendas a URLs de íconos
ICONOS_TIENDA = {
    "steam": "https://api.iconify.design/simple-icons/steam.svg?color=currentColor",
    "playstation-store": "https://api.iconify.design/simple-icons/playstation.svg?color=currentColor",
    "xbox-store": "https://api.iconify.design/simple-icons/xbox.svg?color=currentColor",
    "nintendo-eshop": "https://api.iconify.design/simple-icons/nintendo.svg?color=currentColor",
    "epic-games": "https://api.iconify.design/simple-icons/epicgames.svg?color=currentColor",
    "gog": "https://api.iconify.design/simple-icons/gogdotcom.svg?color=currentColor",
    "itch": "https://api.iconify.design/simple-icons/itchdotio.svg?color=currentColor",
    "google-play": "https://api.iconify.design/simple-icons/googleplay.svg?color=currentColor",
    "apple-appstore": "https://api.iconify.design/simple-icons/appstore.svg?color=currentColor",
    "website": "https://api.iconify.design/mdi/web.svg?color=currentColor"
}

# Mapeo de store_id a slugs de tiendas (según la documentación de RAWG)
TIENDAS_SOPORTADAS = {
    1: "steam",
    2: "xbox-store",  # Tienda de xbox moderna, la de xbox 360 era la 7 pero cerró sus servidores.
    3: "playstation-store",
    4: "apple-appstore",
    5: "gog",
    6: "nintendo-eshop",
    8: "google-play",
    9: "itch",
    11: "epic-games"
}

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

# Obtiene el enlace al sitio web oficial del juego usando la API de RAWG.
def obtener_website_juego(game_id: str) -> str:
    
    try:
        # Obtener detalles del juego
        url = f"https://api.rawg.io/api/games/{game_id}?key={rawg_api_key}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Obtener el campo website si existe
        website = data.get("website", "")
        if website and website.startswith(("http://", "https://")):
            return website
        print(f"No se encontró website para game_id {game_id}")
        return ""
    except Exception as e:
        print(f"Error al obtener website para game_id {game_id}: {str(e)}")
        return ""


#Obtiene los enlaces de las tiendas para un juego usando la API de RAWG, priorizando plataformas listadas en la recomendación
def obtener_tiendas_juego(nombre_juego: str, plataformas: str = "") -> list:
    try:
        # Buscar el juego en RAWG
        url = f"https://api.rawg.io/api/games?key={rawg_api_key}&search={nombre_juego}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Obtener el ID y slug del primer juego coincidente
        if not data["results"]:
            print(f"No se encontraron resultados para {nombre_juego}")
            return []
        game_id = data["results"][0]["id"]
        game_slug = data["results"][0]["slug"]

        # Obtener tiendas usando el endpoint /stores
        url_stores = f"https://api.rawg.io/api/games/{game_slug}/stores?key={rawg_api_key}"
        response_stores = requests.get(url_stores)
        response_stores.raise_for_status()
        data_stores = response_stores.json()

        # Mapear plataformas listadas a slugs de tiendas
        plataformas_lista = [p.strip().lower() for p in plataformas.split(",")] if plataformas else []
        plataforma_a_tienda = {
            "pc": ["steam", "epic-games", "gog", "itch"],
            "ps4": ["playstation-store"],
            "ps5": ["playstation-store"],
            "ps3": ["playstation-store"],
            "ps2": ["playstation-store"],
            "xbox one": ["xbox-store"],
            "xbox series x/s": ["xbox-store"],
            "xbox 360": ["xbox-store"],
            "nintendo switch": ["nintendo-eshop"],
            "wii u": ["nintendo-eshop"],
            "wii": ["nintendo-eshop"],
            "android": ["google-play"],
            "ios": ["apple-appstore"],
            "mac": ["apple-appstore", "steam", "gog"]
        }
        tiendas_esperadas = set()
        # Normalizar las plataformas para una mejor coincidencia
        for plat in plataformas_lista:
            for key in plataforma_a_tienda.keys():
                # Normalizar para manejar variaciones como "PlayStation 4" o "xbox series x"
                key_normalized = key.replace("x/s", "").strip()
                plat_normalized = plat.replace("playstation 4", "ps4").replace("playstation 5", "ps5").replace("xbox series x", "xbox series x/s").replace("nintendo", "nintendo switch").strip()
                if key_normalized in plat_normalized:
                    tiendas_esperadas.update(plataforma_a_tienda[key])

        # Procesar las tiendas
        tiendas = []
        tiendas_priorizadas = []  # Tiendas que coinciden con las plataformas listadas
        tiendas_secundarias = []  # Tiendas que no coinciden pero tienen URLs válidas
        for store in data_stores.get("results", []):
            store_id = store["store_id"]
            store_url = store.get("url", "")
            store_slug = TIENDAS_SOPORTADAS.get(store_id)
            if not store_url:
                print(f"URL vacía para {nombre_juego} en la tienda con store_id {store_id}, omitiendo...")
                continue
            if store_slug and store_url and store_slug in ICONOS_TIENDA:  # Solo incluir si la tienda es soportada y tiene URL
                # Usamos el enlace de RAWG
                if not store_url.startswith(("http://", "https://")):
                    store_url = f"https://{store_url}"
                tienda_info = {
                    "nombre": store_slug.replace("-", " ").title(),  # Ejemplo: "playstation-store" -> "Playstation Store"
                    "slug": store_slug,
                    "url": store_url,
                    "icono": ICONOS_TIENDA[store_slug]
                }
                if tiendas_esperadas and store_slug in tiendas_esperadas:
                    tiendas_priorizadas.append(tienda_info)
                else:
                    tiendas_secundarias.append(tienda_info)

        # Combinar tiendas: primero las priorizadas, luego las secundarias
        tiendas = tiendas_priorizadas + tiendas_secundarias

        # Si no hay tiendas, intentar usar el website del juego
        if not tiendas:
            website = obtener_website_juego(game_id)
            if website:
                tiendas.append({
                    "nombre": "Sitio Oficial",
                    "slug": "website",
                    "url": website,
                    "icono": ICONOS_TIENDA["website"]
                })

        return tiendas
    except Exception as e:
        print(f"Error al obtener tiendas para {nombre_juego}: {str(e)}")
        return []