#!/bin/bash

echo "Inicializando base de datos y colecciones..."

mongosh <<EOF
use LangGames

// Crear colecciones si no existen
db.createCollection("Usuarios")
db.Usuarios.createIndex({ correo: 1 }, { unique: true })
db.Usuarios.createIndex({ nombre: 1 }, { unique: true })

EOF
