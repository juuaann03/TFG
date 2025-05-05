import os
import json
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from pathlib import Path
from openai import BadRequestError

# Cargar variables del .env
dotenv_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Prompt para los modelos de recomendación individuales
prompt_recomendacion = PromptTemplate(
    input_variables=["descripcionUsuario"],
    template="""
Actúa como un experto en videojuegos. Un usuario ha solicitado recomendaciones con la siguiente descripción:

"{descripcionUsuario}"

Recomienda algunos videojuegos que se adapten a lo que pide. Ten en cuenta si ha mencionado:
- Plataformas específicas
- Requisitos técnicos del PC
- Géneros preferidos
- Juegos similares
- Otras necesidades particulares

Responde en español, de forma clara, concisa y amigable. Presenta las recomendaciones en formato de lista con esta estructura:

1. **Nombre del juego**
   - Género:
   - Plataformas:
   - ¿Porqué este videojuego? Breve razón por la que se adapta a lo que busca el usuario

No expliques tu razonamiento, solo da la respuesta final con los juegos recomendados.
"""
)

# Prompt para el modelo que sintetiza las respuestas
prompt_sintesis = PromptTemplate(
    input_variables=["descripcionUsuario", "respuestasModelos"],
    template="""
Eres un experto en videojuegos y tu tarea es sintetizar recomendaciones de videojuegos provenientes de múltiples fuentes para generar una lista final coherente y optimizada. 

El usuario proporcionó la siguiente descripción:

"{descripcionUsuario}"

Recibiste las siguientes recomendaciones de modelos:

{respuestasModelos}

Tu tarea es:
1. Combinar las recomendaciones, eliminando duplicados.
2. Seleccionar las 3-5 recomendaciones más relevantes (si es posible) y coherentes con la descripción del usuario. Si el usuario pidió un número específico de juegos (por ejemplo, "quiero un juego"), selecciona solo ese número, eligiendo el más adecuado.
3. Asegurarte de que las recomendaciones sean variadas en género y plataformas cuando sea posible.
4. Cada recomendación DEBE incluir una razón clara y específica en el campo "¿Porqué este videojuego?". Este campo es OBLIGATORIO y no puede estar vacío bajo ninguna circunstancia.

Presenta las recomendaciones en el siguiente formato:

1. **Nombre del juego**
   - Género:
   - Plataformas:
   - ¿Porqué este videojuego? [Razón clara y específica, obligatoria]

Responde solo con la lista final de recomendaciones, sin explicaciones adicionales. Si no puedes proporcionar una razón válida para una recomendación, no la incluyas.
"""
)

def generarRecomendacionesBasicas(descripcionUsuario: str) -> List[Dict]:
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY no está definido en el .env")

    os.environ["OPENAI_API_KEY"] = openrouter_api_key
    os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"

    # Definir los modelos para recomendaciones iniciales
    modelos_recomendacion = [
        "meta-llama/llama-guard-4-12b",  # Modelo gratuito disponible
        "qwen/qwen3-0.6b-04-28:free",  # Modelo corregido
        "openai/gpt-3.5-turbo"  # Modelo de respaldo
    ]

    # Crear cadenas para cada modelo de recomendación
    respuestas_modelos = []
    for modelo in modelos_recomendacion:
        try:
            llm = ChatOpenAI(model_name=modelo, temperature=0.7)
            chain = prompt_recomendacion | llm | StrOutputParser()
            respuesta = chain.invoke({"descripcionUsuario": descripcionUsuario})
            respuestas_modelos.append(respuesta)
        except BadRequestError as e:
            print(f"Error con el modelo {modelo}: {str(e)}. Continuando con los demás modelos.")
            continue
        except Exception as e:
            print(f"Error inesperado con el modelo {modelo}: {str(e)}. Continuando con los demás modelos.")
            continue

    # Si no se obtuvo ninguna respuesta, lanzar error
    if not respuestas_modelos:
        raise ValueError("No se pudo obtener respuestas de ningún modelo de recomendación.")

    # Combinar respuestas para el modelo de síntesis
    respuestas_combinadas = "\n\n".join([f"Modelo {i+1}:\n{resp}" for i, resp in enumerate(respuestas_modelos)])

    # Definir los modelos para síntesis
    modelos_sintesis = [
        "openai/gpt-4o-mini",  # Modelo principal
        "openai/gpt-3.5-turbo",  # Respaldo 1
        "qwen/qwen3-0.6b-04-28:free"  # Respaldo 2
    ]

    # Intentar con cada modelo de síntesis hasta obtener una respuesta válida
    respuesta_final = None
    for modelo in modelos_sintesis:
        try:
            llm_sintesis = ChatOpenAI(model_name=modelo, temperature=0.5)
            chain_sintesis = prompt_sintesis | llm_sintesis | StrOutputParser()
            respuesta_final = chain_sintesis.invoke({
                "descripcionUsuario": descripcionUsuario,
                "respuestasModelos": respuestas_combinadas
            })
            break  # Salir del bucle si la síntesis es exitosa
        except BadRequestError as e:
            print(f"Error con el modelo de síntesis {modelo}: {str(e)}. Intentando con el siguiente modelo.")
            continue
        except Exception as e:
            print(f"Error inesperado con el modelo de síntesis {modelo}: {str(e)}. Intentando con el siguiente modelo.")
            continue

    # Si no se obtuvo respuesta final, lanzar error
    if respuesta_final is None:
        raise ValueError("No se pudo obtener una respuesta válida de ningún modelo de síntesis.")

    # Convertir la respuesta final a una lista de diccionarios
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
                # Solo añadir la recomendación si tiene una razón válida
                if razon:
                    recomendaciones.append({
                        "nombre": nombre,
                        "genero": genero,
                        "plataformas": plataformas,
                        "razon": razon
                    })
        if not recomendaciones:
            raise ValueError("No se encontraron recomendaciones con razones válidas.")
        return recomendaciones
    except Exception as e:
        raise ValueError(f"Error al parsear la respuesta final: {str(e)}")