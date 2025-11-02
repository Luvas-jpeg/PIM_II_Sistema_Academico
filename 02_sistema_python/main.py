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
from markupsafe import escape, Markup  # Para proteção contra XSS e permitir HTML seguro
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
            input[type="text"], input[type="password"], input[type="email"], input[type="date"] {{
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
        <div class="brand">
            <h2>Cadastro</h2>
        </div>
        {error_html}
        <form method="POST" action="{url_for('registrar')}">
            <label for="nome">Nome:</label>
            <input type="text" name="nome" id="nome" required>
            <label for="sobrenome">Sobrenome:</label>
            <input type="text" name="sobrenome" id="sobrenome">
            <label for="email">E-mail:</label>
            <input type="email" name="email" id="email" required>
            <label for="senha">Senha:</label>
            <input type="password" name="senha" id="senha" required>
            <label for="data_nascimento">Data Nascimento (AAAA-MM-DD):</label>
            <input type="date" name="data_nascimento" id="data_nascimento"> 
            
            <button type="submit">Registrar Aluno</button>
        </form>
        <div class="help">
            <p>Já tem conta? <a href="{url_for('login')}" style="color: var(--accent); text-decoration: none;">Faça Login</a></p>
        </div>
    </div>
    '''
    # Use o render_login_base (sem sidebar)
    return render_login_base(form_html, "Registrar Aluno")

def render_login_form(error_message=None):
    # Conteúdo do seu formulário de login (sem a sidebar)
    error_html = f'<p class="error-message" style="color:#d32f2f;text-align:center;font-size:0.9rem;">{escape(error_message)}</p>' if error_message else ''
    
    form_html = f'''
    <div class="login-card">
        <div class="brand">
            <h2>Login</h2>
        </div>
        {error_html}
        <form method="POST" action="{url_for('login')}">
            <label for="usuario">E-mail:</label>
            <input id="usuario" type="text" name="usuario" required>
            <label for="senha">Senha:</label>
            <input id="senha" type="password" name="senha" required>
            <button type="submit">Entrar</button>
        </form>
        
        <div class="help">
            <p>Não tem uma conta? 
               <a href="{url_for('registrar')}" style="color: var(--accent); text-decoration: none;">Registre-se aqui</a>
            </p>
        </div>
    </div>
    '''
    # Usa render_login_base que já tem o CSS com a imagem de fundo
    return render_login_base(form_html, "Login")

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


def render_professor_content(user_type, turmas, message, message_class):
    """Gera o HTML do painel do professor, incluindo cards visuais."""
    
    # CSS adicional para melhor apresentação
    professor_css = """
    <style>
        .professor-header {
            background: linear-gradient(135deg, #1b55f8 0%, #133fe0 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(27, 85, 248, 0.2);
        }
        .professor-header h1 {
            margin: 0 0 10px 0;
            font-size: 2rem;
        }
        .professor-stats {
            display: flex;
            gap: 20px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.15);
            padding: 15px 20px;
            border-radius: 8px;
            backdrop-filter: blur(10px);
        }
        .stat-card strong {
            display: block;
            font-size: 1.8rem;
            margin-bottom: 5px;
        }
        .stat-card span {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        .turmas-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .turma-card {
            background: #fff;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid #1b55f8;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .turma-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .turma-card-header {
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #eee;
        }
        .turma-card-header h3 {
            margin: 0 0 5px 0;
            color: #1b55f8;
            font-size: 1.3rem;
        }
        .turma-card-header .ano {
            color: #666;
            font-size: 0.9rem;
        }
        .disciplina-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .disciplina-item:last-child {
            margin-bottom: 0;
        }
        .disciplina-nome {
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            font-size: 1.1rem;
        }
        .disciplina-id {
            color: #666;
            font-size: 0.85rem;
            margin-bottom: 12px;
        }
        .btn-gerenciar {
            display: inline-block;
            background: #4CAF50;
            color: white;
            padding: 10px 20px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            transition: background 0.2s;
            width: 100%;
            text-align: center;
            box-sizing: border-box;
        }
        .btn-gerenciar:hover {
            background: #45a049;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            background: #f8f9fa;
            border-radius: 12px;
            color: #666;
        }
        .empty-state-icon {
            font-size: 4rem;
            margin-bottom: 20px;
        }
        .feedback-box {
            padding: 12px 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            border-left: 4px solid;
        }
        .feedback-box.success {
            background: #d4edda;
            border-color: #28a745;
            color: #155724;
        }
        .feedback-box.error {
            background: #f8d7da;
            border-color: #dc3545;
            color: #721c24;
        }
    </style>
    """
    
    # Mensagens de Feedback melhoradas
    feedback_html = ''
    if message:
        box_class = 'success' if message_class == 'success' else 'error'
        feedback_html = f'<div class="feedback-box {box_class}">{escape(message)}</div>'
    
    # Contagem de estatísticas
    total_turmas = len(set(t.get('turma_id') for t in turmas)) if turmas else 0
    total_disciplinas = len(turmas) if turmas else 0
    
    # Header com estatísticas
    header_html = f"""
    <div class="professor-header">
        <h1>Painel do Professor</h1>
        <p style="margin: 0; opacity: 0.9;">Gerencie suas turmas e disciplinas atribuídas</p>
        <div class="professor-stats">
            <div class="stat-card">
                <strong>{total_turmas}</strong>
                <span>Turma{'s' if total_turmas != 1 else ''}</span>
            </div>
            <div class="stat-card">
                <strong>{total_disciplinas}</strong>
                <span>Disciplina{'s' if total_disciplinas != 1 else ''}</span>
            </div>
        </div>
    </div>
    """
    
    # Cards de Turmas e Disciplinas
    if turmas:
        # Agrupa disciplinas por turma
        turmas_agrupadas = {}
        for t in turmas:
            turma_id = t.get('turma_id')
            if turma_id not in turmas_agrupadas:
                 turmas_agrupadas[turma_id] = {
                     'nome': t.get('nome_turma'), 
                     'ano': t.get('ano'), 
                     'disciplinas': []
                 }
            turmas_agrupadas[turma_id]['disciplinas'].append(t)
        
        turmas_cards_html = '<div class="turmas-grid">'
        
        for turma_id, info in turmas_agrupadas.items():
            nome_turma = escape(info['nome'])
            ano = info['ano']
            
            disciplinas_html = ''
            for disc_info in info['disciplinas']:
                disciplina_id = disc_info.get('disciplina_id')
                disciplina_nome = escape(disc_info.get('nome_disciplina', 'N/A'))
                gerenciar_url = url_for('gerenciar_turma', turma_id=turma_id, disciplina_id=disciplina_id) if disciplina_id else '#'
                
                disciplinas_html += f"""
                <div class="disciplina-item">
                    <div class="disciplina-nome">{disciplina_nome}</div>
                    <div class="disciplina-id">ID: {disciplina_id}</div>
                    <a href='{gerenciar_url}' class="btn-gerenciar">
                        Gerenciar Alunos e Notas
                    </a>
                </div>
                """
            
            turmas_cards_html += f"""
            <div class="turma-card">
                <div class="turma-card-header">
                    <h3>{nome_turma}</h3>
                    <div class="ano">Ano: {ano} • ID: {turma_id}</div>
                </div>
                {disciplinas_html}
            </div>
            """
        
        turmas_cards_html += '</div>'
    else:
        turmas_cards_html = """
        <div class="empty-state">
            <h2 style="color: #666; margin-bottom: 10px;">Nenhuma turma atribuída</h2>
            <p>Você ainda não possui turmas ou disciplinas atribuídas.</p>
            <p style="margin-top: 10px; font-size: 0.9rem;">Entre em contato com o administrador do sistema.</p>
        </div>
        """
    
    # Conteúdo final
    return f"""
    {professor_css}
    {header_html}
    {feedback_html}
    <h2 style="color: #333; margin-top: 30px; margin-bottom: 20px;">📋 Minhas Turmas e Disciplinas</h2>
    {turmas_cards_html}
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
    
    # CSS adicional para melhor organização
    admin_css = """
    <style>
        .admin-section { margin-bottom: 40px; }
        .admin-section-title { 
            font-size: 1.5rem; 
            color: #333; 
            margin-bottom: 20px; 
            padding-bottom: 10px; 
            border-bottom: 2px solid #1b55f8; 
        }
        .admin-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px; 
        }
        .admin-card { 
            background: #fff; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.1); 
            border-left: 4px solid #1b55f8;
        }
        .admin-card.danger { border-left-color: #d32f2f; }
        .admin-card.warning { border-left-color: #ff9800; }
        .admin-card h3 { 
            margin-top: 0; 
            color: #1b55f8; 
            font-size: 1.2rem; 
        }
        .admin-card.danger h3 { color: #d32f2f; }
        .admin-card.warning h3 { color: #ff9800; }
        .admin-card label { 
            display: block; 
            margin-top: 10px; 
            margin-bottom: 5px; 
            font-weight: 500; 
            color: #555; 
        }
        .admin-card input, .admin-card select, .admin-card textarea { 
            width: 100%; 
            padding: 8px 12px; 
            border: 1px solid #ddd; 
            border-radius: 4px; 
            font-size: 0.95rem; 
            box-sizing: border-box;
        }
        .admin-card button { 
            margin-top: 15px; 
            padding: 10px 20px; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
            font-weight: 600; 
            font-size: 0.95rem;
        }
        .admin-card button.primary { 
            background: #1b55f8; 
            color: white; 
        }
        .admin-card button.primary:hover { background: #133fe0; }
        .admin-card button.danger { 
            background: #d32f2f; 
            color: white; 
        }
        .admin-card button.danger:hover { background: #b71c1c; }
        .admin-card button.warning { 
            background: #ff9800; 
            color: white; 
        }
        .admin-card button.warning:hover { background: #f57c00; }
        .info-box { 
            background: #e3f2fd; 
            padding: 12px; 
            border-radius: 4px; 
            margin-top: 10px; 
            font-size: 0.9rem; 
            color: #1976d2; 
        }
        .admin-table-section { 
            background: #fff; 
            padding: 25px; 
            border-radius: 8px; 
            margin-top: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .admin-table-section h2 {
            margin-top: 0;
            margin-bottom: 20px;
            color: #333;
            font-size: 1.4rem;
        }
        .admin-table-section table {
            width: 100%;
            border-collapse: collapse;
            background: #fff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .admin-table-section table thead {
            background: linear-gradient(135deg, #1b55f8 0%, #133fe0 100%);
            color: white;
        }
        .admin-table-section table th {
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            font-size: 0.95rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .admin-table-section table tbody tr {
            border-bottom: 1px solid #e0e0e0;
            transition: background-color 0.2s;
        }
        .admin-table-section table tbody tr:hover {
            background-color: #f5f5f5;
        }
        .admin-table-section table tbody tr:last-child {
            border-bottom: none;
        }
        .admin-table-section table tbody tr:nth-child(even) {
            background-color: #fafafa;
        }
        .admin-table-section table tbody tr:nth-child(even):hover {
            background-color: #f0f0f0;
        }
        .admin-table-section table td {
            padding: 12px;
            color: #333;
            font-size: 0.95rem;
        }
        .admin-table-section table tbody tr td:first-child {
            font-weight: 600;
            color: #1b55f8;
        }
    </style>
    """
    
    # HTML de feedback (permite <br> tags para quebras de linha)
    if feedback_msg:
        # Se a mensagem contém <br>, permite renderizar como HTML; caso contrário, escapa
        if '<br>' in feedback_msg:
            # Separa por <br>, escapa cada parte, e junta com <br>
            partes = feedback_msg.split('<br>')
            partes_seguras = [escape(p) for p in partes]
            safe_msg = Markup('<br>'.join(partes_seguras))
        else:
            # Mensagem sem <br>, escapa normalmente
            safe_msg = escape(feedback_msg)
        
        feedback_html = f'<div class="{feedback_cls}" style="padding: 12px; margin-bottom: 20px; border-radius: 4px; background: {"#d4edda" if feedback_cls == "success" else "#f8d7da"}; color: {"#155724" if feedback_cls == "success" else "#721c24"};">{safe_msg}</div>'
    else:
        feedback_html = ''

    # Cria as opções para selects (turmas e disciplinas)
    turma_options = ''.join(f'<option value="{t["turma_id"]}">{escape(t["nome_turma"])} ({t["ano"]})</option>' for t in recursos['turmas'])
    disciplina_options = ''.join(f'<option value="{d["disciplina_id"]}">{escape(d["nome_disciplina"])}</option>' for d in recursos['disciplinas'])
    
    # Cria lista de professores para select melhorado
    professor_options = ''.join(f'<option value="{p.get("id_usuario")}">{escape(p.get("email", "N/A"))} (ID: {p.get("id_usuario")})</option>' for p in recursos.get('professores', []))

    # === SEÇÃO 1: CRIAÇÃO DE RECURSOS ===
    secao_criacao = f"""
    <div class="admin-section">
        <h2 class="admin-section-title">Criar Recursos</h2>
        <div class="admin-grid">
            <div class="admin-card">
                <h3>Criar Conta de Professor</h3>
                <form method="POST">
                    <input type="hidden" name="action" value="create_professor">
                    <label for="email">E-mail:</label>
                    <input type="email" name="email" id="email" required>
                    <label for="senha">Senha:</label>
                    <input type="password" name="senha" id="senha" required>
                    <button type="submit" class="primary">Criar Conta</button>
                </form>
            </div>
            
            <div class="admin-card">
                <h3>Criar Turma</h3>
                <form method="POST">
                    <input type="hidden" name="action" value="create_turma">
                    <label for="nome_turma">Nome da Turma:</label>
                    <input type="text" name="nome_turma" id="nome_turma" required>
                    <label for="ano">Ano:</label>
                    <input type="number" name="ano" id="ano" required min="2020" max="2100">
                    <button type="submit" class="primary">Criar Turma</button>
                </form>
            </div>
            
            <div class="admin-card">
                <h3>Criar Disciplina</h3>
                <form method="POST">
                    <input type="hidden" name="action" value="create_disciplina">
                    <label for="nome_disciplina">Nome da Disciplina:</label>
                    <input type="text" id="nome_disciplina" name="nome_disciplina" required>
                    <label for="descricao_disciplina">Descrição (Opcional):</label>
                    <textarea id="descricao_disciplina" name="descricao" rows="3"></textarea>
                    <button type="submit" class="primary">Criar Disciplina</button>
                </form>
            </div>
        </div>
    </div>
    """
    
    # === SEÇÃO 2: GESTÃO DE TURMAS ===
    secao_gestao_turmas = f"""
    <div class="admin-section">
        <h2 class="admin-section-title">Gestão de Turmas</h2>
        <div class="admin-grid">
            <div class="admin-card">
                <h3>Atribuir Professor à Turma</h3>
                <form method="POST">
                    <input type="hidden" name="action" value="assign_professor">
                    <label for="turma_id">Turma:</label>
                    <select name="turma_id" id="turma_id">{turma_options if turma_options else '<option>Nenhuma turma disponível</option>'}</select>
                    <label for="professor_id">Professor:</label>
                    <select name="professor_id" id="professor_id" required>
                        {professor_options if professor_options else '<option>Nenhum professor disponível</option>'}
                    </select>
                    <div class="info-box">Selecione o professor na lista acima</div>
                    <button type="submit" class="primary">Atribuir Professor</button>
                </form>
            </div>
            
            <div class="admin-card">
                <h3>Associar Disciplinas à Turma</h3>
                <form method="POST">
                    <input type="hidden" name="action" value="assign_disciplinas">
                    <label for="turma_id_disciplina">Turma:</label>
                    <select name="turma_id_disciplina" id="turma_id_disciplina">{turma_options if turma_options else '<option>Nenhuma turma disponível</option>'}</select>
                    <label for="disciplinas">Disciplinas:</label>
                    <select name="disciplinas" id="disciplinas" multiple size="6">{disciplina_options if disciplina_options else '<option>Nenhuma disciplina disponível</option>'}</select>
                    <div class="info-box">Segure Ctrl (Cmd no Mac) e clique para selecionar múltiplas disciplinas</div>
                    <button type="submit" class="primary">Associar Disciplinas</button>
                </form>
            </div>
            
            <div class="admin-card">
                <h3>Associar Professor à Disciplina</h3>
                <p style="font-size: 0.9em; color: #666; margin-top: 0; margin-bottom: 15px;">Atribui um professor específico para uma disciplina específica dentro de uma turma. Útil quando há múltiplos professores, cada um responsável por sua disciplina.</p>
                <div class="info-box" style="background: #fff3cd; border-left: 4px solid #ffc107; margin-bottom: 15px;">
                    <strong>IMPORTANTE:</strong> Antes de associar o professor, você deve primeiro associar a disciplina à turma usando o formulário "Associar Disciplinas à Turma" acima.
                </div>
                <form method="POST">
                    <input type="hidden" name="action" value="assign_professor_disciplina">
                    <label for="turma_id_prof_disc">Turma:</label>
                    <select name="turma_id_prof_disc" id="turma_id_prof_disc" required>{turma_options if turma_options else '<option>Nenhuma turma disponível</option>'}</select>
                    <label for="disciplina_id_prof_disc">Disciplina:</label>
                    <select name="disciplina_id_prof_disc" id="disciplina_id_prof_disc" required>{disciplina_options if disciplina_options else '<option>Nenhuma disciplina disponível</option>'}</select>
                    <label for="professor_id_prof_disc">Professor:</label>
                    <select name="professor_id_prof_disc" id="professor_id_prof_disc" required>
                        {professor_options if professor_options else '<option>Nenhum professor disponível</option>'}
                    </select>
                    <div class="info-box">Permite que cada professor tenha sua disciplina específica na turma</div>
                    <button type="submit" class="primary">Associar Professor à Disciplina</button>
                </form>
            </div>
        </div>
    </div>
    """
    
    # === SEÇÃO 3: MATRÍCULAS ===
    secao_matriculas = f"""
    <div class="admin-section">
        <h2 class="admin-section-title">Matrículas</h2>
        <div class="admin-grid">
            <div class="admin-card">
                <h3>Matricular Aluno</h3>
                <form method="POST">
                    <input type="hidden" name="action" value="enroll_student">
                    <label for="aluno_id">ID do Aluno:</label>
                    <input type="number" name="aluno_id" id="aluno_id" required>
                    <div class="info-box">Consulte a tabela de alunos abaixo para encontrar o ID</div>
                    <label for="turma_id_matricula">Turma:</label>
                    <select name="turma_id_matricula" id="turma_id_matricula">{turma_options if turma_options else '<option>Nenhuma turma disponível</option>'}</select>
                    <label for="disciplina_id_matricula">Disciplina:</label>
                    <select name="disciplina_id_matricula" id="disciplina_id_matricula">{disciplina_options if disciplina_options else '<option>Nenhuma disciplina disponível</option>'}</select>
                    <button type="submit" class="primary">Matricular Aluno</button>
                </form>
            </div>
        </div>
    </div>
    """

    # === SEÇÃO 4: AÇÕES DESTRUTIVAS ===
    secao_acoes_destrutivas = f"""
    <div class="admin-section">
        <h2 class="admin-section-title" style="border-bottom-color: #d32f2f;">Ações Destrutivas</h2>
        <div class="admin-grid">
            <div class="admin-card danger">
                <h3>Desassociar Disciplina de Turma</h3>
                <p style="font-size: 0.9em; color: #666; margin-top: 0;">Remove a disciplina da grade da turma. A disciplina não é excluída do sistema.</p>
                <form method="POST">
                    <input type="hidden" name="action" value="remove_disciplina_from_turma">
                    <label for="remove_turma_id">Turma:</label>
                    <select name="turma_id" id="remove_turma_id" required>{turma_options if turma_options else '<option>Nenhuma turma disponível</option>'}</select>
                    <label for="remove_disciplina_id">Disciplina a Remover:</label>
                    <select name="disciplina_id" id="remove_disciplina_id" required>{disciplina_options if disciplina_options else '<option>Nenhuma disciplina disponível</option>'}</select>
                    <button type="submit" class="danger">Desassociar Disciplina</button>
                </form>
            </div>
            
            <div class="admin-card warning">
                <h3>Limpar Notas de Disciplina</h3>
                <p style="font-size: 0.9em; color: #666; margin-top: 0;">Exclui TODAS as notas (NP1, NP2, etc.) associadas à disciplina. Use antes de excluir a disciplina.</p>
                <form method="POST">
                    <input type="hidden" name="action" value="delete_notas_da_disciplina">
                    <label for="delete_notas_disciplina_id">Disciplina:</label>
                    <select name="disciplina_id_para_limpar" id="delete_notas_disciplina_id" required>{disciplina_options if disciplina_options else '<option>Nenhuma disciplina disponível</option>'}</select>
                    <button type="submit" class="warning">Limpar Notas</button>
                </form>
            </div>
            
            <div class="admin-card danger">
                <h3>Remover Matrícula</h3>
                <p style="font-size: 0.9em; color: #666; margin-top: 0;">Remove um aluno de uma turma/disciplina. Pode falhar se houver notas lançadas.</p>
                <form method="POST">
                    <input type="hidden" name="action" value="delete_matricula">
                    <label for="delete_matricula_id">ID da Matrícula:</label>
                    <input type="number" id="delete_matricula_id" name="matricula_id" required>
                    <div class="info-box">Ação permanente. Use com cuidado.</div>
                    <button type="submit" class="danger">Excluir Matrícula</button>
                </form>
            </div>
            
            <div class="admin-card danger">
                <h3>Excluir Disciplina (Permanente)</h3>
                <p style="font-size: 0.9em; color: #666; margin-top: 0;">Exclui a disciplina de TODO o sistema. Só funciona se nenhuma turma ou matrícula depender dela.</p>
                <form method="POST">
                    <input type="hidden" name="action" value="delete_disciplina">
                    <label for="delete_disciplina_id">Disciplina a Excluir:</label>
                    <select name="disciplina_id" id="delete_disciplina_id" required>{disciplina_options if disciplina_options else '<option>Nenhuma disciplina disponível</option>'}</select>
                    <div class="info-box">Ação PERMANENTE e IRREVERSÍVEL!</div>
                    <button type="submit" class="danger">EXCLUIR PERMANENTEMENTE</button>
                </form>
            </div>
        </div>
    </div>
    """
    
    # === SEÇÃO 5: LISTAS DE REFERÊNCIA ===
    # Tabela de Professores
    tabela_professores_html = """
    <div class="admin-table-section">
        <h2>Professores Cadastrados</h2>
        <table>
            <thead>
                <tr>
                    <th>ID Usuário</th>
                    <th>E-mail</th>
                </tr>
            </thead>
            <tbody>
    """
    if recursos.get('professores'):
        for prof in recursos['professores']:
            tabela_professores_html += f"""
                <tr>
                    <td>{prof.get('id_usuario')}</td>
                    <td>{escape(prof.get('email', 'N/A'))}</td>
                </tr>
            """
    else:
        tabela_professores_html += '<tr><td colspan="2" style="text-align: center; color: #999; padding: 20px;">Nenhum professor encontrado.</td></tr>'
    tabela_professores_html += '</tbody></table></div>'

    # Tabela de Alunos
    tabela_alunos_html = """
    <div class="admin-table-section">
        <h2>Alunos Cadastrados</h2>
        <table>
            <thead>
                <tr>
                    <th>ID Aluno</th>
                    <th>Nome Completo</th>
                    <th>E-mail</th>
                </tr>
            </thead>
            <tbody>
    """
    if recursos.get('alunos'):
        for aluno in recursos['alunos']:
            nome_completo = f"{escape(aluno.get('nome', ''))} {escape(aluno.get('sobrenome', ''))}".strip()
            tabela_alunos_html += f"""
                <tr>
                    <td>{aluno.get('aluno_id')}</td>
                    <td>{nome_completo}</td>
                    <td>{escape(aluno.get('email', 'N/A'))}</td>
                </tr>
            """
    else:
        tabela_alunos_html += '<tr><td colspan="3" style="text-align: center; color: #999; padding: 20px;">Nenhum aluno encontrado.</td></tr>'
    tabela_alunos_html += '</tbody></table></div>'


    return f"""
    {admin_css}
    <h1>Painel do Administrador</h1>
    {feedback_html}
    {secao_criacao}
    {secao_gestao_turmas}
    {secao_matriculas}
    {secao_acoes_destrutivas}
    {tabela_professores_html}
    {tabela_alunos_html}
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
                return render_login_form(erro_msg)

        except requests.exceptions.ConnectionError:
            erro_msg = "ERRO: O servidor Node.js (API) não está rodando na porta 3000."
            return render_login_form(erro_msg)

    return render_login_form()


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
        
        elif action == 'assign_professor_disciplina':
            # Associa professor diretamente a uma disciplina específica dentro de uma turma
            try:
                turma_id = int(form_data.get('turma_id_prof_disc'))
                disciplina_id = int(form_data.get('disciplina_id_prof_disc'))
                professor_id = int(form_data.get('professor_id_prof_disc'))
            except ValueError:
                return {"msg": "Erro: IDs inválidos. Verifique Turma, Disciplina e Professor.", "cls": "error"}
            
            # Rota para associar professor à disciplina
            url = f"{API_BASE_URL}/academico/turmas/{turma_id}/disciplinas/{disciplina_id}/professor"
            payload = {"professor_id": professor_id}
            # Tenta PUT primeiro, se falhar tenta POST
            method = requests.put
            
            # Tenta fazer a requisição (primeiro com PUT, depois com POST como fallback)
            try:
                response = requests.put(url, json=payload, headers={"Authorization": f"Bearer {token}"})
                
                # Log para debug
                print(f"[Flask POST Debug - Assign Professor Disciplina]")
                print(f"URL: {url}")
                print(f"Payload: {payload}")
                print(f"Status: {response.status_code}")
                print(f"Response Text: {response.text[:500]}")
                
                # Se PUT retornar 404, tenta POST
                if response.status_code == 404:
                    print("[Flask POST Debug] PUT retornou 404, tentando POST...")
                    response = requests.post(url, json=payload, headers={"Authorization": f"Bearer {token}"})
                    print(f"[Flask POST Debug] POST Status: {response.status_code}")
                    print(f"[Flask POST Debug] POST Response: {response.text[:500]}")
                
                # Tenta fazer parse do JSON
                try:
                    response_data = response.json()
                    result_msg = response_data.get("message", f"Erro desconhecido na API ({response.status_code})")
                    
                    # Mensagens de erro mais amigáveis baseadas no status code
                    if response.status_code in [200, 201]:
                        return {"msg": result_msg, "cls": "success"}
                    elif response.status_code == 404:
                        # Mensagens específicas para diferentes tipos de 404
                        if "disciplina não está associada" in result_msg.lower() or "não está associada" in result_msg.lower():
                            error_msg = f"{result_msg} Use o formulário 'Associar Disciplinas à Turma' primeiro."
                        elif "não encontrado" in result_msg.lower():
                            error_msg = f"{result_msg}"
                        else:
                            error_msg = f"{result_msg}"
                        return {"msg": error_msg, "cls": "error"}
                    elif response.status_code == 400:
                        return {"msg": f"{result_msg}", "cls": "error"}
                    elif response.status_code == 403:
                        return {"msg": f"{result_msg}", "cls": "error"}
                    elif response.status_code == 500:
                        error_detail = response_data.get("error", "")
                        if error_detail:
                            return {"msg": f"Erro interno do servidor: {result_msg}\nDetalhes: {error_detail}", "cls": "error"}
                        return {"msg": f"Erro interno do servidor: {result_msg}", "cls": "error"}
                    else:
                        return {"msg": f"{result_msg} (Status: {response.status_code})", "cls": "error"}
                        
                except (ValueError, requests.exceptions.JSONDecodeError) as json_err:
                    # Se não conseguir fazer parse do JSON
                    print(f"[Flask POST Debug] Erro ao fazer parse JSON: {json_err}")
                    print(f"[Flask POST Debug] Response completa: {response.text}")
                    
                    if response.status_code == 404:
                        if "Cannot" in response.text or "Cannot POST" in response.text or "Cannot PUT" in response.text:
                            error_msg = "Rota não encontrada (404). O servidor Node.js precisa ser REINICIADO para carregar as novas rotas."
                            if "Cannot" in response.text:
                                error_msg += f"\nErro do servidor: {response.text[:200]}"
                            return {"msg": error_msg, "cls": "error"}
                        else:
                            # HTML de erro do Express
                            return {"msg": "Rota não encontrada (404). Verifique se o servidor Node.js está rodando e se a rota está implementada.", "cls": "error"}
                    
                    error_text = response.text[:500] if len(response.text) > 500 else response.text
                    return {"msg": f"Resposta inválida da API (Status: {response.status_code}): {error_text}", "cls": "error"}
                    
            except requests.exceptions.ConnectionError:
                return {"msg": "Erro: Não foi possível conectar ao servidor Node.js. Verifique se o servidor está rodando na porta 3000.", "cls": "error"}
            except requests.exceptions.RequestException as e:
                return {"msg": f"Erro de Conexão com API: {str(e)}", "cls": "error"}
            except Exception as e:
                print(f"[Flask POST Debug] Exceção não tratada: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                return {"msg": f"Erro ao processar: {str(e)}", "cls": "error"}
        
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
            url = f"{API_BASE_URL}/academico/turmas/associar-disciplinas" # Rota correta: associar-disciplinas
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
                try:
                    response_data = response.json()
                    print(f"[Flask POST Debug] Resposta JSON API: {response_data}")
                    
                    result_msg = response_data.get("message", f"Erro desconhecido na API ({response.status_code})")
                    
                    # Preserva quebras de linha na mensagem (substitui \n por <br> para HTML)
                    if isinstance(result_msg, str):
                        result_msg_html = result_msg.replace('\n', '<br>')
                    else:
                        result_msg_html = str(result_msg)
                    
                    if response.status_code in [200, 201]:
                        result_cls = "success"
                    else:
                        result_cls = "error"
                    
                    return {"msg": result_msg_html, "cls": result_cls}
                    
                except (ValueError, requests.exceptions.JSONDecodeError) as json_err:
                    # Se a resposta não for JSON válido, mostra o texto da resposta ou erro genérico
                    print(f"[Flask POST Debug] Erro ao fazer parse JSON: {json_err}")
                    if response.text:
                        # Tenta mostrar parte do texto da resposta
                        error_text = response.text[:200] if len(response.text) > 200 else response.text
                        return {"msg": f"Resposta inválida da API (Status: {response.status_code}): {error_text}", "cls": "error"}
                    else:
                        return {"msg": f"API retornou resposta vazia (Status: {response.status_code})", "cls": "error"}

            except requests.exceptions.RequestException as e:
                # Captura erro de conexão
                print(f"[Flask POST Debug] Erro de Conexão: {e}")
                return {"msg": f"Erro de Conexão com API: {str(e)}", "cls": "error"}
            except Exception as e: 
                # Captura outros erros (ex: API não retornou JSON válido)
                print(f"[Flask POST Debug] Erro ao processar resposta da API: {e}")
                return {"msg": f"Erro ao processar resposta da API: {str(e)}", "cls": "error"}

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

    # 4. Constrói o HTML do Dashboard do Aluno (Melhorado e Moderno)
    
    # Determina a cor da média baseado no valor
    media_cor = "#28a745"  # Verde (aprovado)
    if media_geral != "N/D":
        try:
            media_num = float(media_geral.replace(',', '.'))
            if media_num < 5:
                media_cor = "#dc3545"  # Vermelho (reprovado)
            elif media_num < 7:
                media_cor = "#ffc107"  # Amarelo (recuperação)
        except:
            pass
    
    aluno_css = """
    <style>
        .aluno-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            border-radius: 16px;
            margin-bottom: 30px;
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        }
        .aluno-header h1 {
            margin: 0 0 10px 0;
            font-size: 2.2rem;
            font-weight: 700;
        }
        .aluno-header p {
            margin: 0;
            font-size: 1.1rem;
            opacity: 0.95;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: #fff;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            border-left: 5px solid;
            transition: transform 0.3s, box-shadow 0.3s;
            position: relative;
            overflow: hidden;
        }
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.12);
        }
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 100px;
            height: 100px;
            background: radial-gradient(circle, rgba(0,0,0,0.03) 0%, transparent 70%);
            border-radius: 50%;
            transform: translate(30px, -30px);
        }
        .stat-card.media {
            border-left-color: var(--media-color, #667eea);
        }
        .stat-card.disciplinas {
            border-left-color: #4CAF50;
        }
        .stat-card.faltas {
            border-left-color: #ff9800;
        }
        .stat-value {
            font-size: 3rem;
            font-weight: 700;
            margin: 0 0 10px 0;
            color: var(--stat-color, #333);
            line-height: 1;
        }
        .stat-label {
            font-size: 1rem;
            color: #666;
            margin: 0;
            font-weight: 500;
        }
        .stat-description {
            font-size: 0.85rem;
            color: #999;
            margin-top: 8px;
        }
        .quick-actions {
            background: #fff;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            margin-top: 30px;
        }
        .quick-actions h3 {
            margin: 0 0 20px 0;
            color: #333;
            font-size: 1.4rem;
        }
        .action-buttons {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        .action-btn {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 25px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s;
            box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);
        }
        .action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(102, 126, 234, 0.4);
        }
        .action-btn.secondary {
            background: #f8f9fa;
            color: #333;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .action-btn.secondary:hover {
            background: #e9ecef;
        }
        .feedback-alert {
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 25px;
            background: #f8d7da;
            color: #721c24;
            border-left: 4px solid #dc3545;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            background: #f8f9fa;
            border-radius: 16px;
            color: #666;
            margin-top: 30px;
        }
        .empty-state-icon {
            font-size: 4rem;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
            .stat-value {
                font-size: 2.5rem;
            }
        }
    </style>
    """
    
    # Feedback de erro se houver
    feedback_html = ''
    if feedback:
        feedback_html = f'<div class="feedback-alert">{escape(feedback)}</div>'
    
    # Header do painel
    header_html = """
    <div class="aluno-header">
        <h1>Painel do Aluno</h1>
        <p>Bem-vindo! Acompanhe seu desempenho acadêmico em tempo real.</p>
    </div>
    """
    
    # Cards de estatísticas
    stats_html = f"""
    <div class="stats-grid">
        <div class="stat-card media" style="--media-color: {media_cor}; --stat-color: {media_cor};">
            <div class="stat-value">{media_geral}</div>
            <p class="stat-label">Média Geral</p>
            <p class="stat-description">Baseada em NP1 e NP2</p>
        </div>
        
        <div class="stat-card disciplinas" style="--stat-color: #4CAF50;">
            <div class="stat-value">{total_disciplinas}</div>
            <p class="stat-label">Disciplinas Matriculadas</p>
            <p class="stat-description">Total de matérias cursadas</p>
        </div>
        
        <div class="stat-card faltas" style="--stat-color: #ff9800;">
            <div class="stat-value">{faltas}</div>
            <p class="stat-label">Total de Faltas</p>
            <p class="stat-description">Registro de ausências</p>
        </div>
    </div>
    """
    
    # Ações rápidas
    boletim_url = url_for('boletim')
    quick_actions_html = f"""
    <div class="quick-actions">
        <h3>Ações Rápidas</h3>
        <div class="action-buttons">
            <a href="{boletim_url}" class="action-btn">
                Ver Boletim Completo
            </a>
        </div>
    </div>
    """
    
    # Se não houver dados, mostra estado vazio
    if total_disciplinas == 0 and not feedback:
        empty_state_html = """
        <div class="empty-state">
            <h3>Nenhum dado disponível</h3>
            <p>Você ainda não possui disciplinas matriculadas ou notas lançadas.</p>
        </div>
        """
        conteudo_aluno_html = f'''
        {aluno_css}
        {header_html}
        {feedback_html}
        {empty_state_html}
        {quick_actions_html}
        '''
    else:
        conteudo_aluno_html = f'''
        {aluno_css}
        {header_html}
        {feedback_html}
        {stats_html}
        {quick_actions_html}
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

    # ----------------------------------------------------
    # LÓGICA DE BUSCA DE TURMAS (GET)
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
            # A mensagem de busca só é relevante se não houver mensagem anterior
            if not message: 
                message = "Suas turmas foram carregadas."
                message_class = "success"
        else:
            # Se a busca falhar, mostra mensagem de erro
            if not message:
                message = response_data_turmas.get('message', 'Erro ao carregar turmas da API.')
                message_class = 'error'
            
    except requests.exceptions.RequestException:
        if not message: # Só mostra erro de conexão se não houver mensagem anterior
            message = "ERRO: Não foi possível conectar à API Node.js."
            message_class = "error"
            
    # Renderiza o conteúdo final passando todos os dados necessários
    conteudo_professor_html = render_professor_content(user_type, turmas, message, message_class)
    
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
    
    # Buscar informações da turma e disciplina para exibir no header
    # Por enquanto, vamos usar apenas os IDs, mas poderia buscar os nomes da API
    gestao_css = """
    <style>
        .gestao-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 16px;
            margin-bottom: 30px;
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        }
        .gestao-header h1 {
            margin: 0 0 15px 0;
            font-size: 2rem;
            font-weight: 700;
        }
        .gestao-info {
            display: flex;
            gap: 30px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        .info-badge {
            background: rgba(255, 255, 255, 0.15);
            padding: 10px 20px;
            border-radius: 8px;
            backdrop-filter: blur(10px);
        }
        .info-badge strong {
            display: block;
            font-size: 1.2rem;
            margin-bottom: 5px;
        }
        .info-badge span {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        .action-buttons-top {
            display: flex;
            gap: 15px;
            margin-bottom: 25px;
            flex-wrap: wrap;
        }
        .btn-nav {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 12px 20px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }
        .btn-nav.secondary {
            background: #6c757d;
            color: white;
        }
        .btn-nav.secondary:hover {
            background: #5a6268;
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(0,0,0,0.15);
        }
        .btn-nav.primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-nav.primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(102, 126, 234, 0.4);
        }
        .feedback-message {
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 25px;
            background: #d4edda;
            color: #155724;
            border-left: 4px solid #28a745;
        }
        .feedback-message.error {
            background: #f8d7da;
            color: #721c24;
            border-left-color: #dc3545;
        }
        .gestao-table-container {
            background: #fff;
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            overflow-x: auto;
        }
        .gestao-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        .gestao-table thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .gestao-table th {
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .gestao-table th.text-center {
            text-align: center;
        }
        .gestao-table tbody tr {
            border-bottom: 1px solid #e0e0e0;
            transition: background-color 0.2s;
        }
        .gestao-table tbody tr:hover {
            background-color: #f8f9fa;
        }
        .gestao-table tbody tr:nth-child(even) {
            background-color: #fafafa;
        }
        .gestao-table tbody tr:nth-child(even):hover {
            background-color: #f0f0f0;
        }
        .gestao-table td {
            padding: 15px 12px;
            color: #333;
            font-size: 0.95rem;
        }
        .gestao-table td.text-center {
            text-align: center;
        }
        .nota-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.9rem;
        }
        .nota-badge.presente {
            background: #d4edda;
            color: #155724;
        }
        .nota-badge.ausente {
            background: #fff3cd;
            color: #856404;
        }
        .nota-badge.empty {
            background: #f8d7da;
            color: #721c24;
        }
        .media-badge {
            display: inline-block;
            padding: 8px 14px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 1rem;
        }
        .media-badge.aprovado {
            background: #d4edda;
            color: #155724;
        }
        .media-badge.recuperacao {
            background: #fff3cd;
            color: #856404;
        }
        .media-badge.reprovado {
            background: #f8d7da;
            color: #721c24;
        }
        .form-nota {
            display: flex;
            gap: 8px;
            align-items: center;
            flex-wrap: wrap;
        }
        .form-nota input[type="number"] {
            width: 80px;
            padding: 8px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 0.95rem;
            transition: border-color 0.3s;
        }
        .form-nota input[type="number"]:focus {
            outline: none;
            border-color: #667eea;
        }
        .form-nota select {
            padding: 8px 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 0.95rem;
            background: white;
            cursor: pointer;
            transition: border-color 0.3s;
        }
        .form-nota select:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn-lancar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
        }
        .btn-lancar:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 10px rgba(102, 126, 234, 0.4);
        }
        .btn-presenca {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            border: none;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        }
        .btn-presenca.presente {
            background: #28a745;
            color: white;
        }
        .btn-presenca.presente:hover {
            background: #218838;
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(40, 167, 69, 0.4);
        }
        .btn-presenca.ausente {
            background: #dc3545;
            color: white;
        }
        .btn-presenca.ausente:hover {
            background: #c82333;
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(220, 53, 69, 0.4);
        }
        .presenca-actions {
            display: flex;
            gap: 8px;
            justify-content: center;
            align-items: center;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            background: #f8f9fa;
            border-radius: 16px;
            color: #666;
            margin-top: 20px;
        }
        .empty-state h3 {
            margin: 0 0 10px 0;
            color: #333;
        }
        @media (max-width: 768px) {
            .gestao-table-container {
                padding: 15px;
            }
            .gestao-table {
                font-size: 0.85rem;
            }
            .gestao-table th,
            .gestao-table td {
                padding: 10px 8px;
            }
            .form-nota {
                flex-direction: column;
                align-items: stretch;
            }
            .form-nota input,
            .form-nota select,
            .btn-lancar {
                width: 100%;
            }
        }
    </style>
    """
    
    # Header com informações
    header_html = f"""
    <div class="gestao-header">
        <h1>Gestão de Turma/Disciplina</h1>
        <div class="gestao-info">
            <div class="info-badge">
                <strong>Turma</strong>
                <span>ID: {turma_id}</span>
            </div>
            <div class="info-badge">
                <strong>Disciplina</strong>
                <span>ID: {disciplina_id}</span>
            </div>
            <div class="info-badge">
                <strong>Total de Alunos</strong>
                <span>{len(alunos) if alunos else 0}</span>
            </div>
        </div>
    </div>
    """
    
    # Feedback message
    feedback_html = ''
    if feedback:
        feedback_cls = 'error' if 'ERRO' in feedback.upper() or 'erro' in feedback.lower() else ''
        feedback_html = f'<div class="feedback-message {feedback_cls}">{escape(feedback)}</div>'
    
    # Botões de navegação
    nav_buttons = f"""
    <div class="action-buttons-top">
        <a href="{url_for('painel_professor')}" class="btn-nav secondary">
            &laquo; Voltar para Minhas Turmas
        </a>
        <a href="{url_for('relatorio_desempenho', turma_id=turma_id, disciplina_id=disciplina_id)}" class="btn-nav primary">
            Ver Relatório de Desempenho (C)
        </a>
    </div>
    """
    
    # Tabela de alunos
    if not alunos:
        empty_state_html = """
        <div class="empty-state">
            <h3>Nenhum aluno matriculado</h3>
            <p>Nenhum aluno foi encontrado para esta turma e disciplina.</p>
        </div>
        """
        return f"""
        {gestao_css}
        {header_html}
        {feedback_html}
        {nav_buttons}
        {empty_state_html}
        """
    
    # Construir tabela
    table_html = """
    <div class="gestao-table-container">
        <table class="gestao-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Nome do Aluno</th>
                    <th class="text-center">NP1</th>
                    <th class="text-center">NP2</th>
                    <th class="text-center">Média Final</th>
                    <th>Lançar Nota</th>
                    <th class="text-center">Presença</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for aluno in alunos:
        aluno_id = aluno.get('aluno_id', 'N/A')
        nome = escape(aluno.get('nome', ''))
        sobrenome = escape(aluno.get('sobrenome', ''))
        nome_completo = f"{nome} {sobrenome}".strip()
        
        nota_np1 = aluno.get('nota_np1')
        nota_np2 = aluno.get('nota_np2')
        media_final = aluno.get('media_final')
        
        matricula_id = aluno.get('matricula_id', '')
        
        # Formata notas com badges
        def formatar_nota_badge(nota):
            if nota is None:
                return '<span class="nota-badge empty">N/D</span>'
            try:
                nota_float = float(nota)
                return f'<span class="nota-badge presente">{nota_float:.1f}</span>'
            except:
                return f'<span class="nota-badge empty">{nota}</span>'
        
        # Formata média com badge colorido
        def formatar_media_badge(media):
            if media is None:
                return '<span class="media-badge empty">N/D</span>'
            try:
                media_float = float(media)
                if media_float >= 7:
                    classe = 'aprovado'
                    texto = f'{media_float:.1f}'
                elif media_float >= 5:
                    classe = 'recuperacao'
                    texto = f'{media_float:.1f}'
                else:
                    classe = 'reprovado'
                    texto = f'{media_float:.1f}'
                return f'<span class="media-badge {classe}">{texto}</span>'
            except:
                return f'<span class="media-badge empty">{media}</span>'
        
        nota_np1_html = formatar_nota_badge(nota_np1)
        nota_np2_html = formatar_nota_badge(nota_np2)
        media_html = formatar_media_badge(media_final)
        
        # Formulário de lançar nota
        form_nota_html = f"""
        <form action="{url_for('lancar_nota_form')}" method="POST" class="form-nota">
            <input type="hidden" name="aluno_id" value="{aluno_id}">
            <input type="hidden" name="disciplina_id" value="{disciplina_id}">
            <input type="hidden" name="turma_id" value="{turma_id}">
            <input type="number" 
                   step="0.1" 
                   min="0" 
                   max="10" 
                   name="valor_nota" 
                   placeholder="Nota" 
                   required>
            <select name="tipo_avaliacao" required>
                <option value="NP1">NP1</option>
                <option value="NP2">NP2</option>
                <option value="Exame">Exame</option>
            </select>
            <button type="submit" class="btn-lancar">Lançar</button>
        </form>
        """
        
        # Botões de presença
        presenca_html = f"""
        <div class="presenca-actions">
            <form action="{url_for('marcar_presenca_form')}" method="POST" style="margin: 0;">
                <input type="hidden" name="matricula_id" value="{matricula_id}">
                <input type="hidden" name="status" value="presente">
                <input type="hidden" name="turma_id" value="{turma_id}">
                <input type="hidden" name="disciplina_id" value="{disciplina_id}">
                <button type="submit" class="btn-presenca presente" title="Marcar Presença">P</button>
            </form>
            <form action="{url_for('marcar_presenca_form')}" method="POST" style="margin: 0;">
                <input type="hidden" name="matricula_id" value="{matricula_id}">
                <input type="hidden" name="status" value="ausente">
                <input type="hidden" name="turma_id" value="{turma_id}">
                <input type="hidden" name="disciplina_id" value="{disciplina_id}">
                <button type="submit" class="btn-presenca ausente" title="Marcar Falta">F</button>
            </form>
        </div>
        """
        
        table_html += f"""
            <tr>
                <td><strong>{aluno_id}</strong></td>
                <td><strong>{nome_completo}</strong></td>
                <td class="text-center">{nota_np1_html}</td>
                <td class="text-center">{nota_np2_html}</td>
                <td class="text-center">{media_html}</td>
                <td>{form_nota_html}</td>
                <td class="text-center">{presenca_html}</td>
            </tr>
        """
    
    table_html += """
            </tbody>
        </table>
    </div>
    """
    
    return f"""
    {gestao_css}
    {header_html}
    {feedback_html}
    {nav_buttons}
    {table_html}
    """

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
        empty_html = """
        <style>
            .relatorio-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 16px;
                margin-bottom: 30px;
                box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
            }
            .relatorio-header h1 {
                margin: 0 0 15px 0;
                font-size: 2rem;
                font-weight: 700;
            }
            .empty-state {
                text-align: center;
                padding: 60px 20px;
                background: #f8f9fa;
                border-radius: 16px;
                color: #666;
                margin-top: 20px;
            }
            .empty-state h3 {
                margin: 0 0 10px 0;
                color: #333;
            }
        </style>
        <div class="relatorio-header">
            <h1>Relatório de Desempenho</h1>
        </div>
        <div class="empty-state">
            <h3>Nenhum aluno com média lançada</h3>
            <p>Não há dados suficientes para gerar o ranking de desempenho.</p>
            <p style="margin-top: 15px;">
                <a href="{url_for('gerenciar_turma', turma_id=turma_id, disciplina_id=disciplina_id)}" 
                   style="display: inline-block; padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 8px; margin-top: 15px;">
                   &laquo; Voltar para Gestão
                </a>
            </p>
        </div>
        """
        return render_base(empty_html.format(url_for=url_for), "Relatório de Desempenho")
    
    # Calcula a média da turma (como fizemos antes)
    media_da_turma = Decimal('0.0')
    if medias_validas:
        media_da_turma = sum(medias_validas) / Decimal(len(medias_validas))
    media_da_turma_str = f"{float(media_da_turma):.2f}"

    # 2. Chama a função C para ordenar
    count = len(desempenhos)
    ArrayType = DesempenhoAluno * count
    array_c = ArrayType(*desempenhos)
    
    lib_c.ordenar_por_desempenho(array_c, count) # ⬅️ CHAMADA CRÍTICA AO C
    
    # Buscar nomes dos alunos para exibir no ranking
    alunos_dict = {aluno.get('aluno_id'): aluno for aluno in alunos_data}

    # 3. Renderiza o HTML com os dados ordenados
    relatorio_css = """
    <style>
        .relatorio-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 16px;
            margin-bottom: 30px;
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        }
        .relatorio-header h1 {
            margin: 0 0 15px 0;
            font-size: 2rem;
            font-weight: 700;
        }
        .relatorio-info {
            display: flex;
            gap: 30px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        .info-badge {
            background: rgba(255, 255, 255, 0.15);
            padding: 10px 20px;
            border-radius: 8px;
            backdrop-filter: blur(10px);
        }
        .info-badge strong {
            display: block;
            font-size: 1.2rem;
            margin-bottom: 5px;
        }
        .info-badge span {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        .stats-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        }
        .stat-card h3 {
            margin: 0 0 10px 0;
            color: #666;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .stat-card .value {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
        }
        .stat-card.media .value {
            color: #667eea;
        }
        .stat-card.total .value {
            color: #764ba2;
        }
        .stat-card.aprovados .value {
            color: #28a745;
        }
        .stat-card.reprovados .value {
            color: #dc3545;
        }
        .ranking-section {
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            margin-bottom: 30px;
        }
        .ranking-section h2 {
            margin: 0 0 25px 0;
            color: #333;
            font-size: 1.5rem;
            padding-bottom: 15px;
            border-bottom: 2px solid #667eea;
        }
        .ranking-table {
            width: 100%;
            border-collapse: collapse;
        }
        .ranking-table thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .ranking-table th {
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .ranking-table th.text-center {
            text-align: center;
        }
        .ranking-table tbody tr {
            border-bottom: 1px solid #e0e0e0;
            transition: background-color 0.2s;
        }
        .ranking-table tbody tr:hover {
            background-color: #f8f9fa;
        }
        .ranking-table tbody tr:nth-child(even) {
            background-color: #fafafa;
        }
        .ranking-table tbody tr:nth-child(even):hover {
            background-color: #f0f0f0;
        }
        .ranking-table tbody tr:first-child {
            background: linear-gradient(90deg, #fff9e6 0%, #ffffff 100%);
            border-left: 4px solid #ffd700;
        }
        .ranking-table tbody tr:nth-child(2) {
            background: linear-gradient(90deg, #f5f5f5 0%, #ffffff 100%);
            border-left: 4px solid #c0c0c0;
        }
        .ranking-table tbody tr:nth-child(3) {
            background: linear-gradient(90deg, #fff4e6 0%, #ffffff 100%);
            border-left: 4px solid #cd7f32;
        }
        .ranking-table td {
            padding: 15px 12px;
            color: #333;
            font-size: 0.95rem;
        }
        .ranking-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            font-weight: 700;
            font-size: 1rem;
            color: white;
        }
        .ranking-badge.ouro {
            background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
            box-shadow: 0 4px 12px rgba(255, 215, 0, 0.4);
        }
        .ranking-badge.prata {
            background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%);
            box-shadow: 0 4px 12px rgba(192, 192, 192, 0.4);
        }
        .ranking-badge.bronze {
            background: linear-gradient(135deg, #cd7f32 0%, #e6a85c 100%);
            box-shadow: 0 4px 12px rgba(205, 127, 50, 0.4);
        }
        .ranking-badge.normal {
            background: #667eea;
            box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
        }
        .media-badge {
            display: inline-block;
            padding: 8px 14px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 1rem;
        }
        .media-badge.aprovado {
            background: #d4edda;
            color: #155724;
        }
        .media-badge.recuperacao {
            background: #fff3cd;
            color: #856404;
        }
        .media-badge.reprovado {
            background: #f8d7da;
            color: #721c24;
        }
        .btn-voltar {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 12px 20px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            background: #6c757d;
            color: white;
        }
        .btn-voltar:hover {
            background: #5a6268;
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(0,0,0,0.15);
        }
        .badge-modulo {
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            padding: 5px 12px;
            border-radius: 12px;
            font-size: 0.8rem;
            margin-left: 10px;
            font-weight: 500;
        }
        @media (max-width: 768px) {
            .ranking-section {
                padding: 15px;
            }
            .stats-cards {
                grid-template-columns: 1fr;
            }
            .ranking-table {
                font-size: 0.85rem;
            }
            .ranking-table th,
            .ranking-table td {
                padding: 10px 8px;
            }
        }
    </style>
    """
    
    # Calcular estatísticas
    aprovados = sum(1 for aluno in array_c if aluno.media_final >= 7)
    reprovados = sum(1 for aluno in array_c if aluno.media_final < 5)
    recuperacao = sum(1 for aluno in array_c if 5 <= aluno.media_final < 7)
    
    # Header
    header_html = f"""
    <div class="relatorio-header">
        <h1>Relatório de Desempenho <span class="badge-modulo">Ordenado pelo Módulo C</span></h1>
        <div class="relatorio-info">
            <div class="info-badge">
                <strong>Turma</strong>
                <span>ID: {turma_id}</span>
            </div>
            <div class="info-badge">
                <strong>Disciplina</strong>
                <span>ID: {disciplina_id}</span>
            </div>
        </div>
    </div>
    """
    
    # Cards de estatísticas
    stats_html = f"""
    <div class="stats-cards">
        <div class="stat-card media">
            <h3>Média Geral da Turma</h3>
            <p class="value">{media_da_turma_str}</p>
        </div>
        <div class="stat-card total">
            <h3>Total de Alunos</h3>
            <p class="value">{count}</p>
        </div>
        <div class="stat-card aprovados">
            <h3>Aprovados (≥ 7.0)</h3>
            <p class="value">{aprovados}</p>
        </div>
        <div class="stat-card reprovados">
            <h3>Reprovados (&lt; 5.0)</h3>
            <p class="value">{reprovados}</p>
        </div>
    </div>
    """
    
    # Tabela de ranking
    ranking_html = """
    <div class="ranking-section">
        <h2>Ranking de Desempenho</h2>
        <table class="ranking-table">
            <thead>
                <tr>
                    <th>Posição</th>
                    <th>ID Aluno</th>
                    <th>Nome do Aluno</th>
                    <th class="text-center">Média Final</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Função para determinar badge de ranking
    def get_ranking_badge(position):
        if position == 1:
            return '<span class="ranking-badge ouro">1</span>'
        elif position == 2:
            return '<span class="ranking-badge prata">2</span>'
        elif position == 3:
            return '<span class="ranking-badge bronze">3</span>'
        else:
            return f'<span class="ranking-badge normal">{position}</span>'
    
    # Função para formatar média com badge
    def formatar_media_badge(media):
        try:
            media_float = float(media)
            if media_float >= 7:
                classe = 'aprovado'
            elif media_float >= 5:
                classe = 'recuperacao'
            else:
                classe = 'reprovado'
            return f'<span class="media-badge {classe}">{media_float:.2f}</span>'
        except:
            return f'<span class="media-badge reprovado">{media}</span>'
    
    # Itera sobre o array que o C modificou
    for i, aluno in enumerate(array_c):
        position = i + 1
        aluno_id = aluno.id_aluno
        aluno_info = alunos_dict.get(aluno_id, {})
        nome_aluno = f"{aluno_info.get('nome', '')} {aluno_info.get('sobrenome', '')}".strip()
        if not nome_aluno:
            nome_aluno = f"Aluno ID {aluno_id}"
        
        ranking_badge = get_ranking_badge(position)
        media_badge = formatar_media_badge(aluno.media_final)
        
        ranking_html += f"""
            <tr>
                <td>{ranking_badge}</td>
                <td><strong>{aluno_id}</strong></td>
                <td>{escape(nome_aluno)}</td>
                <td class="text-center">{media_badge}</td>
            </tr>
        """
    
    ranking_html += """
            </tbody>
        </table>
    </div>
    """
    
    # Botão voltar
    voltar_html = f"""
    <div style="margin-top: 20px;">
        <a href="{url_for('gerenciar_turma', turma_id=turma_id, disciplina_id=disciplina_id)}" class="btn-voltar">
            &laquo; Voltar para Gestão
        </a>
    </div>
    """
    
    html = f"""
    {relatorio_css}
    {header_html}
    {stats_html}
    {ranking_html}
    {voltar_html}
    """
    
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