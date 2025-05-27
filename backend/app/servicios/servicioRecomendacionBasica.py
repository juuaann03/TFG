# archivo: app/servicios/servicioRecomendacionBasica.py

from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from pathlib import Path
from openai import BadRequestError
import re
from app.utils.utilidadesVarias import *

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

Responde en español por defecto, o en el idioma que te haya hablado o pedido, de forma clara, concisa y amigable. 
Presenta las recomendaciones en formato de lista con esta estructura:

Si el usuario especificó un número exacto de juegos (por ejemplo, "quiero 10 juegos" o "recomiendame un juego(en este caso sería 
solo uno)" o recomienda un par(en este caso serían 2)), selecciona EXACTAMENTE ese número de recomendaciones, eligiendo las más 
relevantes y coherentes con la descripción del usuario.Si no se especificó un número, selecciona las recomendaciones que consideres 
adecuadas.

Debes de poner todas las plataformas en las que está ese videojuego, no solo la que te pidió el usuario.

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
Eres un experto en videojuegos y tu tarea es sintetizar recomendaciones de videojuegos provenientes de múltiples fuentes para 
generar una lista final coherente y optimizada.

El usuario proporcionó la siguiente descripción:

"{descripcionUsuario}"

Recibiste las siguientes recomendaciones de modelos:

{respuestasModelos}

Tu tarea es:
1. Combinar las recomendaciones, eliminando duplicados.
2. Si el usuario especificó un número exacto de juegos (por ejemplo, "quiero 10 juegos" o "dame un juego(en este caso sería solo uno)" 
o dame un par(en este caso serían 2)), selecciona EXACTAMENTE ese número de recomendaciones, eligiendo las más relevantes 
y coherentes con la descripción del usuario.Si no se especificó un número, selecciona las recomendaciones que consideres adecuadas.
3. Asegurarte de que las recomendaciones sean variadas en género y plataformas cuando sea posible.
4. Cada recomendación DEBE incluir una razón clara y específica en el campo "¿Porqué este videojuego?". 
Este campo es OBLIGATORIO y no puede estar vacío bajo ninguna circunstancia.
5.Debes de poner todas las plataformas en las que está ese videojuego, no solo la que te pidió el usuario.

Presenta las recomendaciones en el siguiente formato:

1. **Nombre del juego**
   - Género:
   - Plataformas:
   - ¿Porqué este videojuego? [Razón clara y específica, obligatoria]

Responde solo con la lista final de recomendaciones, sin explicaciones adicionales. Si no puedes proporcionar una razón 
válida para una recomendación, no la incluyas.
"""
)


def generarRecomendacionesBasicas(descripcionUsuario: str) -> List[Dict]:
    # Crear cadenas para cada modelo de recomendación
    respuestas_modelos = []
    for modelo in modelos:
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

    # Intentar con cada modelo de síntesis hasta obtener una respuesta válida
    respuesta_final = None
    for modelo in modelos:
        try:
            llm_sintesis = ChatOpenAI(model_name=modelo, temperature=0.5)
            chain_sintesis = prompt_sintesis | llm_sintesis | StrOutputParser()
            respuesta_final = chain_sintesis.invoke({
                "descripcionUsuario": descripcionUsuario,
                "respuestasModelos": respuestas_combinadas
            })
            break
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
        lines = respuesta_final.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # Verificar si la línea comienza con un número seguido de un punto (por ejemplo, "1. ", "2. ", etc.)
            if line and line[0].isdigit() and line[1:3] == ". ":
                nombre = line.split("**")[1].strip() if "**" in line else line[3:].strip()
                genero = ""
                plataformas = ""
                razon = ""
                # Procesar las líneas siguientes hasta encontrar otra recomendación o el final
                j = i + 1
                while j < len(lines) and not (lines[j].strip() and lines[j].strip()[0].isdigit() and lines[j].strip()[1:3] == ". "):
                    sublinea = lines[j].strip()
                    if sublinea.startswith("- Género:"):
                        genero = sublinea.replace("- Género:", "").strip()
                    elif sublinea.startswith("- Plataformas:"):
                        plataformas = sublinea.replace("- Plataformas:", "").strip()
                    elif sublinea.startswith("- ¿Porqué este videojuego?"):
                        razon = sublinea.replace("- ¿Porqué este videojuego?", "").strip()
                    j += 1
                # Solo añadir la recomendación si tiene una razón válida
                if razon:
                    imagen = obtener_imagen_juego(nombre)  # Obtener URL de la imagen
                    # Pasar el campo plataformas para ordenar tiendas
                    tiendas = obtener_tiendas_juego(nombre, plataformas)
                    recomendaciones.append({
                        "nombre": nombre,
                        "genero": genero,
                        "plataformas": plataformas,
                        "razon": razon,
                        "imagen": imagen,
                        "tiendas": tiendas
                    })
                i = j
            else:
                i += 1

        if not recomendaciones:
            raise ValueError("No se encontraron recomendaciones con razones válidas.")

        return recomendaciones
    except Exception as e:
        raise ValueError(f"Error al parsear la respuesta final: {str(e)}")