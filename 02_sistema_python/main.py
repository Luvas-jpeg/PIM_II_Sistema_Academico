"""
Sistema Acadêmico PIM - Módulo Web Flask

Este módulo implementa a interface web do Sistema Acadêmico PIM, oferecendo funcionalidades
para alunos, professores e administradores. O sistema se integra com uma API Node.js
para gerenciamento de dados e autenticação.

Funcionalidades principais:
- Autenticação de usuários (alunos, professores, administradores)
- Gestão de boletins e notas
- Gerenciamento de turmas e disciplinas
- Interface administrativa
- Painel do professor para lançamento de notas

Estrutura do projeto:
- Rotas principais para cada tipo de usuário
- Sistema de templates usando render_template_string
- Integração com API REST
- Gestão de sessões para autenticação

Autor: [Seu Nome]
Data: Outubro 2025
"""
import ctypes
import platform
from flask import Flask, render_template_string, request, redirect, url_for, session
from markupsafe import escape  # Para proteção contra XSS
import requests  # Para comunicação com a API
import os
from decimal import Decimal, ROUND_HALF_UP
from dotenv import load_dotenv  # Carregamento de variáveis de ambiente
import random


# --- Configurações Iniciais ---
# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# URL base da API - usa fallback para localhost se não configurado
API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:3000/api") 

# Inicialização da aplicação Flask
app = Flask(__name__)

# Configuração da chave secreta para sessions
# IMPORTANTE: Em produção, use uma chave secreta forte através de variável de ambiente
app.secret_key = os.getenv("FLASK_SECRET_KEY", "chave_de_dev_insegura_use_o_env") 

# Constantes para chaves de sessão
SESSION_KEY_TOKEN = 'user_token'  # Armazena o token JWT
SESSION_KEY_TYPE = 'user_type'    # Armazena o tipo de usuário (aluno/professor/admin)



# --- Carregamento da Biblioteca C (DLL/SO) ---
lib_c = None
try:
    lib_name = "algorithms.dll" if platform.system() == "Windows" else "algorithms.so"
    # O caminho é relativo à pasta 02_sistema_python (onde o main.py está)
    lib_path = os.path.join(os.path.dirname(__file__), "..", "03_algorithms_c", lib_name)
    
    lib_c = ctypes.CDLL(lib_path)
    
    # Definir a estrutura (struct) em Python
    class DesempenhoAluno(ctypes.Structure):
        _fields_ = [("id_aluno", ctypes.c_int), ("media_final", ctypes.c_float)]

    # Definir interface da função C: ordenar_por_desempenho
    lib_c.ordenar_por_desempenho.argtypes = [
        ctypes.POINTER(DesempenhoAluno), 
        ctypes.c_int
    ]
    lib_c.ordenar_por_desempenho.restype = None
    
    print("✅ (Flask) Biblioteca C 'algorithms' carregada com sucesso.")

except Exception as e:
    print(f"❌ (Flask) ERRO AO CARREGAR BIBLIOTECA C: {e}")
    print("   As funcionalidades de relatório C (ordenação) estarão desativadas.")
    lib_c = None # Garante que o app rode mesmo se o C falhar

# --------------------------------------------------------------------------------------
# FUNÇÕES DE RENDERIZAÇÃO E BASE HTML
# --------------------------------------------------------------------------------------

def render_base(content_html, page_title="Sistema Acadêmico PIM"):
    """
    Função principal de renderização que fornece o template base do sistema.
    
    Args:
        content_html (str): Conteúdo HTML específico da página
        page_title (str): Título da página, padrão é "Sistema Acadêmico PIM"
    
    Returns:
        str: HTML renderizado com o layout base completo
        
    O layout inclui:
    - Sidebar de navegação
    - Área principal de conteúdo
    - Estilos CSS básicos
    """
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

def render_login_base(content_html, page_title="Login"):
    # (Este é o CSS/HTML que você usou para a tela de login)
    base_html = f'''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{page_title}</title>
        <style>
            :root {{ --accent: #1b55f8; --accent-hover: #133fe0; --muted: #6b7280; --error: #d32f2f; }}
            * {{ box-sizing: border-box; }}
            body {{
                margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto;
                background-image: linear-gradient(rgba(12,18,32,0.45), rgba(12,18,32,0.45)), url('/static/tech-bg.jpg');
                background-size: cover; background-position: center center; background-attachment: fixed;
                min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 24px;
            }}
            .login-card {{
                width: 100%; max-width: 420px; background: #ffffff; border-radius: 12px;
                box-shadow: 0 10px 30px rgba(16,24,40,0.08); padding: 28px;
            }}
            .brand {{ text-align: center; margin-bottom: 18px; }}
            .brand h2 {{ margin: 0; color: var(--accent); }}
            label {{ display:block; font-size:0.9rem; color:var(--muted); margin-bottom:6px; }}
            input[type="text"], input[type="password"] {{
                width: 100%; padding: 10px 12px; border-radius: 8px; border: 1px solid #e6e9ef;
                margin-bottom: 14px; font-size: 1rem;
            }}
            button[type="submit"] {{
                width: 100%; padding: 12px 14px; border-radius: 8px; border: none;
                background: var(--accent); color: #fff; font-weight: 600; cursor: pointer; font-size: 1rem;
            }}
            button[type="submit"]:hover {{ background: var(--accent-hover); }}
            .help {{ text-align:center; margin-top:12px; color:var(--muted); font-size:0.9rem; }}
            .error-message {{ color: var(--error); text-align: center; margin-bottom: 15px; font-size: 0.9rem; }}
        </style>
    </head>
    <body>
        {content_html}
    </body>
    </html>
    '''
    return render_template_string(base_html, page_title=page_title)


# FUNÇÃO 2: Layout para o Aplicativo (COM Sidebar) - Renomeie sua função antiga
def render_app_base(content_html, page_title="Sistema Acadêmico"):
    # ⚠️ Certifique-se de que esta é a sua função com o código da SIDEBAR
    app_base_html = f'''
    <!DOCTYPE html>
    <a href="{url_for('dashboard')}">Home</a>
    
    
    '''
    return render_template_string(app_base_html, page_title=page_title)

# 02_sistema_python/main.py

# ... (após def render_base(...) e suas funções auxiliares, mas antes de @app.route('/login'))

def render_register_form(error_message=None):
    error_html = f'<p class="error-message">{escape(error_message)}</p>' if error_message else ''
    form_html = f'''
    <div class="login-card"> 
        <h2>Cadastro</h2>
        {error_html}
        <form method="POST" action="{url_for('registrar')}">
            <label for="nome">Nome:</label>
            <input type="text" name="nome" required>
            <label for="sobrenome">Sobrenome:</label>
            <input type="text" name="sobrenome">
            <label for="email">E-mail:</label>
            <input type="email" name="email" required>
            <label for="senha">Senha:</label>
            <input type="password" name="senha" required>
            <label for="data_nascimento">Data Nascimento (AAAA-MM-DD):</label>
            <input type="date" name="data_nascimento"> 
            
            <button type="submit">Registrar Aluno</button>
        </form>
        <p style="text-align: center; margin-top: 15px;">Já tem conta? <a href="{url_for('login')}">Faça Login</a></p>
    </div>
    '''
    # Use o render_login_base (sem sidebar)
    return render_login_base(form_html, "Registrar Aluno")

def render_login_form(error_message=None):
    # Conteúdo do seu formulário de login (sem a sidebar)
    error_html = f'<p class="error-message" style="color:#d32f2f;text-align:center;font-size:0.9rem;">{escape(error_message)}</p>' if error_message else ''
    
    form_html = f'''
    <div class="login-card" style="max-width: 420px; margin: auto; padding: 28px; border: 1px solid #ddd; border-radius: 12px;">
        <div style="text-align:center;"><h2>Login</h2></div>
        {error_html}
        <form method="POST" action="{url_for('login')}">
            <label for="usuario">E-mail:</label>
            <input id="usuario" type="text" name="usuario" required style="width: 100%; margin-bottom: 10px;">
            <label for="senha">Senha:</label>
            <input id="senha" type="password" name="senha" required style="width: 100%; margin-bottom: 15px;">
            <button type="submit" style="background: #1b55f8; color: white; padding: 10px; border: none; width: 100%; border-radius: 4px; cursor: pointer;">Entrar</button>
        </form>
        
        <div style="text-align: center; margin-top: 15px;">
            <p>Não tem uma conta? 
               <a href="{url_for('registrar')}" style="color: var(--accent); text-decoration: none;">Registre-se aqui</a>
            </p>
        </div>
    </div>
    '''
    # Note que esta função DEVE chamar render_base para envolver o formulário no layout de página completa
    return render_base(form_html, "Página de Login")

def require_login(view_func):
    """
    Decorator para proteger rotas que requerem autenticação.
    
    Este decorator verifica se existe um token de autenticação válido na sessão
    antes de permitir o acesso à rota. Caso não exista, redireciona para a
    página de login.
    
    Args:
        view_func (callable): A função de view do Flask a ser protegida
        
    Returns:
        callable: Função wrapper que realiza a verificação de autenticação
        
    Exemplo de uso:
        @app.route('/rota-protegida')
        @require_login
        def rota_protegida():
            return 'Conteúdo protegido'
    """
    def wrapper(*args, **kwargs):
        # Verifica se o token de sessão existe
        if SESSION_KEY_TOKEN not in session:
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    # Garante que o Flask registra a função com o nome correto
    wrapper.__name__ = view_func.__name__ 
    return wrapper

def render_notas_form():
    """
    Gera o HTML do formulário para lançamento de notas pelos professores.
    
    Esta função cria um formulário com campos para:
    - ID do Aluno
    - ID da Disciplina
    - Valor da Nota (0.0 a 10.0)
    
    O formulário é estilizado e inclui validações básicas de entrada.
    Os dados são enviados via POST para a rota do painel do professor.
    
    Returns:
        str: HTML do formulário de lançamento de notas
    """
    form_html = f"""
    <div style="background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-top: 40px;">
        <h2>Lançamento Rápido de Notas</h2>
        <form method="POST" action="{url_for('painel_professor')}">
            <input type="hidden" name="action" value="lancar_nota"> 
            
            <label for="aluno_id" style="display:block; margin-top: 10px;">ID do Aluno:</label>
            <input type="number" id="aluno_id" name="aluno_id" required style="width: 100%; padding: 8px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px;">

            <label for="disciplina_id" style="display:block;">ID da Disciplina:</label>
            <input type="number" id="disciplina_id" name="disciplina_id" required style="width: 100%; padding: 8px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px;">
            
            <label for="valor_nota" style="display:block;">Nota (0.0 a 10.0):</label>
            <input type="number" step="0.1" min="0" max="10" id="valor_nota" name="valor_nota" required style="width: 100%; padding: 8px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 4px;">
            
            <button type="submit" style="background: var(--accent); color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer;">
                Lançar Nota
            </button>
        </form>
    </div>
    """
    return form_html

def render_professor_content(user_type, turmas, message, message_class, notas_feedback=None):
    """Gera o HTML do painel do professor, incluindo a tabela e o formulário."""
    
    # Mensagens de Feedback
    feedback_html = f'<div class="{message_class}" style="padding: 10px; margin-bottom: 20px; border-radius: 4px;">{escape(message)}</div>' if message else ''
    notas_feedback_html = f'<div class="{notas_feedback["cls"]}" style="padding: 10px; margin-bottom: 20px; border-radius: 4px;">{escape(notas_feedback["msg"])}</div>' if notas_feedback else ''

    # --- Tabela de Turmas Atribuídas ---
    tabela_html = """
    <h2 style="color: #333; margin-top: 25px;">Minhas Turmas Atribuídas</h2>
    <table class="boletim">
        <thead>
            <tr><th>Turma</th><th>Disciplina</th><th>Ano</th><th>Ação</th></tr>
        </thead>
        <tbody>
    """
    
    if turmas:
        # Agrupa disciplinas por turma para melhor visualização (se a API retornar duplicatas)
        turmas_agrupadas = {}
        for t in turmas:
            turma_id = t.get('turma_id')
            if turma_id not in turmas_agrupadas:
                 turmas_agrupadas[turma_id] = {'nome': t.get('nome_turma'), 'ano': t.get('ano'), 'disciplinas': []}
            turmas_agrupadas[turma_id]['disciplinas'].append(t)

        for turma_id, info in turmas_agrupadas.items():
            nome_turma = escape(info['nome'])
            ano = info['ano']
            
            # Exibe cada disciplina como uma linha separada para gestão
            for disc_info in info['disciplinas']:
                disciplina_id = disc_info.get('disciplina_id')
                disciplina_nome = escape(disc_info.get('nome_disciplina', 'N/A'))
                
                # Link para a tela de gestão detalhada
                gerenciar_url = url_for('gerenciar_turma', turma_id=turma_id, disciplina_id=disciplina_id) if disciplina_id else '#'
                
                tabela_html += f"""
                <tr>
                    <td>{nome_turma} (ID: {turma_id})</td>
                    <td>{disciplina_nome} (ID: {disciplina_id})</td>
                    <td>{ano}</td>
                    <td>
                        <a href='{gerenciar_url}' style='background: #4CAF50; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none;'>
                            Gerenciar Alunos/Notas
                        </a>
                    </td>
                </tr>
                """
    else:
        tabela_html += '<tr><td colspan="4">Nenhuma turma atribuída a você no momento.</td></tr>'
        
    tabela_html += '</tbody></table>'
    
    # --- Conteúdo final ---
    form_html_notas = render_notas_form()
    
    return f"""
    <h1>Painel do Professor ({user_type.upper()})</h1>
    {notas_feedback_html}
    {feedback_html}
    {tabela_html}
    {form_html_notas} 
    """

def build_alunos_table_gestao(turma_id, disciplina_id, alunos, feedback):
    """Constrói a tabela de alunos com formulários de ação (Nota/Presença)."""
    from flask import url_for # Garante que url_for funciona dentro desta função
    
    html = f'<h1>Gestão de Turma/Disciplina</h1>'
    html += f'<h2>Turma: {turma_id} | Disciplina: {disciplina_id}</h2>'
    html += f'<p style="color:red;">{feedback}</p>'
    
    if not alunos:
        html += '<p>Nenhum aluno matriculado ou erro de busca.</p>'
        return html
    
    # Tabela de Gestão
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

        # Formulário para Nota (action deve apontar para uma rota POST que processa a nota)
        html += f'''
        <tr>
            <td>{aluno_id}</td>
            <td>{nome_completo}</td>
            <td>{nota_atual}</td>
            <td>
                <form action="{url_for('lancar_nota_form')}" method="POST" style="display:inline-flex; gap: 5px;">
                    <input type="hidden" name="aluno_id" value="{aluno_id}">
                    <input type="hidden" name="disciplina_id" value="{disciplina_id}">
                    <input type="number" step="0.1" name="valor_nota" placeholder="Nota" style="width: 70px; border-radius: 4px;">
                    <button type="submit">Lançar</button>
                </form>
            </td>
            <td>
                <button onclick="alert('Presença para {nome_completo} marcada!')" style="background: green; color: white; border: none; padding: 5px; border-radius: 4px;">Marcar Presença</button>
            </td>
        </tr>
        '''
    html += '</table>'
    return html
def render_admin_content(user_type, recursos, feedback_msg, feedback_cls):
    print(f"\n--- [render_admin_content] Iniciando Renderização ---")
    print(f"[render_admin_content] Número de Professores Recebidos: {len(recursos.get('professores', []))}")
    print(f"[render_admin_content] Número de Alunos Recebidos: {len(recursos.get('alunos', []))}\n")
    # HTML de feedback (usamos render_base para estilizar isso)
    feedback_html = f'<div class="{feedback_cls}" style="padding: 10px; margin-bottom: 20px;">{escape(feedback_msg)}</div>' if feedback_msg else ''

    # Cria as opções para selects (turmas e disciplinas)
    turma_options = ''.join(f'<option value="{t["turma_id"]}">{escape(t["nome_turma"])} ({t["ano"]})</option>' for t in recursos['turmas'])
    disciplina_options = ''.join(f'<option value="{d["disciplina_id"]}">{escape(d["nome_disciplina"])}</option>' for d in recursos['disciplinas'])

    # --- Formulário 1: Criar Conta de Professor ---
    form_create_prof = f"""
    <div style="background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
        <h2>1. Criar Conta de Professor</h2>
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
    form_criarDiciplina = f"""
    <div style="background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
        <h2>5. Criar Nova Disciplina</h2>
        <form method="POST">
            <input type="hidden" name="action" value="create_disciplina"> 
            
            <label for="nome_disciplina">Nome da Disciplina:</label>
            <input type="text" id="nome_disciplina" name="nome_disciplina" required style="width: 100%; padding: 8px; margin-bottom: 10px;">
            
            <label for="descricao_disciplina">Descrição (Opcional):</label>
            <textarea id="descricao_disciplina" name="descricao" rows="3" style="width: 100%; padding: 8px; margin-bottom: 15px;"></textarea>
            
            <button type="submit">Criar Disciplina</button>
        </form>
    </div>
    """


    # --- Formulário 2: Criar Turma ---
    form_turma = f"""
    <div style="background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
        <h2>2. Criar Turma</h2>
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
    
    # --- Formulário 3: Atribuir Professor à Turma ---
    form_atribuir = f"""
    <div style="background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
        <h2>3. Atribuir Professor à Turma</h2>
        <form method="POST">
            <input type="hidden" name="action" value="assign_professor">
            <label for="turma_id">Turma:</label>
            <select name="turma_id">{turma_options}</select>
            <label for="professor_id">ID do Professor (Busque o ID na tabela 'usuarios'):</label>
            <input type="number" name="professor_id" required>
            <button type="submit">Atribuir Professor</button>
        </form>
    </div>
    """
    
    # --- Formulário 4: Associar Disciplinas à Turma ---
    form_disciplinas = f"""
    <div style="background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
        <h2>4. Associar Disciplinas à Turma</h2>
        <form method="POST">
            <input type="hidden" name="action" value="assign_disciplinas">
            <label for="turma_id_disciplina">Turma:</label>
            <select name="turma_id_disciplina">{turma_options}</select>
            <label for="disciplinas">Disciplinas (Ctrl+click para múltiplas):</label>
            <select name="disciplinas" multiple size="6">{disciplina_options}</select>
            <button type="submit">Associar Disciplinas</button>
        </form>
    </div>
    """

    form_matricular = f"""
    <div style="background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
        <h2>5. Matricular Aluno em Turma/Disciplina</h2>
        <form method="POST">
            <input type="hidden" name="action" value="enroll_student"> 
            
            <label for="aluno_id">ID do Aluno (Tabela 'alunos'):</label>
            <input type="number" name="aluno_id" required>
            
            <label for="turma_id_matricula">Turma:</label>
            <select name="turma_id_matricula">{turma_options}</select> 
            
            <label for="disciplina_id_matricula">Disciplina:</label>
            <select name="disciplina_id_matricula">{disciplina_options}</select>
            
            <button type="submit">Matricular Aluno</button>
        </form>
    </div>
    """

    tabela_professores = """
    <div style="margin-top: 40px;">
        <h2>Professores Cadastrados</h2>
        <table class="boletim">
            <thead><tr><th>ID Usuário</th><th>E-mail</th></tr></thead>
            <tbody>
    """
    form_remover_associacao = f"""
    <div style="background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 30px; border: 1px solid #f44336;">
        <h2>6. Desassociar Disciplina de uma Turma</h2>
        <p style="font-size: 0.9em; color: #666;">Isso remove a disciplina da grade da turma. (Não exclui a disciplina).</p>
        <form method="POST">
            <input type="hidden" name="action" value="remove_disciplina_from_turma">
            
            <label for="remove_turma_id">Selecione a Turma:</label>
            <select name="turma_id" required>{turma_options}</select>
            
            <label for="remove_disciplina_id">Selecione a Disciplina a Remover:</label>
            <select name="disciplina_id" required>{disciplina_options}</select>
            
            <button type="submit" style="background: #d32f2f; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer;">
                Desassociar Disciplina
            </button>
        </form>
    </div>
    """

    # --- Formulário 7: Excluir Disciplina (Global) ---
    form_excluir_disciplina = f"""
    <div style="background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 30px; border: 1px solid #f44336;">
        <h2>7. Excluir Disciplina (Ação Permanente)</h2>
        <p style="font-size: 0.9em; color: #666;">Isso excluirá a disciplina de TODO o sistema. Só funcionará se nenhuma turma ou matrícula depender dela.</p>
        <form method="POST">
            <input type="hidden" name="action" value="delete_disciplina">
            
            <label for="delete_disciplina_id">Selecione a Disciplina a Excluir:</label>
            <select name="disciplina_id" required>{disciplina_options}</select>
            
            <button type="submit" style="background: #d32f2f; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer;">
                EXCLUIR PERMANENTEMENTE
            </button>
        </form>
    </div>
    """

    if recursos.get('professores'):
        for prof in recursos['professores']:
            tabela_professores += f"<tr><td>{prof.get('id_usuario')}</td><td>{escape(prof.get('email', 'N/A'))}</td></tr>"
    else:
        tabela_professores += '<tr><td colspan="2">Nenhum professor encontrado.</td></tr>'
    tabela_professores += '</tbody></table></div>'

    # --- Tabela de Alunos ---
    tabela_alunos = """
    <div style="margin-top: 40px;">
        <h2>Alunos Cadastrados</h2>
        <table class="boletim">
            <thead><tr><th>ID Aluno</th><th>Nome Completo</th><th>E-mail</th></tr></thead>
            <tbody>
    """
    form_remover_matricula = f"""
    <div style="background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 30px; border: 1px solid #f44336;">
        <h2>8. Remover Aluno da Turma/Disciplina (Excluir Matrícula)</h2>
        <p style="font-size: 0.9em; color: #666;">Isso excluirá a matrícula do aluno. (Pode falhar se houver notas lançadas para esta matrícula).</p>
        <form method="POST">
            <input type="hidden" name="action" value="delete_matricula">
            
            <label for="delete_matricula_id">ID da Matrícula (Tabela 'matriculas'):</label>
            <input type="number" id="delete_matricula_id" name="matricula_id" required>
            
            <button type="submit" style="background: #d32f2f; color: white; ...">
                EXCLUIR MATRÍCULA
            </button>
        </form>
    </div>
    """

    form_limpar_notas = f"""
    <div style="background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 30px; border: 1px solid #ff9800;">
        <h2>9. Limpar Notas de uma Disciplina (Pré-requisito para Excluir)</h2>
        <p style="font-size: 0.9em; color: #666;">Isso excluirá TODAS as notas (NP1, NP2, etc.) associadas a esta disciplina.</p>
        <form method="POST">
            <input type="hidden" name="action" value="delete_notas_da_disciplina">
            
            <label for="delete_notas_disciplina_id">Selecione a Disciplina para Limpar:</label>
            <select name="disciplina_id_para_limpar" required>{disciplina_options}</select>
            
            <button type="submit" style="background: #ff9800; color: white; ...">
                LIMPAR NOTAS DESTA DISCIPLINA
            </button>
        </form>
    </div>
    """
    
    if recursos.get('alunos'):
        for aluno in recursos['alunos']:
             nome_completo = f"{escape(aluno.get('nome', ''))} {escape(aluno.get('sobrenome', ''))}".strip()
             tabela_alunos += f"<tr><td>{aluno.get('aluno_id')}</td><td>{nome_completo}</td><td>{escape(aluno.get('email', 'N/A'))}</td></tr>"
    else:
        tabela_alunos += '<tr><td colspan="3">Nenhum aluno encontrado.</td></tr>'
    tabela_alunos += '</tbody></table></div>'


    return f"""
    <h1>Painel do Administrador</h1>
    {feedback_html}
    {form_create_prof}
    {form_turma}
    {form_disciplinas}
    {form_atribuir}
    {form_matricular} 
    {form_disciplinas}
    {form_remover_associacao} 
    {form_excluir_disciplina}
    {form_remover_matricula}
    {form_limpar_notas} 
    """

# --------------------------------------------------------------------------------------
# ROTAS PRINCIPAIS: LOGIN, LOGOUT E ROTEAMENTO
# --------------------------------------------------------------------------------------

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        # 1. Coleta TODOS os dados do formulário
        data = {
            "nome": request.form.get('nome'),
            "sobrenome": request.form.get('sobrenome'),
            "email": request.form.get('email'),
            "senha": request.form.get('senha'),
            "data_nascimento": request.form.get('data_nascimento'),
            "tipo_usuario": "aluno" # Define o tipo diretamente
        }

        register_url = f"{API_BASE_URL}/auth/register"
        
        try:
            # 2. Chama a API Node.js (rota /register agora aceita mais dados)
            response = requests.post(register_url, json=data)
            response_data = response.json()

            if response.status_code == 201:
                # SUCESSO: Redireciona para o login ou mostra mensagem
                return redirect(url_for('login', msg="Registro realizado! Faça login."))
            else:
                # FALHA: Mostra erro da API
                erro_msg = response_data.get("message", "Erro ao registrar.")
                return render_register_form(erro_msg) # Mostra o form de novo com erro

        except requests.exceptions.ConnectionError:
            return render_register_form("ERRO: API Node.js offline.")
        except Exception as e:
             return render_register_form(f"Erro inesperado: {e}")

    # Método GET: Apenas mostra o formulário
    return render_register_form()

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Rota de autenticação do sistema.
    
    GET: Exibe o formulário de login
    POST: Processa a tentativa de login
    
    O processo de login inclui:
    1. Verificação de sessão existente
    2. Validação das credenciais via API
    3. Armazenamento do token e tipo de usuário na sessão
    4. Redirecionamento para o dashboard apropriado
    
    Returns:
        - GET: Página de login
        - POST sucesso: Redirecionamento para dashboard
        - POST erro: Página de login com mensagem de erro
    """
    # Verifica se já existe uma sessão ativa
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




# ------------------------------------------------------
# Interface Admin
# -----------------------------------------------------

@app.route('/painel/admin', methods=['GET', 'POST'])
@require_login
def painel_admin():
    user_type = session.get(SESSION_KEY_TYPE)
    token = session.get(SESSION_KEY_TOKEN)
    
    # Proteção: Apenas Admin pode acessar
    if user_type != 'admin' or not token:
        return redirect(url_for('logout'))

    # Variáveis de feedback (se houver um POST)
    feedback_msg = None
    feedback_cls = None
    
    # ----------------------------------------------------
    # LÓGICA POST (Processamento dos Formulários)
    # ----------------------------------------------------
    if request.method == 'POST':
        action = request.form.get('action')
        
        try:
            result = process_admin_action(action, request.form, token)
            feedback_msg = result['msg']
            feedback_cls = result['cls']
            # Redireciona para o GET com a mensagem de feedback
            return redirect(url_for('painel_admin', msg=feedback_msg, cls=feedback_cls))
            
        except requests.exceptions.RequestException:
            feedback_msg = "ERRO DE CONEXÃO com a API Node.js."
            feedback_cls = "error"
        except Exception as e:
            feedback_msg = f"Erro inesperado: {e}"
            feedback_cls = "error"
            
        # Se houver um erro de exceção, recarrega a página com a mensagem
        return redirect(url_for('painel_admin', msg=feedback_msg, cls=feedback_cls))


    # ----------------------------------------------------
    # LÓGICA GET (Exibir Formulários e Dados)
    # ----------------------------------------------------
    
    # Busca recursos (Turmas e Disciplinas) para preencher os <select>
    recursos = fetch_admin_resources(token)
    
    # Obtém mensagem do redirecionamento
    feedback_msg = request.args.get('msg')
    feedback_cls = request.args.get('cls')
    
    conteudo_admin_html = render_admin_content(user_type, recursos, feedback_msg, feedback_cls)
    
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
    
def process_admin_action(action, form_data, token):
    """Processa a ação específica de POST para a API Node.js."""
    try:
        url = None
        payload = {}
        
        if action == 'create_professor':
            url = f"{API_BASE_URL}/auth/register"
            payload = {"email": form_data.get('email'), "senha": form_data.get('senha'), "tipo_usuario": "professor"}
            method = requests.post
            success_msg = f"Professor {form_data.get('email')} criado com sucesso!"
        
        elif action == 'create_turma':
            url = f"{API_BASE_URL}/academico/turmas"
            payload = {"nome_turma": form_data.get('nome_turma'), "ano": int(form_data.get('ano'))}
            method = requests.post
            success_msg = "Turma criada com sucesso!"

        elif action == 'assign_professor':
            url = f"{API_BASE_URL}/academico/turmas/atribuir-professor"
            payload = {"turma_id": int(form_data.get('turma_id')), "professor_id": int(form_data.get('professor_id'))}
            method = requests.put
            success_msg = f"Professor {form_data.get('professor_id')} atribuído à turma com sucesso!"
        
        # ⚠️ (FUTURO) Caso para Associar Disciplinas
        elif action == 'assign_disciplinas':
            # 1. Obter os dados brutos
            turma_id_str = form_data.get('turma_id_disciplina')
            disciplinas_list_str = form_data.getlist('disciplinas')

            # 2. Validar
            if not turma_id_str or not disciplinas_list_str:
                 return {"msg": "Erro: Selecione uma Turma e pelo menos uma Disciplina.", "cls": "error"}

            # 3. Tentar a conversão
            try:
                turma_id_disciplina = int(turma_id_str)
                disciplina_ids = [int(x) for x in disciplinas_list_str]
            except ValueError:
                 print(f"[ADMIN POST - assign_disciplinas] Erro ao converter: turma='{turma_id_str}', disciplinas='{disciplinas_list_str}'")
                 return {"msg": "Erro: IDs de Turma ou Disciplina inválidos.", "cls": "error"}

            # 4. Montar payload e definir chamada
            url = f"{API_BASE_URL}/academico/turmas/atribuir-disciplinas" # Verifique se a rota na API é 'atribuir-disciplinas'
            payload = {"turma_id": turma_id_disciplina, "disciplina_ids": disciplina_ids}
            method = requests.post
            # success_msg não é mais necessário aqui, pegaremos da API

            # 🔥 DEBUG LOGS (Manter por enquanto) 🔥
            print(f"\n--- [Flask POST Debug - Assign Disciplinas] ---")
            print(f"URL Alvo: {url}")
            print(f"Payload Enviado: {payload}")
            print(f"Token (primeiros 10 chars): Bearer {token[:10]}...")
            print(f"---------------------------------------------\n")
            
            # --- 👇 CÓDIGO FALTANTE: EXECUTAR A REQUISIÇÃO E PROCESSAR RESPOSTA 👇 ---
            try:
                response = method(url, json=payload, headers={"Authorization": f"Bearer {token}"})
                
                # 🔥 LOG ANTES DO JSON PARSE 🔥
                print(f"[Flask POST Debug] Status Recebido: {response.status_code}")
                print(f"[Flask POST Debug] Texto da Resposta Bruta: '{response.text}'") # Loga o texto

                # Tenta processar como JSON DEPOIS de logar
                response_data = response.json() 

                print(f"[Flask POST Debug] Resposta JSON API: {response_data}") 
                
                result_msg = response_data.get("message", f"Erro desconhecido na API ({response.status_code})")
                
                if response.status_code in [200, 201]:
                    result_cls = "success"
                else:
                    result_cls = "error"
                
                return {"msg": result_msg, "cls": result_cls}
                

            except requests.exceptions.RequestException as e:
                # Captura erro de conexão
                print(f"[Flask POST Debug] Erro de Conexão: {e}")
                return {"msg": f"Erro de Conexão com API: {e}", "cls": "error"}
            except Exception as e: 
                # Captura outros erros (ex: API não retornou JSON válido)
                print(f"[Flask POST Debug] Erro ao processar resposta da API: {e}")
                return {"msg": f"Erro ao processar resposta da API: {e}", "cls": "error"}

        elif action == 'enroll_student':
            url = f"{API_BASE_URL}/academico/matriculas"
            payload = {
                "aluno_id": int(form_data.get('aluno_id')), 
                "turma_id": int(form_data.get('turma_id_matricula')), 
                "disciplina_id": int(form_data.get('disciplina_id_matricula'))
            }
            method = requests.post
            success_msg = f"Aluno {form_data.get('aluno_id')} matriculado com sucesso!"

        elif action == 'create_disciplina':
            url = f"{API_BASE_URL}/academico/disciplinas"
            payload = {
                "nome_disciplina": form_data.get('nome_disciplina'),
                "descricao": form_data.get('descricao') 
            }
            method = requests.post
            success_msg = f"Disciplina '{form_data.get('nome_disciplina')}' criada com sucesso!"

        elif action == 'remove_disciplina_from_turma':
            url = f"{API_BASE_URL}/academico/turmas/remover-disciplina"
            try:
                payload = {
                    "turma_id": int(form_data.get('turma_id')),
                    "disciplina_id": int(form_data.get('disciplina_id'))
                }
            except ValueError:
                return {"msg": "Erro: ID da Turma ou Disciplina inválido (remove).", "cls": "error"}
            
            method = requests.post # Usando POST como definido na API (para formulário HTML)
            success_msg = "Disciplina desassociada da turma com sucesso!"

        # 🔥 BLOCO FALTANTE 2: Excluir Disciplina (Global) 🔥
        elif action == 'delete_disciplina':
            try:
                disciplina_id = int(form_data.get('disciplina_id'))
            except ValueError:
                return {"msg": "Erro: ID da Disciplina inválido (delete).", "cls": "error"}

            # A rota da API é DELETE /api/academico/disciplinas/:id
            url = f"{API_BASE_URL}/academico/disciplinas/{disciplina_id}"
            payload = None # DELETE não precisa de payload
            method = requests.delete # Usando o método HTTP DELETE
            success_msg = "Disciplina excluída permanentemente com sucesso!"
        
        elif action == 'delete_matricula':
            try:
                matricula_id = int(form_data.get('matricula_id'))
            except ValueError:
                return {"msg": "Erro: ID da Matrícula inválido.", "cls": "error"}

            # A rota da API é DELETE /api/academico/matriculas/:id
            url = f"{API_BASE_URL}/academico/matriculas/{matricula_id}"
            payload = None
            method = requests.delete # Método HTTP DELETE
            success_msg = f"Matrícula {matricula_id} excluída com sucesso!"

        elif action == 'delete_notas_da_disciplina':
            try:
                disciplina_id = int(form_data.get('disciplina_id_para_limpar'))
            except ValueError:
                return {"msg": "Erro: ID da Disciplina inválido.", "cls": "error"}

            # A rota da API é DELETE /api/academico/disciplinas/:id/notas
            url = f"{API_BASE_URL}/academico/disciplinas/{disciplina_id}/notas"
            payload = None
            method = requests.delete # Método HTTP DELETE
            success_msg = f"Notas da disciplina {disciplina_id} excluídas com sucesso!"
        
        else:
            return {"msg": f"Ação desconhecida: {action}", "cls": "error"}
        
        if url and method is not None:
            # Se não houver payload (como no DELETE), envia None
            json_payload = payload if payload else None
            
            response = method(url, json=json_payload, headers={"Authorization": f"Bearer {token}"})
            
            response_data = {}
            try:
                response_data = response.json() # Tenta ler o JSON
            except requests.exceptions.JSONDecodeError:
                pass # API pode não retornar JSON em alguns erros

            # Verifica sucesso
            if response.status_code in [200, 201]:
                success_msg = response_data.get("message", success_msg)
                return {"msg": success_msg, "cls": "success"}
            else:
                # Tenta pegar a mensagem de erro da API
                error_msg = response_data.get("message", f"Erro na API ({response.status_code})")
                return {"msg": error_msg, "cls": "error"}
        else:
             return {"msg": f"Erro interno: Configuração incompleta para a ação '{action}'.", "cls": "error"}

    except requests.exceptions.RequestException as e:
        return {"msg": f"Erro de Conexão com API: {e}", "cls": "error"}
    except Exception as e:
        print(f"[ADMIN POST - Exception] Erro: {e}") 
        return {"msg": f"Erro inesperado no processamento: {e}", "cls": "error"}

# --- AUXILIAR: BUSCAR RECURSOS PARA SELECTS ---
def fetch_admin_resources(token):
    """Busca listas de turmas, disciplinas, professores e alunos."""
    headers = {"Authorization": f"Bearer {token}"}
    
    resources = {'turmas': [], 'disciplinas': [], 'professores': [], 'alunos': []} # Default

    try:
        # Busca Turmas
        turmas_res = requests.get(f"{API_BASE_URL}/academico/turmas", headers=headers)
        if turmas_res.status_code == 200:
            resources['turmas'] = turmas_res.json().get('turmas', [])

        # Busca Disciplinas
        disciplinas_res = requests.get(f"{API_BASE_URL}/academico/disciplinas", headers=headers)
        if disciplinas_res.status_code == 200:
            resources['disciplinas'] = disciplinas_res.json().get('disciplinas', [])
            
        # 🔥 Busca Professores 🔥
        professores_res = requests.get(f"{API_BASE_URL}/academico/professores", headers=headers)
        if professores_res.status_code == 200:
            resources['professores'] = professores_res.json().get('professores', [])

            

        # 🔥 Busca Alunos 🔥
        alunos_res = requests.get(f"{API_BASE_URL}/academico/alunos", headers=headers)
        if alunos_res.status_code == 200:
            resources['alunos'] = alunos_res.json().get('alunos', [])
        

    except requests.exceptions.RequestException as e:
        print(f"[FETCH RESOURCES ERROR]: {e}") 

    # 👇 LOG FINAL DA FUNÇÃO 👇
    print(f"--- [fetch_admin_resources] Retornando Recursos ---\n")
    return resources
# ROTAS DE INTERFACE POR PERFIL
# --------------------------------------------------------------------------------------

@app.route('/painel/aluno')
@require_login
def painel_aluno():
    """Página inicial (Dashboard) após o login do aluno."""
    
    # 1. Proteção: Garante que é realmente um aluno logado
    if session.get(SESSION_KEY_TYPE) != 'aluno':
        return redirect(url_for('dashboard')) 

    token = session.get(SESSION_KEY_TOKEN)
    boletim_data = []
    feedback = None

    try:
        # 2. Busca os dados do boletim na API (a mesma chamada da rota /boletim)
        response = requests.get(
            f"{API_BASE_URL}/academico/boletim", 
            headers={"Authorization": f"Bearer {token}"}
        )
        response_data = response.json()

        if response.status_code == 200 and 'boletim' in response_data:
            boletim_data = response_data['boletim']
        else:
            feedback = response_data.get("message", "Erro ao carregar dados.")
            
    except requests.exceptions.RequestException:
        feedback = "ERRO DE CONEXÃO com API Node.js."
    except Exception as e: 
        feedback = f"Erro inesperado ao processar dados: {e}"

    # 3. Processar os dados para o Dashboard (Média Geral)
    media_geral = "N/D"
    total_disciplinas = 0
    notas_validas = []
    faltas = 0

    if boletim_data:
        for item in boletim_data:
            total_disciplinas += 1
            media_final_str = item.get('media_final')
            if media_final_str is not None:
                try:
                    notas_validas.append(Decimal(str(media_final_str)))
                except Exception:
                    pass # Ignora notas inválidas
            faltas += int(item.get('total_faltas', 0))
    
    if notas_validas:
        media_geral_decimal = sum(notas_validas) / Decimal(len(notas_validas))
        media_geral = formatar_nota(media_geral_decimal, bold=True) # Reusa a função de formatação

    # 4. Constrói o HTML do Dashboard do Aluno (Melhorado)
    
    # (Estilos CSS para os cards do dashboard)
    style_bloco = "background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center;"
    style_h2_bloco = "margin: 0; font-size: 2.5rem; color: var(--accent);"
    style_p_bloco = "margin: 5px 0 0 0; color: var(--muted);"

    conteudo_aluno_html = f'''
    <h1>Painel do Aluno (Dashboard)</h1>
    <p>Olá, Aluno! Este é o resumo do seu progresso acadêmico.</p>
    
    {f'<p style="color:red; font-weight: bold;">{escape(feedback)}</p>' if feedback else ''}

    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 30px;">
        
        <div style="{style_bloco}">
            <h2 style="{style_h2_bloco}">{media_geral}</h2>
            <p style="{style_p_bloco}">Média Geral (NP1+NP2)</p>
        </div>
        
        <div style="{style_bloco}">
            <h2 style="{style_h2_bloco}">{total_disciplinas}</h2>
            <p style="{style_p_bloco}">Disciplinas Matriculadas</p>
        </div>
        
        <div style="{style_bloco}">
            <h2 style="{style_h2_bloco}">{faltas}</h2>
            <p style="{style_p_bloco}">Total de Faltas</p>
        </div>
        
    </div>
    
    <div style="margin-top: 40px;">
        <h3>Ações Rápidas</h3>
        <a href="{url_for('boletim')}" style="background: var(--accent); color: white; padding: 10px 15px; border-radius: 4px; text-decoration: none;">
            Ver Boletim Detalhado
        </a>
    </div>
    '''
    
    # 5. Renderiza usando a base com a sidebar
    # (Certifique-se que 'render_base' é a função com a sidebar!)
    return render_base(conteudo_aluno_html, "Painel do Aluno")

def formatar_nota(nota_str, bold=False):
    """
    Converte a string da nota (ou None) para Decimal, formata para 1 casa decimal,
    e trata erros de notação científica ou valores inválidos.
    """
    # Valor padrão se a nota for None (não lançada)
    if nota_str is None:
        return '<span style="color: grey;">---</span>'
        
    try:
        # 1. Converte a string (ou float) para Decimal para precisão
        nota_decimal = Decimal(str(nota_str)) 
        # 2. Arredonda para 1 casa decimal
        nota_formatada = nota_decimal.quantize(Decimal('0.0'), rounding=ROUND_HALF_UP)
        # 3. Converte para string
        resultado_str = str(nota_formatada) 

        # Aplica negrito se for a média final
        if bold:
            return f'<strong style="color: #0056b3;">{resultado_str}</strong>'
        return resultado_str
        
    except Exception:
        # Se a conversão falhar (valor inválido)
        return f'<span style="color: red;">Inválido</span>'




@app.route('/boletim')
@require_login # Protege a rota, garantindo que o usuário está logado
def boletim():
    """Busca dados de notas na API Node.js e exibe a tabela do boletim."""
    
    # Opcional: Verificar se é aluno (se outros perfis não devem ver)
    if session.get(SESSION_KEY_TYPE) != 'aluno':
        return render_base("<h1>Acesso Negado</h1><p>Apenas alunos podem visualizar o boletim.</p>", "Acesso Negado")

    token = session.get(SESSION_KEY_TOKEN)
    boletim_data = [] # Lista para armazenar as notas
    feedback = None   # Mensagem para o usuário

    try:
        # 1. Chama a API Node.js para buscar o boletim do aluno logado
        response = requests.get(
            f"{API_BASE_URL}/academico/boletim", 
            headers={"Authorization": f"Bearer {token}"}
        )
        response_data = response.json()

        # 2. Processa a resposta da API
        if response.status_code == 200 and 'boletim' in response_data:
            boletim_data = response_data['boletim'] # Pega a lista de notas/disciplinas
            feedback = "Seu boletim foi carregado."
            feedback_cls = "success" # Classe CSS (opcional)
        else:
            feedback = response_data.get("message", "Erro ao carregar dados do boletim da API.")
            feedback_cls = "error"
            
    except requests.exceptions.RequestException:
        feedback = "ERRO DE CONEXÃO: Não foi possível conectar à API. Verifique o servidor Node.js."
        feedback_cls = "error"
    except Exception as e: # Captura outros erros (ex: JSON inválido)
        feedback = f"Erro inesperado ao processar dados: {e}"
        feedback_cls = "error"

    # 3. Constrói o HTML da Tabela do Boletim
    tabela_html = f'<h1>Meu Boletim</h1>'
    tabela_html += f'<p class="{feedback_cls}" style="margin-bottom: 20px;">{escape(feedback)}</p>'
    
    if not boletim_data:
        tabela_html += '<p style="color: grey;">Nenhuma nota encontrada para você.</p>'
    else:
        tabela_html += '''
        <table class="boletim" style="width:100%; border-collapse: collapse;">
            <thead>
                <tr style="background-color: #f0f0f0;">
                    <th style="padding: 10px; border: 1px solid #ddd;">Disciplina</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">Nota NP1</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">Nota NP2</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">Média Final</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">Faltas (Simuladas)</th> 
                </tr>
            </thead>
            <tbody>
        '''
        for item in boletim_data:
            # Pega os dados REAIS da API
            disciplina = escape(item.get('nome_disciplina', 'Disciplina Desconhecida'))
            nota_np1 = formatar_nota(item.get('nota_np1'))
            nota_np2 = formatar_nota(item.get('nota_np2'))
            media_final = formatar_nota(item.get('media_final'), bold=True)
            faltas = item.get('total_faltas', 0)
            
            tabela_html += f"""
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 10px; border: 1px solid #ddd;">{disciplina}</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{nota_np1}</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{nota_np2}</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{media_final}</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{faltas}</td> 
            </tr>
            """
        tabela_html += '</tbody></table>'
    
    # Renderiza usando o layout com sidebar
    return render_base(tabela_html, page_title="Meu Boletim")


# ----------------------------------------------------------------------
# ROTA PRINCIPAL DO PROFESSOR
# ----------------------------------------------------------------------

@app.route('/painel/professor', methods=['GET', 'POST'])
@require_login
def painel_professor():
    """
    Painel principal do professor.
    
    Esta rota oferece duas funcionalidades principais:
    GET:
    - Lista todas as turmas atribuídas ao professor
    - Exibe formulário para lançamento de notas
    - Mostra mensagens de feedback de operações anteriores
    
    POST:
    - Processa o lançamento de notas
    - Valida e envia os dados para a API
    - Retorna feedback das operações
    
    O acesso é restrito a usuários do tipo 'professor' ou 'admin'.
    
    Returns:
        GET: Página HTML do painel do professor
        POST: Redirecionamento com mensagem de sucesso/erro
    """
    user_type = session.get(SESSION_KEY_TYPE)
    token = session.get(SESSION_KEY_TOKEN)
    
    # Proteção (redundante com @require_login, mas boa prática)
    if user_type not in ['professor', 'admin'] or not token:
        return redirect(url_for('logout'))

    turmas = []
    message = request.args.get('msg') # Mensagem vinda de um redirect (GET)
    message_class = request.args.get('cls')
    notas_form_result = None # Feedback específico do POST de nota

    # ----------------------------------------------------
    # LÓGICA DE LANÇAMENTO DE NOTAS (POST)
    # ----------------------------------------------------
    if request.method == 'POST':
        # Verifica se a ação é lançar nota (caso haja mais formulários no futuro)
        action = request.form.get('action', 'lancar_nota') # Assume 'lancar_nota' por padrão
        
        if action == 'lancar_nota':
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
                    notas_form_result = {"msg": error_data.get("message", f"Erro na API ({response.status_code})"), "cls": "error"}

            except requests.exceptions.RequestException:
                notas_form_result = {"msg": "ERRO: Não foi possível conectar à API Node.js.", "cls": "error"}
            except ValueError:
                 notas_form_result = {"msg": "Erro: ID do Aluno, ID da Disciplina e Nota devem ser números válidos.", "cls": "error"}
            
            # Após o POST, continua para o GET para recarregar a página com feedback
    
    # ----------------------------------------------------
    # LÓGICA DE BUSCA DE TURMAS (GET - Sempre executa, mesmo após POST)
    # ----------------------------------------------------
    try:
        # Chama a API Node.js (rota correta: /professor/turmas)
        response_turmas = requests.get(
            f"{API_BASE_URL}/academico/professor/turmas", 
            headers={"Authorization": f"Bearer {token}"}
        )
        response_data_turmas = response_turmas.json()
        
        if response_turmas.status_code == 200 and 'turmas' in response_data_turmas:
            turmas = response_data_turmas.get('turmas', [])
            # A mensagem de busca só é relevante se não houver feedback do POST
            if not notas_form_result and not message: 
                message = "Suas turmas foram carregadas."
                message_class = "success"
        else:
            # Se a busca falhar, mas houve um POST, não sobrescreve o feedback do POST
            if not notas_form_result: 
                message = response_data_turmas.get('message', 'Erro ao carregar turmas da API.')
                message_class = 'error'
            
    except requests.exceptions.RequestException:
        if not notas_form_result: # Só mostra erro de conexão se não houver feedback de POST
            message = "ERRO: Não foi possível conectar à API Node.js."
            message_class = "error"
            
    # Renderiza o conteúdo final passando todos os dados necessários
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
    tabela_alunos_html = build_alunos_table_gestao(turma_id, disciplina_id, alunos, feedback)
    
    return render_base(tabela_alunos_html, f"Gerenciar Turma {turma_id}")

@app.route('/lancar_nota_form', methods=['POST'])
@require_login
def lancar_nota_form():
    """Processa o formulário de lançamento de nota e chama a API Node.js."""
    user_type = session.get(SESSION_KEY_TYPE)
    token = session.get(SESSION_KEY_TOKEN)

    
    # Proteção: Apenas Professor ou Admin pode lançar nota
    if user_type not in ['professor', 'admin'] or not token:
        # Idealmente, redireciona para login com mensagem de erro
        return redirect(url_for('logout')) 

    # 1. Obter dados do formulário
    aluno_id = request.form.get('aluno_id')
    disciplina_id = request.form.get('disciplina_id')
    valor_nota = request.form.get('valor_nota')
    tipo_avaliacao = request.form.get('tipo_avaliacao') # ⬅️ Pega o tipo
    turma_id = request.form.get('turma_id')

    feedback_msg = "Dados inválidos."
    feedback_cls = "error"

    # 2. Validar e tentar chamar a API
    if aluno_id and disciplina_id and valor_nota and turma_id:
        try:
            payload = {
                "aluno_id": int(aluno_id),
                "disciplina_id": int(disciplina_id),
                "valor_nota": float(valor_nota),
                "tipo_avaliacao": tipo_avaliacao # ⬅️ Envia o tipo para a API
            }
            
            # Chama a API Node.js /academico/notas
            response = requests.post(
                f"{API_BASE_URL}/academico/notas",
                json=payload,
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 201:
                feedback_msg = f"Nota ({tipo_avaliacao}) lançada/atualizada!"
                feedback_cls = "success"
            else:
                # Tenta pegar a mensagem de erro da API (ex: nota duplicada, aluno não matriculado)
                try:
                    feedback_msg = response.json().get("message", f"Erro na API ({response.status_code})")
                except Exception:
                     feedback_msg = f"Erro desconhecido na API ({response.status_code})"
                feedback_cls = "error"
        
        except ValueError:
            feedback_msg = "Erro: IDs ou Nota devem ser números válidos."
            feedback_cls = "error"
        except requests.exceptions.RequestException:
            feedback_msg = "ERRO DE CONEXÃO com a API Node.js."
            feedback_cls = "error"
    
    # 3. Redireciona DE VOLTA para a tela de gerenciamento com a mensagem
    return redirect(url_for('gerenciar_turma', 
                            turma_id=turma_id, 
                            disciplina_id=disciplina_id, 
                            msg=feedback_msg, 
                            cls=feedback_cls))

@app.route('/marcar_presenca_form', methods=['POST'])
@require_login
def marcar_presenca_form():
    """Processa o formulário de marcar presença e chama a API Node.js."""
    user_type = session.get(SESSION_KEY_TYPE)
    token = session.get(SESSION_KEY_TOKEN)
    
    if user_type not in ['professor', 'admin'] or not token:
        return redirect(url_for('logout'))

    # 1. Obter dados do formulário
    matricula_id = request.form.get('matricula_id')
    status = request.form.get('status')
    turma_id = request.form.get('turma_id')
    disciplina_id = request.form.get('disciplina_id')
    
    feedback_msg = "Dados inválidos para marcar presença."
    feedback_cls = "error"

    # 2. Validar e chamar a API /academico/presenca
    if matricula_id and status and turma_id and disciplina_id:
        try:
            payload = {"matricula_id": int(matricula_id), "status": status}
            
            response = requests.post(
                f"{API_BASE_URL}/academico/presenca",
                json=payload,
                headers={"Authorization": f"Bearer {token}"}
            )
            response_data = response.json() # Tenta ler a resposta

            if response.status_code == 201:
                feedback_msg = f"Presença ({status}) marcada!"
                feedback_cls = "success"
            elif response.status_code == 409: # Conflito (já marcado hoje)
                 feedback_msg = response_data.get("message", "Já marcado hoje.")
                 feedback_cls = "warning" 
            else:
                feedback_msg = response_data.get("message", "Erro na API.")
                feedback_cls = "error"
                
        except ValueError:
             feedback_msg = "Erro: ID de Matrícula inválido."
             feedback_cls = "error"
        except requests.exceptions.RequestException:
            feedback_msg = "ERRO DE CONEXÃO com a API Node.js."
            feedback_cls = "error"
            
    # 3. Redireciona de volta para a tela de gerenciamento com feedback
    return redirect(url_for('gerenciar_turma', 
                            turma_id=turma_id, 
                            disciplina_id=disciplina_id, 
                            msg=feedback_msg, 
                            cls=feedback_cls))


# Função auxiliar (adicionar ao main.py)

# 02_sistema_python/main.py

def build_alunos_table_gestao(turma_id, disciplina_id, alunos, feedback):
    """Constrói a tabela de alunos com formulários de ação (Nota/Presença)."""
    from flask import url_for # Garante que url_for funciona
    
    html = f'<h1>Gestão de Turma/Disciplina</h1>'
    html += f'<h2>Turma: {turma_id} | Disciplina: {disciplina_id}</h2>'
    html += f'<p style="color:red; font-weight: bold;">{escape(feedback)}</p>'
    
    # Links de Navegação (Voltar e Relatório C)
    html += f'''
    <div style="margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 10px;">
        <a href="{url_for('painel_professor')}" 
           style="background: #6c757d; color: white; padding: 8px 15px; border-radius: 4px; text-decoration: none;">
           &laquo; Voltar para Minhas Turmas 
        </a>
        <a href="{url_for('relatorio_desempenho', turma_id=turma_id, disciplina_id=disciplina_id)}" 
           style="background: #007bff; color: white; padding: 8px 15px; border-radius: 4px; text-decoration: none;">
           Ver Relatório de Desempenho (C)
        </a>
    </div>
    '''
    
    # --- Tabela de Alunos (Início) ---
    # ⚠️ Usamos o estilo da classe 'boletim' que você já definiu
    html += '''
    <table class="boletim" style="width: 100%; border-collapse: collapse; margin-top: 20px;">
        <thead>
            <tr style="background-color: #f0f0f0; text-align: left;">
                <th style="padding: 10px; border: 1px solid #ddd;">ID Aluno</th>
                <th style="padding: 10px; border: 1px solid #ddd;">Nome</th>
                <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">NP1</th>
                <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">NP2</th>
                <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Média Final</th>
                <th style="padding: 10px; border: 1px solid #ddd;">Lançar Nova Nota</th>
                <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Presença</th>
            </tr>
        </thead>
        <tbody>
    '''
    
    # --- Loop pelos Alunos (Ponto Crítico) ---
    if not alunos:
        html += '<tr><td colspan="5" style="padding: 10px; border: 1px solid #ddd; text-align: center;">Nenhum aluno matriculado nesta turma/disciplina.</td></tr>'
    else:
        # Se a lista NÃO está vazia, o loop executa
        for aluno in alunos:
            # Pega os dados com segurança
            aluno_id = aluno.get('aluno_id', 'Erro')
            nome = escape(aluno.get('nome', ''))
            sobrenome = escape(aluno.get('sobrenome', ''))
            nome_completo = f"{nome} {sobrenome}".strip()
            nota_np1 = aluno.get('nota_np1')
            nota_np2 = aluno.get('nota_np2')
            media_final = aluno.get('media_final')
            
            # Pega a média (que a API chama de 'nota_atual' ou 'media_final')
            
            
            matricula_id = aluno.get('matricula_id', '') # Essencial para Presença

            # Constrói a linha da tabela (F-string corrigida)
            html += f'''
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 8px; border: 1px solid #ddd;">{aluno_id}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{nome_completo}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{nota_np1}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{nota_np2}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{media_final}</td>
                
                <td style="padding: 8px; border: 1px solid #ddd;">
                    <form action="{url_for('lancar_nota_form')}" method="POST" style="display:inline-flex; gap: 5px; align-items: center;">
                        <input type="hidden" name="aluno_id" value="{aluno_id}">
                        <input type="hidden" name="disciplina_id" value="{disciplina_id}">
                        <input type="hidden" name="turma_id" value="{turma_id}">
                        
                        <input type="number" step="0.1" min="0" max="10" name="valor_nota" placeholder="Nota" required style="width: 70px; padding: 4px; border-radius: 4px;">
                        <select name="tipo_avaliacao" required style="padding: 4px; border-radius: 4px;">
                            <option value="NP1">NP1</option>
                            <option value="NP2">NP2</option>
                            <option value="Exame">Exame</option>
                        </select>
                        <button type="submit" style="background: var(--accent); ...">Lançar</button>
                    </form>
                </td>
                
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">
                    <form action="{url_for('marcar_presenca_form')}" method="POST" style="display:inline;">
                    <input type="hidden" name="matricula_id" value="{matricula_id}">
                    <input type="hidden" name="status" value="presente">
                    
                    <input type="hidden" name="turma_id" value="{turma_id}">
                    <input type="hidden" name="disciplina_id" value="{disciplina_id}">
                    
                    <button type="submit" style="background: green; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">P</button>
                </form>
                
                
                <form action="{url_for('marcar_presenca_form')}" method="POST" style="display:inline;">
                    <input type="hidden" name="matricula_id" value="{matricula_id}">
                    <input type="hidden" name="status" value="ausente">
                    
                    <input type="hidden" name="turma_id" value="{turma_id}">
                    <input type="hidden" name="disciplina_id" value="{disciplina_id}">
                    
                    <button type="submit" style="background: red; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">F</button>
                </form>
                </td>
            </tr>
            '''
    
    html += '</tbody></table>'
    return html

@app.route('/relatorio/desempenho/<int:turma_id>/<int:disciplina_id>')
@require_login # Garante que está logado
def relatorio_desempenho(turma_id, disciplina_id):
    if lib_c is None: # Verifica se a DLL carregou
        return render_base("<h1>Erro</h1><p>Módulo de algoritmos C não foi carregado.</p>", "Erro")
        
    token = session.get(SESSION_KEY_TOKEN)
    
    # 1. Busca os dados dos alunos na API Node.js
    alunos_data = []
    try:
        response = requests.get(
            f"{API_BASE_URL}/academico/turmas/{turma_id}/disciplinas/{disciplina_id}/alunos", 
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            alunos_data = response.json().get('alunos', [])
        else:
            raise Exception(f"Erro da API: {response.json().get('message')}")
    except Exception as e:
        return render_base(f"<h1>Erro ao buscar dados</h1><p>{e}</p>", "Erro")

    # ... (Prepara os dados para o C, filtrando alunos com média) ...
    desempenhos = []
    medias_validas = []
    for aluno in alunos_data:
        media_aluno_str = aluno.get('media_final')
        if media_aluno_str is not None:
            try:
                media_float = float(media_aluno_str)
                medias_validas.append(Decimal(media_aluno_str)) 
                desempenhos.append(
                    DesempenhoAluno(
                        id_aluno=int(aluno['aluno_id']), 
                        media_final=media_float
                    )
                )
            except (ValueError, TypeError):
                continue

    if not desempenhos:
         return render_base("<h1>Relatório de Desempenho</h1><p>Nenhum aluno com média lançada para ordenar.</p>", "Relatório")
    
    # Calcula a média da turma (como fizemos antes)
    media_da_turma = Decimal('0.0')
    if medias_validas:
        media_da_turma = sum(medias_validas) / Decimal(len(medias_validas))
    media_da_turma_str = media_da_turma


    # 2. Chama a função C para ordenar
    count = len(desempenhos)
    ArrayType = DesempenhoAluno * count
    array_c = ArrayType(*desempenhos)
    
    lib_c.ordenar_por_desempenho(array_c, count) # ⬅️ CHAMADA CRÍTICA AO C

    # 3. Renderiza o HTML com os dados ordenados
    html = f"<h1>Relatório de Desempenho (Turma {turma_id} / Disc {disciplina_id})</h1>"
    html += f'<h2 style="color: #333;">Média Geral da Turma: {media_da_turma_str}</h2>'
    html += "<h3>Ranking de Desempenho (Ordenado pelo módulo C)</h3>"
    html += "<table class='boletim'><thead><tr><th>Ranking</th><th>ID Aluno</th><th>Média Final</th></tr></thead><tbody>"
    
    # Itera sobre o array que o C modificou
    for i, aluno in enumerate(array_c): 
        html += f"<tr><td>{i+1}º</td><td>{aluno.id_aluno}</td><td>{aluno.media_final:.2f}</td></tr>"
        
    html += "</tbody></table>"
    html += f"<p style='margin-top: 20px;'><a href='{url_for('gerenciar_turma', turma_id=turma_id, disciplina_id=disciplina_id)}'>&laquo; Voltar para Gestão</a></p>"
    
    return render_base(html, "Relatório de Desempenho")

# ⚠️ Adicione uma rota dummy para o FORM POST (lancar_nota_form) para que os links funcionem.

@app.route('/dashboard')
@require_login
def dashboard():
    """
    Rota central de redirecionamento após o login.
    
    Esta função atua como um hub de redirecionamento inteligente:
    - Verifica o tipo do usuário na sessão
    - Redireciona para o painel apropriado:
        * Alunos -> painel_aluno
        * Professores -> painel_professor
        * Administradores -> painel_admin
    
    A rota é protegida pelo decorator @require_login.
    
    Returns:
        redirect: Redirecionamento para o painel específico do usuário
    """
    user_type = session.get(SESSION_KEY_TYPE)
    
    # Redireciona para o painel específico
    if user_type == 'aluno':
        return redirect(url_for('painel_aluno'))
    elif user_type == 'professor': 
        return redirect(url_for('painel_professor'))
    elif user_type == 'admin':    
        return redirect(url_for('painel_admin')) 
    else:
        return redirect(url_for('logout'))


@app.route('/')
def index():
    """
    Rota raiz do sistema.
    
    Comportamento:
    - Se existe uma sessão ativa: redireciona para o dashboard
    - Se não existe sessão: redireciona para a página de login
    
    Esta rota serve como ponto de entrada principal do sistema.
    
    Returns:
        redirect: Redirecionamento para dashboard ou login
    """
    if SESSION_KEY_TYPE in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


if __name__ == '__main__':
    """
    Ponto de entrada principal da aplicação Flask.
    
    Para executar o sistema:
    1. Certifique-se de que todas as dependências estão instaladas:
       pip install -r requirements.txt
    
    2. Configure as variáveis de ambiente no arquivo .env:
       - API_URL: URL da API Node.js
       - FLASK_SECRET_KEY: Chave secreta para sessions
    
    3. Certifique-se de que a API Node.js está rodando na porta 3000
    
    4. Execute este arquivo:
       python main.py
    
    O servidor iniciará na porta 5000 e estará acessível em:
    http://127.0.0.1:5000
    
    Em desenvolvimento, o modo debug está ativado para facilitar
    a identificação e correção de problemas.
    """
    print("Iniciando servidor Flask (porta 5000)...")
    app.run(debug=True, host='127.0.0.1', port=5000)