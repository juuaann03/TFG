#!/bin/bash

# Instalacion y activacion base de datos
bash ./baseDeDatos/instalacion.sh
bash ./baseDeDatos/servicios.sh
bash ./baseDeDatos/inicializarBaseDeDatos.sh 

# Instalacion del backend
bash ./backend/instalarBackend.sh


# Instalacion del frontend
cd ./frontend
bash ./instalarFrontend.sh
cd ..


