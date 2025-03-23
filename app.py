from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import init_db, mysql

app = Flask(__name__)
app.secret_key = '1111122222'  

init_db(app)


# Tela de Login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, username, password, tipo FROM usuarios WHERE username = %s", [username])
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['tipo'] = user[3]  # Define o tipo de usuário na sessão

            # Redirecionamento conforme o tipo de usuário
            if user[3] == "cliente":
                return redirect(url_for('abertura_os'))
            else:
                return redirect(url_for('dashboard'))

        else:
            error = "Usuário ou senha inválidos."
            return render_template('login.html', error=error)

    return render_template('login.html')

# Cadastro de Usuário
@app.route('/cadastro_usuario', methods=['GET', 'POST'])
def cadastro_usuario():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        tipo = request.form['tipo']  # Cliente ou Prestador de Serviço

        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM usuarios WHERE username = %s", [username])
        existing_user = cur.fetchone()

        if existing_user:
            error = "Usuário já cadastrado!"
            return render_template('cadastro_usuario.html', error=error)

        cur.execute("INSERT INTO usuarios (username, password, tipo) VALUES (%s, %s, %s)", 
                    (username, password, tipo))
        mysql.connection.commit()
        cur.close()

        session['username'] = username
        session['tipo'] = tipo

        # Redirecionamento conforme o tipo de usuário
        if tipo == "cliente":
            return redirect(url_for('abertura_os'))
        else:
            return redirect(url_for('dashboard'))

    return render_template('cadastro_usuario.html')

# Rotas para as páginas
@app.route('/abertura_os')
def abertura_os():
    return render_template('abertura_os.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/cadastro_os')
def cadastro_os():
    return render_template('cadastro_os.html')

@app.route('/cadastro_equipamento')
def cadastro_equipamento():
    return render_template('cadastro_equipamento.html')

@app.route('/acompanhamento_os')
def acompanhamento_os():
    return render_template('acompanhamento_os.html')

if __name__ == '__main__':
    app.run(debug=True)
