from fastapi import FastAPI
from app.rutas.rutaHello import router as helloRouter
from app.rutas.rutaUsuario import router as usuarioRouter
from app.rutas.rutaRecomendacionBasica import router as recomendacionBasicaRouter
from app.rutas.rutaRecomendacionPersonalizada import router as recomendacionPersonalizadaRouter

app = FastAPI()

app.include_router(helloRouter)
app.include_router(usuarioRouter)
app.include_router(recomendacionBasicaRouter)
app.include_router(recomendacionPersonalizadaRouter)