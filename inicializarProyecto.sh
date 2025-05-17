#!/bin/bash

# Inicializar backend en segundo plano
cd ./backend
bash ./inicializarBackend.sh > ../backend.log 2>&1 &
echo $! > ../backend.pid
cd ..

# Inicializar frontend en segundo plano
cd ./frontend
bash ./inicializarFrontend.sh > ../frontend.log 2>&1 &
echo $! > ../frontend.pid
cd ..

echo "Backend y frontend lanzados en segundo plano."
