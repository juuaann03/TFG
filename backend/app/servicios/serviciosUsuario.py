# archivo: servicios/serviciosUsuarios.py

from app.gestores.gestorUsuario import *
from app.modelos.modeloUsuario import Usuario

def crearUsuarioServicio(usuario: Usuario) -> dict:
    return crearUsuario(usuario.dict())

def obtenerUsuarioServicio(usuarioId: str) -> dict:
    return obtenerUsuarioPorId(usuarioId)

def actualizarUsuarioServicio(usuarioId: str, usuario: Usuario) -> bool:
    return actualizarUsuarioPorId(usuarioId, usuario.dict(exclude_unset=True))

def borrarUsuarioServicio(usuarioId: str) -> bool:
    return borrarUsuarioPorId(usuarioId)

def obtenerUsuarioPorCorreoServicio(correo: str) -> dict | None:
    return obtenerUsuarioPorCorreo(correo)

def actualizarUsuarioPorCorreoServicio(correo: str, usuario: Usuario) -> bool:
    return actualizarUsuarioPorCorreo(correo, usuario.dict(exclude_unset=True))

def borrarUsuarioPorCorreoServicio(correo: str) -> bool:
    return borrarUsuarioPorCorreo(correo)


