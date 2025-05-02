# archivo: rutas/rutaUsuario.py

from fastapi import APIRouter, HTTPException
from app.modelos.modeloUsuario import Usuario, UsuarioEnBaseDeDatos
from app.servicios.serviciosUsuario import *

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

@router.post("/", response_model=dict)
def crearUsuario(usuario: Usuario):
    try:
        return crearUsuarioServicio(usuario)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{usuarioId}", response_model=UsuarioEnBaseDeDatos)
def obtenerUsuario(usuarioId: str):
    usuario = obtenerUsuarioServicio(usuarioId)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@router.put("/{usuarioId}", response_model=dict)
def actualizarUsuario(usuarioId: str, usuario: Usuario):
    exito = actualizarUsuarioServicio(usuarioId, usuario)
    if not exito:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o no modificado")
    return {"mensaje": "Usuario actualizado correctamente"}

@router.delete("/{usuarioId}", response_model=dict)
def borrarUsuario(usuarioId: str):
    exito = borrarUsuarioServicio(usuarioId)
    if not exito:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"mensaje": "Usuario eliminado correctamente"}

@router.get("/porCorreo/{correo}", response_model=dict)
def obtenerUsuarioPorCorreoRuta(correo: str):
    usuario = obtenerUsuarioPorCorreoServicio(correo)
    if usuario:
        usuario["id"] = str(usuario["_id"])
        del usuario["_id"]
        return usuario
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@router.put("/porCorreo/{correo}", response_model=dict)
def actualizarUsuarioPorCorreoRuta(correo: str, usuario: Usuario):
    actualizado = actualizarUsuarioPorCorreoServicio(correo, usuario)
    if actualizado:
        return {"mensaje": "Usuario actualizado correctamente"}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@router.delete("/porCorreo/{correo}", response_model=dict)
def borrarUsuarioPorCorreoRuta(correo: str):
    eliminado = borrarUsuarioPorCorreoServicio(correo)
    if eliminado:
        return {"mensaje": "Usuario eliminado correctamente"}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

