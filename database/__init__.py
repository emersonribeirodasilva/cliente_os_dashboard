from flask import Flask
from database.db import init_db

app = Flask(__name__)

# 🔥 Certifique-se de que o nome do banco está definido
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'cliente_os'  # ✅ Nome do banco está aqui
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

init_db(app)
