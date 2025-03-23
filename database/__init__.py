from flask import Flask
from database.db import init_db

app = Flask(__name__)

# Configuração do banco de dados
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "cliente_os"

# Inicializar banco de dados
init_db(app)
