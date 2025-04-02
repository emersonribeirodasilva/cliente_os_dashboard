'''from flask import Flask
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash

app = Flask(__name__)

# Configuração do MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'sua_senha'  # Altere para a senha do seu MySQL
app.config['MYSQL_DB'] = 'cliente_os'

# Inicializar o banco de dados
mysql = MySQL(app)

# Função para criar um novo usuário com senha hashada
def create_user():
    # Gerar a senha hashada
    hashed_password = generate_password_hash('senha_secreta', method='sha256')

    # Inserir o novo usuário no banco de dados
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO usuarios (username, password) VALUES (%s, %s)", ('novo_usuario', hashed_password))
    mysql.connection.commit()

    print("Usuário criado com sucesso!")

if __name__ == '__main__':
    create_user()
'''