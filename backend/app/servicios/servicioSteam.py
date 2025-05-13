# archivo: app/servicios/servicioSteam.py

import os
import requests
from typing import List, Dict
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables del .env
dotenv_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=dotenv_path)

def obtener_juegos_steam(steam_id: str) -> List[Dict]:
    """
    Obtiene los juegos poseídos por un usuario de Steam usando la Steam Web API.
    
    Args:
        steam_id (str): SteamID64 del usuario.
        
    Returns:
        List[Dict]: Lista de juegos con nombre, appid y tiempo jugado.
        
    Raises:
        ValueError: Si la clave de API no está definida o la solicitud falla.
    """
    steam_api_key = os.getenv("STEAM_API_KEY")
    if not steam_api_key:
        raise ValueError("STEAM_API_KEY no está definido en el .env")

    url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
    params = {
        "key": steam_api_key,
        "steamid": steam_id,
        "include_appinfo": True,
        "include_played_free_games": True
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Verificar si la respuesta contiene juegos
        if not data.get("response") or not data["response"].get("games"):
            return []

        # Procesar los juegos
        juegos = [
            {
                "nombre": game["name"],
                "appid": game["appid"],
                "playtime_forever": game["playtime_forever"]
            }
            for game in data["response"]["games"]
        ]
        return juegos

    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error al consultar la API de Steam: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error inesperado al procesar la respuesta de Steam: {str(e)}")