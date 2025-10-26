# 02_sistema_python/main.py

from flask import Flask, render_template_string, request, redirect, url_for, session
from markupsafe import escape
import requests 
import os
from dotenv import load_dotenv
import random

# --- Configurações Iniciais ---
load_dotenv()
API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:3000/api") 

app = Flask(__name__)
# A chave secreta é essencial para usar a sessão (session) de forma segura.
app.secret_key = os.getenv("FLASK_SECRET_KEY", "chave_de_dev_insegura_use_o_env") 

# Chaves de sessão
SESSION_KEY_TOKEN = 'user_token'
SESSION_KEY_TYPE = 'user_type'

# --------------------------------------------------------------------------------------
# FUNÇÕES DE RENDERIZAÇÃO E BASE HTML
# --------------------------------------------------------------------------------------

# Função de Layout Principal (Base com Sidebar)
def render_base(content_html, page_title="Sistema Acadêmico PIM"):
    # IMPORTANTE: Você deve colocar seu código HTML/CSS completo (com a sidebar) aqui
    # Para o propósito de teste, usaremos um layout simples.
    base_html = f'''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>{page_title}</title>
        <style>
            :root {{ --accent: #1b55f8; --error: #d32f2f; }}
            body {{ font-family: Arial, sans-serif; margin-left: 200px; padding: 20px; }}
            .sidebar {{ position: fixed; left: 0; width: 180px; height: 100vh; background: var(--accent); color: white; padding-top: 20px; }}
            .sidebar a {{ display: block; padding: 10px; color: white; text-decoration: none; }}
            .login-card {{ max-width: 400px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
            .error-message {{ color: var(--error); text-align: center; margin-bottom: 15px; }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h2>Menu Principal</h2>
            <a href="{url_for('dashboard')}">Dashboard</a>
            <a href="{url_for('logout')}">Sair</a>
            <a href="{url_for('boletim')}">Boletim</a>
        </div>
        <div class="main-content">
            {content_html}
        </div>
    </body>
    </html>
    '''
    return render_template_string(base_html, page_title=page_title)

# 02_sistema_python/main.py

# ... (após def render_base(...) e suas funções auxiliares, mas antes de @app.route('/login'))

def render_login_form(error_message=None):
    # Conteúdo do seu formulário de login (sem a sidebar)
    error_html = f'<p class="error-message" style="color:#d32f2f;text-align:center;font-size:0.9rem;">{escape(error_message)}</p>' if error_message else ''
    
    form_html = f'''
    <div class="login-card" style="max-width: 420px; margin: auto; padding: 28px; border: 1px solid #ddd; border-radius: 12px;">
        <div style="text-align:center;"><h2>Login</h2></div>
        {error_html}
        <form method="POST">
            <label for="usuario">E-mail:</label>
            <input id="usuario" type="text" name="usuario" required style="width: 100%; margin-bottom: 10px;">
            <label for="senha">Senha:</label>
            <input id="senha" type="password" name="senha" required style="width: 100%; margin-bottom: 15px;">
            <button type="submit" style="background: #1b55f8; color: white; padding: 10px; border: none; width: 100%;">Entrar</button>
        </form>
    </div>
    '''
    # Note que esta função DEVE chamar render_base para envolver o formulário no layout de página completa
    return render_base(form_html, "Página de Login")

def require_login(view_func):
    """Decorator para proteger rotas."""
    def wrapper(*args, **kwargs):
        # Verifica se o token de sessão existe
        if SESSION_KEY_TOKEN not in session:
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    # Garante que o Flask registra a função com o nome correto
    wrapper.__name__ = view_func.__name__ 
    return wrapper

def render_notas_form(turmas):
    """Gera o HTML do formulário de lançamento de notas."""
    
    # ⚠️ Simplificação: Aqui o professor inseriria o ID do Aluno e da Disciplina.
    # Em um projeto avançado, você usaria AJAX ou rotas separadas para carregar listas dropdown.
    
    form_html = f"""
    <div style="background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-top: 40px;">
        <h2>Lançamento de Notas</h2>
        <form method="POST" action="{url_for('painel_professor', action='lancar_nota')}">
            
            <label for="aluno_id" style="display:block; margin-top: 10px;">ID do Aluno:</label>
            <input type="number" id="aluno_id" name="aluno_id" required style="width: 100%; padding: 8px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px;">

            <label for="disciplina_id" style="display:block;">ID da Disciplina:</label>
            <input type="number" id="disciplina_id" name="disciplina_id" required style="width: 100%; padding: 8px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px;">
            
            <label for="valor_nota" style="display:block;">Nota (0.0 a 10.0):</label>
            <input type="number" step="0.1" id="valor_nota" name="valor_nota" required style="width: 100%; padding: 8px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 4px;">
            
            <button type="submit" style="background: var(--accent); color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer;">
                Lançar Nota
            </button>
        </form>
    </div>
    """
    return form_html

def render_professor_content(user_type, turmas, message, message_class, notas_form_result=None):
    """Gera o HTML do painel, focando em gestão e ações."""
    
    # ⚠️ O CSS da classe 'error' e 'success' deve estar definido na sua render_base
    feedback_html = f'<div class="{message_class}" style="padding: 10px; margin-bottom: 20px;">{escape(message)}</div>' if message else ''
    
    notas_feedback = ""
    if notas_form_result:
         notas_feedback = f'<div class="{notas_form_result["cls"]}" style="padding: 10px; border-radius: 5px; margin-bottom: 20px; border: 1px solid;">Resultado Lançamento: {notas_form_result["msg"]}</div>'


    # --- Agrupa turmas por turma_id para apresentar um menu com disciplinas dentro de cada turma ---
    grouped = {}
    if turmas:
        for t in turmas:
            turma_id = t.get('turma_id')
            nome_turma = escape(t.get('nome_turma', 'N/A'))
            disc = {
                'disciplina_id': t.get('disciplina_id'),
                'nome_disciplina': t.get('nome_disciplina', 'N/A')
            }
            if turma_id not in grouped:
                grouped[turma_id] = {'nome_turma': nome_turma, 'disciplinas': [disc]}
            else:
                grouped[turma_id]['disciplinas'].append(disc)

    # --- HTML do menu (colapsável) ---
    menu_html = '<h2 style="color: #333; margin-top: 25px;">Minhas Turmas</h2>'
    if not grouped:
        menu_html += '<p>Nenhuma turma atribuída a você.</p>'
    else:
        menu_html += '<div class="turmas-menu" style="margin-bottom:20px;">'
        for turma_id, info in grouped.items():
            disc_list_id = f"turma_{turma_id}_discs"
            menu_html += f"""
            <div style='border:1px solid #eee; margin-bottom:8px; border-radius:6px; overflow:hidden;'>
                <button onclick="(function(id){{var el=document.getElementById(id); el.style.display = el.style.display==='none' ? 'block' : 'none';}})('{disc_list_id}')"
                    style='width:100%; text-align:left; padding:12px; background:#f7f7f7; border:none; cursor:pointer;'>
                    <strong>{info['nome_turma']}</strong> <small style="color:#666;">(Turma ID: {turma_id})</small>
                </button>
                <div id='{disc_list_id}' style='display:none; padding:10px; background:#fff;'>
            """
            # disciplinas
            for d in info['disciplinas']:
                disciplina_id = d.get('disciplina_id')
                nome_disc = escape(d.get('nome_disciplina', 'N/A'))
                menu_html += f"""
                    <div style='display:flex; justify-content:space-between; align-items:center; padding:6px 0; border-bottom:1px solid #fafafa;'>
                        <div>{nome_disc}</div>
                        <div><a href='{url_for('gerenciar_turma', turma_id=turma_id, disciplina_id=disciplina_id)}' style='background: var(--accent); color: white; padding:5px 8px; border-radius:4px; text-decoration:none;'>Gerenciar</a></div>
                    </div>
                """
            menu_html += "</div></div>"
        menu_html += '</div>'

    # --- Conteúdo final (menu + formulário de lançamento de notas) ---
    form_html = render_notas_form(turmas)

    return f"""
    <h1>Painel do Professor ({user_type.upper()})</h1>
    {notas_feedback}
    {feedback_html}
    {menu_html}
    {form_html}
    """

def render_admin_content(user_type, recursos, feedback_msg, feedback_cls):
    # HTML de feedback
    feedback_html = f'<div class="{feedback_cls}" style="padding: 10px; margin-bottom: 20px;">{escape(feedback_msg)}</div>' if feedback_msg else ''

    # --- Formulário 1: Criar Turma ---
    form_turma = f"""
    <div style="background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
        <h2>1. Criar Turma/Disciplina</h2>
        <form method="POST">
            <input type="hidden" name="action" value="create_turma">
            <label for="nome_turma">Nome da Turma:</label>
            <input type="text" name="nome_turma" required>
            <label for="ano">Ano:</label>
            <input type="number" name="ano" required>
            <button type="submit">Criar Turma</button>
        </form>
    </div>
    """
    
    # --- Formulário 2: Atribuir Professor à Turma ---
    form_atribuir = f"""
    <div style="background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
        <h2>2. Atribuir Professor</h2>
        <form method="POST">
            <input type="hidden" name="action" value="assign_professor">
            <label for="turma_id">Turma:</label>
            <select name="turma_id">
                {''.join(f'<option value="{t["turma_id"]}">{t["nome_turma"]} ({t["ano"]})</option>' for t in recursos['turmas'])}
            </select>
            <label for="professor_id">ID do Professor (Busque o ID na tabela 'usuarios'):</label>
            <input type="number" name="professor_id" required>
            <button type="submit">Atribuir Professor</button>
        </form>
    </div>
    """
    
    # --- Formulário 3: Criar Professor ---
    form_create_prof = """
    <div style="background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
        <h2>3. Criar Conta de Professor (Login)</h2>
        <form method="POST">
            <input type="hidden" name="action" value="create_professor">
            <label for="email">E-mail:</label>
            <input type="email" name="email" required>
            <label for="senha">Senha:</label>
            <input type="password" name="senha" required>
            <button type="submit">Criar Conta</button>
        </form>
    </div>
    """

    # --- Formulário 4: Criar Turma com Disciplinas (Admin) ---
    # lista de disciplinas disponíveis em recursos['disciplinas']
    options_disciplinas = ''.join(f'<option value="{d["disciplina_id"]}">{d["nome_disciplina"]}</option>' for d in recursos.get('disciplinas', []))
    form_turma_with_disc = f"""
    <div style="background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
        <h2>4. Criar Turma e Associar Disciplinas</h2>
        <form method="POST">
            <input type="hidden" name="action" value="create_turma_with_disciplinas">
            <label for="nome_turma">Nome da Turma:</label>
            <input type="text" name="nome_turma" required>
            <label for="ano">Ano:</label>
            <input type="number" name="ano" required>
            <label for="disciplinas">Disciplinas (Ctrl+click para múltiplas):</label>
            <select name="disciplinas" multiple size="6">{options_disciplinas}</select>
            <label for="professor_id">Professor (ID opcional):</label>
            <input type="number" name="professor_id">
            <button type="submit">Criar Turma com Disciplinas</button>
        </form>
    </div>
    """

    return f"""
    <h1>Painel do Administrador</h1>
    {feedback_html}
    {form_create_prof}
    {form_turma}
    {form_turma_with_disc}
    {form_atribuir}
    """


# --------------------------------------------------------------------------------------
# ROTAS PRINCIPAIS: LOGIN, LOGOUT E ROTEAMENTO
# --------------------------------------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if SESSION_KEY_TYPE in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('usuario')
        senha = request.form.get('senha')
        login_url = f"{API_BASE_URL}/auth/login"
        
        try:
            # 1. Chama a API Node.js para autenticação
            response = requests.post(login_url, json={"email": email, "senha": senha})
            response_data = response.json()

            if response.status_code == 200:
                # 2. SUCESSO: Armazena o token e o tipo de usuário na sessão
                session[SESSION_KEY_TOKEN] = response_data.get("token")
                session[SESSION_KEY_TYPE] = response_data.get("usuario").get("tipo_usuario")
                
                return redirect(url_for('dashboard')) # Redireciona para o portão
            
            else:
                # 3. FALHA: Exibe o erro da API
                erro_msg = response_data.get("message", "Credenciais inválidas.")
                return render_base(render_login_form(erro_msg), "Erro de Login")

        except requests.exceptions.ConnectionError:
            erro_msg = "ERRO: O servidor Node.js (API) não está rodando na porta 3000."
            return render_base(render_login_form(erro_msg), "Erro de Conexão")

    return render_base(render_login_form(), "Página de Login")


@app.route('/logout')
def logout():
    session.pop(SESSION_KEY_TOKEN, None)
    session.pop(SESSION_KEY_TYPE, None)
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    user_type = session.get(SESSION_KEY_TYPE)
    if not user_type:
        return redirect(url_for('login'))

    if user_type == 'aluno':
        return redirect(url_for('painel_aluno'))
    elif user_type == 'professor': # ⬅️ APENAS PROFESSOR AQUI
        return redirect(url_for('painel_professor'))
    elif user_type == 'admin':    # ⬅️ NOVA ROTA PARA ADMIN
        return redirect(url_for('painel_admin'))
    else:
        return redirect(url_for('logout'))
    

# ------------------------------------------------------
# Interface Admin
# -----------------------------------------------------

@app.route('/painel/admin', methods=['GET', 'POST'])
def painel_admin():
    user_type = session.get(SESSION_KEY_TYPE)
    token = session.get(SESSION_KEY_TOKEN)
    
    # Proteção: Apenas Admin pode acessar
    if user_type != 'admin' or not token:
        return redirect(url_for('logout'))

    # Variáveis de feedback
    feedback_msg = request.args.get('msg')
    feedback_cls = request.args.get('cls')
    
    # ----------------------------------------------------
    # 🔥 LÓGICA POST (Processamento dos Formulários)
    # ----------------------------------------------------
    if request.method == 'POST':
        action = request.form.get('action') # Identifica qual formulário foi enviado
        
        # Variáveis de retorno do processamento
        result_msg = "Ação desconhecida."
        result_cls = "error"
        
        try:
            if action == 'create_turma':
                nome_turma = request.form.get('nome_turma')
                ano = request.form.get('ano')
                
                # ⚠️ 1. Chama a API Node.js para criar a Turma
                response = requests.post(
                    f"{API_BASE_URL}/academico/turmas", 
                    json={"nome_turma": nome_turma, "ano": int(ano)}, 
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 201:
                    result_msg = "Turma criada com sucesso!"
                    result_cls = "success"
                else:
                    result_msg = response.json().get("message", "Erro ao criar turma na API.")
                    result_cls = "error"

            elif action == 'create_professor':
                email = request.form.get('email')
                senha = request.form.get('senha')
                
                # ⚠️ 2. Chama a API Node.js para criar a conta de Professor
                response = requests.post(
                    f"{API_BASE_URL}/auth/register", 
                    json={"email": email, "senha": senha, "tipo_usuario": "professor"}, 
                    headers={"Authorization": f"Bearer {token}"} # Embora o registro não precise de token, o admin está logado.
                )
                
                if response.status_code == 201:
                    result_msg = f"Professor {email} criado com sucesso!"
                    result_cls = "success"
                else:
                    result_msg = response.json().get("message", "Erro ao criar professor na API.")
                    result_cls = "error"

            elif action == 'create_turma_with_disciplinas':
                nome_turma = request.form.get('nome_turma')
                ano = request.form.get('ano')
                # campos múltiplos
                disciplinas_list = request.form.getlist('disciplinas')
                professor_id = request.form.get('professor_id')

                payload = {"nome_turma": nome_turma, "ano": int(ano)}
                if disciplinas_list:
                    # converter para inteiros
                    payload['disciplinas'] = [int(x) for x in disciplinas_list]
                if professor_id:
                    payload['professor_id'] = int(professor_id)

                response = requests.post(
                    f"{API_BASE_URL}/academico/turmas/with-disciplinas",
                    json=payload,
                    headers={"Authorization": f"Bearer {token}"}
                )

                if response.status_code == 201:
                    result_msg = "Turma criada e disciplinas associadas com sucesso!"
                    result_cls = "success"
                else:
                    # tenta ler mensagem da API
                    try:
                        result_msg = response.json().get('message', 'Erro ao criar turma com disciplinas')
                    except Exception:
                        result_msg = 'Erro ao criar turma com disciplinas (sem detalhe)'
                    result_cls = 'error'

            elif action == 'assign_professor':
                turma_id = request.form.get('turma_id')
                professor_id = request.form.get('professor_id')
                if not token:
                    return redirect(url_for('logout'))
                
                # ⚠️ 3. Chama a API Node.js para Atribuir Professor à Turma
                # Usamos PUT para atualizar o campo professor_id na turma
                response = requests.put(
                    f"{API_BASE_URL}/academico/turmas/atribuir-professor", 
                    json={"turma_id": int(turma_id), "professor_id": int(professor_id)}, 
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    result_msg = f"Professor {professor_id} atribuído à Turma {turma_id}."
                    result_cls = "success"
                else:
                    result_msg = response.json().get("message", "Erro ao atribuir professor.")
                    result_cls = "error"
            
            # Redireciona para o GET com a mensagem de feedback
            return redirect(url_for('painel_admin', msg=result_msg, cls=result_cls))
            
        except ValueError:
            return redirect(url_for('painel_admin', msg="Erro: ID ou Ano inválido.", cls="error"))
        except requests.exceptions.RequestException:
            return redirect(url_for('painel_admin', msg="ERRO DE CONEXÃO com a API Node.js.", cls="error"))


    # ----------------------------------------------------
    # LÓGICA GET (Exibir Formulários)
    # ----------------------------------------------------
    
    # ⚠️ Vamos reusar a função render_professor_content para listar Turmas/Disciplinas
    turmas_disponiveis = listar_recursos_para_admin(token)
    
    # O conteúdo final será uma coleção de formulários
    conteudo_admin_html = render_admin_content(user_type, turmas_disponiveis, feedback_msg, feedback_cls)
    
    return render_base(conteudo_admin_html, "Painel do Administrador")

# --- Função auxiliar para buscar dados (DEVE SER CRIADA NO SEU CÓDIGO) ---
def listar_recursos_para_admin(token):
    # Por simplicidade, faremos um GET de todas as turmas e disciplinas
    try:
        turmas_res = requests.get(f"{API_BASE_URL}/academico/turmas", headers={"Authorization": f"Bearer {token}"}).json()
        disciplinas_res = requests.get(f"{API_BASE_URL}/academico/disciplinas", headers={"Authorization": f"Bearer {token}"}).json()
        
        return {
            'turmas': turmas_res.get('turmas', []),
            'disciplinas': disciplinas_res.get('disciplinas', [])
        }
    except requests.exceptions.RequestException:
        return {'turmas': [], 'disciplinas': []}

# --------------------------------------------------------------------------------------
# ROTAS DE INTERFACE POR PERFIL
# --------------------------------------------------------------------------------------

@app.route('/painel/aluno')
@require_login
def painel_aluno():
    """Página inicial após o login do aluno."""
    # 1. Proteção: Garante que é realmente um aluno logado
    if session.get(SESSION_KEY_TYPE) != 'aluno':
        # Se não for aluno, envia para o dashboard para roteamento correto ou logout
        return redirect(url_for('dashboard')) 
    
    # 2. Conteúdo da Interface do Aluno (Simulação da página inicial)
    conteudo_aluno = f'''
    <h1>Bem-vindo(a) ao Sistema Acadêmico PIM</h1>
    <p>Olá, Aluno! Use o menu lateral para consultar suas informações e notas.</p>
    <p>Seu token está ativo, permitindo acesso seguro aos dados.</p>
    '''
    # 3. Renderiza a base (sua base com a sidebar)
    return render_base(conteudo_aluno, "Painel do Aluno")

@app.route('/boletim')
@require_login
def boletim():
    # 1. Proteção: Garante que o usuário logado é um aluno (opcional, mas recomendado)
    if session.get(SESSION_KEY_TYPE) != 'aluno':
         # Se não for aluno, apenas mostra uma mensagem de acesso negado
        return render_base("<h1>Acesso Negado</h1><p>Esta página é exclusiva para alunos.</p>", "Acesso Negado")


    token = session.get(SESSION_KEY_TOKEN)
    boletim_data = []

    try:
        # 2. Chama a API Node.js
        response = requests.get(
            f"{API_BASE_URL}/academico/boletim", 
            headers={"Authorization": f"Bearer {token}"}
        )
        response_data = response.json()

        if response.status_code == 200 and 'boletim' in response_data:
            boletim_data = response_data['boletim']
            feedback = "Boletim carregado."
        else:
            feedback = response_data.get("message", "Erro ao carregar dados da API.")
            
    except requests.exceptions.RequestException:
        feedback = "ERRO DE CONEXÃO: Verifique se a API Node.js está rodando."


    # 3. Constrói a tabela HTML com os dados
    tabela = '<h1>Boletim de Notas</h1>'
    if not boletim_data:
        tabela += f'<p style="color: red;">{feedback} Nenhuma nota encontrada.</p>'
    else:
        tabela += '<table class="boletim"><tr><th>Disciplina</th><th>Nota</th><th>Faltas (Simuladas)</th></tr>'
        for item in boletim_data:
            # ⚠️ Faltas são simuladas aqui, pois a API não as retorna diretamente neste JOIN
            nota = item.get('valor_nota', 'N/D') if item.get('valor_nota') is not None else 'SEM NOTA'
            tabela += f"""
            <tr>
                <td>{escape(item.get('nome_disciplina', 'N/A'))}</td>
                <td>{nota}</td>
                <td>{random.randint(0, 5)}</td> 
            </tr>
            """
        tabela += '</table>'
    
    return render_base(tabela, page_title="Meu Boletim")

# ----------------------------------------------------------------------
# ROTA PRINCIPAL DO PROFESSOR
# ----------------------------------------------------------------------

@app.route('/painel/professor', methods=['GET', 'POST'])
def painel_professor():
    user_type = session.get(SESSION_KEY_TYPE)
    token = session.get(SESSION_KEY_TOKEN)
    
    if user_type not in ['professor', 'admin'] or not token:
        return redirect(url_for('logout'))

    turmas = []
    message = None
    message_class = None
    notas_form_result = None # Variável para feedback de POST

    # ----------------------------------------------------
    # 🔥 LÓGICA DE LANÇAMENTO DE NOTAS (POST)
    # ----------------------------------------------------
    if request.method == 'POST':
        aluno_id = request.form.get('aluno_id')
        disciplina_id = request.form.get('disciplina_id')
        valor_nota = request.form.get('valor_nota')
        
        try:
            # Chama a API Node.js para Lançar a Nota
            response = requests.post(
                f"{API_BASE_URL}/academico/notas", 
                json={
                    "aluno_id": int(aluno_id), 
                    "disciplina_id": int(disciplina_id), 
                    "valor_nota": float(valor_nota)
                }, 
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 201:
                notas_form_result = {"msg": "Nota lançada com sucesso!", "cls": "success"}
            else:
                error_data = response.json()
                notas_form_result = {"msg": error_data.get("message", "Erro na API ao lançar nota."), "cls": "error"}

        except requests.exceptions.RequestException:
            notas_form_result = {"msg": "ERRO: Não foi possível conectar à API Node.js.", "cls": "error"}
        except ValueError:
             notas_form_result = {"msg": "Erro: ID ou Nota precisam ser números válidos.", "cls": "error"}
        
        # O código deve continuar para carregar a lista de turmas (GET)
    
    
    # ----------------------------------------------------
    # LÓGICA DE BUSCA DE TURMAS (GET - Acontece após o POST)
    # ----------------------------------------------------
    try:
        # Chama a API Node.js para listar as turmas
        response = requests.get(
            f"{API_BASE_URL}/academico/professor/turmas", 
            headers={"Authorization": f"Bearer {token}"}
        )
        response_data = response.json()
        if response.status_code == 200 and 'turmas' in response_data:
            # API retorna lista de turmas (cada item pode conter disciplina info)
            turmas = response_data.get('turmas', [])
        else:
            message = response_data.get('message', 'Erro ao carregar turmas da API.')
            message_class = 'error'
        
    except requests.exceptions.RequestException:
        # Se falhar a busca (GET), a mensagem de POST deve ser preservada se houver
        if not notas_form_result:
            message = "ERRO: Não foi possível conectar à API Node.js."
            message_class = "error"
            
    # Renderiza o conteúdo final
    conteudo_professor_html = render_professor_content(user_type, turmas, message, message_class, notas_form_result)
    
    return render_base(conteudo_professor_html, "Painel do Professor")

@app.route('/gerenciar/turma/<int:turma_id>/<int:disciplina_id>')
@require_login
def gerenciar_turma(turma_id, disciplina_id):
    """Interface de gestão de notas e faltas para uma turma/disciplina específica."""
    user_type = session.get(SESSION_KEY_TYPE)
    token = session.get(SESSION_KEY_TOKEN)
    
    # Proteção adicional no frontend
    if user_type not in ['professor', 'admin'] or not token:
        return redirect(url_for('logout'))

    alunos = []
    
    try:
        # 1. Chama a nova rota da API Node.js
        response = requests.get(
            f"{API_BASE_URL}/academico/turmas/{turma_id}/disciplinas/{disciplina_id}/alunos", 
            headers={"Authorization": f"Bearer {token}"}
        )
        response_data = response.json()

        if response.status_code == 200 and 'alunos' in response_data:
            alunos = response_data['alunos']
            feedback = "Lista de alunos carregada."
        else:
            feedback = response_data.get("message", "Erro ao carregar lista de alunos.")

    except requests.exceptions.RequestException:
        feedback = "ERRO DE CONEXÃO com API Node.js."

    # 2. Constrói o HTML da Tabela de Gestão
    
    # ... (Aqui o código HTML será construído) ...
    tabela_alunos_html = build_alunos_table(turma_id, disciplina_id, alunos, feedback)
    
    return render_base(tabela_alunos_html, f"Gerenciar Turma {turma_id}")


# Função auxiliar (adicionar ao main.py)
def build_alunos_table(turma_id, disciplina_id, alunos, feedback):
    """Constrói a tabela de alunos com formulários de ação (Nota/Presença)."""
    
    html = f'<h1>Gestão de Turma/Disciplina</h1>'
    html += f'<p>Turma ID: {turma_id} | Disciplina ID: {disciplina_id}</p>'
    html += f'<p style="color:red;">{feedback}</p>'
    
    if not alunos:
        html += '<p>Nenhum aluno matriculado ou erro de busca.</p>'
        return html
    
    # Tabela com as colunas necessárias para as ações
    html += '''
    <table class="boletim">
        <tr>
            <th>ID</th>
            <th>Nome do Aluno</th>
            <th>Nota Atual</th>
            <th>Ação: Lançar Nota</th>
            <th>Ação: Presença</th>
        </tr>
    '''
    for aluno in alunos:
        aluno_id = aluno.get('aluno_id')
        nome_completo = f"{escape(aluno.get('nome', ''))} {escape(aluno.get('sobrenome', ''))}"
        nota_atual = aluno.get('nota_atual', 'N/D') if aluno.get('nota_atual') is not None else 'Lançar'

        html += f'''
        <tr>
            <td>{aluno_id}</td>
            <td>{nome_completo}</td>
            <td>{nota_atual}</td>
            <td>
                <form action="{url_for('lancar_nota_form')}" method="POST">
                    <input type="hidden" name="aluno_id" value="{aluno_id}">
                    <input type="hidden" name="disciplina_id" value="{disciplina_id}">
                    <input type="number" step="0.1" name="valor_nota" placeholder="Nota" style="width: 80px;">
                    <button type="submit">Lançar</button>
                </form>
            </td>
            <td>
                <button onclick="alert('Presença para {nome_completo} marcada!')">
                    Marcar Presença
                </button>
            </td>
        </tr>
        '''
    html += '</table>'
    return html

# ⚠️ Adicione uma rota dummy para o FORM POST (lancar_nota_form) para que os links funcionem.
@app.route('/lancar_nota_form', methods=['POST'])
@require_login
def lancar_nota_form():
    # Esta função irá pegar os dados do POST e chamar a API /academico/notas
    return "A ser implementado: Processar POST e chamar a API /academico/notas"


@app.route('/')
def index():
    if SESSION_KEY_TYPE in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


if __name__ == '__main__':
    # ⚠️ Certifique-se de que a API Node.js está rodando na porta 3000!
    print("Iniciando servidor Flask (porta 5000)...")
    app.run(debug=True, host='127.0.0.1', port=5000)