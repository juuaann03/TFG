# archivo: main.py

from fastapi import FastAPI
from app.rutas.rutaHello import router as helloRouter
from app.rutas.rutaUsuario import router as usuarioRouter
from app.rutas.rutaRecomendacionBasica import router as recomendacionBasicaRouter
from app.rutas.rutaRecomendacionPersonalizada import router as recomendacionPersonalizadaRouter
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Origen del frontend
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permitir todas las cabeceras
)

app.include_router(helloRouter)
app.include_router(usuarioRouter)
app.include_router(recomendacionBasicaRouter)
app.include_router(recomendacionPersonalizadaRouter)