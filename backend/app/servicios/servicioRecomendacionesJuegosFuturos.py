# archivo: app/servicios/servicioRecomendacionesJuegosFuturos.py


import os
import json
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from openai import BadRequestError
from app.modelos.modeloUsuario import UsuarioOpcionalConHistorial
import requests

# Cargar variables del .env
dotenv_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Prompt para preprocesar los datos del usuario
prompt_preprocesamiento = PromptTemplate(
    input_variables=["datosUsuario", "historial"],
    template="""
Analiza los datos del usuario y su historial de conversaciones para extraer información relevante que ayude a generar recomendaciones de videojuegos futuros (lanzamientos en 2025 o más allá):

Datos del usuario:
{datosUsuario}

Historial de conversaciones (preguntas y recomendaciones previas):
{historial}

Devuelve un JSON con la siguiente estructura:
- "generos": Lista de géneros preferidos o inferidos (ej. ["acción", "aventura"]).
- "plataformas": Lista de plataformas preferidas o disponibles (ej. ["PS5", "PC"]).
- "idiomas": Lista de idiomas preferidos (ej. ["español", "inglés"]).
- "necesidadesEspeciales": Lista de necesidades especiales (ej. ["subtítulos grandes"]).
- "excluirJuegos": Lista de juegos que no deben recomendarse (jugados, no gustados, o ya recomendados).
- "suscripciones": Lista de suscripciones relevantes (ej. ["PS Plus", "Xbox Game Pass"]).
- "requisitosPc": Objeto con requisitos de PC (ej. {{"procesador": "i7-12700H", "tarjetaGrafica": "RTX 3080"}}).
- "preferenciasAdicionales": Otras preferencias inferidas (ej. "juegos cortos", "multijugador").
- "contexto": Breve descripción del análisis para usar en el historial (ej. "Recomendaciones de juegos futuros para PS5 basadas en preferencias de acción").

Usa abreviaturas estándar:
- Consolas: "PlayStation 5" → "PS5", "Nintendo Switch" → "Switch", "Xbox Series X" → "XSX".
- Juegos: "Grand Theft Auto 5" → "GTA 5", "The Legend of Zelda: Breath of the Wild" → "Zelda BOTW".
- Hardware: "Intel Core i7-12700H" → "i7-12700H", "NVIDIA GeForce RTX 3080" → "RTX 3080".
- Corrige errores tipográficos (ej. "Play Staton 5" → "PS5").
- Las abreviaturas deben estar en mayúsculas.

Devuelve solo el JSON.
"""
)

# Prompt para generar recomendaciones iniciales
prompt_recomendacion = PromptTemplate(
    input_variables=["datosProcesados"],
    template="""
Actúa como un experto en videojuegos. Busca en internet videojuegos que serán lanzados en 2025 o más allá y genera recomendaciones basadas en los datos procesados del usuario:

Datos procesados:
{datosProcesados}

Instrucciones:
- Recomienda exactamente 4 videojuegos que coincidan con los géneros, plataformas, idiomas, suscripciones, necesidades especiales, y requisitos de PC especificados.
- Excluye los juegos listados en "excluirJuegos".
- Usa abreviaturas estándar (ej. "PS5", "GTA 5", "i7-12700H").
- Presenta las recomendaciones en formato de lista con esta estructura:

1. **Nombre del juego**
   - Fecha de lanzamiento: [Formato DD Month YYYY, ej. "30 May 2025"]
   - Plataformas:
   - Imagen: [URL de la imagen, si no está disponible usa "https://via.placeholder.com/150"]

Devuelve solo la lista de recomendaciones, sin explicaciones adicionales.
"""
)

# Prompt para sintetizar y validar recomendaciones
prompt_sintesis = PromptTemplate(
    input_variables=["datosProcesados", "respuestasModelos"],
    template="""
Eres un experto en videojuegos. Tu tarea es sintetizar y validar recomendaciones de videojuegos futuros (lanzamientos en 2025 o más allá) provenientes de múltiples modelos para generar una lista final coherente.

Datos procesados del usuario:
{datosProcesados}

Recomendaciones de modelos:
{respuestasModelos}

Instrucciones:
- Combina las recomendaciones, eliminando duplicados y juegos en "excluirJuegos".
- Selecciona exactamente 4 videojuegos más relevantes y coherentes con los géneros, plataformas, idiomas, suscripciones, necesidades especiales, y requisitos de PC.
- Asegúrate de que las recomendaciones sean variadas en género y plataformas cuando sea posible.
- Usa abreviaturas estándar (ej. "PS5", "GTA 5", "i7-12700H").
- Cada recomendación DEBE incluir nombre, fecha de lanzamiento, plataformas, e imagen.
- Si la imagen no está disponible, usa "https://via.placeholder.com/150".
- Presenta las recomendaciones en el siguiente formato:

1. **Nombre del juego**
   - Fecha de lanzamiento: [DD Month YYYY]
   - Plataformas:
   - Imagen: [URL]

Devuelve solo la lista final de recomendaciones.
"""
)

def obtener_juegos_futuros_rawg(generos: List[str], plataformas: List[str]) -> List[Dict]:
    """Obtiene juegos futuros de la API de RAWG."""
    rawg_api_key = os.getenv("RAWG_API_KEY")
    if not rawg_api_key:
        return []

    try:
        # Filtrar por fechas futuras (2025 en adelante)
        url = f"https://api.rawg.io/api/games?key={rawg_api_key}&dates=2025-01-01,2030-12-31"
        if generos:
            # Convertir géneros a slugs (simplificado, necesitarías mapear géneros a IDs de RAWG)
            url += f"&genres={','.join(generos).lower().replace(' ', '-')}"
        if plataformas:
            # Convertir plataformas a IDs (simplificado, necesitarías mapear plataformas a IDs de RAWG)
            url += f"&platforms={','.join(['1' if p == 'PC' else '4' if p == 'PS5' else '18' if p == 'XSX' else '7' for p in plataformas])}"
        
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        juegos = []
        for juego in data["results"][:10]:  # Limitar a 10 para no sobrecargar
            juegos.append({
                "nombre": juego.get("name", "Juego desconocido"),
                "fecha_lanzamiento": juego.get("released", "Desconocida"),
                "plataformas": ", ".join([p["platform"]["name"] for p in juego.get("platforms", [])]),
                "imagen": juego.get("background_image", "https://via.placeholder.com/150")
            })
        return juegos
    except Exception as e:
        print(f"Error al obtener juegos de RAWG: {str(e)}")
        return []

def generarRecomendacionesJuegosFuturos(datos_usuario: dict) -> Tuple[List[Dict], str]:
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY no está definido en el .env")

    os.environ["OPENAI_API_KEY"] = openrouter_api_key
    os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"

    # Preprocesar los datos del usuario
    try:
        llm_preprocesamiento = ChatOpenAI(model_name="openai/gpt-3.5-turbo", temperature=0.4)
        chain_preprocesamiento = prompt_preprocesamiento | llm_preprocesamiento | StrOutputParser()
        datos_procesados = json.loads(chain_preprocesamiento.invoke({
            "datosUsuario": json.dumps(datos_usuario, default=str),
            "historial": json.dumps(datos_usuario.get("historialConversaciones", []), default=str)
        }))
    except Exception as e:
        raise ValueError(f"Error al preprocesar los datos del usuario: {str(e)}")

    # Extraer contexto
    contexto = datos_procesados.get("contexto", "Recomendaciones de juegos futuros basadas en datos del usuario.")

    # Obtener juegos futuros de RAWG
    juegos_rawg = obtener_juegos_futuros_rawg(
        datos_procesados.get("generos", []),
        datos_procesados.get("plataformas", [])
    )

    # Generar recomendaciones iniciales con modelos :online
    modelos_recomendacion = [
        "openai/o1:online",  # Principal, con acceso a internet
        "openai/o3-mini:online",  # Respaldo 1
        "meta-ai/llama-3.1-8b-instruct:free"  # Respaldo 2 (sin :online)
    ]
    respuestas_modelos = []
    for modelo in modelos_recomendacion:
        try:
            llm = ChatOpenAI(model_name=modelo, temperature=0.7)
            chain = prompt_recomendacion | llm | StrOutputParser()
            respuesta = chain.invoke({
                "datosProcesados": json.dumps(datos_procesados, default=str)
            })
            respuestas_modelos.append(respuesta)
        except BadRequestError as e:
            print(f"Error con el modelo {modelo}: {str(e)}. Continuando con los demás modelos.")
            continue
        except Exception as e:
            print(f"Error inesperado con el modelo {modelo}: {str(e)}. Continuando con los demás modelos.")
            continue

    # Añadir juegos de RAWG como una "respuesta" adicional
    if juegos_rawg:
        respuesta_rawg = "\n".join([
            f"1. **{juego['nombre']}**\n"
            f"   - Fecha de lanzamiento: {juego['fecha_lanzamiento']}\n"
            f"   - Plataformas: {juego['plataformas']}\n"
            f"   - Imagen: {juego['imagen']}"
            for juego in juegos_rawg[:4]
        ])
        respuestas_modelos.append(respuesta_rawg)

    if not respuestas_modelos:
        raise ValueError("No se pudo obtener respuestas de ningún modelo ni de RAWG.")

    # Sintetizar recomendaciones
    respuestas_combinadas = "\n\n".join([f"Modelo {i+1}:\n{resp}" for i, resp in enumerate(respuestas_modelos)])
    modelos_sintesis = [
        "openai/gpt-4o-mini",  # Principal
        "openai/o1:online",  # Respaldo 1
        "openai/gpt-3.5-turbo",  # Respaldo 2
        "meta-ai/llama-3.1-8b-instruct:free"  # Respaldo 3
    ]

    for modelo in modelos_sintesis:
        try:
            llm_sintesis = ChatOpenAI(model_name=modelo, temperature=0.5)
            chain_sintesis = prompt_sintesis | llm_sintesis | StrOutputParser()
            respuesta_final = chain_sintesis.invoke({
                "datosProcesados": json.dumps(datos_procesados, default=str),
                "respuestasModelos": respuestas_combinadas
            })
            break  # Si la síntesis es exitosa, salir del bucle
        except BadRequestError as e:
            print(f"Error con el modelo de síntesis {modelo}: {str(e)}. Intentando con el siguiente modelo.")
            continue
        except Exception as e:
            print(f"Error inesperado con el modelo de síntesis {modelo}: {str(e)}. Intentando con el siguiente modelo.")
            continue
    else:
        raise ValueError("No se pudo obtener una respuesta válida de ningún modelo de síntesis.")

    # Parsear la respuesta final
    try:
        recomendaciones = []
        for linea in respuesta_final.split("\n"):
            if linea.strip().startswith(("1. ", "2. ", "3. ", "4. ")):
                nombre = linea.split("**")[1].strip()
                fecha_lanzamiento = ""
                plataformas = ""
                imagen = "https://via.placeholder.com/150"
                for sublinea in respuesta_final.split("\n")[respuesta_final.split("\n").index(linea)+1:]:
                    if sublinea.strip().startswith("- Fecha de lanzamiento:"):
                        fecha_lanzamiento = sublinea.replace("- Fecha de lanzamiento:", "").strip()
                    elif sublinea.strip().startswith("- Plataformas:"):
                        plataformas = sublinea.replace("- Plataformas:", "").strip()
                    elif sublinea.strip().startswith("- Imagen:"):
                        imagen = sublinea.replace("- Imagen:", "").strip()
                    elif sublinea.strip().startswith(("1. ", "2. ", "3. ", "4. ")):
                        break
                # Intentar obtener imagen de RAWG si no se proporcionó
                if imagen == "https://via.placeholder.com/150":
                    rawg_imagen = obtener_juegos_futuros_rawg([nombre], [])[0]["imagen"] if obtener_juegos_futuros_rawg([nombre], []) else imagen
                    imagen = rawg_imagen or imagen
                recomendaciones.append({
                    "nombre": nombre,
                    "fecha_lanzamiento": fecha_lanzamiento,
                    "plataformas": plataformas,
                    "imagen": imagen
                })
        if len(recomendaciones) != 4:
            raise ValueError("No se obtuvieron exactamente 4 recomendaciones.")
    except Exception as e:
        raise ValueError(f"Error al parsear la respuesta final: {str(e)}")

    return recomendaciones, contexto