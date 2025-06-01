import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from app.gestores.gestorUsuario import coleccionUsuarios
import mongomock

class TestRutaAuth(unittest.TestCase):
    def setUp(self):
        # Configurar cliente de prueba para FastAPI
        self.client = TestClient(app)
        # Configurar colección simulada con mongomock
        self.client_mongo = mongomock.MongoClient()
        self.db = self.client_mongo["LangGames"]
        self.coleccionUsuarios = self.db["Usuarios"]
        # Parchear la colección global
        self.patcher = patch("app.gestores.gestorUsuario.coleccionUsuarios", self.coleccionUsuarios)
        self.patcher.start()
        # Parchear bcrypt
        self.bcrypt_patcher = patch("app.gestores.gestorUsuario.bcrypt")
        self.mock_bcrypt = self.bcrypt_patcher.start()
        # Ajustar el mock para devolver bytes, como el bcrypt real
        self.mock_bcrypt.hashpw.side_effect = lambda x, _: f"hashed_{x.decode('utf-8') if isinstance(x, bytes) else x}".encode('utf-8')
        self.mock_bcrypt.checkpw.side_effect = lambda plain, hashed: (plain.decode('utf-8') if isinstance(plain, bytes) else plain) == (hashed.decode('utf-8') if isinstance(hashed, bytes) else hashed).replace("hashed_", "")
        # Parchear JWT
        self.jwt_patcher = patch("app.rutas.rutaAuth.jwt")
        self.mock_jwt = self.jwt_patcher.start()
        self.mock_jwt.encode.return_value = "mocked_token"
        # Datos de prueba
        self.usuario = {
            "nombre": "test_user",
            "correo": "test@example.com",
            "contrasena": "hashed_password123",
            "rol": "usuario"
        }
        self.coleccionUsuarios.insert_one(self.usuario.copy())

    def tearDown(self):
        # Detener los parches
        self.patcher.stop()
        self.bcrypt_patcher.stop()
        self.jwt_patcher.stop()

    def test_login_exitoso(self):
        # Prueba: Login con credenciales correctas
        response = self.client.post("/auth/login", json={
            "correo": "test@example.com",
            "contrasena": "password123"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "token": "mocked_token",
            "correo": "test@example.com",
            "nombre": "test_user"
        })

    def test_login_credenciales_incorrectas(self):
        # Prueba: Login con contraseña incorrecta
        response = self.client.post("/auth/login", json={
            "correo": "test@example.com",
            "contrasena": "wrongpassword"
        })
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Credenciales incorrectas"})

    def test_login_usuario_no_existe(self):
        # Prueba: Login con usuario inexistente
        response = self.client.post("/auth/login", json={
            "correo": "noexiste@example.com",
            "contrasena": "password123"
        })
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Credenciales incorrectas"})

if __name__ == "__main__":
    unittest.main()