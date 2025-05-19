# archivo: app/servicios/servicioSteam.py

import requests
from typing import List, Dict
from app.utils.utilidadesVarias import *

# Obtiene los juegos poseídos por un usuario de Steam usando la Steam Web API.

def obtener_juegos_steam(steam_id: str) -> List[Dict]:

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