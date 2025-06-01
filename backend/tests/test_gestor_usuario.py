import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch
from pymongo.errors import DuplicateKeyError
import mongomock
from app.gestores.gestorUsuario import (
    crearUsuario, obtenerUsuarioPorCorreo, verificarContrasena,
    actualizarUsuarioPorCorreo, borrarUsuarioPorCorreo, limpiarCamposOpcionalesPorCorreo
)

class TestGestorUsuario(unittest.TestCase):
    def setUp(self):
        # Configurar una colección simulada con mongomock
        self.client = mongomock.MongoClient()
        self.db = self.client["LangGames"]
        self.coleccionUsuarios = self.db["Usuarios"]
        # Crear índices únicos para correo y nombre
        self.coleccionUsuarios.create_index("correo", unique=True)
        self.coleccionUsuarios.create_index("nombre", unique=True)
        # Parchear la colección global para usar la simulada
        self.patcher = patch("app.gestores.gestorUsuario.coleccionUsuarios", self.coleccionUsuarios)
        self.patcher.start()
        # Parchear bcrypt para evitar hasheos reales
        self.bcrypt_patcher = patch("app.gestores.gestorUsuario.bcrypt")
        self.mock_bcrypt = self.bcrypt_patcher.start()
        # Ajustar el mock para devolver bytes, como el bcrypt real
        self.mock_bcrypt.hashpw.side_effect = lambda x, _: f"hashed_{x.decode('utf-8') if isinstance(x, bytes) else x}".encode('utf-8')
        self.mock_bcrypt.checkpw.side_effect = lambda plain, hashed: (plain.decode('utf-8') if isinstance(plain, bytes) else plain) == (hashed.decode('utf-8') if isinstance(hashed, bytes) else hashed).replace("hashed_", "")
        # Datos de prueba
        self.usuario = {
            "nombre": "test_user",
            "correo": "test@example.com",
            "contrasena": "password123",
            "rol": "usuario"
        }

    def tearDown(self):
        # Detener los parches
        self.patcher.stop()
        self.bcrypt_patcher.stop()

    def test_crear_usuario_exitoso(self):
        # Prueba: Crear un usuario nuevo
        resultado = crearUsuario(self.usuario.copy())
        self.assertIn("id", resultado)
        usuario_db = self.coleccionUsuarios.find_one({"correo": "test@example.com"})
        self.assertIsNotNone(usuario_db)
        self.assertEqual(usuario_db["nombre"], "test_user")
        self.assertEqual(usuario_db["contrasena"], "hashed_password123")

    def test_crear_usuario_duplicado_correo(self):
        # Prueba: Crear un usuario con correo duplicado
        self.coleccionUsuarios.insert_one(self.usuario.copy())
        usuario_duplicado = self.usuario.copy()
        usuario_duplicado["nombre"] = "otro_usuario"
        with self.assertRaises(ValueError) as cm:
            crearUsuario(usuario_duplicado)
        self.assertEqual(str(cm.exception), "El nombre o el correo ya están registrados")

    def test_crear_usuario_duplicado_nombre(self):
        # Prueba: Crear un usuario con nombre duplicado
        self.coleccionUsuarios.insert_one(self.usuario.copy())
        usuario_duplicado = self.usuario.copy()
        usuario_duplicado["correo"] = "otro@example.com"
        with self.assertRaises(ValueError) as cm:
            crearUsuario(usuario_duplicado)
        self.assertEqual(str(cm.exception), "El nombre o el correo ya están registrados")

    def test_obtener_usuario_por_correo_existe(self):
        # Prueba: Obtener un usuario existente
        self.coleccionUsuarios.insert_one(self.usuario.copy())
        usuario = obtenerUsuarioPorCorreo("test@example.com")
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario["nombre"], "test_user")
        self.assertEqual(usuario["correo"], "test@example.com")

    def test_obtener_usuario_por_correo_no_existe(self):
        # Prueba: Obtener un usuario inexistente
        usuario = obtenerUsuarioPorCorreo("noexiste@example.com")
        self.assertIsNone(usuario)

    def test_verificar_contrasena_correcta(self):
        # Prueba: Verificar contraseña correcta
        self.coleccionUsuarios.insert_one({
            "nombre": "test_user",
            "correo": "test@example.com",
            "contrasena": "hashed_password123",
            "rol": "usuario"
        })
        usuario = verificarContrasena("test@example.com", "password123")
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario["correo"], "test@example.com")

    def test_verificar_contrasena_incorrecta(self):
        # Prueba: Verificar contraseña incorrecta
        self.coleccionUsuarios.insert_one({
            "nombre": "test_user",
            "correo": "test@example.com",
            "contrasena": "hashed_password123",
            "rol": "usuario"
        })
        usuario = verificarContrasena("test@example.com", "wrongpassword")
        self.assertIsNone(usuario)

    def test_verificar_contrasena_usuario_no_existe(self):
        # Prueba: Verificar contraseña de usuario inexistente
        usuario = verificarContrasena("noexiste@example.com", "password123")
        self.assertIsNone(usuario)

    def test_actualizar_usuario_exitoso(self):
        # Prueba: Actualizar datos de un usuario
        self.coleccionUsuarios.insert_one(self.usuario.copy())
        datos_actualizados = {"nombre": "nuevo_nombre"}
        resultado = actualizarUsuarioPorCorreo("test@example.com", datos_actualizados)
        self.assertTrue(resultado)
        usuario_db = self.coleccionUsuarios.find_one({"correo": "test@example.com"})
        self.assertEqual(usuario_db["nombre"], "nuevo_nombre")

    def test_actualizar_usuario_no_existe(self):
        # Prueba: Actualizar usuario inexistente
        resultado = actualizarUsuarioPorCorreo("noexiste@example.com", {"nombre": "nuevo_nombre"})
        self.assertFalse(resultado)

    def test_borrar_usuario_exitoso(self):
        # Prueba: Borrar un usuario existente
        self.coleccionUsuarios.insert_one(self.usuario.copy())
        resultado = borrarUsuarioPorCorreo("test@example.com")
        self.assertTrue(resultado)
        usuario_db = self.coleccionUsuarios.find_one({"correo": "test@example.com"})
        self.assertIsNone(usuario_db)

    def test_borrar_usuario_no_existe(self):
        # Prueba: Borrar un usuario inexistente
        resultado = borrarUsuarioPorCorreo("noexiste@example.com")
        self.assertFalse(resultado)

    def test_limpiar_campos_opcionales_exitoso(self):
        # Prueba: Limpiar campos opcionales de un usuario
        self.coleccionUsuarios.insert_one({
            **self.usuario,
            "consolas": ["PS4"],
            "juegosGustados": ["GTA 5"],
            "historialConversaciones": [{"pregunta": "test"}]
        })
        resultado = limpiarCamposOpcionalesPorCorreo("test@example.com")
        self.assertTrue(resultado)
        usuario_db = self.coleccionUsuarios.find_one({"correo": "test@example.com"})
        self.assertNotIn("consolas", usuario_db)
        self.assertNotIn("juegosGustados", usuario_db)
        self.assertNotIn("historialConversaciones", usuario_db)

    def test_limpiar_campos_opcionales_no_existe(self):
        # Prueba: Limpiar campos de usuario inexistente
        resultado = limpiarCamposOpcionalesPorCorreo("noexiste@example.com")
        self.assertFalse(resultado)

if __name__ == "__main__":
    unittest.main()