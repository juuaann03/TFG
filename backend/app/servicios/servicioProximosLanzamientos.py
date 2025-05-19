# archivo: app/servicios/servicioProximosLanzamientos.py

import os
import json
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from openai import BadRequestError
import requests
from datetime import datetime, timedelta
from app.utils.utilidadesVarias import *



# Prompt para preprocesar los datos del usuario
prompt_preprocesamiento = PromptTemplate(
    input_variables=["datosUsuario"],
    template="""
Analiza los siguientes datos del perfil del usuario para extraer información relevante que ayude a recomendar próximos lanzamientos de videojuegos:

Datos del usuario:
{datosUsuario}

Devuelve un JSON con la siguiente estructura:
- "generos": Lista de géneros preferidos o inferidos (ej. ["acción", "aventura"]).
- "plataformas": Lista de plataformas disponibles (ej. ["PS4", "PC"]).
- "idiomas": Lista de idiomas preferidos (ej. ["español", "inglés"]).
- "necesidadesEspeciales": Lista de necesidades especiales (ej. ["subtítulos grandes"]).
- "suscripciones": Lista de suscripciones relevantes (ej. ["PS Plus", "Xbox Game Pass"]).
- "requisitosPc": Objeto con requisitos de PC (ej. {{"procesador": "i7-12700H", "tarjetaGrafica": "RTX 3080"}}).
- "juegosGustados": Lista de juegos gustados para inferir preferencias.
- "juegosNoGustados": Lista de juegos no gustados para evitar similitudes.

Usa abreviaturas estándar:
- Consolas: "PlayStation 4" → "PS4", "PlayStation 5" → "PS5", "Nintendo Switch" → "Switch", "Xbox Series X" → "XSX".
- Juegos: "Grand Theft Auto 5" → "GTA 5", "The Legend of Zelda: Breath of the Wild" → "Zelda BOTW".
- Hardware: "Intel Core i7-12700H" → "i7-12700H", "NVIDIA GeForce RTX 3080" → "RTX 3080".
- Corrige errores tipográficos (ej. "Play Staton 4" → "PS4").
- Las abreviaturas deben estar en mayúsculas.

Devuelve solo el JSON.
"""
)

# Prompt para filtrar y personalizar recomendaciones
prompt_filtrado = PromptTemplate(
    input_variables=["datosProcesados", "juegosDisponibles"],
    template="""
Actúa como un experto en videojuegos. Tu tarea es filtrar y seleccionar videojuegos de una lista de próximos lanzamientos para recomendar al usuario, basándote en sus preferencias.

Datos procesados del usuario:
{datosProcesados}

Lista de juegos disponibles (próximos lanzamientos):
{juegosDisponibles}

Instrucciones:
- Selecciona exactamente 4 videojuegos de la lista proporcionada que sean los más relevantes para el usuario.
- Los juegos deben coincidir con los géneros, plataformas, idiomas, suscripciones, necesidades especiales, franquicias
 y requisitos de PC especificados si es posible.
- Asegúrate de que las recomendaciones sean variadas en género y plataformas cuando sea posible.
- Usa abreviaturas estándar (ej. "PS4", "i7-12700H").
- No modifiques los datos de los juegos (nombres, plataformas, fechas) ni inventes información.
- Presenta las recomendaciones en el siguiente formato:

1. **Nombre del juego**
   - Plataformas:
   - Fecha de lanzamiento:

Devuelve solo la lista de recomendaciones.
"""
)

#Obtiene una lista de juegos próximos a lanzarse usando la API de RAWG.
def obtener_juegos_proximos() -> List[Dict]:



    # Calcular fechas para los próximos 2 años
    today = datetime.now()
    start_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (today + timedelta(days=730)).strftime("%Y-%m-%d")

    juegos = []
    page = 1
    max_pages = 3  # Limitar a 3 páginas para evitar excesivas solicitudes

    try:
        while page <= max_pages:
            url = f"https://api.rawg.io/api/games?key={rawg_api_key}&dates={start_date},{end_date}&page_size=40&page={page}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            results = data.get("results")
            if not results:
                break

            for game in results:
                nombre = game.get("name")
                fecha = game.get("released")
                plataformas = game.get("platforms")
                
                if not (nombre and fecha and plataformas):
                    continue  # Saltar juegos con datos incompletos

                plataformas_str = ", ".join(
                    [p["platform"]["name"] for p in plataformas if p.get("platform", {}).get("name")]
                )
                # Normalizar plataformas a abreviaturas estándar
                plataformas_str = plataformas_str.replace("PlayStation 4", "PS4") \
                    .replace("PlayStation 5", "PS5") \
                    .replace("Nintendo Switch", "Switch") \
                    .replace("Xbox Series S/X", "XSX") \
                    .replace("PC", "PC") \
                    .replace("Xbox One", "XOne")
                
                juegos.append({
                    "nombre": nombre,
                    "plataformas": plataformas_str,
                    "fecha_lanzamiento": fecha,
                    "generos": [g["name"].lower() for g in game.get("genres", [])]
                })

            # Verificar si hay más páginas
            if not data.get("next"):
                break
            page += 1

        if not juegos:
            raise ValueError("No se encontraron juegos próximos en el rango de fechas especificado.")
        
        return juegos

    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error al obtener juegos próximos de RAWG: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error al obtener juegos próximos de RAWG: {str(e)}")



def obtenerProximosLanzamientosServicio(datos_usuario: dict) -> List[Dict]:

    # Preprocesar los datos del usuario
    datos_procesados = None
    for modelo in modelos:
        try:
            llm_preprocesamiento = ChatOpenAI(model_name=modelo, temperature=0.4)
            chain_preprocesamiento = prompt_preprocesamiento | llm_preprocesamiento | StrOutputParser()
            respuesta = chain_preprocesamiento.invoke({
                "datosUsuario": json.dumps(datos_usuario, default=str)
            })
            # Limpiar respuesta
            respuesta_limpia = limpiar_respuesta(respuesta)
            if not respuesta_limpia:
                continue  # Pasa al siguiente modelo si no se obtuvo JSON válido
            # Parsear respuesta
            datos_procesados = json.loads(respuesta_limpia)
            break  # Salir si se obtiene una respuesta válida
        except (BadRequestError, json.JSONDecodeError, Exception):
            continue  # Pasa al siguiente modelo si hay un error

    if not datos_procesados:
        raise ValueError("No se pudo preprocesar los datos del usuario con ningún modelo")

    # Obtener juegos próximos desde RAWG
    try:
        juegos_disponibles = obtener_juegos_proximos()
        if not juegos_disponibles:
            raise ValueError("No se encontraron juegos próximos en RAWG.")
    except Exception as e:
        raise ValueError("Error al obtener juegos próximos: {str(e)}")

    # Filtrar y personalizar recomendaciones
    recomendaciones = []
    seen = set()
    for modelo in modelos:
        if len(recomendaciones) >= 4:  # Detener si ya tenemos 4 recomendaciones únicas
            break
        try:
            llm = ChatOpenAI(model_name=modelo, temperature=0.7)
            chain = prompt_filtrado | llm | StrOutputParser()
            respuesta = chain.invoke({
                "datosProcesados": json.dumps(datos_procesados, default=str),
                "juegosDisponibles": json.dumps(juegos_disponibles, default=str)
            })
            # Parsear respuesta del modelo
            for linea in respuesta.split("\n"):
                if linea.strip().startswith(("1. ", "2. ", "3. ", "4. ")):
                    nombre = linea.split("**")[1].strip()
                    plataformas = ""
                    fecha_lanzamiento = ""
                    for sublinea in respuesta.split("\n")[respuesta.split("\n").index(linea)+1:]:
                        if sublinea.strip().startswith("- Plataformas:"):
                            plataformas = sublinea.replace("- Plataformas:", "").strip()
                        elif sublinea.strip().startswith("- Fecha de lanzamiento:"):
                            fecha_lanzamiento = sublinea.replace("- Fecha de lanzamiento:", "").strip()
                        elif sublinea.strip() and not sublinea.strip().startswith("- "):
                            break
                    # Validar contra datos de RAWG
                    for game in juegos_disponibles:
                        if game["nombre"].lower() == nombre.lower() and game["nombre"] not in seen:
                            recomendaciones.append({
                                "titulo": game["nombre"],
                                "plataformas": game["plataformas"],
                                "fecha_lanzamiento": game["fecha_lanzamiento"],
                                "imagen": obtener_imagen_juego(game["nombre"])
                            })
                            seen.add(game["nombre"])
                            break
        except BadRequestError:
            continue
        except Exception:
            continue

    # Si no se alcanzaron 4 recomendaciones, completar con juegos adicionales
    if len(recomendaciones) < 4:
        for game in juegos_disponibles:
            if game["nombre"] not in seen and len(recomendaciones) < 4:
                recomendaciones.append({
                    "titulo": game["nombre"],
                    "plataformas": game["plataformas"],
                    "fecha_lanzamiento": game["fecha_lanzamiento"],
                    "imagen": obtener_imagen_juego(game["nombre"])
                })
                seen.add(game["nombre"])

    if not recomendaciones:
        # Fallback: Seleccionar 4 juegos aleatorios si los modelos fallan
        import random
        recomendaciones = random.sample(juegos_disponibles, min(4, len(juegos_disponibles)))
        recomendaciones = [{
            "titulo": game["nombre"],
            "plataformas": game["plataformas"],
            "fecha_lanzamiento": game["fecha_lanzamiento"],
            "imagen": obtener_imagen_juego(game["nombre"])
        } for game in recomendaciones]

    return recomendaciones[:4]