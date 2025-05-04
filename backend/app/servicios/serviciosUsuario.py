# archivo: app/servicios/servicioRecomendacionBasica.py


from app.gestores.gestorUsuario import *
from app.modelos.modeloUsuario import Usuario, UsuarioObligatorio, UsuarioOpcional

def crearUsuarioServicio(usuario: Usuario) -> dict:
    return crearUsuario(usuario.dict())

def obtenerUsuarioPorCorreoServicio(correo: str) -> dict | None:
    return obtenerUsuarioPorCorreo(correo)

def actualizarUsuarioPorCorreoServicio(correo: str, datos) -> bool:
    return actualizarUsuarioPorCorreo(correo, datos.dict(exclude_unset=True))

def borrarUsuarioPorCorreoServicio(correo: str) -> bool:
    return borrarUsuarioPorCorreo(correo)

def limpiarCamposOpcionalesServicioPorCorreo(correo: str) -> bool:
    return limpiarCamposOpcionalesPorCorreo(correo)
