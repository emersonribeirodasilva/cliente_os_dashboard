import requests

import io
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import init_db, mysql
from flask import current_app



app = Flask(__name__)
app.secret_key = '1111122222'

# Configuração do banco de dados
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'cliente_os'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Inicializa o DB apenas após as configurações estarem definidas
init_db(app)



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
                    (nome_cliente, endereco_cliente, email_cliente, telefone_cliente, cpf_cliente))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('suporte_dashboard'))

    return render_template('cadastro_cliente.html')

# 📌 Cadastro de Equipamento
@app.route('/cadastro_equipamento', methods=['GET', 'POST'])
def cadastro_equipamento():
    cur = mysql.connection.cursor()
    cur.execute("USE cliente_os")

    if request.method == 'POST':
        modelo = request.form.get('modelo')
        marca = request.form.get('marca')
        data_fabricacao = request.form.get('data_fabricacao') or None
        descricao = request.form.get('descricao')
        status = request.form.get('status')  # 'Ativo' ou 'Inativo'

        cur.execute(
            "INSERT INTO equipamentos (modelo, marca, data_fabricacao, descricao, status) VALUES (%s, %s, %s, %s, %s)",
            (modelo, marca, data_fabricacao, descricao, status)
        )
        mysql.connection.commit()
        equipamento_id = cur.lastrowid

        # Se for inativo, registrar automaticamente na tabela de baixa (se não existir)
        if status == 'Inativo':
            cur.execute(
                "SELECT id FROM baixa_equipamentos WHERE equipamento_id = %s",
                (equipamento_id,)
            )
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO baixa_equipamentos (equipamento_id, data_baixa) VALUES (%s, NOW())",
                    (equipamento_id,)
                )
                mysql.connection.commit()

        cur.close()
        flash('Equipamento cadastrado com sucesso.', 'success')
        return redirect(url_for('lista_equipamentos'))

    # GET -> mostra formulário (vazio)
    cur.close()
    return render_template('cadastro_equipamento.html', equipamento=None)

@app.route('/cadastro_os', methods=['GET', 'POST'])
def cadastro_os():
    """
    Rota reforçada com logs e tratamento. Deve salvar:
      - save_os -> insere em ordens_servico
      - save_empresa -> insere em compradores
    """
    # determina aba ativa (default 'os')
    active_tab = request.args.get('tab', 'os')

    if request.method == 'POST':
        # log do form para ajudar debug
        current_app.logger.info("POST /cadastro_os form data: %s", dict(request.form))

        action = request.form.get('action')
        # cursor e uso do DB
        cur = mysql.connection.cursor()
        cur.execute("USE cliente_os")

        try:
            if action == 'save_os':
                cliente_id = request.form.get('cliente_id') or None
                equipamento_id = request.form.get('equipamento_id') or None
                descricao = (request.form.get('descricao') or '').strip()
                status = request.form.get('status') or 'Aberto'

                # validação mínima
                if not cliente_id:
                    flash('Selecione um cliente antes de salvar a O.S.', 'danger')
                    return redirect(url_for('cadastro_os', tab='os'))

                try:
                    cur.execute("""
                        INSERT INTO ordens_servico (cliente_id, equipamento_id, descricao, status)
                        VALUES (%s, %s, %s, %s)
                    """, (cliente_id, equipamento_id, descricao, status))
                    mysql.connection.commit()
                    flash('Ordem de serviço cadastrada com sucesso!', 'success')
                    current_app.logger.info("Ordem inserida: cliente=%s equipamento=%s", cliente_id, equipamento_id)
                except Exception as exc:
                    mysql.connection.rollback()
                    current_app.logger.exception("Erro inserindo ordens_servico: %s", exc)
                    flash('Erro ao cadastrar a O.S. (ver logs).', 'danger')

                return redirect(url_for('cadastro_os', tab='os'))

            elif action == 'save_empresa':
                nome = (request.form.get('nome') or '').strip()
                cnpj = request.form.get('cnpj') or ''
                contato = request.form.get('contato') or ''
                email = request.form.get('email') or ''
                telefone = request.form.get('telefone') or ''
                endereco = request.form.get('endereco') or ''

                if not nome:
                    flash('O campo Nome da Empresa é obrigatório.', 'danger')
                    return redirect(url_for('cadastro_os', tab='empresa'))

                try:
                    cur.execute("""
                        INSERT INTO compradores (nome, cnpj, contato, email, telefone, endereco)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (nome, cnpj, contato, email, telefone, endereco))
                    mysql.connection.commit()
                    flash('Empresa compradora cadastrada com sucesso!', 'success')
                    current_app.logger.info("Comprador inserido: %s", nome)
                except Exception as exc:
                    mysql.connection.rollback()
                    current_app.logger.exception("Erro inserindo compradores: %s", exc)
                    flash('Erro ao cadastrar a empresa (ver logs).', 'danger')

                return redirect(url_for('cadastro_os', tab='empresa'))

            else:
                # ação não reconhecida
                current_app.logger.warning("Ação desconhecida no cadastro_os: %s", action)
                flash('Ação inválida.', 'warning')
                return redirect(url_for('cadastro_os', tab=active_tab))

        finally:
            try:
                cur.close()
            except Exception:
                pass

    # GET: carregar selects
    cur = mysql.connection.cursor()
    cur.execute("USE cliente_os")
    try:
        cur.execute("SELECT id, nome FROM clientes ORDER BY nome")
        clientes = cur.fetchall()

        cur.execute("SELECT id, modelo, marca, status FROM equipamentos ORDER BY id DESC")
        equipamentos = cur.fetchall()
    finally:
        cur.close()

    return render_template(
        'cadastro_os.html',
        clientes=clientes,
        equipamentos=equipamentos,
        active_tab=active_tab
    )
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
    cur.execute("UPDATE ordens_servico SET status = 'Excluído' WHERE id = %s", (os_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('acompanhamento_os'))


@app.route('/finalizar_os/<int:os_id>', methods=['POST'])
def finalizar_os(os_id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE ordens_servico SET status = 'Finalizado' WHERE id = %s", (os_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('acompanhamento_os'))


@app.route('/estoque_baixa')
def estoque_baixa():
    cur = mysql.connection.cursor()
    cur.execute("USE cliente_os")
    cur.execute("""
        SELECT b.id AS baixa_id, b.equipamento_id, b.data_baixa,
               e.modelo, e.marca, e.descricao, e.status,
               TIMESTAMPDIFF(YEAR, e.data_fabricacao, CURDATE()) AS idade
        FROM baixa_equipamentos b
        JOIN equipamentos e ON e.id = b.equipamento_id
        ORDER BY b.data_baixa DESC
    """)
    baixas = cur.fetchall()
    cur.close()
    return render_template('estoque_baixa.html', baixas=baixas)

@app.route('/lista_equipamentos')
def lista_equipamentos():
    cur = mysql.connection.cursor()
    cur.execute("USE cliente_os")
    cur.execute("""
        SELECT id, modelo, marca, data_fabricacao,
               descricao, status,
               TIMESTAMPDIFF(YEAR, data_fabricacao, CURDATE()) AS idade
        FROM equipamentos
        ORDER BY id DESC
    """)
    equipamentos = cur.fetchall()

    # Formata data_fabricacao para YYYY-MM-DD (compatível com <input type="date">)
    for e in equipamentos:
        df = e.get('data_fabricacao')
        if df is not None:
            try:
                e['data_fabricacao'] = df.strftime('%Y-%m-%d')
            except Exception:
                # caso venha como string, tenta deixar como está
                e['data_fabricacao'] = str(df)

    cur.close()
    return render_template('lista_equipamentos.html', equipamentos=equipamentos)

@app.route('/editar_equipamento/<int:equip_id>', methods=['GET', 'POST'])
def editar_equipamento(equip_id):
    cur = mysql.connection.cursor()
    cur.execute("USE cliente_os")

    if request.method == 'POST':
        modelo = request.form.get('modelo')
        marca = request.form.get('marca')
        data_fabricacao = request.form.get('data_fabricacao') or None
        descricao = request.form.get('descricao')
        status = request.form.get('status')

        cur.execute("""
            UPDATE equipamentos
            SET modelo=%s, marca=%s, data_fabricacao=%s, descricao=%s, status=%s
            WHERE id=%s
        """, (modelo, marca, data_fabricacao, descricao, status, equip_id))
        mysql.connection.commit()

        # se passou a ser Inativo, garante registro em baixa
        if status == 'Inativo':
            cur.execute("SELECT id FROM baixa_equipamentos WHERE equipamento_id = %s", (equip_id,))
            if not cur.fetchone():
                cur.execute("INSERT INTO baixa_equipamentos (equipamento_id, data_baixa) VALUES (%s, NOW())", (equip_id,))
                mysql.connection.commit()

        cur.close()
        flash('Equipamento atualizado.', 'success')
        return redirect(url_for('lista_equipamentos'))

    # GET -> carregar equipamento e calcular idade (sem usar DATE_FORMAT no SQL)
    cur.execute("""
        SELECT id, modelo, marca, data_fabricacao,
               descricao, status,
               TIMESTAMPDIFF(YEAR, data_fabricacao, CURDATE()) AS idade
        FROM equipamentos
        WHERE id = %s
    """, (equip_id,))
    equipamento = cur.fetchone()

    # formata data para o input date
    if equipamento and equipamento.get('data_fabricacao') is not None:
        try:
            equipamento['data_fabricacao'] = equipamento['data_fabricacao'].strftime('%Y-%m-%d')
        except Exception:
            equipamento['data_fabricacao'] = str(equipamento['data_fabricacao'])

    cur.close()

    if not equipamento:
        flash('Equipamento não encontrado.', 'danger')
        return redirect(url_for('lista_equipamentos'))

    return render_template('cadastro_equipamento.html', equipamento=equipamento)

@app.route('/compradores')
def compradores():
    cur = mysql.connection.cursor()
    cur.execute("USE cliente_os")
    cur.execute("SELECT id, nome, cnpj, contato, email, telefone, endereco, created_at FROM compradores ORDER BY created_at DESC")
    compradores = cur.fetchall()
    cur.close()
    return render_template('compradores_list.html', compradores=compradores)

@app.route('/editar_comprador/<int:comprador_id>', methods=['GET', 'POST'])
def editar_comprador(comprador_id):
    cur = mysql.connection.cursor()
    cur.execute("USE cliente_os")

    if request.method == 'POST':
        nome = request.form.get('nome') or ''
        cnpj = request.form.get('cnpj') or ''
        contato = request.form.get('contato') or ''
        email = request.form.get('email') or ''
        telefone = request.form.get('telefone') or ''
        endereco = request.form.get('endereco') or ''

        cur.execute("""
            UPDATE compradores
            SET nome=%s, cnpj=%s, contato=%s, email=%s, telefone=%s, endereco=%s
            WHERE id=%s
        """, (nome, cnpj, contato, email, telefone, endereco, comprador_id))
        mysql.connection.commit()
        cur.close()
        flash('Comprador atualizado.', 'success')
        return redirect(url_for('compradores'))

    # GET
    cur.execute("SELECT id, nome, cnpj, contato, email, telefone, endereco FROM compradores WHERE id = %s", (comprador_id,))
    comprador = cur.fetchone()
    cur.close()

    if not comprador:
        flash('Comprador não encontrado.', 'danger')
        return redirect(url_for('compradores'))

    return render_template('editar_comprador.html', comprador=comprador)

@app.route('/relatorio_os')
def relatorio_os():
    cur = mysql.connection.cursor()
    cur.execute("USE cliente_os")

    query = """
        SELECT o.id, o.descricao, o.status, o.data_criacao,
               c.nome AS cliente_nome,
               e.modelo AS equipamento_modelo
        FROM ordens_servico o
        LEFT JOIN clientes c ON o.cliente_id = c.id
        LEFT JOIN equipamentos e ON o.equipamento_id = e.id
        ORDER BY o.data_criacao DESC
        LIMIT 500
    """

    try:
        cur.execute(query)
    except Exception as exc:
        # tenta corrigir schema se coluna inexistente (erro 1054)
        msg = str(exc)
        if 'Unknown column' in msg or '1054' in msg:
            try:
                # tenta adicionar a coluna; MySQL 8 aceita IF NOT EXISTS
                cur.execute("ALTER TABLE ordens_servico ADD COLUMN IF NOT EXISTS data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP")
            except Exception:
                # fallback para versões sem IF NOT EXISTS (silencia erro se já existir)
                try:
                    cur.execute("ALTER TABLE ordens_servico ADD COLUMN data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP")
                except Exception:
                    pass
            # reexecuta a query depois da correção
            cur.execute(query)
        else:
            cur.close()
            raise

    rows = cur.fetchall()
    cur.close()
    return render_template('relatorio_os.html', rows=rows)

@app.route('/relatorio_os/pdf')
def relatorio_os_pdf():
    cur = mysql.connection.cursor()
    cur.execute("USE cliente_os")
    cur.execute("""
        SELECT o.id, o.descricao, o.status, o.data_criacao,
               c.nome AS cliente_nome,
               e.modelo AS equipamento_modelo
        FROM ordens_servico o
        LEFT JOIN clientes c ON o.cliente_id = c.id
        LEFT JOIN equipamentos e ON o.equipamento_id = e.id
        ORDER BY o.data_criacao DESC
        LIMIT 1000
    """)
    rows = cur.fetchall()
    cur.close()

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        flash('Dependência reportlab não instalada. Execute: pip install reportlab', 'danger')
        return redirect(url_for('relatorio_os'))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Relatório de Ordens de Serviço", styles['Title']))
    story.append(Spacer(1, 12))

    data = [['ID', 'Cliente', 'Equipamento', 'Status', 'Data', 'Descrição']]
    for r in rows:
        data.append([
            str(r.get('id') or ''),
            r.get('cliente_nome') or '-',
            r.get('equipamento_modelo') or '-',
            r.get('status') or '-',
            str(r.get('data_criacao') or ''),
            (r.get('descricao') or '')[:120]  # corta para caber no PDF
        ])

    table = Table(data, colWidths=[36, 110, 90, 70, 80, 150])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.gray),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
    ]))
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name='relatorio_os.pdf')


@app.route('/relatorio_baixa')
def relatorio_baixa():
    cur = mysql.connection.cursor()
    cur.execute("USE cliente_os")
    cur.execute("""
        SELECT b.id, b.equipamento_id, b.data_baixa, b.motivo,
               e.modelo, e.marca
        FROM baixa_equipamentos b
        LEFT JOIN equipamentos e ON e.id = b.equipamento_id
        ORDER BY b.data_baixa DESC
        LIMIT 500
    """)
    rows = cur.fetchall()
    cur.close()
    return render_template('relatorio_baixa.html', rows=rows)

@app.route('/relatorio_baixa/pdf')
def relatorio_baixa_pdf():
    cur = mysql.connection.cursor()
    cur.execute("USE cliente_os")
    cur.execute("""
        SELECT b.id, b.equipamento_id, b.data_baixa, b.motivo,
               e.modelo, e.marca
        FROM baixa_equipamentos b
        LEFT JOIN equipamentos e ON e.id = b.equipamento_id
        ORDER BY b.data_baixa DESC
        LIMIT 1000
    """)
    rows = cur.fetchall()
    cur.close()

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        flash('Dependência reportlab não instalada. Execute: pip install reportlab', 'danger')
        return redirect(url_for('relatorio_baixa'))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Relatório - Estoque (Baixa)", styles['Title']))
    story.append(Spacer(1, 12))

    data = [['ID', 'ID Equip.', 'Modelo', 'Marca', 'Data Baixa', 'Motivo']]
    for r in rows:
        data.append([
            str(r.get('id') or ''),
            str(r.get('equipamento_id') or ''),
            r.get('modelo') or '-',
            r.get('marca') or '-',
            str(r.get('data_baixa') or ''),
            (r.get('motivo') or '')[:180]
        ])

    table = Table(data, colWidths=[36, 56, 120, 100, 90, 150])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.gray),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
    ]))
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name='relatorio_baixa.pdf')


@app.route('/relatorio_os/<int:os_id>')
def relatorio_os_individual(os_id):
    cur = mysql.connection.cursor()
    cur.execute("USE cliente_os")

    # detectar coluna de contato existente na tabela clientes
    cur.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'clientes'
    """)
    cols = [row['COLUMN_NAME'] for row in cur.fetchall()]

    if 'contato' in cols:
        contato_expr = 'c.contato AS cliente_contato'
    elif 'telefone' in cols:
        contato_expr = 'c.telefone AS cliente_contato'
    else:
        contato_expr = "'' AS cliente_contato"

    query = f"""
        SELECT o.*, c.nome AS cliente_nome, {contato_expr},
               e.modelo, e.marca
        FROM ordens_servico o
        LEFT JOIN clientes c ON o.cliente_id = c.id
        LEFT JOIN equipamentos e ON o.equipamento_id = e.id
        WHERE o.id = %s
        LIMIT 1
    """
    cur.execute(query, (os_id,))
    os_row = cur.fetchone()
    cur.close()
    if not os_row:
        flash('Ordem de Serviço não encontrada.', 'danger')
        return redirect(url_for('relatorio_os'))

    company = {
        'name': app.config.get('COMPANY_NAME', 'Minha Empresa Prestadora de Serviço'),
        'address': app.config.get('COMPANY_ADDRESS', 'Endereço da Empresa'),
        'phone': app.config.get('COMPANY_PHONE', '(00) 0000-0000'),
        'email': app.config.get('COMPANY_EMAIL', 'contato@empresa.com')
    }
    return render_template('relatorio_os_detail.html', os=os_row, company=company)


@app.route('/relatorio_os/<int:os_id>/pdf')
def relatorio_os_individual_pdf(os_id):
    cur = mysql.connection.cursor()
    cur.execute("USE cliente_os")

    # detectar coluna de contato existente
    cur.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'clientes'
    """)
    cols = [row['COLUMN_NAME'] for row in cur.fetchall()]

    if 'contato' in cols:
        contato_expr = 'c.contato AS cliente_contato'
    elif 'telefone' in cols:
        contato_expr = 'c.telefone AS cliente_contato'
    else:
        contato_expr = "'' AS cliente_contato"

    query = f"""
        SELECT o.*, c.nome AS cliente_nome, {contato_expr},
               e.modelo, e.marca
        FROM ordens_servico o
        LEFT JOIN clientes c ON o.cliente_id = c.id
        LEFT JOIN equipamentos e ON o.equipamento_id = e.id
        WHERE o.id = %s
        LIMIT 1
    """
    cur.execute(query, (os_id,))
    r = cur.fetchone()
    cur.close()

    if not r:
        flash('Ordem de Serviço não encontrada.', 'danger')
        return redirect(url_for('relatorio_os'))

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        flash('reportlab não instalado. Execute: pip install reportlab', 'danger')
        return redirect(url_for('relatorio_os_individual', os_id=os_id))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    # cabeçalho com informações da empresa
    company_name = app.config.get('COMPANY_NAME', 'Minha Empresa Prestadora de Serviço')
    company_address = app.config.get('COMPANY_ADDRESS', 'Endereço da Empresa')
    company_phone = app.config.get('COMPANY_PHONE', '(00) 0000-0000')
    company_email = app.config.get('COMPANY_EMAIL', 'contato@empresa.com')

    story.append(Paragraph(company_name, styles['Title']))
    story.append(Paragraph(company_address, styles['Normal']))
    story.append(Paragraph(f"Tel: {company_phone} • {company_email}", styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"Ordem de Serviço #{r.get('id')}", styles['Heading2']))
    story.append(Paragraph(f"Data: {r.get('data_criacao')}", styles['Normal']))
    story.append(Spacer(1, 8))

    data = [
        ['Cliente', r.get('cliente_nome') or '-'],
        ['Contato', r.get('cliente_contato') or '-'],
        ['Equipamento', (r.get('modelo') or '-') + ' / ' + (r.get('marca') or '-')],
        ['Status', r.get('status') or '-'],
        ['Descrição', r.get('descricao') or '-']
    ]
    table = Table(data, colWidths=[100, 400])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f6f6f6')),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.gray),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
    ]))
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'os_{r.get("id")}.pdf')

if __name__ == '__main__':
    app.run(debug=True)