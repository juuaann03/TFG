# archivo: main.py

from fastapi import FastAPI
from app.rutas.rutaHello import router as helloRouter
from app.rutas.rutaUsuario import router as usuarioRouter
from app.rutas.rutaRecomendacionBasica import router as recomendacionRouter

app = FastAPI()

app.include_router(helloRouter)
app.include_router(usuarioRouter)
app.include_router(recomendacionRouter)
