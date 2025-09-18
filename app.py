import requests
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import init_db, mysql


app = Flask(__name__)
app.secret_key = '1111122222'

init_db(app)

# Configuração do banco de dados
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'cliente_os'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'



@app.route('/weather/<city_name>', methods=['GET'])
def get_weather(city_name):
    API_KEY = "9e17be5dd05622ea023dd42a7c93b64a"
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city_name}&appid={API_KEY}&units=metric&lang=pt"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Levanta erro HTTP se houver falha
        data = response.json()

        if "list" not in data or not data["list"]:
            return {"error": "Dados do clima não disponíveis"}, 404

        weather_data = {
            "description": data["list"][0]["weather"][0]["description"],
            "icon": data["list"][0]["weather"][0]["icon"],
            "temperature": data["list"][0]["main"]["temp"],
            "windspeed": data["list"][0]["wind"]["speed"],
            "time": data["list"][0]["dt_txt"],
            "city_name": data["city"]["name"]
        }

        return weather_data

    except requests.exceptions.RequestException as e:
        print("Erro na requisição HTTP:", e)
        return {"error": "Erro ao obter dados do clima"}, 500
    except Exception as e:
        print("Erro inesperado:", e)
        return {"error": "Erro inesperado"}, 500

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    city_name = "Sao Paulo"  # ID padrão (Nova York)
    
    if request.method == 'POST':  # Verifica se o formulário foi enviado
        city_name = request.form.get('city_id', city_name)  # Pega o ID do formulário, se existir

    weather_data = get_weather(city_name)  # Obtém os dados do clima city_name para a função

    cur = mysql.connection.cursor()  # Retorna os resultados como dicionários
    cur.execute("USE cliente_os")

    # Obter o total de clientes
    cur.execute('SELECT COUNT(*) AS total FROM clientes')  
    total_clientes = cur.fetchone()["total"]  

    # Obter o total de equipamentos
    cur.execute('SELECT COUNT(*) AS total FROM equipamentos')
    total_equipamentos = cur.fetchone()["total"]  

    # Obter o total de ordens de serviço
    cur.execute('SELECT COUNT(*) AS total FROM ordens_servico')
    total_os = cur.fetchone()["total"]  
   



   # cur.execute('SELECT COUNT(*) AS total FROM ordens_servico')
    #total_os = cur.fetchone()["total"] 

    # Buscar os status das OS
    cur.execute("SELECT status FROM ordens_servico")
    status_list = cur.fetchall()  # Lista de tuplas: [{'status': 'Aberto'}, ...]

    # Contar os status
    status_counts = {"Aberto": 0, "Em andamento": 0, "Finalizado": 0}
    for row in status_list:
        status = row['status']
        if status in status_counts:
            status_counts[status] += 1

    os_status = [
        {"label": "Aberto", "value": status_counts["Aberto"]},
        {"label": "Em andamento", "value": status_counts["Em andamento"]},
        {"label": "Finalizado", "value": status_counts["Finalizado"]}
    ]

   


    return render_template('dashboard.html', 
                           total_equipamentos=total_equipamentos,
                           total_os=total_os,
                           os_status=os_status,
                           total_clientes= total_clientes,
                           weather_data=weather_data,  # Passando diretamente os dados do clima
                           )



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
        cur.execute("INSERT INTO clientes (nome, endereco, email, telefone,cpf) VALUES (%s, %s, %s, %s,%s)", 
                    (nome_cliente, endereco_cliente, email_cliente, telefone_cliente,cpf_cliente))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('suporte_dashboard'))

    return render_template('cadastro_cliente.html')

# 📌 Cadastro de Equipamento
@app.route('/cadastro_equipamento', methods=['GET', 'POST'])
def cadastro_equipamento():
    if request.method == 'POST':
        modelo_equipamento = request.form['modelo']
        descricao_equipamento = request.form['descricao']       
        marca_equipamento = request.form['marca']
        data_fabricacao_eq = request.form['data_fabricacao'] 
        status_equipamento = request.form['status']
       

        cur = mysql.connection.cursor()
        cur.execute(
             "INSERT INTO equipamentos (modelo, descricao, marca, data_fabricacao, status) VALUES (%s, %s, %s, %s, %s)", 
             (modelo_equipamento, descricao_equipamento, marca_equipamento, data_fabricacao_eq, status_equipamento)
              )
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

@app.route('/acompanhamento_os', methods=['GET'])
def acompanhamento_os():
    # Criando o cursor
    cur = mysql.connection.cursor()

    # Consultando as ordens de serviço
    cur.execute("SELECT id, cliente_id, equipamento_id,descricao,status FROM ordens_servico")  # Remover a vírgula extra após 'nome'
    ordens_servico = cur.fetchall()

    # Fechando o cursor
    cur.close()

    # Passando os dados para o template HTML
    return render_template('acompanhamento_os.html', ordens_servico=ordens_servico)



@app.route('/acompanhamento_cliente', methods=['GET'])
def acompanhamento_cliente():
    # Criando o cursor
    cur = mysql.connection.cursor()

    # Consultando as ordens de serviço
    cur.execute("SELECT id, nome, email,telefone,endereco,cpf FROM clientes")  # Remover a vírgula extra após 'nome'
    clientes = cur.fetchall()

    # Fechando o cursor
    cur.close()

    # Passando os dados para o template HTML
    return render_template('acompanhamento_cliente.html', clientes=clientes)
# Editar cliente (carrega formulário de edição)
@app.route('/editar_cliente/<int:cliente_id>', methods=['GET', 'POST'])
def editar_cliente(cliente_id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        endereco = request.form['endereco']
        cpf = request.form['cpf']

        cur.execute("""
            UPDATE clientes 
            SET nome=%s, email=%s, telefone=%s, endereco=%s, cpf=%s 
            WHERE id=%s
        """, (nome, email, telefone, endereco, cpf, cliente_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('acompanhamento_cliente'))

    # Busca os dados do cliente para preencher o formulário
    cur.execute("SELECT * FROM clientes WHERE id = %s", (cliente_id,))
    cliente = cur.fetchone()
    cur.close()
    return render_template('editar_cliente.html', cliente=cliente)

# Desativar cliente
@app.route('/desativar_cliente/<int:cliente_id>', methods=['POST'])
def desativar_cliente(cliente_id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE clientes SET ativo = FALSE WHERE id = %s", (cliente_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('acompanhamento_cliente'))

# Ativar cliente
@app.route('/ativar_cliente/<int:cliente_id>', methods=['POST'])
def ativar_cliente(cliente_id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE clientes SET ativo = TRUE WHERE id = %s", (cliente_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('acompanhamento_cliente'))

@app.route('/editar_os/<int:os_id>', methods=['GET', 'POST'])
def editar_os(os_id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        equipamento_id = request.form['equipamento_id']
        descricao = request.form['descricao']
        status = request.form['status']

        cur.execute("""
            UPDATE ordens_servico 
            SET cliente_id=%s, equipamento_id=%s, descricao=%s, status=%s
            WHERE id=%s
        """, (cliente_id, equipamento_id, descricao, status, os_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('acompanhamento_os'))

    # Busca os dados da O.S. para preencher o formulário
    cur.execute("SELECT * FROM ordens_servico WHERE id = %s", (os_id,))
    ordem = cur.fetchone()
    cur.close()

    return render_template('editar_os.html', ordem=ordem)


@app.route('/excluir_os/<int:os_id>', methods=['POST'])
def excluir_os(os_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM ordens_servico WHERE id = %s", (os_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('acompanhamento_os'))


@app.route('/finalizar_os/<int:os_id>', methods=['POST'])
def finalizar_os(os_id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE ordens_servico SET status = 'Finalizada' WHERE id = %s", (os_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('acompanhamento_os'))





if __name__ == '__main__':
    app.run(debug=True)