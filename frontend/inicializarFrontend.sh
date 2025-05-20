#!/bin/bash

echo "Iniciando el servidor de desarrollo de Angular..."

# Verificar si el proyecto Angular existe
if [ ! -f "angular/package.json" ] || [ ! -d "angular/src" ]; then
  echo "No se encontró un proyecto Angular en la carpeta 'frontend/angular'. Asegúrate de que el proyecto está creado."
  exit 1
fi

# Verificar si las dependencias están instaladas
if [ ! -d "angular/node_modules" ]; then
  echo "Instalando dependencias del proyecto (npm install)..."
  cd angular
  npm install
  cd ..
fi

# Iniciar el servidor de desarrollo
echo "Iniciando Angular con 'ng serve'..."
cd angular
ng serve > ../../frontend.log 2>&1 &    # Ejecuta en segundo plano y guarda log
echo $! > ../../frontend.pid            # Guardar PID real
sleep 3
# Abrir el navegador automáticamente en la URL de Angular
xdg-open http://localhost:4200           # En Linux, esto abre el navegador automáticamente

cd ..

echo "Servidor de Angular iniciado en http://localhost:4200"