# archivo: app/servicios/servicioRecomendacionPersonalizada.py
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
import requests  # Añadir para solicitudes HTTP

# Cargar variables del .env
dotenv_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Prompt para preprocesar la petición
prompt_preprocesamiento = PromptTemplate(
    input_variables=["peticion", "datosUsuario", "historial"],
    template="""
Analiza la siguiente petición del usuario y los datos de su perfil para extraer información relevante que ayude a generar una recomendación de videojuegos personalizada:

Petición: "{peticion}"

Datos del usuario:
{datosUsuario}

Historial de conversaciones (preguntas y recomendaciones previas):
{historial}

Devuelve un JSON con la siguiente estructura:
- "generos": Lista de géneros mencionados o inferidos (ej. ["acción", "aventura"]).
- "plataformas": Lista de plataformas mencionadas o disponibles (ej. ["PS4", "PC"]).
- "idiomas": Lista de idiomas preferidos o mencionados (ej. ["español", "inglés"]).
- "necesidadesEspeciales": Lista de necesidades especiales mencionadas o del perfil (ej. ["subtítulos grandes"]).
- "excluirJuegos": Lista de juegos que no deben recomendarse (jugados, no gustados, o ya recomendados).
- "suscripciones": Lista de suscripciones relevantes (ej. ["PS Plus", "Xbox Game Pass"]).
- "requisitosPc": Objeto con requisitos de PC inferidos o del perfil (ej. {{"procesador": "i7-12700H", "tarjetaGrafica": "RTX 3080"}}).
- "preferenciasAdicionales": Cualquier otra preferencia mencionada (ej. "juegos cortos", "multijugador").

Usa abreviaturas estándar:
- Consolas: "PlayStation 4" → "PS4", "PlayStation 5" → "PS5", "Nintendo Switch" → "Switch", "Xbox Series X" → "XSX".
- Juegos: "Grand Theft Auto 5" → "GTA 5", "The Legend of Zelda: Breath of the Wild" → "Zelda BOTW".
- Hardware: "Intel Core i7-12700H" → "i7-12700H", "NVIDIA GeForce RTX 3080" → "RTX 3080".
- Corrige errores tipográficos (ej. "Play Staton 4" → "PS4").
- Las abreviaturas deben estar en mayúsculas.

Devuelve solo el JSON.
"""
)

# Prompt para generar cambios implícitos en el perfil
prompt_cambios = PromptTemplate(
    input_variables=["estadoActual", "peticion"],
    template="""
Tienes este estado actual del perfil del usuario. Solo se incluyen campos opcionales del esquema completo (sin historial de conversaciones):

{estadoActual}

El usuario ha escrito esta petición para una recomendación de videojuegos:

"{peticion}"

Tu tarea es devolver un JSON **válido** con dos campos:
- "mensaje": una cadena que describe los cambios realizados o indica si no se hicieron cambios.
- "actualizacion": un JSON mínimo y conforme al siguiente esquema parcial, con solo los cambios necesarios para reflejar información implícita en la petición que deba actualizarse en el perfil del usuario.

Este es el formato correcto para los campos opcionales:
- consolas: lista de strings
- configuracionPc: objeto con claves so, procesador, memoria, tarjetaGrafica
- necesidadesEspeciales: lista de strings
- juegosGustados / juegosNoGustados / juegosJugados / suscripciones / idiomas: listas de strings
- juegosPoseidos: lista de objetos con nombre y consolasDisponibles (lista de strings)

Instrucciones:
- No devuelvas texto adicional, solo el JSON.
- Si no hay cambios necesarios, devuelve un objeto con "mensaje" indicando que no se hicieron cambios y "actualizacion" como {{}}.
- Solo genera cambios basados en información explícita o implícita en la petición que sea relevante para el perfil (ej. consolas adquiridas, juegos no gustados, suscripciones mencionadas). Ignora frases relacionadas con recomendaciones (ej. "recomiéndame juegos como GTA") a menos que indiquen claramente una actualización del perfil.
- Usa abreviaturas estándar para consolas, juegos y hardware:
  - Consolas: "PlayStation 4" o "Play Station 4" → "PS4", "PlayStation 5" → "PS5", "Nintendo Switch" → "Switch", "Xbox Series X" → "XSX".
  - Juegos: "Grand Theft Auto 5" o "Grand Theft Auto Cinco" → "GTA 5", "The Legend of Zelda: Breath of the Wild" → "Zelda BOTW".
  - Hardware: "Intel Core i7-12700H" → "i7-12700H", "NVIDIA GeForce RTX 3080" → "RTX 3080".
- Corrige errores tipográficos obvios (ej. "Play Staton 4" → "PS4").
- Si no conoces una abreviatura estándar, usa el nombre completo corregido.
- Las abreviaturas deben estar en mayúsculas (ej. "PS4", no "ps4").
- Para hardware, conserva detalles importantes como la generación del procesador (ej. "i7-12700H", no solo "i7").
- Ejemplos:
  - Petición: "Me compré una PS4 y no me gustó The Last of Us"
    Respuesta: {{"mensaje": "Se añadió la PS4 a consolas y The Last of Us a juegosNoGustados", "actualizacion": {{"consolas": ["PS4"], "juegosNoGustados": ["The Last of Us"]}}}}
  - Petición: "Recomiéndame juegos como GTA 5"
    Respuesta: {{"mensaje": "No se realizaron cambios", "actualizacion": {{}}}}
  - Petición: "Tengo una suscripción a PS Plus"
    Respuesta: {{"mensaje": "Se añadió PS Plus a suscripciones", "actualizacion": {{"suscripciones": ["PS Plus"]}}}}
  - Petición: "Quiero un juego para mi PC con procesador i7"
    Respuesta: {{"mensaje": "Se actualizó la configuración de PC con procesador i7", "actualizacion": {{"configuracionPc": {{"procesador": "i7"}}}}}}

Devuelve solo el JSON.
"""
)

# Prompt para generar recomendaciones iniciales
prompt_recomendacion = PromptTemplate(
    input_variables=["peticion", "datosProcesados"],
    template="""
Actúa como un experto en videojuegos. Genera recomendaciones de videojuegos basadas en la siguiente petición y datos procesados del usuario:

Petición: "{peticion}"

Datos procesados:
{datosProcesados}

Instrucciones:
- Recomienda 3-5 videojuegos que cumplan con los géneros, plataformas, idiomas, suscripciones, necesidades especiales, y requisitos de PC especificados, 
(si es posible) y coherentes con la descripción del usuario. Si el usuario pidió un número específico de juegos (por ejemplo, "quiero un juego"), selecciona solo ese número, eligiendo el más adecuado.
- Excluye los juegos listados en "excluirJuegos".
- Usa abreviaturas estándar (ej. "PS4", "GTA 5", "i7-12700H").
- Presenta las recomendaciones en formato de lista con esta estructura:

1. **Nombre del juego**
   - Género:
   - Plataformas:
   - ¿Porqué este videojuego? Breve razón por la que se adapta a la petición y datos del usuario

Devuelve solo la lista de recomendaciones, sin explicaciones adicionales.
"""
)

# Prompt para sintetizar y validar recomendaciones
prompt_sintesis = PromptTemplate(
    input_variables=["peticion", "datosProcesados", "respuestasModelos"],
    template="""
Eres un experto en videojuegos. Tu tarea es sintetizar y validar recomendaciones de videojuegos provenientes de múltiples modelos para generar una lista final coherente y personalizada.

Petición del usuario: "{peticion}"

Datos procesados del usuario:
{datosProcesados}

Recomendaciones de modelos:
{respuestasModelos}

Instrucciones:
- Combina las recomendaciones, eliminando duplicados y juegos en "excluirJuegos".
- Selecciona las recomendaciones más relevantes y coherentes con la petición, géneros, plataformas, idiomas, suscripciones, necesidades especiales, y requisitos de PC.
- Asegúrate de que las recomendaciones sean variadas en género y plataformas cuando sea posible.
- Usa abreviaturas estándar (ej. "PS4", "GTA 5", "i7-12700H").
- Cada recomendación DEBE incluir una razón clara y específica en "¿Porqué este videojuego?".
- Presenta las recomendaciones en el siguiente formato:

1. **Nombre del juego**
   - Género:
   - Plataformas:
   - ¿Porqué este videojuego? [Razón clara y específica]

Devuelve solo la lista final de recomendaciones.
"""
)

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

def generarCambiosDesdePeticionRecomendacion(estado_actual: dict, peticion: str) -> tuple[str, dict]:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY no está definido")

    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"

    # Definir modelos: principal y de respaldo
    modelos = [
        "openai/gpt-3.5-turbo",  # Modelo principal
        "meta-ai/llama-3.1-8b-instruct:free",  # Respaldo 1
        "qwen/qwen3-0.6b-04-28:free"  # Respaldo 2
    ]

    # Intentar con cada modelo hasta obtener una respuesta válida
    for modelo in modelos:
        try:
            llm = ChatOpenAI(model_name=modelo, temperature=0.4)
            chain = prompt_cambios | llm | StrOutputParser()
            respuesta = chain.invoke({"estadoActual": json.dumps(estado_actual, default=str), "peticion": peticion})

            # Parsear la respuesta
            try:
                respuesta_json = json.loads(respuesta)
                mensaje = respuesta_json.get("mensaje", "No se proporcionó un mensaje")
                actualizacion = respuesta_json.get("actualizacion", {})
                return mensaje, actualizacion
            except json.JSONDecodeError:
                print(f"Error: La respuesta de {modelo} no es un JSON válido. Intentando con el siguiente modelo.")
                continue

        except BadRequestError as e:
            print(f"Error con el modelo {modelo}: {str(e)}. Intentando con el siguiente modelo.")
            continue
        except Exception as e:
            print(f"Error inesperado con el modelo {modelo}: {str(e)}. Intentando con el siguiente modelo.")
            continue

    # Si ningún modelo funciona, lanzar error
    raise ValueError("No se pudo obtener una respuesta válida de ningún modelo para generar cambios")

def generarRecomendacionPersonalizada(peticion: str, datos_usuario: dict) -> Tuple[List[Dict], str]:
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY no está definido en el .env")

    os.environ["OPENAI_API_KEY"] = openrouter_api_key
    os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"

    # Preprocesar la petición
    try:
        llm_preprocesamiento = ChatOpenAI(model_name="openai/gpt-3.5-turbo", temperature=0.4)
        chain_preprocesamiento = prompt_preprocesamiento | llm_preprocesamiento | StrOutputParser()
        datos_procesados = json.loads(chain_preprocesamiento.invoke({
            "peticion": peticion,
            "datosUsuario": json.dumps(datos_usuario, default=str),
            "historial": json.dumps(datos_usuario.get("historialConversaciones", []), default=str)
        }))
    except Exception as e:
        raise ValueError(f"Error al preprocesar la petición: {str(e)}")


    # Generar recomendaciones iniciales
    modelos_recomendacion = [
        "meta-llama/llama-guard-4-12b",
        "qwen/qwen3-0.6b-04-28:free",
        "openai/gpt-3.5-turbo"
    ]
    respuestas_modelos = []
    for modelo in modelos_recomendacion:
        try:
            llm = ChatOpenAI(model_name=modelo, temperature=0.7)
            chain = prompt_recomendacion | llm | StrOutputParser()
            respuesta = chain.invoke({
                "peticion": peticion,
                "datosProcesados": json.dumps(datos_procesados, default=str)
            })
            respuestas_modelos.append(respuesta)
        except BadRequestError as e:
            print(f"Error con el modelo {modelo}: {str(e)}. Continuando con los demás modelos.")
            continue
        except Exception as e:
            print(f"Error inesperado con el modelo {modelo}: {str(e)}. Continuando con los demás modelos.")
            continue

    if not respuestas_modelos:
        raise ValueError("No se pudo obtener respuestas de ningún modelo de recomendación.")

    # Sintetizar recomendaciones
    respuestas_combinadas = "\n\n".join([f"Modelo {i+1}:\n{resp}" for i, resp in enumerate(respuestas_modelos)])
    modelos_sintesis = [
        "openai/gpt-4o-mini",  # Modelo principal
        "openai/gpt-3.5-turbo",  # Respaldo 1
        "meta-ai/llama-3.1-8b-instruct:free",  # Respaldo 2
        "qwen/qwen3-0.6b-04-28:free"  # Respaldo 3
    ]

    for modelo in modelos_sintesis:
        try:
            llm_sintesis = ChatOpenAI(model_name=modelo, temperature=0.5)
            chain_sintesis = prompt_sintesis | llm_sintesis | StrOutputParser()
            respuesta_final = chain_sintesis.invoke({
                "peticion": peticion,
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
            if linea.strip().startswith(("1. ", "2. ", "3. ", "4. ", "5. ")):
                nombre = linea.split("**")[1].strip()
                genero = ""
                plataformas = ""
                razon = ""
                for sublinea in respuesta_final.split("\n")[respuesta_final.split("\n").index(linea)+1:]:
                    if sublinea.strip().startswith("- Género:"):
                        genero = sublinea.replace("- Género:", "").strip()
                    elif sublinea.strip().startswith("- Plataformas:"):
                        plataformas = sublinea.replace("- Plataformas:", "").strip()
                    elif sublinea.strip().startswith("- ¿Porqué este videojuego?"):
                        razon = sublinea.replace("- ¿Porqué este videojuego?", "").strip()
                    elif sublinea.strip().startswith(("1. ", "2. ", "3. ", "4. ", "5. ")):
                        break
                if razon:
                    imagen = obtener_imagen_juego(nombre)  # Obtener URL de la imagen
                    recomendaciones.append({
                        "nombre": nombre,
                        "genero": genero,
                        "plataformas": plataformas,
                        "razon": razon,
                        "imagen": imagen  # Añadir campo imagen
                    })
        if not recomendaciones:
            raise ValueError("No se encontraron recomendaciones con razones válidas.")
    except Exception as e:
        raise ValueError(f"Error al parsear la respuesta final: {str(e)}")

    return recomendaciones