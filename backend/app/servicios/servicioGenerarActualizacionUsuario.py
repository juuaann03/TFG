# archivo: app/servicios/servicioGenerarActualizacionUsuario.py

import os
import json
from dotenv import load_dotenv
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from openai import BadRequestError
from pydantic import ValidationError
from app.modelos.modeloUsuario import UsuarioOpcionalSinHistorial
from app.utils.utilidadesVarias import *


# Prompt para generar actualizaciones
prompt = PromptTemplate(
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
   - **Preserva datos existentes**: Si modificas un campo (ej. `consolas`, `juegosGustados`), incluye TODOS los elementos previos no afectados. Ejemplo: Si `consolas` es ["PS4", "XSX"] y se añade "PS5", el resultado es ["PS4", "XSX", "PS5"], NO ["PS5"].
   - **Conflictos de gustos**:
     - Si un juego gusta y está en `juegosNoGustados`, elimina SOLO ese juego de `juegosNoGustados`, añádelo a `juegosGustados`, y **preserva todos los demás juegos** en `juegosNoGustados`.
     - Si un juego no gusta y está en `juegosGustados`, elimina SOLO ese juego de `juegosGustados`, añádelo a `juegosNoGustados`, y **preserva todos los demás juegos** en `juegosGustados`.
     - Ejemplo: Si `juegosNoGustados` es ["GTA 5", "FIFA 23"] y el usuario dice "Me gusta GTA 5", elimina solo "GTA 5", dejando `juegosNoGustados` como ["FIFA 23"].
     - Ejemplo: Si `juegosGustados` es ["GTA 5", "Zelda BOTW"] y el usuario dice "Ya no me gusta GTA 5", elimina solo "GTA 5", dejando `juegosGustados` como ["Zelda BOTW"].
   - Añade juegos mencionados como gustados/no gustados a `juegosJugados` si no están.
   - Si el usuario indica que ya no tiene algo (ej. "Vendí mi PS4"), establece el campo como lista vacía ([]) si corresponde, no `null`.
   - **IMPORTANTE**: Nunca elimines elementos de una lista (ej. `juegosGustados`, `consolas`) a menos que el usuario lo indique explícitamente para ese elemento específico.

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
     - Si no se especifica consola, usa [] y explica en `mensaje` (ej. "Añadido Pokémon Oro, consola no especificada").
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
- Petición: "Ya no me gusta GTA 5, recomiéndame juegos distintos"
  - Estado: {{"juegosGustados": ["GTA 5", "Zelda BOTW"], "juegosNoGustados": [], "juegosJugados": []}}
  - Respuesta: {{"mensaje": "GTA 5 movido a juegosNoGustados", "actualizacion": {{"juegosGustados": ["Zelda BOTW"], "juegosNoGustados": ["GTA 5"], "juegosJugados": ["GTA 5"]}}}}
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
- **Preserva TODOS los elementos no afectados** en listas como `juegosGustados`, `juegosNoGustados`, `consolas`, etc., a menos que el usuario indique explícitamente eliminarlos.

**Salida**: SOLO JSON válido, nada más.
"""
)


#Valida que la actualización cumpla con el esquema.
def validar_actualizacion(actualizacion: dict) -> bool:

    try:
        UsuarioOpcionalSinHistorial(**actualizacion)
        return True
    except ValidationError:
        return False

#Genera una actualización del perfil basada en la petición del usuario.
def generarActualizacionDesdePeticion(estado_actual: dict, peticion: str) -> tuple[str, dict]:
    
    for modelo in modelos:
        try:
            llm = ChatOpenAI(model_name=modelo, temperature=0.2)
            chain = prompt | llm | StrOutputParser()
            respuesta = chain.invoke({"estadoActual": estado_actual, "peticion": peticion})

            # Limpiar respuesta
            respuesta_limpia = limpiar_respuesta(respuesta)
            if not respuesta_limpia:
                continue  # Pasa al siguiente modelo si no se obtuvo JSON válido

            # Parsear respuesta
            try:
                respuesta_json = json.loads(respuesta_limpia)
                mensaje = respuesta_json.get("mensaje", "No se proporcionó un mensaje")
                actualizacion = respuesta_json.get("actualizacion", {})

                # Validar esquema
                if not validar_actualizacion(actualizacion):
                    continue  # Pasa al siguiente modelo si la validación falla

                return mensaje, actualizacion

            except json.JSONDecodeError:
                continue  # Pasa al siguiente modelo si el JSON es inválido

        except BadRequestError:
            continue  # Pasa al siguiente modelo si hay un error de API
        except Exception:
            continue  # Pasa al siguiente modelo si hay un error inesperado

    raise ValueError("No se pudo obtener una respuesta válida de ningún modelo")