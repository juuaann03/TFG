# archivo: app/routes/rutaUsuario.py

from fastapi import APIRouter, HTTPException
from app.modelos.modeloUsuario import Usuario, UsuarioEnBaseDeDatos, UsuarioObligatorio, UsuarioOpcionalSinHistorial, UsuarioOpcionalConHistorial
from app.servicios.serviciosUsuario import *
from fastapi import Body
from pydantic import BaseModel

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

# Modelo de respuesta para el endpoint modificarPorPeticion
class RespuestaModificarPorPeticion(BaseModel):
    mensaje: str
    actualizacion: dict

@router.post("/", response_model=dict)
def crearUsuario(usuario: Usuario):
    try:
        return crearUsuarioServicio(usuario)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/porCorreo/{correo}", response_model=UsuarioEnBaseDeDatos)
def obtenerUsuarioPorCorreoRuta(correo: str):
    usuario = obtenerUsuarioPorCorreoServicio(correo)
    if usuario:
        usuario["id"] = str(usuario["_id"])
        del usuario["_id"]
        return usuario
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@router.delete("/porCorreo/{correo}", response_model=dict)
def borrarUsuarioPorCorreoRuta(correo: str):
    eliminado = borrarUsuarioPorCorreoServicio(correo)
    if eliminado:
        return {"mensaje": "Usuario eliminado correctamente"}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@router.put("/porCorreo/{correo}/limpiar", response_model=dict)
def limpiarCamposUsuarioPorCorreo(correo: str):
    exito = limpiarCamposOpcionalesServicioPorCorreo(correo)
    if not exito:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o no modificado")
    return {"mensaje": "Campos opcionales eliminados correctamente"}

@router.get("/porCorreo/{correo}/obligatorios", response_model=UsuarioObligatorio)
def obtenerDatosObligatorios(correo: str):
    usuario = obtenerUsuarioPorCorreoServicio(correo)
    if usuario:
        return {clave: usuario[clave] for clave in UsuarioObligatorio.__fields__ if clave in usuario}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@router.get("/porCorreo/{correo}/optativos", response_model=UsuarioOpcionalSinHistorial)
def obtenerDatosOptativos(correo: str):
    usuario = obtenerUsuarioPorCorreoServicio(correo)
    if usuario:
        return {clave: usuario.get(clave) for clave in UsuarioOpcionalSinHistorial.__fields__}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@router.put("/porCorreo/{correo}/optativos", response_model=dict)
def actualizarDatosOptativos(correo: str, datos: UsuarioOpcionalSinHistorial):
    actualizado = actualizarUsuarioPorCorreoServicio(correo, datos)
    if actualizado:
        return {"mensaje": "Datos optativos actualizados correctamente"}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@router.get("/porCorreo/{correo}/optativosConHistorial", response_model=UsuarioOpcionalConHistorial)
def obtenerDatosOptativosConHistorial(correo: str):
    usuario = obtenerUsuarioPorCorreoServicio(correo)
    if usuario:
        return {clave: usuario.get(clave) for clave in UsuarioOpcionalConHistorial.__fields__}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@router.put("/porCorreo/{correo}/optativosConHistorial", response_model=dict)
def actualizarDatosOptativosConHistorial(correo: str, datos: UsuarioOpcionalConHistorial):
    actualizado = actualizarUsuarioPorCorreoServicio(correo, datos)
    if actualizado:
        return {"mensaje": "Datos optativos con historial actualizados correctamente"}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@router.put("/porCorreo/{correo}/modificarPorPeticion", response_model=RespuestaModificarPorPeticion)
def modificarUsuarioPorPeticionRuta(correo: str, peticion: str = Body(..., embed=True)):
    exito, mensaje, actualizacion = modificarUsuarioPorPeticionServicio(correo, peticion)
    if exito:
        return {"mensaje": mensaje, "actualizacion": actualizacion}
    raise HTTPException(status_code=404, detail=mensaje)