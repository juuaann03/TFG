# archivo: app/servicios/servicioGenerarActualizacionUsuario.py

import os
import json
from dotenv import load_dotenv
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

prompt = PromptTemplate(
    input_variables=["estadoActual", "peticion"],
    template="""
Tienes este estado actual del perfil del usuario. Solo se incluyen campos opcionales del esquema completo:

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
- historialConversaciones: lista de objetos con pregunta, respuesta, fecha, contexto

Instrucciones:
- No devuelvas texto adicional, solo el JSON.
- Si no hay cambios necesarios, devuelve un objeto con "mensaje" indicando que no se hicieron cambios y "actualizacion" como {{}}.
- Ejemplos:
  - Petición: "he vendido la PS4"
    Respuesta: {{"mensaje": "Se eliminó la PS4 de consolas", "actualizacion": {{"consolas": ["Xbox"]}}}}
  - Petición: "me compré la Xbox"
    Respuesta: {{"mensaje": "Se añadió la Xbox a consolas", "actualizacion": {{"consolas": ["PS4", "Xbox"]}}}}
  - Petición: "ya no me gusta el Fortnite"
    Respuesta: {{"mensaje": "Se eliminó Fortnite de juegosGustados", "actualizacion": {{"juegosGustados": []}}}}
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

    llm = ChatOpenAI(model_name="openai/gpt-3.5-turbo", temperature=0.4)

    chain = prompt | llm
    respuesta = chain.invoke({"estadoActual": estado_actual, "peticion": peticion})

    try:
        respuesta_json = json.loads(respuesta.content)
        mensaje = respuesta_json.get("mensaje", "No se proporcionó un mensaje")
        actualizacion = respuesta_json.get("actualizacion", {})
        return mensaje, actualizacion
    except json.JSONDecodeError:
        raise ValueError("La respuesta de la IA no es un JSON válido")