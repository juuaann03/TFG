#!/bin/bash

# Evitar la creación de __pycache__ y redirigir los archivos de caché
export PYTHONPYCACHEPREFIX="./.pycache"

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
  echo "Creando entorno virtual..."
  python3 -m venv venv                # Crea un entorno virtual aislado llamado 'venv'
  source venv/bin/activate            # Activa el entorno virtual

  echo "Instalando dependencias..."
  pip install --upgrade pip           # Actualiza pip dentro del entorno

  # Instala las dependencias necesarias para el backend
  pip install fastapi
  pip install uvicorn
  pip install pymongo
  pip install pydantic
  pip install openai
  pip install langchain
  pip install langchain-community
  pip install python-dotenv

else
  # Activar entorno virtual si ya existe
  source ./venv/bin/activate
fi

# Lanzar el servidor FastAPI con recarga automática
echo "Iniciando backend con Uvicorn..."
uvicorn main:app --reload             # Ejecuta la app definida como `app` en el archivo `main.py`, con recarga automática al guardar cambios
