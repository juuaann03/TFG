# archivo: app/servicios/servicioRecomendacionBasica.py

import os
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables del .env
dotenv_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=dotenv_path)

prompt = PromptTemplate(
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



def generarRecomendacionesBasicas(descripcionUsuario: str) -> str:
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

    if not openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY no está definido en el .env")

    os.environ["OPENAI_API_KEY"] = openrouter_api_key
    os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"

    llm = ChatOpenAI(
        temperature=0.7,
        model_name="qwen/qwen3-1.7b:free",
    )

    chain = prompt | llm
    respuesta = chain.invoke({"descripcionUsuario": descripcionUsuario})
    return respuesta.content if hasattr(respuesta, "content") else str(respuesta)
