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

API_KEY = "9e17be5dd05622ea023dd42a7c93b64a"

@app.route('/weather/<int:city_id>', methods=['GET'])
def get_weather(city_id):
    API_KEY = "9e17be5dd05622ea023dd42a7c93b64a"
    url = f"http://api.openweathermap.org/data/2.5/forecast?id={city_id}&appid={API_KEY}&units=metric&lang=pt"

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
            "city_name": data["city"]["name"]  # Adicionando o nome da cidade
        }

        return weather_data  # Retorna os dados diretamente (não jsonify)

    except requests.exceptions.RequestException as e:
        print("Erro na requisição HTTP:", e)
        return {"error": "Erro ao obter dados do clima"}, 500
    except Exception as e:
        print("Erro inesperado:", e)
        return {"error": "Erro inesperado"}, 500

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    city_id = "5128581"  # ID padrão (Nova York)
    
    if request.method == 'POST':  # Verifica se o formulário foi enviado
        city_id = request.form.get('city_id', city_id)  # Pega o ID do formulário, se existir

    weather_data = get_weather(city_id)  # Obtém os dados do clima city_id para a função

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
    os_status = [25, 15, 10]  # Em andamento, Finalizado, Abertos

    # Obtendo os dados do clima
    
    # Exemplo de ordens de serviço recentes
    ordens_servico = [
        {"id": 1, "cliente": "Cliente 1", "status": "Em andamento"},
        {"id": 2, "cliente": "Cliente 2", "status": "Finalizado"},
        {"id": 3, "cliente": "Cliente 3", "status": "Abertos"},
    ]

    return render_template('dashboard.html', 
                           total_equipamentos=total_equipamentos,
                           total_os=total_os,
                           os_status=os_status,
                           total_clientes= total_clientes,
                           weather_data=weather_data,  # Passando diretamente os dados do clima
                           ordens_servico=ordens_servico)



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



if __name__ == '__main__':
    app.run(debug=True)