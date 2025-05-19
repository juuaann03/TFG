#!/bin/bash

# Detener backend
if [ -f backend.pid ]; then
    PID=$(cat backend.pid)
    echo "Matando proceso backend con PID $PID"
    kill $PID
    rm backend.pid
else
    echo "No se encontró backend.pid"
fi

# Detener frontend
if [ -f frontend.pid ]; then
    PID=$(cat frontend.pid)
    echo "Matando proceso frontend con PID $PID"
    kill $PID
    rm frontend.pid
else
    echo "No se encontró frontend.pid"
fi
