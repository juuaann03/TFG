#!/bin/bash

# Inicializar backend en segundo plano
bash ./backend/inicializarBackend.sh > ./backend.log 2>&1 &
echo $! > ./backend.pid

# Inicializar frontend en segundo plano
bash ./frontend/inicializarFrontend.sh > ./frontend.log 2>&1 &
echo $! > ./frontend.pid

echo "Backend y frontend lanzados en segundo plano."
