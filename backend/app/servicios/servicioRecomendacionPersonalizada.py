# archivo: app/servicios/servicioRecomendacionPersonalizada.py
import json
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from openai import BadRequestError
from app.modelos.modeloUsuario import UsuarioOpcionalConHistorial
from app.utils.utilidadesVarias import *

# Prompt para preprocesar la petición
prompt_preprocesamiento = PromptTemplate(
    input_variables=["peticion", "datosUsuario", "historial"],
    template="""
Analiza la siguiente petición del usuario y los datos de su perfil para extraer información relevante que ayude a generar una 
recomendación de videojuegos personalizada:

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
**Tarea**: Generar un JSON válido con los cambios necesarios para actualizar el perfil de un usuario basado en información explícita o implícita en una petición de recomendación de videojuegos, según el estado actual del perfil. Sigue estrictamente las instrucciones y el esquema.

**Estado actual del perfil**:
{estadoActual}

**Petición del usuario**:
"{peticion}"

**Instrucciones**:
- Devuelve EXCLUSIVAMENTE un JSON válido con dos campos:
  - `"mensaje"`: String breve (máx. 100 caracteres) que describe los cambios realizados o explica por qué no se hicieron.
  - `"actualizacion"`: Objeto con solo los campos modificados, conforme al esquema. Si no hay cambios, devuelve {{}}.
- NO incluyas markdown (ej. ```json), comentarios, espacios extra, saltos de línea fuera del JSON, ni texto adicional.
- Ejemplo de salida correcta: {{"mensaje": "Se añadió PS5 a consolas", "actualizacion": {{"consolas": ["PS5"]}}}}.
- Solo genera actualizaciones basadas en información explícita o implícita en la petición que sea relevante para el perfil (ej. consolas adquiridas, juegos gustados/no gustados, suscripciones).
- Ignora frases relacionadas con recomendaciones (ej. "recomiéndame juegos como GTA 5") a menos que indiquen una actualización clara del perfil (ej. "Me compré una PS5, recomiéndame juegos" implica añadir "PS5" a consolas).
- Si la petición es vaga o solo pide recomendaciones sin actualizaciones (ej. "Quiero juegos divertidos"), devuelve: {{"mensaje": "Petición no implica cambios", "actualizacion": {{}}}}.

**Esquema de los campos opcionales**:
- `consolas`: Lista de strings (ej. ["PS5", "XSX"]).
- `configuracionPc`: Objeto con claves `so`, `procesador`, `memoria`, `tarjetaGrafica` (ej. {{"so": "Windows 11", "procesador": "i7-12700H", "memoria": "16GB", "tarjetaGrafica": "RTX 3080"}}).
- `necesidadesEspeciales`: Lista de strings (ej. ["Dificultad en la visión"]).
- `juegosGustados`, `juegosNoGustados`, `juegosJugados`: Listas de strings (ej. ["GTA 5", "Zelda BOTW"]).
- `suscripciones`: Lista de strings (ej. ["Xbox Game Pass", "PS Plus"]).
- `idiomas`: Lista de strings (ej. ["Inglés", "Español"]).
- `juegosPoseidos`: Lista de objetos con `nombre` (string) y `consolasDisponibles` (lista de strings, ej. [{{"nombre": "Pokémon Oro", "consolasDisponibles": ["Game Boy"]}}]).

**Reglas**:
1. **Modificaciones**:
   - Preserva datos existentes: Si modificas un campo (ej. `consolas`), incluye elementos previos no afectados (ej. ["PS4", "XSX"] con nueva PS5 → ["PS4", "XSX", "PS5"], no ["PS5"]).
   - **Conflictos de gustos**:
     - Si un juego gusta y está en `juegosNoGustados`, elimina SOLO ese juego de `juegosNoGustados`, añádelo a `juegosGustados`, y preserva los demás juegos en `juegosNoGustados`.
     - Si no gusta y está en `juegosGustados`, elimina SOLO ese juego de `juegosGustados`, añádelo a `juegosNoGustados`, y preserva los demás juegos en `juegosGustados`.
     - Ejemplo: If `juegosNoGustados` is ["GTA 5", "FIFA 23"] and the user says "Me gusta GTA 5", remove only "GTA 5", leaving ["FIFA 23"].
   - Añade juegos mencionados como gustados/no gustados a `juegosJugados` si no están.
   - Si el usuario indica que ya no tiene algo (ej. "Vendí mi PS4"), establece el campo como lista vacía ([]) si corresponde, no `null`.

2. **Campos específicos**:
   - **Idiomas**:
     - Estandariza: "inglés" → "Inglés", "español" o "castellano" → "Español".
     - Idiomas comunes: "Inglés", "Español", "Francés", "Alemán", "Italiano", "Portugués", "Japonés", "Chino", "Ruso".
     - Añade idiomas mencionados a `idiomas`, respetando los existentes (ej. "Hablo inglés" → ["Inglés"]).
     - Elimina idiomas si el usuario lo indica (ej. "Ya no hablo francés" → elimina "Francés").
   - **Suscripciones**:
     - Nombres estándar: "Xbox Game Pass", "PS Plus", "Nintendo Switch Online", "EA Play", "Steam", "Epic Games Store".
     - Corrige: "gamepass" → "Xbox Game Pass", "playstation plus" → "PS Plus".
     - Añade suscripciones mencionadas, respetando existentes (ej. "Suscrito a PS Plus" → ["PS Plus"]).
     - Elimina si el usuario lo indica (ej. "Cancelé PS Plus" → elimina "PS Plus").
   - **Juegos poseídos**:
     - Para cada juego mencionado (ej. "Tengo Pokémon Oro"), crea un objeto con `nombre` y `consolasDisponibles`.
     - `consolasDisponibles`: Usa SOLO consolas mencionadas explícitamente (ej. "Pokémon Oro en Game Boy" → ["Game Boy"]).
     - Si no se especifica consola, usa [] and explica en `mensaje` (ej. "Añadido Pokémon Oro, consola no especificada").
     - **No asumas consolas** bajo ninguna circunstancia.
     - Corrige nombres: "Pokemon Oro" → "Pokémon Oro", "Sonic 1" → "Sonic the Hedgehog".
     - Elimina juegos si el usuario lo indica (ej. "Vendí Pokémon Oro").
   - **Configuración de PC**:
     - Actualiza solo las claves mencionadas (ej. "Tengo un PC con i7" → {{"procesador": "i7"}}).
     - Si se menciona un modelo específico (ej. "i7-12700H"), úsalo; si es genérico (ej. "i7"), explica en `mensaje` que falta detalle.

3. **Abreviaturas y correcciones**:
   - Consolas: "PlayStation 4" → "PS4", "PlayStation 5" → "PS5", "Nintendo Switch" → "Switch", "Xbox Series X" → "XSX", "Xbox One" → "XONE", "Game Boy" → "Game Boy".
   - Juegos: "Grand Theft Auto 5" → "GTA 5", "The Legend of Zelda: Breath of the Wild" → "Zelda BOTW", "Pokemon Oro" → "Pokémon Oro", "Sonic 1" → "Sonic the Hedgehog".
   - Hardware: "Intel Core i7-12700H" → "i7-12700H", "NVIDIA GeForce RTX 3080" → "RTX 3080", "16 GB RAM" → "16GB".
   - Corrige errores: "Play Staton 4" → "PS4", "Pokemón" → "Pokémon".
   - Usa nombre completo si no hay abreviatura estándar: "PlayStation 4 Pro" → "PS4 Pro".
   - Conserva detalles en hardware: "i7-12700H", no "i7".
   - Usa mayúsculas para abreviaturas: "PS4", no "ps4".

4. **Casos extremos**:
   - Petición vaga (ej. "Recomiéndame juegos divertidos"): {{"mensaje": "Petición no implica cambios", "actualizacion": {{}}}}.
   - Petición contradictoria (ej. "Me gusta y no me gusta GTA 5"): Prioriza el último sentimiento y explica en `mensaje` (ej. "Se procesó el último sentimiento sobre GTA 5").
   - Nombres desconocidos: Usa el nombre corregido, sin duplicados.
   - Evita duplicados en listas (ej. no añadir "PS4" si ya está en `consolas`).

**Ejemplos**:
- Petición: "Me compré una PS5, recomiéndame juegos para ella"
  - Estado: {{"consolas": ["PS4"]}}
  - Respuesta: {{"mensaje": "Añadida PS5 a consolas", "actualizacion": {{"consolas": ["PS4", "PS5"]}}}}
- Petición: "Recomiéndame juegos como GTA 5"
  - Estado: {{}}
  - Respuesta: {{"mensaje": "Petición no implica cambios", "actualizacion": {{}}}}
- Petición: "No me gustó The Last of Us en mi PS4"
  - Estado: {{"consolas": [], "juegosNoGustados": [], "juegosJugados": []}}
  - Respuesta: {{"mensaje": "Añadidos PS4 y The Last of Us a no gustados", "actualizacion": {{"consolas": ["PS4"], "juegosNoGustados": ["The Last of Us"], "juegosJugados": ["The Last of Us"]}}}}
- Petición: "Ahora me gusta GTA 5, recomiéndame juegos similares"
  - Estado: {{"juegosGustados": [], "juegosNoGustados": ["GTA 5", "FIFA 23"], "juegosJugados": []}}
  - Respuesta: {{"mensaje": "GTA 5 movido a juegosGustados", "actualizacion": {{"juegosGustados": ["GTA 5"], "juegosNoGustados": ["FIFA 23"], "juegosJugados": ["GTA 5"]}}}}
- Petición: "Tengo una suscripción a PS Plus"
  - Estado: {{"suscripciones": ["Xbox Game Pass"]}}
  - Respuesta: {{"mensaje": "Añadida PS Plus a suscripciones", "actualizacion": {{"suscripciones": ["Xbox Game Pass", "PS Plus"]}}}}
- Petición: "Quiero juegos para mi PC con procesador i7-12700H y RTX 3080"
  - Estado: {{"configuracionPc": {{}}}}
  - Respuesta: {{"mensaje": "Actualizada configuración de PC", "actualizacion": {{"configuracionPc": {{"procesador": "i7-12700H", "tarjetaGrafica": "RTX 3080"}}}}}}
- Petición: "Tengo Pokémon Oro en Game Boy"
  - Estado: {{"juegosPoseidos": [], "consolas": []}}
  - Respuesta: {{"mensaje": "Añadido Pokémon Oro en Game Boy", "actualizacion": {{"juegosPoseidos": [{{"nombre": "Pokémon Oro", "consolasDisponibles": ["Game Boy"]}}], "consolas": ["Game Boy"]}}}}
- Petición: "Cancelé mi suscripción a PS Plus"
  - Estado: {{"suscripciones": ["PS Plus", "Xbox Game Pass"]}}
  - Respuesta: {{"mensaje": "Eliminada PS Plus", "actualizacion": {{"suscripciones": ["Xbox Game Pass"]}}}}
- Petición: "Ya no hablo francés"
  - Estado: {{"idiomas": ["Inglés", "Francés"]}}
  - Respuesta: {{"mensaje": "Eliminado Francés", "actualizacion": {{"idiomas": ["Inglés"]}}}}

**Advertencias estrictas**:
- Devuelve SOLO JSON válido, sin markdown (ej. ```json), comentarios, espacios extra, ni texto adicional.
- Cumple estrictamente el esquema; no añadas campos no especificados.
- Evita duplicados en listas (ej. no añadir "PS4" si ya está en `consolas`).
- No inventes datos (ej. no asumas consolas para juegos si no se mencionan explícitamente).

**Salida**: SOLO JSON válido, nada más.
"""
)

# Prompt para generar recomendaciones iniciales
prompt_recomendacion = PromptTemplate(
    input_variables=["peticion", "datosProcesados"],
    template="""
Actúa como un experto en videojuegos. Genera recomendaciones de videojuegos basadas en la siguiente petición y datos 
procesados del usuario:

Petición: "{peticion}"

Datos procesados:
{datosProcesados}

Instrucciones:
- Recomienda 3-5 videojuegos que cumplan con los géneros, plataformas, idiomas, suscripciones, necesidades especiales, y 
requisitos de PC especificados, (si es posible) y coherentes con la descripción del usuario.
- Si el usuario especificó un número exacto de juegos (por ejemplo, "quiero 10 juegos" o "recomiendame un juego(en este caso sería 
solo uno)" o recomienda un par(en este caso serían 2)), selecciona EXACTAMENTE ese número de recomendaciones, eligiendo las más 
relevantes y coherentes con la descripción del usuario.Si no se especificó un número, selecciona las recomendaciones que consideres 
adecuadas.
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
Eres un experto en videojuegos. Tu tarea es sintetizar y validar recomendaciones de videojuegos provenientes de múltiples 
modelos para generar una lista final coherente y personalizada.

Petición del usuario: "{peticion}"

Datos procesados del usuario:
{datosProcesados}

Recomendaciones de modelos:
{respuestasModelos}

Instrucciones:
- Combina las recomendaciones, eliminando duplicados y juegos en "excluirJuegos".
- Selecciona las recomendaciones más relevantes y coherentes con la petición, géneros, plataformas, idiomas, 
suscripciones, necesidades especiales, y requisitos de PC.
- Asegúrate de que las recomendaciones sean variadas en género y plataformas cuando sea posible.
- Usa abreviaturas estándar (ej. "PS4", "GTA 5", "i7-12700H").
- Cada recomendación DEBE incluir una razón clara y específica en "¿Porqué este videojuego?".
- Presenta las recomendaciones en el siguiente formato:
- Si el usuario especificó un número exacto de juegos (por ejemplo, "quiero 10 juegos" o "recomiendame un juego(en este caso sería 
solo uno)" o recomienda un par(en este caso serían 2)), selecciona EXACTAMENTE ese número de recomendaciones, eligiendo las más 
relevantes y coherentes con la descripción del usuario.Si no se especificó un número, selecciona las recomendaciones que consideres 
adecuadas.


1. **Nombre del juego**
   - Género:
   - Plataformas:
   - ¿Porqué este videojuego? [Razón clara y específica]

Devuelve solo la lista final de recomendaciones.
"""
)



def generarCambiosDesdePeticionRecomendacion(estado_actual: dict, peticion: str) -> tuple[str, dict]:

    # Intentar con cada modelo hasta obtener una respuesta válida
    for modelo in modelos:
        try:
            llm = ChatOpenAI(model_name=modelo, temperature=0.4)
            chain = prompt_cambios | llm | StrOutputParser()
            respuesta = chain.invoke({"estadoActual": json.dumps(estado_actual, default=str), "peticion": peticion})
            # Limpiar respuesta
            respuesta_limpia = limpiar_respuesta(respuesta)
            if not respuesta_limpia:
                continue  # Pasa al siguiente modelo si no se obtuvo JSON válido
            # Parsear la respuesta
            try:
                respuesta_json = json.loads(respuesta_limpia)
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

    respuestas_modelos = []
    for modelo in modelos:
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

    for modelo in modelos:
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
                    recomendaciones.append({
                        "nombre": nombre,
                        "genero": genero,
                        "plataformas": plataformas,
                        "razon": razon,
                        "imagen": imagen
                    })
                i = j
            else:
                i += 1
        if not recomendaciones:
            raise ValueError("No se encontraron recomendaciones con razones válidas.")
    except Exception as e:
        raise ValueError(f"Error al parsear la respuesta final: {str(e)}")

    return recomendaciones