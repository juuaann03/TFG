# archivo: app/gestores/gestorUsuario.py

from app.db.mongodb import coleccionUsuarios
from pymongo.errors import DuplicateKeyError
import bcrypt

def crearUsuario(usuario: dict) -> dict:
    # Hashear la contraseña directamente (llega en texto plano)
    contrasena_plana = usuario["contrasena"]
    usuario["contrasena"] = bcrypt.hashpw(contrasena_plana.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        resultado = coleccionUsuarios.insert_one(usuario)
        return {"id": str(resultado.inserted_id)}
    except DuplicateKeyError:
        raise ValueError("El nombre o el correo ya están registrados")

def obtenerUsuarioPorCorreo(correo: str) -> dict | None:
    return coleccionUsuarios.find_one({"correo": correo})

def verificarContrasena(correo: str, contrasena: str) -> dict | None:
    usuario = obtenerUsuarioPorCorreo(correo)
    if usuario:
        print(f"Correo encontrado: {correo}")
        print(f"Contraseña recibida: {contrasena}")
        print(f"Hash almacenado: {usuario['contrasena']}")
        if bcrypt.checkpw(contrasena.encode('utf-8'), usuario["contrasena"].encode('utf-8')):
            print("Contraseña verificada correctamente")
            return usuario
        else:
            print("Contraseña no coincide")
    else:
        print(f"Correo no encontrado: {correo}")
    return None

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