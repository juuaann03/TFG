# archivo: main.py

from fastapi import FastAPI
from app.rutas.rutaHello import router as helloRouter
from app.rutas.rutaUsuario import router as usuarioRouter
from app.rutas.rutaRecomendacionBasica import router as recomendacionBasicaRouter
from app.rutas.rutaRecomendacionPersonalizada import router as recomendacionPersonalizadaRouter
from app.rutas.rutaAuth import router as authRouter
from app.rutas.rutaProximosLanzamientos import router as proximosLanzamientosRouter
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(helloRouter)
app.include_router(usuarioRouter)
app.include_router(recomendacionBasicaRouter)
app.include_router(recomendacionPersonalizadaRouter)
app.include_router(authRouter)
app.include_router(proximosLanzamientosRouter)