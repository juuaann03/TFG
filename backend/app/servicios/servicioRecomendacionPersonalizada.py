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
- "cambiosSugeridos": Objeto con cambios sugeridos en los datos opcionales del usuario basados en la petición (ej. {{"consolas": ["PS4"], "juegosNoGustados": ["The Last of Us"]}}).
- "contexto": Breve descripción del análisis para usar en el historial de conversaciones (ej. "Recomendación de aventuras para PS4, excluyendo God of War").

Usa abreviaturas estándar:
- Consolas: "PlayStation 4" → "PS4", "PlayStation 5" → "PS5", "Nintendo Switch" → "Switch", "Xbox Series X" → "XSX".
- Juegos: "Grand Theft Auto 5" → "GTA 5", "The Legend of Zelda: Breath of the Wild" → "Zelda BOTW".
- Hardware: "Intel Core i7-12700H" → "i7-12700H", "NVIDIA GeForce RTX 3080" → "RTX 3080".
- Corrige errores tipográficos (ej. "Play Staton 4" → "PS4").
- Las abreviaturas deben estar en mayúsculas.

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

def generarRecomendacionPersonalizada(peticion: str, datos_usuario: dict) -> Tuple[List[Dict], dict, str]:
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

    # Extraer cambios sugeridos y contexto
    cambios_sugeridos = datos_procesados.get("cambiosSugeridos", {})
    contexto = datos_procesados.get("contexto", "Recomendación personalizada basada en la petición y datos del usuario.")

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
    try:
        llm_sintesis = ChatOpenAI(model_name="openai/gpt-4o-mini", temperature=0.5)
        chain_sintesis = prompt_sintesis | llm_sintesis | StrOutputParser()
        respuesta_final = chain_sintesis.invoke({
            "peticion": peticion,
            "datosProcesados": json.dumps(datos_procesados, default=str),
            "respuestasModelos": respuestas_combinadas
        })
    except Exception as e:
        raise ValueError(f"Error al sintetizar recomendaciones: {str(e)}")

    # Parsear la respuesta final
    try:
        recomendaciones = []
        for linea in respuesta_final.split("\n"):
            if linea.strip().startswith(("1. ", "2. ", "3. ")):
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
                    elif sublinea.strip().startswith(("1. ", "2. ", "3. ")):
                        break
                if razon:
                    recomendaciones.append({
                        "nombre": nombre,
                        "genero": genero,
                        "plataformas": plataformas,
                        "razon": razon
                    })
        if not recomendaciones:
            raise ValueError("No se encontraron recomendaciones con razones válidas.")
    except Exception as e:
        raise ValueError(f"Error al parsear la respuesta final: {str(e)}")

    return recomendaciones, cambios_sugeridos, contexto