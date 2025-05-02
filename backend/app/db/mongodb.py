# archivo: db/mongodb.py

from pymongo import MongoClient

cliente = MongoClient("mongodb://localhost:27017")
bd = cliente["PlataformaConLangChainParaRecomendarVideojuegos"]
coleccionUsuarios = bd["Usuarios"]

