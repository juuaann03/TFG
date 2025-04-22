#!/bin/bash

# Actualizar paquetes
sudo apt update && sudo apt upgrade -y

# Instalar dependencias necesarias
sudo apt install -y gnupg curl

# Obtener la versión de Ubuntu
UBUNTU_VERSION=$(lsb_release -c | awk '{print $2}')

# Añadir clave GPG de MongoDB
curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | \
  sudo gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor

# Añadir repositorio oficial de MongoDB basado en la versión de Ubuntu
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu $UBUNTU_VERSION/mongodb-org/8.0 multiverse" | \
  sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list

# Instalar MongoDB
sudo apt update
sudo apt install -y mongodb-org
