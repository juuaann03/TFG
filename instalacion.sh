#!/bin/bash

# Actualizar paquetes
sudo apt update && sudo apt upgrade -y

# Instalar git
sudo apt install git -y

# Instalar Python y pip
sudo apt install python3 python3-pip -y

# Instalar virtualenv (opcional pero recomendable)
pip3 install virtualenv

# Instalar Node.js y Angular CLI (si usas Angular en el frontend)
sudo apt install nodejs npm -y
sudo npm install -g @angular/cli

# Instalar MongoDB client (si te conectas a Atlas puedes usar drivers desde Python, esto es opcional)
sudo apt install mongodb-clients -y

echo "✅ Instalación completa. Puedes ahora clonar tu repositorio y empezar a trabajar."
