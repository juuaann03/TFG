#!/bin/bash

echo "Inicializando base de datos y colecciones..."

mongosh <<EOF
use LangGames

// Crear colecciones si no existen
db.createCollection("Usuarios")

print("Colecciones creadas correctamente en LangGames.");
EOF
