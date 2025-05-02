# archivo: app/servicios/servicioRecomendacionBasica.py

from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os

# Cargar variables del archivo .env
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Configurar el modelo
modelo = ChatOpenAI(temperature=0.7, openai_api_key=openai_api_key)

# Prompt
prompt = PromptTemplate(
    input_variables=["descripcionUsuario"],
    template="""
Eres un experto en videojuegos. Con base en la siguiente descripción del usuario:

"{descripcionUsuario}"

Recomienda 3 videojuegos actuales que se adapten bien, indicando su género y plataforma. Sé claro y conciso.
"""
)

recomendacionBasicaChain = LLMChain(llm=modelo, prompt=prompt)

def generarRecomendacionesBasicas(descripcionUsuario: str) -> str:
    return recomendacionBasicaChain.run({"descripcionUsuario": descripcionUsuario})
