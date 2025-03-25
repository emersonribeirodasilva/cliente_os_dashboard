from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import init_db, mysql

app = Flask(__name__)
app.secret_key = '1111122222'  # Chave segura para sessão

init_db(app)

# Configurações do banco de dados
app.config['MYSQL_HOST'] = '127.0.0.1'  # Ou o IP do seu servidor MySQL
app.config['MYSQL_USER'] = 'root'  # Seu usuário MySQL
app.config['MYSQL_PASSWORD'] = ''  # Sua senha do MySQL, se houver
app.config['MYSQL_DB'] = 'cliente_os'  # Nome do seu banco de dados
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # Para retornar resultados como dicionário

# 🔐 Tela de Login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        tipo = request.form['tipo']  # Novo campo para selecionar o perfil

        cur = mysql.connection.cursor()
        cur.execute("USE cliente_os")  # 🔥 Adicionando isso antes da primeira query
        cur.execute("SELECT id, username, password, tipo FROM usuarios WHERE username = %s", [username])       
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user['password'], password):  # Corrigido para DictCursor
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['tipo'] = user['tipo']

            if tipo == "cliente":  # Verificação para o cliente
                return redirect(url_for('cadastro_os'))  # Redireciona para cadastro_os
            elif tipo == 'suporte':  # Verificação para o suporte
                return redirect(url_for('suporte_dashboard'))  # Redireciona para suporte_dashboard
        else:
            error = "Usuário ou senha inválidos."
            return render_template('login.html', error=error)

    return render_template('login.html')

# 📌 Cadastro de Usuário
@app.route('/cadastro_usuario', methods=['GET', 'POST'])
def cadastro_usuario():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')  # Correção
        tipo = request.form['tipo']

        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM usuarios WHERE username = %s", [username])
        existing_user = cur.fetchone()

        if existing_user:
            return render_template('cadastro_usuario.html', error="Usuário já cadastrado!")

        cur.execute("INSERT INTO usuarios (username, password, tipo) VALUES (%s, %s, %s)", 
                    (username, password, tipo))
        mysql.connection.commit()
        cur.close()

        session['username'] = username
        session['tipo'] = tipo

        if tipo == "cliente":
            return redirect(url_for('cadastro_os'))
        else:
            return redirect(url_for('suporte_dashboard'))

    return render_template('cadastro_usuario.html')

# 📌 Cadastro de Cliente
@app.route('/cadastro_cliente', methods=['GET', 'POST'])
def cadastro_cliente():
    if request.method == 'POST':
        nome_cliente = request.form['nome_cliente']
        endereco_cliente = request.form['endereco_cliente']
        email_cliente = request.form['email_cliente']
        telefone_cliente = request.form['telefone_cliente']
        cpf_cliente = request.form['cpf_cliente']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO clientes (nome, endereco, email, telefone,cpf) VALUES (%s, %s, %s, %s)", 
                    (nome_cliente, endereco_cliente, email_cliente, telefone_cliente,cpf_cliente))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('suporte_dashboard'))

    return render_template('cadastro_cliente.html')

# 📌 Cadastro de Equipamento
@app.route('/cadastro_equipamento', methods=['GET', 'POST'])
def cadastro_equipamento():
    if request.method == 'POST':
        nome_equipamento = request.form['nome']
        modelo_equipamento = request.form['modelo']
        serie_equipamento = request.form['serie']
        cliente_id = request.form['cliente_id']  # Relacionamento com cliente

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO equipamentos (nome, modelo, serie, cliente_id) VALUES (%s, %s, %s, %s)", 
                    (nome_equipamento, modelo_equipamento, serie_equipamento, cliente_id))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('suporte_dashboard'))

    return render_template('cadastro_equipamento.html')

# 📌 Cadastro de Ordem de Serviço (O.S.)
@app.route('/cadastro_os', methods=['GET', 'POST'])
def cadastro_os():
    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        equipamento_id = request.form['equipamento_id']
        descricao = request.form['descricao']
        status = request.form['status']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO ordens_servico (cliente_id, equipamento_id, descricao, status) VALUES (%s, %s, %s, %s)", 
                    (cliente_id, equipamento_id, descricao, status))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('suporte_dashboard'))

    return render_template('cadastro_os.html')

# 🔍 Outras rotas
@app.route('/suporte_dashboard')
def suporte_dashboard():
    return render_template('suporte_dashboard.html')  # Tela do suporte com botões

@app.route('/acompanhamento_os')
def acompanhamento_os():
    return render_template('acompanhamento_os.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
