# archivo: gestores/gestorUsuario.py

from app.db.mongodb import coleccionUsuarios
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError

def crearUsuario(usuario: dict) -> dict:
    try:
        resultado = coleccionUsuarios.insert_one(usuario)
        return {"id": str(resultado.inserted_id)}
    except DuplicateKeyError:
        raise ValueError("El nombre o el correo ya están registrados")

def obtenerUsuarioPorCorreo(correo: str) -> dict | None:
    return coleccionUsuarios.find_one({"correo": correo})

def actualizarUsuarioPorCorreo(correo: str, datosActualizados: dict) -> bool:
    resultado = coleccionUsuarios.update_one({"correo": correo}, {"$set": datosActualizados})
    return resultado.modified_count > 0

def borrarUsuarioPorCorreo(correo: str) -> bool:
    resultado = coleccionUsuarios.delete_one({"correo": correo})
    return resultado.deleted_count > 0

def limpiarCamposOpcionalesPorCorreo(correo: str) -> bool:
    campos_a_eliminar = {
        "consolas": None,
        "configuracionPc": None,
        "necesidadesEspeciales": None,
        "juegosGustados": None,
        "juegosNoGustados": None,
        "juegosJugados": None,
        "suscripciones": None,
        "idiomas": None,
        "juegosPoseidos": None,
        "historialConversaciones": None
    }
    resultado = coleccionUsuarios.update_one({"correo": correo}, {"$unset": campos_a_eliminar})
    return resultado.modified_count > 0
