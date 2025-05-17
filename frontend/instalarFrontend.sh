#!/bin/bash

echo "Iniciando instalación de dependencias para el frontend con Angular..."

# Función para verificar si un comando está instalado
check_command() {
  if ! command -v $1 &> /dev/null; then
    echo "$1 no está instalado."
    return 1
  else
    echo "$1 está instalado."
    return 0
  fi
}

# Verificar e instalar Node.js y npm
if ! check_command node; then
  echo "Instalando Node.js y npm..."
  sudo apt update
  sudo apt install -y nodejs npm
fi

# Verificar versión de Node.js
NODE_VERSION=$(node -v)
echo "Versión de Node.js: $NODE_VERSION"
if [[ ! $NODE_VERSION =~ ^v(16|18|20)\. ]]; then
  echo "Se recomienda Node.js versión 16.x, 18.x o 20.x para Angular. Actualizando..."
  curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
  sudo apt install -y nodejs
fi

# Verificar e instalar Angular CLI
if ! check_command ng; then
  echo "Instalando Angular CLI globalmente..."
  sudo npm install -g @angular/cli
fi

# Instalar dependencias del proyecto Angular
if [ -f "angular/package.json" ]; then
  echo "Instalando dependencias del proyecto (npm install)..."
  cd angular
  npm install
  npm install -D tailwindcss postcss autoprefixer
  echo "Lanzando ng serve para primeras configuraciones."
  ng serve

  cd ..
else
  echo "No se encontró package.json en frontend/angular/. Asegúrate de que el proyecto Angular está creado."
  exit 1
fi

echo "Instalación de dependencias para el frontend completada."