#!/bin/bash

# Instalacion y activacion base de datos

cd  ./baseDeDatos
bash ./instalacion.sh
bash ./servicios.sh
bash ./inicializarBaseDeDatos.sh 
cd ..

# Instalacion del backend
cd ./backend
bash ./instalarBackend.sh
bash ./inicializarBackend.sh
cd ..

# Instalacion del frontend
cd ./frontend
bash ./instalarFrontend.sh
cd ..
