#!/bin/bash

echo "🛠️ Inicializando base de datos y colecciones..."

mongosh <<EOF
use PlataformaConLangChainParaRecomendarVideojuegos

// Crear colecciones si no existen (Mongo las crea automáticamente con insert, pero aquí es explícito)
db.createCollection("Usuarios")
db.createCollection("UsuarioAdministradores")

// Puedes agregar más colecciones si lo necesitas
// db.createCollection("Recomendaciones")
// db.createCollection("Config")

print("✅ Colecciones creadas correctamente en PlataformaConLangChainParaRecomendarVideojuegos.");
EOF
