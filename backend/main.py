# archivo: main.py

from fastapi import FastAPI
from app.rutas.rutaHello import router as helloRouter
from app.rutas.rutaUsuario import router as usuarioRouter
from app.rutas.rutaRecomendacionBasica import router as recomendacionBasicaRouter
from app.rutas.rutaRecomendacionPersonalizada import router as recomendacionPersonalizadaRouter
from app.rutas.rutaRecomendacionesJuegosFuturos import router as recomendacionJuegosFuturosRouter
from app.rutas.rutaAuth import router as authRouter
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
app.include_router(recomendacionJuegosFuturosRouter)
app.include_router(authRouter)