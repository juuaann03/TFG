# archivo: app/utils/crypto.py


from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables del .env
dotenv_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=dotenv_path)

def descifrar_contrasena(encrypted_password: str) -> str:
    try:
        crypto_key = os.getenv("CRYPTO_KEY")
        if not crypto_key:
            raise ValueError("CRYPTO_KEY no está definido en el .env")
        
        # Decodificar la contraseña cifrada (base64)
        cipher_text = base64.b64decode(encrypted_password)
        
        # Extraer IV (primeros 16 bytes) y texto cifrado
        iv = cipher_text[:16]
        cipher_text = cipher_text[16:]
        
        # Crear cifrador AES
        cipher = AES.new(crypto_key.encode('utf-8'), AES.MODE_CBC, iv)
        
        # Descifrar y despadear
        plain_text = unpad(cipher.decrypt(cipher_text), AES.block_size)
        return plain_text.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Error al descifrar la contraseña: {str(e)}")