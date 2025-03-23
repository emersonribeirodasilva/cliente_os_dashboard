from flask_mysqldb import MySQL

mysql = MySQL()

def init_db(app):
    mysql.init_app(app)

    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute("SELECT DATABASE()")  # 🔍 Testar conexão com o banco
        db_selected = cur.fetchone()
        print("Banco de dados conectado:", db_selected)
        cur.close()
