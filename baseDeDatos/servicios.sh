#!/bin/bash

echo "Iniciando el servicio de MongoDB..."

# Iniciar MongoDB
sudo systemctl start mongod

# Recargar los servicios si hubo cambios
sudo systemctl daemon-reexec
sudo systemctl daemon-reload

# Habilitar MongoDB para que arranque al inicio
sudo systemctl enable mongod

# Comprobar el estado
if systemctl is-active --quiet mongod; then
    echo "MongoDB se ha iniciado correctamente y está funcionando."
else
    echo "Ha ocurrido un error al iniciar MongoDB. Revisa con: sudo systemctl status mongod"
fi
