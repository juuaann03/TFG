#!/bin/bash

# Instala Python, pip y venv

echo "Actualizando paquetes del sistema..."
sudo apt update && sudo apt upgrade -y

echo "Instalando Python3, pip y venv..."
sudo apt install -y python3 python3-pip python3-venv

# Verificar instalación
echo
echo "Verificaciones:"
python3 --version || echo "Python no se instaló correctamente."
pip3 --version || echo "pip no se instaló correctamente."

echo
echo "Instalación completada."
