# archivo: app/servicios/servicioUsuario.py


from app.gestores.gestorUsuario import *
from app.modelos.modeloUsuario import Usuario, UsuarioObligatorio, UsuarioOpcional
from app.gestores.gestorUsuario import obtenerUsuarioPorCorreo, actualizarUsuarioPorCorreo
from app.servicios.servicioGenerarActualizacionUsuario import generarActualizacionDesdePeticion

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

def modificarUsuarioPorPeticionServicio(correo: str, peticion: str) -> tuple[bool, str, dict]:
    usuario = obtenerUsuarioPorCorreo(correo)
    if not usuario:
        return False, "Usuario no encontrado", {}

    estado_actual = {k: usuario.get(k) for k in UsuarioOpcional.__fields__}
    mensaje, actualizacion = generarActualizacionDesdePeticion(estado_actual, peticion)

    if not actualizacion:
        return True, mensaje, actualizacion  # No hay cambios que hacer

    exito = actualizarUsuarioPorCorreo(correo, actualizacion)
    return exito, mensaje, actualizacion
