# archivo: app/servicios/serviciosUsuario.py
from app.gestores.gestorUsuario import *
from app.modelos.modeloUsuario import Usuario, UsuarioObligatorio, UsuarioOpcionalSinHistorial, UsuarioOpcionalConHistorial, Conversacion, JuegoRecomendado
from app.gestores.gestorUsuario import obtenerUsuarioPorCorreo, actualizarUsuarioPorCorreo
from app.servicios.servicioGenerarActualizacionUsuario import generarActualizacionDesdePeticion
from app.servicios.servicioRecomendacionPersonalizada import generarRecomendacionPersonalizada, generarCambiosDesdePeticionRecomendacion
from app.servicios.servicioProximosLanzamientos import obtenerProximosLanzamientosServicio
from app.servicios.servicioSteam import obtener_juegos_steam
from app.modelos.modeloUsuario import JuegoPoseido
from datetime import datetime
import json
from typing import List

def crearUsuarioServicio(usuario: Usuario) -> dict:
    return crearUsuario(usuario.dict())

def obtenerUsuarioPorCorreoServicio(correo: str) -> dict | None:
    return obtenerUsuarioPorCorreo(correo)

def actualizarUsuarioPorCorreoServicio(correo: str, datos) -> bool:
    return actualizarUsuarioPorCorreo(correo, datos.dict(exclude_unset=True) if hasattr(datos, 'dict') else datos)

def borrarUsuarioPorCorreoServicio(correo: str) -> bool:
    return borrarUsuarioPorCorreo(correo)

def limpiarCamposOpcionalesServicioPorCorreo(correo: str) -> bool:
    return limpiarCamposOpcionalesPorCorreo(correo)

def modificarUsuarioPorPeticionServicio(correo: str, peticion: str) -> tuple[bool, str, dict]:
    usuario = obtenerUsuarioPorCorreo(correo)
    if not usuario:
        return False, "Usuario no encontrado", {}
    estado_actual = {k: usuario.get(k) for k in UsuarioOpcionalSinHistorial.__fields__}
    mensaje, actualizacion = generarActualizacionDesdePeticion(estado_actual, peticion)
    if not actualizacion:
        return True, mensaje, actualizacion  # No hay cambios que hacer
    exito = actualizarUsuarioPorCorreo(correo, actualizacion)
    return exito, mensaje, actualizacion

def obtenerRecomendacionPersonalizadaServicio(correo: str, peticion: str) -> List[dict]:
    # Obtener datos del usuario
    usuario = obtenerUsuarioPorCorreoServicio(correo)
    if not usuario:
        raise ValueError("Usuario no encontrado")
    # Extraer datos opcionales
    datos_usuario = {k: usuario.get(k) for k in UsuarioOpcionalConHistorial.__fields__}
    historial = datos_usuario.get("historialConversaciones", []) or []  # Asegurar que historial sea una lista
    # Filtrar el historial para excluir imágenes
    historial_filtrado = [
        {
            "pregunta": conv.get("pregunta"),
            "juegos": [{"nombre": juego["nombre"]} for juego in conv.get("juegos", [])]
        }
        for conv in historial
    ]
    datos_usuario_filtrado = {**datos_usuario, "historialConversaciones": historial_filtrado}
    # Procesar cambios implícitos en la petición
    try:
        mensaje_cambios, actualizacion = generarCambiosDesdePeticionRecomendacion(
            {k: datos_usuario.get(k) for k in UsuarioOpcionalSinHistorial.__fields__},
            peticion
        )
    except Exception as e:
        print(f"Error al procesar cambios de la petición: {str(e)}")
        mensaje_cambios, actualizacion = "No se procesaron cambios de la petición", {}
    # Generar recomendación personalizada con historial filtrado
    try:
        recomendaciones = generarRecomendacionPersonalizada(peticion, datos_usuario_filtrado)
    except Exception as e:
        raise ValueError(f"Error al generar recomendación: {str(e)}")
    # Actualizar el perfil si hay cambios
    if actualizacion:
        try:
            if not actualizarUsuarioPorCorreoServicio(correo, actualizacion):
                raise ValueError("No se pudo actualizar el perfil del usuario")
        except Exception as e:
            raise ValueError(f"Error al actualizar el perfil: {str(e)}")
    # Guardar la conversación con el nuevo formato (incluyendo imágenes)
    juegos_recomendados = [
        JuegoRecomendado(nombre=rec["nombre"], imagen=rec["imagen"]).dict()
        for rec in recomendaciones
    ]
    nueva_conversacion = Conversacion(
        pregunta=peticion,
        juegos=juegos_recomendados
    )
    try:
        if not actualizarUsuarioPorCorreoServicio(correo, {
            "historialConversaciones": historial + [nueva_conversacion.dict()]
        }):
            raise ValueError("No se pudo guardar la conversación en el historial")
    except Exception as e:
        raise ValueError(f"Error al guardar la conversación: {str(e)}")
    return recomendaciones

def obtenerProximosLanzamientosServicioWrapper(correo: str) -> List[dict]:
    # Obtener datos del usuario
    usuario = obtenerUsuarioPorCorreoServicio(correo)
    if not usuario:
        raise ValueError("Usuario no encontrado")
    # Extraer datos opcionales (sin historial)
    datos_usuario = {k: usuario.get(k) for k in UsuarioOpcionalSinHistorial.__fields__}
    # Llamar al servicio
    return obtenerProximosLanzamientosServicio(datos_usuario)

def obtenerDatosSteamServicio(correo: str, steam_id: str) -> dict:
    """
    Obtiene los juegos de un usuario desde Steam y actualiza su perfil.
    Args:
        correo (str): Correo del степа usuario en la base de datos.
        steam_id (str): SteamID64 del usuario.
    Returns:
        dict: Mensaje de éxito y número de juegos añadidos.
    Raises:
        ValueError: Si el usuario no se encuentra o la solicitud a Steam falla.
    """
    # Obtener el usuario
    usuario = obtenerUsuarioPorCorreoServicio(correo)
    if not usuario:
        raise ValueError("Usuario no encontrado")

    # Obtener juegos de Steam
    juegos_steam = obtener_juegos_steam(steam_id)
    if not juegos_steam:
        return {
            "mensaje": "No se encontraron juegos en el perfil de Steam (puede ser privado o no existir)",
            "juegos_anadidos": 0,
            "juegos_jugados_anadidos": 0
        }

    # Preparar listas para actualizar
    juegos_poseidos = usuario.get("juegosPoseidos", []) or []
    juegos_jugados = usuario.get("juegosJugados", []) or []

    # Crear nuevos juegos poseídos y jugados
    nuevos_juegos_poseidos = []
    nuevos_juegos_jugados = []
    for juego in juegos_steam:
        nombre_juego = juego["nombre"]
        # Evitar duplicados en juegos poseídos
        if not any(j["nombre"] == nombre_juego for j in juegos_poseidos):
            nuevos_juegos_poseidos.append(JuegoPoseido(
                nombre=nombre_juego,
                consolasDisponibles=["PC"]
            ).dict())
        # Añadir a juegos jugados si tiene más de 60 minutos
        if juego["playtime_forever"] > 60 and nombre_juego not in juegos_jugados:
            nuevos_juegos_jugados.append(nombre_juego)

    # Si no hay cambios, devolver mensaje sin actualizar
    if not nuevos_juegos_poseidos and not nuevos_juegos_jugados:
        return {
            "mensaje": "No hay nuevos juegos o juegos jugados para añadir",
            "juegos_anadidos": 0,
            "juegos_jugados_anadidos": 0
        }

    # Actualizar las listas
    juegos_poseidos.extend(nuevos_juegos_poseidos)
    juegos_jugados.extend(nuevos_juegos_jugados)

    # Preparar la actualización
    actualizacion = {
        "juegosPoseidos": juegos_poseidos,
        "juegosJugados": juegos_jugados
    }

    # Intentar actualizar el perfil
    try:
        if not actualizarUsuarioPorCorreoServicio(correo, actualizacion):
            raise ValueError("No se pudo actualizar el perfil del usuario: posible problema con la base de datos o datos idénticos")
    except Exception as e:
        raise ValueError(f"Error al actualizar el perfil: {str(e)}")

    return {
        "mensaje": "Juegos de Steam añadidos correctamente",
        "juegos_anadidos": len(nuevos_juegos_poseidos),
        "juegos_jugados_anadidos": len(nuevos_juegos_jugados)
    }