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

def obtenerUsuarioPorId(usuarioId: str) -> dict | None:
    usuario = coleccionUsuarios.find_one({"_id": ObjectId(usuarioId)})
    if usuario:
        usuario["id"] = str(usuario["_id"])
        usuario.pop("_id", None)
        return usuario
    return None

def actualizarUsuarioPorId(usuarioId: str, datosActualizados: dict) -> bool:
    resultado = coleccionUsuarios.update_one({"_id": ObjectId(usuarioId)}, {"$set": datosActualizados})
    return resultado.modified_count > 0

def borrarUsuarioPorId(usuarioId: str) -> bool:
    resultado = coleccionUsuarios.delete_one({"_id": ObjectId(usuarioId)})
    return resultado.deleted_count > 0

def obtenerUsuarioPorCorreo(correo: str) -> dict | None:
    return coleccionUsuarios.find_one({"correo": correo})

def actualizarUsuarioPorCorreo(correo: str, datosActualizados: dict) -> bool:
    resultado = coleccionUsuarios.update_one({"correo": correo}, {"$set": datosActualizados})
    return resultado.modified_count > 0

def borrarUsuarioPorCorreo(correo: str) -> bool:
    resultado = coleccionUsuarios.delete_one({"correo": correo})
    return resultado.deleted_count > 0

