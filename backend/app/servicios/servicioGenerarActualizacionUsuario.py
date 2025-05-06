# archivo: app/servicios/servicioGenerarActualizacionUsuario.py


import os
import json
from dotenv import load_dotenv
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from openai import BadRequestError

# Cargar variables del .env
dotenv_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Prompt para generar actualizaciones
prompt = PromptTemplate(
    input_variables=["estadoActual", "peticion"],
    template="""
Tienes este estado actual del perfil del usuario. Solo se incluyen campos opcionales del esquema completo (sin historial de conversaciones):

{estadoActual}

El usuario ha escrito esta petición:

"{peticion}"

Tu tarea es devolver un JSON **válido** con dos campos:
- "mensaje": una cadena que describe los cambios realizados o indica si no se hicieron cambios.
- "actualizacion": un JSON mínimo y conforme al siguiente esquema parcial, con solo los cambios necesarios para reflejar la petición.

Este es el formato correcto para los campos opcionales:

- consolas: lista de strings
- configuracionPc: objeto con claves so, procesador, memoria, tarjetaGrafica
- necesidadesEspeciales: lista de strings
- juegosGustados / juegosNoGustados / juegosJugados / suscripciones / idiomas: listas de strings
- juegosPoseidos: lista de objetos con nombre y consolasDisponibles (lista de strings)

Instrucciones:
- No devuelvas texto adicional, solo el JSON.
- Si no hay cambios necesarios, devuelve un objeto con "mensaje" indicando que no se hicieron cambios y "actualizacion" como {{}}.
- Usa abreviaturas estándar para consolas, juegos y hardware cuando sea posible. Ejemplos:
  - Consolas: "PlayStation 4" o "Play Station 4" → "PS4", "PlayStation 5" → "PS5", "Nintendo Switch" → "Switch", "Xbox Series X" → "XSX".
  - Juegos: "Grand Theft Auto 5" o "Grand Theft Auto Cinco" → "GTA 5", "The Legend of Zelda: Breath of the Wild" → "Zelda BOTW".
  - Hardware: "Intel Core i7-12700H" → "i7-12700H", "NVIDIA GeForce RTX 3080" → "RTX 3080".
- Corrige errores tipográficos obvios en los nombres (ej. "Play Staton 4" → "PS4").
- Si no conoces una abreviatura estándar, usa el nombre completo corregido.
- Las abreviaturas deben estar en mayúsculas (ej. "PS4", no "ps4").
- Para hardware, conserva detalles importantes como la generación del procesador (ej. "i7-12700H", no solo "i7").
- Ejemplos:
  - Petición: "he vendido la Play Station 4"
    Respuesta: {{"mensaje": "Se eliminó la PS4 de consolas", "actualizacion": {{"consolas": ["XSX"]}}}}
  - Petición: "me compré la Xbox Series X"
    Respuesta: {{"mensaje": "Se añadió la XSX a consolas", "actualizacion": {{"consolas": ["PS4", "XSX"]}}}}
  - Petición: "ya no me gusta el Grand Theft Auto Cinco"
    Respuesta: {{"mensaje": "Se eliminó GTA 5 de juegosGustados", "actualizacion": {{"juegosGustados": []}}}}
  - Petición: "no tengo ninguna consola"
    Respuesta: {{"mensaje": "No se realizaron cambios", "actualizacion": {{}}}}

Devuelve solo el JSON.
"""
)

def generarActualizacionDesdePeticion(estado_actual: dict, peticion: str) -> tuple[str, dict]:
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
            chain = prompt | llm | StrOutputParser()
            respuesta = chain.invoke({"estadoActual": estado_actual, "peticion": peticion})

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
            print(f"Error con el modelo {modelo}: {str(e)}. Intentando con el siguiente modelo.");
            continue
        except Exception as e:
            print(f"Error inesperado con el modelo {modelo}: {str(e)}. Intentando con el siguiente modelo.")
            continue

    # Si ningún modelo funciona, lanzar error
    raise ValueError("No se pudo obtener una respuesta válida de ningún modelo")