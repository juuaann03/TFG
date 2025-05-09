#!/bin/bash

bash ./baseDeDatos/instalacion.sh
bash ./baseDeDatos/servicios.sh
bash ./baseDeDatos/inicializarBaseDeDatos.sh  
cd ./frontend && bash ./instalarFrontend.sh
