#!/bin/bash

echo "Creando proyecto Angular para desarrollo..."

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

# Verificar si ya existe un proyecto Angular
if [ -f "angular/package.json" ] && [ -d "angular/src" ]; then
  echo "Ya existe un proyecto Angular en la carpeta 'frontend/angular'. Si quieres recrearlo, elimina la carpeta 'frontend/angular' primero."
  exit 1
fi

# Crear la carpeta 'angular' si no existe
mkdir -p angular

# Crear nuevo proyecto Angular
echo "Creando nuevo proyecto Angular en frontend/angular..."
cd angular
ng new plataforma-recomendaciones-videojuegos --directory . --style=scss --routing=true --ssr=false --skip-tests --force || {
  echo "Error al crear el proyecto Angular. Revisa los mensajes de error arriba."
  exit 1
}
cd ..

# Verificar que la carpeta environments existe
if [ ! -d "angular/src/environments" ]; then
  echo "La carpeta 'angular/src/environments' no existe. Creándola..."
  mkdir -p angular/src/environments
fi

# Instalar dependencias adicionales
echo "Instalando dependencias adicionales..."
cd angular
npm install axios --save
npm install -D tailwindcss postcss autoprefixer



cd ..

# Configurar variables de entorno para conectar con el backend
echo "Configurando entorno para conectar con el backend..."
if [ -f "angular/src/environments/environment.ts" ]; then
  echo "environment.ts ya existe, sobrescribiendo..."
else
  echo "Creando environment.ts..."
fi
cat <<EOF > angular/src/environments/environment.ts
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000'
};
EOF

if [ -f "angular/src/environments/environment.prod.ts" ]; then
  echo "environment.prod.ts ya existe, sobrescribiendo..."
else
  echo "Creando environment.prod.ts..."
fi
cat <<EOF > angular/src/environments/environment.prod.ts
export const environment = {
  production: true,
  apiUrl: 'http://localhost:8000'
};
EOF

# Configurar Tailwind CSS
echo "Configurando Tailwind CSS..."
cd angular
npx tailwindcss init || {
  echo "Error al inicializar Tailwind CSS. Creando tailwind.config.js manualmente..."
  cat <<EOF > tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
  darkMode: 'class'
}
EOF
}
cd ..

# Agregar directivas de Tailwind a styles.scss
echo "Agregando Tailwind CSS a styles.scss..."
if [ -f "angular/src/styles.scss" ]; then
  echo "@tailwind base;\n@tailwind components;\n@tailwind utilities;" > angular/src/styles.scss
else
  echo "No se encontró angular/src/styles.scss. Creándolo..."
  echo "@tailwind base;\n@tailwind components;\n@tailwind utilities;" > angular/src/styles.scss
fi

echo "Proyecto Angular creado y configurado en frontend/angular."
echo "Para iniciar el frontend, ejecuta: cd frontend && bash ./lanzarFrontend.sh"