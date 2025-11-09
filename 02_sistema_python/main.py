"""
================================================================================
SISTEMA ACADÊMICO PIM - MÓDULO WEB FLASK
================================================================================

Este módulo implementa a interface web do Sistema Acadêmico PIM, oferecendo
funcionalidades completas para três perfis distintos de usuários: alunos,
professores e administradores.

ARQUITETURA:
-----------
O sistema adota uma arquitetura em camadas:
- Frontend: Flask (Python) - Renderização server-side
- Backend: API Node.js/Express - Lógica de negócio e autenticação
- Banco de Dados: PostgreSQL - Persistência de dados
- Serviços Externos: Google Gemini (IA) e Biblioteca C (algoritmos)

FUNCIONALIDADES PRINCIPAIS:
---------------------------
1. Autenticação e Autorização
   - Sistema de login/registro com JWT
   - Controle de acesso baseado em perfis (aluno/professor/admin)
   - Gerenciamento de sessões seguro

2. Módulo do Aluno
   - Dashboard com estatísticas acadêmicas
   - Consulta de boletim completo
   - Assistente de IA para orientação acadêmica

3. Módulo do Professor
   - Painel de controle de turmas
   - Lançamento de notas e registro de presença
   - Geração de relatórios de desempenho

4. Módulo do Administrador
   - CRUD completo de turmas, disciplinas, professores e alunos
   - Gerenciamento de matrículas
   - Relatórios avançados com algoritmos otimizados

TECNOLOGIAS UTILIZADAS:
----------------------
- Flask 3.1.2: Framework web Python
- Jinja2: Motor de templates
- Requests: Cliente HTTP para comunicação com API
- Markdown: Processamento de texto formatado
- Google Generative AI: Integração com Gemini para IA
- ctypes: Interface com biblioteca C compilada

SEGURANÇA:
---------
- Proteção XSS através de escape automático
- Autenticação JWT stateless
- Validação de entrada em todas as rotas
- Proteção CSRF através de tokens de sessão

AUTOR: [Nome do Desenvolvedor]
DATA: Janeiro 2025
VERSÃO: 1.0.0
================================================================================
"""
# ============================================================================
# IMPORTAÇÕES DE BIBLIOTECAS
# ============================================================================

# Bibliotecas padrão do Python
import ctypes          # Interface para bibliotecas C compiladas (DLL/SO)
import platform        # Detecção do sistema operacional
import os              # Operações do sistema de arquivos e variáveis de ambiente
from decimal import Decimal, ROUND_HALF_UP  # Precisão decimal para cálculos de notas

# Framework Flask e componentes
from flask import Flask, render_template_string, request, redirect, url_for, session
# Flask: Framework web principal
# render_template_string: Renderização de templates HTML inline
# request: Acesso a dados de requisições HTTP
# redirect: Redirecionamento de rotas
# url_for: Geração de URLs para rotas
# session: Gerenciamento de sessões do usuário

# Segurança e proteção
from markupsafe import escape, Markup
# escape: Proteção contra XSS (Cross-Site Scripting) - escapa HTML malicioso
# Markup: Permite renderizar HTML seguro quando necessário

# Comunicação HTTP
import requests  # Cliente HTTP para comunicação com a API Node.js backend

# Configuração e ambiente
from dotenv import load_dotenv  # Carregamento de variáveis de ambiente do arquivo .env

# Inteligência Artificial
import google.generativeai as genai  # SDK do Google para integração com Gemini AI

# Processamento de texto
import markdown  # Conversão de Markdown para HTML


# ============================================================================
# CONFIGURAÇÕES INICIAIS E VARIÁVEIS DE AMBIENTE
# ============================================================================

# Carrega variáveis de ambiente do arquivo .env na raiz do projeto
# O arquivo .env deve conter: API_URL, FLASK_SECRET_KEY, GEMINI_API_KEY
load_dotenv()

# URL base da API Node.js backend
# Fallback para localhost:3000 se não estiver configurado no .env
API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:3000/api") 

# Configuração da API do Google Gemini para assistente de IA
# A chave deve ser obtida em: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Inicialização da aplicação Flask
# __name__ permite que Flask encontre templates e arquivos estáticos
app = Flask(__name__)

# Configuração da chave secreta para sessões
# IMPORTANTE: Em produção, use uma chave secreta forte e única
# A chave secreta é usada para assinar cookies de sessão
app.secret_key = os.getenv("FLASK_SECRET_KEY", "chave_de_dev_insegura_use_o_env") 

# Constantes para chaves de sessão
# Essas constantes definem as chaves usadas no dicionário de sessão
SESSION_KEY_TOKEN = 'user_token'  # Armazena o token JWT retornado pela API
SESSION_KEY_TYPE = 'user_type'    # Armazena o tipo de usuário (aluno/professor/admin)



# ============================================================================
# CARREGAMENTO DA BIBLIOTECA C (DLL/SO)
# ============================================================================
# 
# Esta seção carrega dinamicamente a biblioteca C compilada que contém
# algoritmos otimizados para processamento de dados acadêmicos.
# 
# A biblioteca C é usada para:
# - Ordenação eficiente de alunos por desempenho (média final)
# - Processamento de grandes volumes de dados com performance otimizada
# 
# A biblioteca é opcional - se não for encontrada, o sistema continua
# funcionando normalmente, mas sem os algoritmos otimizados.

lib_c = None  # Variável global que armazenará a referência à biblioteca

try:
    # Detecta o sistema operacional para carregar a biblioteca correta
    # Windows usa .dll, Linux/Mac usam .so
    lib_name = "algorithms.dll" if platform.system() == "Windows" else "algorithms.so"
    
    # Constrói o caminho relativo para a biblioteca
    # O caminho é: ../03_algorithms_c/algorithms.dll (ou .so)
    lib_path = os.path.join(os.path.dirname(__file__), "..", "03_algorithms_c", lib_name)

    # Carrega a biblioteca dinâmica usando ctypes
    lib_c = ctypes.CDLL(lib_path)

    # Define a estrutura C em Python usando ctypes.Structure
    # Esta estrutura corresponde ao struct DesempenhoAluno em C:
    # struct DesempenhoAluno {
    #     int id_aluno;
    #     float media_final;
    # }
    class DesempenhoAluno(ctypes.Structure):
        _fields_ = [
            ("id_aluno", ctypes.c_int),      # ID do aluno (inteiro)
            ("media_final", ctypes.c_float)   # Média final (ponto flutuante)
        ]

    # Define a assinatura da função C para o Python
    # void ordenar_por_desempenho(DesempenhoAluno* array, int tamanho)
    lib_c.ordenar_por_desempenho.argtypes = [
        ctypes.POINTER(DesempenhoAluno),  # Ponteiro para array de estruturas
        ctypes.c_int                       # Tamanho do array
    ]
    lib_c.ordenar_por_desempenho.restype = None  # Função void (sem retorno)

    print("(Flask) Biblioteca C 'algorithms' carregada com sucesso.")

except Exception as e:
    # Se houver erro ao carregar a biblioteca, registra o erro mas continua
    # Isso permite que o sistema funcione mesmo sem a biblioteca C
    print(f"(Flask) ERRO AO CARREGAR BIBLIOTECA C: {e}")
    print("   As funcionalidades de relatório C (ordenação) estarão desativadas.")
    lib_c = None  # Garante que o app rode mesmo se o C falhar

# ============================================================================
# FUNÇÕES DE RENDERIZAÇÃO E BASE HTML
# ============================================================================
# 
# Estas funções são responsáveis por gerar o HTML das páginas do sistema.
# Utilizam render_template_string do Flask para criar templates dinâmicos
# com conteúdo específico para cada tipo de usuário.

def gerar_sidebar(user_type=None):
    """
    Gera a sidebar de navegação personalizada baseada no tipo de usuário.
    
    Esta função cria uma barra lateral de navegação com links específicos
    para cada perfil de usuário, incluindo cores e ícones personalizados.
    
    Nota: Esta função está atualmente não utilizada (sidebar foi removida),
    mas é mantida para possível uso futuro.
    
    Args:
        user_type (str, optional): Tipo de usuário ('aluno', 'professor', 'admin').
                                   Se None, obtém da sessão atual.
    
    Returns:
        str: HTML completo da sidebar personalizada
    
    Estrutura gerada:
        - Header com título do perfil
        - Links de navegação específicos por perfil
        - Footer com botão de logout
    """
    if not user_type:
        user_type = session.get(SESSION_KEY_TYPE, 'aluno')
    
    # Configurações por tipo de usuário
    configs = {
        'aluno': {
            'titulo': 'Aluno',
            'cor': '#667eea',
            'gradiente': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'links': [
                {'url': url_for('painel_aluno'), 'texto': '📊 Dashboard', 'icon': '📊'},
                {'url': url_for('boletim'), 'texto': '📋 Boletim', 'icon': '📋'},
                {'url': url_for('chat_ia'), 'texto': '🤖 Assistente IA', 'icon': '🤖'},
            ]
        },
        'professor': {
            'titulo': 'Professor',
            'cor': '#4CAF50',
            'gradiente': 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
            'links': [
                {'url': url_for('painel_professor'), 'texto': '📊 Painel', 'icon': '📊'},
                {'url': url_for('dashboard'), 'texto': '👥 Minhas Turmas', 'icon': '👥'},
                {'url': url_for('dashboard'), 'texto': '📝 Lançar Notas', 'icon': '📝'},
            ]
        },
        'admin': {
            'titulo': 'Administrador',
            'cor': '#ff9800',
            'gradiente': 'linear-gradient(135deg, #ff9800 0%, #f57c00 100%)',
            'links': [
                {'url': url_for('painel_admin'), 'texto': '⚙️ Painel Admin', 'icon': '⚙️'},
                {'url': url_for('dashboard'), 'texto': '📊 Dashboard', 'icon': '📊'},
            ]
        }
    }
    
    config = configs.get(user_type, configs['aluno'])
    
    links_html = ''
    for link in config['links']:
        links_html += f'''
            <a href="{link['url']}" class="sidebar-link">
                <span class="sidebar-icon">{link['icon']}</span>
                <span class="sidebar-text">{link['texto']}</span>
            </a>
        '''
    
    sidebar_html = f'''
    <div class="sidebar" style="background: {config['gradiente']};">
        <div class="sidebar-header">
            <h2 class="sidebar-title">{config['titulo']}</h2>
        </div>
        <nav class="sidebar-nav">
            {links_html}
        </nav>
        <div class="sidebar-footer">
            <a href="{url_for('logout')}" class="sidebar-link sidebar-logout">
                <span class="sidebar-icon">🚪</span>
                <span class="sidebar-text">Sair</span>
            </a>
        </div>
    </div>
    '''
    
    return sidebar_html

def render_base(content_html, page_title="Sistema Acadêmico PIM"):
    """
    Função principal de renderização que fornece o template base do sistema.
    
    Esta função cria o HTML base para todas as páginas do sistema, incluindo:
    - Estrutura HTML5 completa
    - Estilos CSS modernos e responsivos
    - Área de conteúdo principal
    - Suporte para botões de navegação
    
    Args:
        content_html (str): Conteúdo HTML específico da página a ser renderizada
        page_title (str): Título da página exibido na aba do navegador
    
    Returns:
        str: HTML completo renderizado usando render_template_string do Flask
    
    Características do layout:
        - Design responsivo (mobile-friendly)
        - Estilos CSS inline para evitar dependências externas
        - Suporte para botões de voltar e sair
        - Background moderno e cores consistentes
    """
    base_html = f'''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{page_title}</title>
        <style>
            :root {{
                --accent: #1b55f8;
                --error: #d32f2f;
            }}
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                padding: 20px;
                background: #f5f7fa;
                min-height: 100vh;
            }}
            
            .main-content {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            
            .btn-voltar {{
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 12px 24px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 1rem;
                transition: all 0.3s ease;
                box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
                margin-bottom: 20px;
            }}
            
            .btn-voltar:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            }}
            
            .btn-sair {{
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 12px 24px;
                background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 1rem;
                transition: all 0.3s ease;
                box-shadow: 0 2px 6px rgba(220, 53, 69, 0.3);
                margin-bottom: 20px;
                margin-left: 15px;
            }}
            
            .btn-sair:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(220, 53, 69, 0.4);
            }}
            
            .nav-buttons-container {{
                display: flex;
                align-items: center;
                flex-wrap: wrap;
                margin-bottom: 20px;
            }}
            
            @media (max-width: 768px) {{
                .nav-buttons-container {{
                    flex-direction: column;
                }}
                
                .btn-sair {{
                    margin-left: 0;
                    margin-top: 10px;
                }}
            }}
        </style>
    </head>
    <body>
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
    # Certifique-se de que esta é a sua função com o código da SIDEBAR
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

# ============================================================================
# DECORATOR DE AUTENTICAÇÃO
# ============================================================================

def require_login(view_func):
    """
    Decorator que protege rotas exigindo autenticação.
    
    Este decorator verifica se o usuário está autenticado antes de permitir
    acesso a uma rota protegida. Se não estiver autenticado, redireciona
    para a página de login.
    
    Funcionamento:
    1. Verifica se existe um token JWT na sessão
    2. Se não existir, redireciona para /login
    3. Se existir, permite o acesso à rota original
    
    Uso:
        @app.route('/rota-protegida')
        @require_login
        def minha_rota():
            return "Conteúdo protegido"
    
    Args:
        view_func: Função da rota a ser protegida
    
    Returns:
        Função wrapper que verifica autenticação antes de executar a rota
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
    
    # Contagem de estatísticas (calcula após agrupamento para evitar duplicatas)
    turmas_agrupadas_temp = {}
    if turmas:
        for t in turmas:
            turma_id = t.get('turma_id')
            disciplina_id = t.get('disciplina_id')
            if turma_id not in turmas_agrupadas_temp:
                turmas_agrupadas_temp[turma_id] = set()
            if disciplina_id:
                turmas_agrupadas_temp[turma_id].add(disciplina_id)
    
    total_turmas = len(turmas_agrupadas_temp) if turmas else 0
    total_disciplinas = sum(len(discs) for discs in turmas_agrupadas_temp.values()) if turmas else 0
    
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
        # Agrupa disciplinas por turma, removendo duplicatas
        turmas_agrupadas = {}
        for t in turmas:
            turma_id = t.get('turma_id')
            disciplina_id = t.get('disciplina_id')
            
            if turma_id not in turmas_agrupadas:
                 turmas_agrupadas[turma_id] = {
                     'nome': t.get('nome_turma'), 
                     'ano': t.get('ano'), 
                     'disciplinas': {}  # Usa dict para evitar duplicatas (chave: disciplina_id)
                 }
            
            # Só adiciona a disciplina se ela ainda não existir nesta turma
            if disciplina_id and disciplina_id not in turmas_agrupadas[turma_id]['disciplinas']:
                turmas_agrupadas[turma_id]['disciplinas'][disciplina_id] = {
                    'disciplina_id': disciplina_id,
                    'nome_disciplina': t.get('nome_disciplina', 'N/A')
                }
        
        turmas_cards_html = '<div class="turmas-grid">'
        
        for turma_id, info in turmas_agrupadas.items():
            nome_turma = escape(info['nome'])
            ano = info['ano']
            
            disciplinas_html = ''
            # Converte o dict de disciplinas para lista e renderiza
            for disciplina_id, disc_info in info['disciplinas'].items():
                disciplina_nome = escape(disc_info['nome_disciplina'])
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
    <h2 style="color: #333; margin-top: 30px; margin-bottom: 20px;">Minhas Turmas e Disciplinas</h2>
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
def render_admin_content(user_type, recursos, feedback_msg, feedback_cls, token=None):
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
    # Preparar dados para JavaScript (disciplinas por turma e matrículas)
    turmas_json = {str(t['turma_id']): {'nome': t['nome_turma'], 'ano': t['ano']} for t in recursos['turmas']}
    
    # Buscar disciplinas associadas a cada turma (usando dados disponíveis)
    disciplinas_por_turma = {}
    try:
        # Tenta buscar disciplinas de cada turma via API
        token = session.get(SESSION_KEY_TOKEN)
        for turma in recursos['turmas']:
            turma_id = str(turma['turma_id'])
            disciplinas_por_turma[turma_id] = []
            # Nota: Será preenchido dinamicamente via JavaScript se necessário
    except:
        pass
    
    # Preparar opções de alunos para busca de matrícula
    alunos_options = ''
    if 'alunos' in recursos:
        alunos_options = ''.join(f'<option value="{a["aluno_id"]}">{escape(a.get("nome", ""))} {escape(a.get("sobrenome", ""))}</option>' for a in recursos.get('alunos', []))
    
    secao_acoes_destrutivas = f"""
    <div class="admin-section">
        <h2 class="admin-section-title" style="border-bottom-color: #d32f2f;">Ações Destrutivas</h2>
        
        <script data-token="{token or ''}">
        // Dados para filtros dinâmicos
        const todasDisciplinas = {{{
            ",".join([f'"{d["disciplina_id"]}": "{escape(d["nome_disciplina"])}"' for d in recursos['disciplinas']])
        }}};
        const apiBaseUrl = "{API_BASE_URL}";
        
        // Função para obter token da sessão
        function getToken() {{
            // Tenta pegar do atributo data-token do script
            const scriptTag = document.querySelector('script[data-token]');
            if (scriptTag) {{
                return scriptTag.getAttribute('data-token') || '';
            }}
            // Fallback: tenta pegar do cookie
            const match = document.cookie.match(/session_token=([^;]+)/);
            if (match) return match[1];
            return '';
        }}
        
        // Função para filtrar disciplinas quando turma é selecionada
        function filtrarDisciplinasPorTurma(turmaId, selectDisciplinaId) {{
            const select = document.getElementById(selectDisciplinaId);
            
            // Limpa opções atuais
            select.innerHTML = '<option value="">Carregando...</option>';
            
            // Se nenhuma turma selecionada, mostra todas
            if (!turmaId || turmaId === '') {{
                select.innerHTML = '<option value="">Selecione uma disciplina...</option>';
                for (const [id, nome] of Object.entries(todasDisciplinas)) {{
                    const option = document.createElement('option');
                    option.value = id;
                    option.textContent = nome;
                    select.appendChild(option);
                }}
                return;
            }}
            
            // Busca disciplinas desta turma via API
            fetch(`${{apiBaseUrl}}/academico/turmas/${{turmaId}}/disciplinas`, {{
                headers: {{'Authorization': 'Bearer ' + getToken()}}
            }})
            .then(res => res.json())
            .then(data => {{
                select.innerHTML = '<option value="">Selecione uma disciplina...</option>';
                if (data.disciplinas && data.disciplinas.length > 0) {{
                    data.disciplinas.forEach(disc => {{
                        const option = document.createElement('option');
                        option.value = disc.disciplina_id;
                        option.textContent = disc.nome_disciplina || todasDisciplinas[disc.disciplina_id] || 'Disciplina';
                        select.appendChild(option);
                    }});
                }} else {{
                    select.innerHTML = '<option value="">Nenhuma disciplina encontrada para esta turma</option>';
                }}
            }})
            .catch(err => {{
                console.error('Erro ao buscar disciplinas:', err);
                select.innerHTML = '<option value="">Erro ao carregar disciplinas</option>';
            }});
        }}
        
        // Função para buscar matrícula
        function buscarMatricula() {{
            const alunoId = document.getElementById('busca_aluno_id').value;
            const turmaId = document.getElementById('busca_turma_id').value;
            const disciplinaId = document.getElementById('busca_disciplina_id').value;
            const resultadoDiv = document.getElementById('resultado_matricula');
            
            if (!alunoId || !turmaId || !disciplinaId) {{
                resultadoDiv.innerHTML = '<p style="color: #666;">Preencha todos os campos para buscar.</p>';
                return;
            }}
            
            resultadoDiv.innerHTML = '<p>Buscando...</p>';
            
            // Busca a matrícula específica (precisa buscar via alunos da turma/disciplina)
            fetch(`${{apiBaseUrl}}/academico/turmas/${{turmaId}}/disciplinas/${{disciplinaId}}/alunos`, {{
                headers: {{'Authorization': 'Bearer ' + getToken()}}
            }})
            .then(res => res.json())
            .then(data => {{
                if (data.alunos && data.alunos.length > 0) {{
                    // Procura o aluno específico na lista
                    const alunoEncontrado = data.alunos.find(a => a.aluno_id == alunoId);
                        if (alunoEncontrado && alunoEncontrado.matricula_id) {{
                        const matId = alunoEncontrado.matricula_id;
                        const nomeAluno = (alunoEncontrado.nome || '') + ' ' + (alunoEncontrado.sobrenome || '');
                        resultadoDiv.innerHTML = `
                            <div style="background: #f0f0f0; padding: 15px; border-radius: 8px; margin-top: 10px;">
                                <p><strong>Matrícula encontrada!</strong></p>
                                <p><strong>ID da Matrícula:</strong> ${{matId}}</p>
                                <p><strong>Aluno:</strong> ${{nomeAluno.trim()}}</p>
                                <button type="button" onclick="confirmarExclusaoMatricula(${{matId}})" class="danger" style="margin-top: 10px; width: 100%;">
                                    Confirmar Exclusão da Matrícula
                                </button>
                            </div>
                        `;
                    }} else {{
                        resultadoDiv.innerHTML = '<p style="color: #d32f2f;"> Aluno não encontrado nesta turma/disciplina.</p>';
                    }}
                }} else {{
                    resultadoDiv.innerHTML = '<p style="color: #d32f2f;"> Nenhuma matrícula encontrada com estes critérios.</p>';
                }}
            }})
            .catch(err => {{
                console.error('Erro:', err);
                resultadoDiv.innerHTML = '<p style="color: #d32f2f;">Erro ao buscar matrícula. Tente novamente.</p>';
            }});
        }}
        
        // Função de confirmação antes de ações destrutivas
        function confirmarAcao(mensagem, formId) {{
            if (confirm(mensagem)) {{
                document.getElementById(formId).submit();
            }}
        }}
        
        function confirmarExclusaoMatricula(matriculaId) {{
            if (confirm('Tem certeza que deseja excluir esta matrícula? Esta ação é permanente e pode falhar se houver notas lançadas.')) {{
                const form = document.createElement('form');
                form.method = 'POST';
                form.innerHTML = `
                    <input type="hidden" name="action" value="delete_matricula">
                    <input type="hidden" name="matricula_id" value="${{matriculaId}}">
                `;
                document.body.appendChild(form);
                form.submit();
            }}
        }}
        </script>
        
        <div class="admin-grid">
            <div class="admin-card danger">
                <h3>Desassociar Disciplina de Turma</h3>
                <p style="font-size: 0.9em; color: #666; margin-top: 0;">Remove a disciplina da grade da turma. A disciplina não é excluída do sistema.</p>
                <form method="POST" id="form_desassociar" onsubmit="return confirm('Tem certeza que deseja desassociar esta disciplina da turma?')">
                    <input type="hidden" name="action" value="remove_disciplina_from_turma">
                    <label for="remove_turma_id">Turma:</label>
                    <select name="turma_id" id="remove_turma_id" required onchange="filtrarDisciplinasPorTurma(this.value, 'remove_disciplina_id')">
                        <option value="">Selecione uma turma...</option>
                        {turma_options if turma_options else '<option>Nenhuma turma disponível</option>'}
                    </select>
                    <label for="remove_disciplina_id">Disciplina a Remover:</label>
                    <select name="disciplina_id" id="remove_disciplina_id" required>
                        <option value="">Selecione primeiro uma turma...</option>
                    </select>
                    <button type="submit" class="danger">Desassociar Disciplina</button>
                </form>
            </div>
            
            <div class="admin-card warning">
                <h3>Limpar Notas de Disciplina</h3>
                <p style="font-size: 0.9em; color: #666; margin-top: 0;">Exclui TODAS as notas (NP1, NP2, Exame, etc.) associadas à disciplina. Use antes de excluir a disciplina.</p>
                <form method="POST" id="form_limpar_notas" onsubmit="return confirm('ATENÇÃO: Todas as notas desta disciplina serão excluídas permanentemente!\\n\\nTem certeza que deseja continuar?')">
                    <input type="hidden" name="action" value="delete_notas_da_disciplina">
                    <label for="delete_notas_disciplina_id">Disciplina:</label>
                    <select name="disciplina_id_para_limpar" id="delete_notas_disciplina_id" required>
                        <option value="">Selecione uma disciplina...</option>
                        {disciplina_options if disciplina_options else '<option>Nenhuma disciplina disponível</option>'}
                    </select>
                    <div class="info-box"> Esta ação não pode ser desfeita!</div>
                    <button type="submit" class="warning">Limpar Todas as Notas</button>
                </form>
            </div>
            
            <div class="admin-card danger">
                <h3>Remover Matrícula</h3>
                <p style="font-size: 0.9em; color: #666; margin-top: 0;">Remove um aluno de uma turma/disciplina. Pode falhar se houver notas lançadas.</p>
                <div style="margin-bottom: 15px;">
                    <label for="busca_aluno_id">Aluno:</label>
                    <select id="busca_aluno_id" style="width: 100%; margin-bottom: 10px;">
                        <option value="">Selecione um aluno...</option>
                        {alunos_options if alunos_options else '<option>Nenhum aluno disponível</option>'}
                    </select>
                    <label for="busca_turma_id">Turma:</label>
                    <select id="busca_turma_id" style="width: 100%; margin-bottom: 10px;">
                        <option value="">Selecione uma turma...</option>
                        {turma_options if turma_options else '<option>Nenhuma turma disponível</option>'}
                    </select>
                    <label for="busca_disciplina_id">Disciplina:</label>
                    <select id="busca_disciplina_id" style="width: 100%; margin-bottom: 10px;">
                        <option value="">Selecione uma disciplina...</option>
                        {disciplina_options if disciplina_options else '<option>Nenhuma disciplina disponível</option>'}
                    </select>
                    <button type="button" onclick="buscarMatricula()" class="primary" style="width: 100%; margin-top: 10px;">
                         Buscar Matrícula
                    </button>
                    <div id="resultado_matricula"></div>
                </div>
                <div class="info-box">
                     Dica: Selecione aluno, turma e disciplina para encontrar a matrícula automaticamente.
                </div>
            </div>
            
            <div class="admin-card danger" style="grid-column: 1 / -1;">
                <h3> Assistente de Exclusão de Disciplina</h3>
                <p style="font-size: 0.9em; color: #666; margin-top: 0;">Siga os passos na ordem correta para excluir uma disciplina do sistema de forma segura.</p>
                
                <div style="margin-bottom: 20px;">
                    <label for="assistente_disciplina_id">Selecione a Disciplina:</label>
                    <select name="disciplina_id" id="assistente_disciplina_id" onchange="verificarStatusExclusao(this.value)" style="width: 100%;">
                        <option value="">Selecione uma disciplina...</option>
                        {disciplina_options if disciplina_options else '<option>Nenhuma disciplina disponível</option>'}
                    </select>
                </div>
                
                <div id="status_exclusao" style="display: none;">
                    <div class="exclusao-checklist">
                        <div class="checklist-item" id="step1">
                            <div class="step-header">
                                <span class="step-number">1</span>
                                <span class="step-title">Limpar Todas as Notas</span>
                                <span class="step-status" id="status1">Pendente</span>
                            </div>
                            <div class="step-details" id="details1">
                                <p>Verificando notas...</p>
                            </div>
                            <button type="button" class="step-btn" id="btn1" onclick="executarEtapa(1)" disabled>Executar</button>
                        </div>
                        
                        <div class="checklist-item" id="step2">
                            <div class="step-header">
                                <span class="step-number">2</span>
                                <span class="step-title">Verificar/Remover Matrículas</span>
                                <span class="step-status" id="status2">Aguardando etapa 1</span>
                            </div>
                            <div class="step-details" id="details2">
                                <p>Aguardando...</p>
                            </div>
                            <button type="button" class="step-btn" id="btn2" onclick="executarEtapa(2)" disabled>Verificar</button>
                        </div>
                        
                        <div class="checklist-item" id="step3">
                            <div class="step-header">
                                <span class="step-number">3</span>
                                <span class="step-title">Desassociar de Todas as Turmas</span>
                                <span class="step-status" id="status3">Aguardando etapas anteriores</span>
                            </div>
                            <div class="step-details" id="details3">
                                <p>Aguardando...</p>
                            </div>
                            <button type="button" class="step-btn" id="btn3" onclick="executarEtapa(3)" disabled>Executar</button>
                        </div>
                        
                        <div class="checklist-item final" id="step4">
                            <div class="step-header">
                                <span class="step-number">4</span>
                                <span class="step-title">Excluir Disciplina Permanentemente</span>
                                <span class="step-status" id="status4"> Aguardando todas as etapas</span>
                            </div>
                            <div class="step-details" id="details4">
                                <p>Aguardando conclusão das etapas anteriores...</p>
                            </div>
                            <form method="POST" id="form_excluir_final" onsubmit="return confirm(' ÚLTIMA CONFIRMAÇÃO!\\n\\nTem ABSOLUTA certeza que deseja excluir esta disciplina permanentemente?\\n\\nEsta ação é IRREVERSÍVEL!')">
                    <input type="hidden" name="action" value="delete_disciplina">
                                <input type="hidden" name="disciplina_id" id="final_disciplina_id" value="">
                                <button type="submit" class="step-btn danger" id="btn4" disabled> EXCLUIR PERMANENTEMENTE</button>
                </form>
                        </div>
                    </div>
                </div>
                
                <style>
                .exclusao-checklist {{
                    margin-top: 20px;
                }}
                .checklist-item {{
                    background: #f8f9fa;
                    border-left: 4px solid #6c757d;
                    padding: 20px;
                    margin-bottom: 15px;
                    border-radius: 8px;
                    transition: all 0.3s;
                }}
                .checklist-item.completed {{
                    background: #d4edda;
                    border-left-color: #28a745;
                }}
                .checklist-item.active {{
                    background: #fff3cd;
                    border-left-color: #ffc107;
                }}
                .checklist-item.blocked {{
                    opacity: 0.6;
                    background: #e9ecef;
                }}
                .checklist-item.final {{
                    background: #ffebee;
                    border-left-color: #d32f2f;
                }}
                .checklist-item.final.completed {{
                    background: #ffcdd2;
                }}
                .step-header {{
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    margin-bottom: 10px;
                }}
                .step-number {{
                    width: 35px;
                    height: 35px;
                    border-radius: 50%;
                    background: #6c757d;
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    font-size: 1.1rem;
                }}
                .checklist-item.completed .step-number {{
                    background: #28a745;
                }}
                .checklist-item.active .step-number {{
                    background: #ffc107;
                    color: #000;
                }}
                .step-title {{
                    flex: 1;
                    font-weight: 600;
                    font-size: 1.1rem;
                }}
                .step-status {{
                    padding: 5px 12px;
                    border-radius: 15px;
                    font-size: 0.9rem;
                    font-weight: 500;
                    background: #e9ecef;
                    color: #6c757d;
                }}
                .checklist-item.completed .step-status {{
                    background: #d4edda;
                    color: #155724;
                }}
                .checklist-item.active .step-status {{
                    background: #fff3cd;
                    color: #856404;
                }}
                .step-details {{
                    margin: 10px 0 15px 50px;
                    padding: 10px;
                    background: white;
                    border-radius: 6px;
                    font-size: 0.9rem;
                    color: #555;
                }}
                .step-btn {{
                    margin-left: 50px;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 600;
                    background: #6c757d;
                    color: white;
                    transition: all 0.3s;
                }}
                .step-btn:hover:not(:disabled) {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }}
                .step-btn:disabled {{
                    opacity: 0.5;
                    cursor: not-allowed;
                }}
                .step-btn.enabled {{
                    background: #28a745;
                }}
                .step-btn.warning {{
                    background: #ffc107;
                    color: #000;
                }}
                .step-btn.danger.enabled {{
                    background: #d32f2f;
                    color: white;
                }}
                </style>
                
                <script>
                let disciplinaSelecionada = null;
                let statusEtapas = {{1: false, 2: false, 3: false, 4: false}};
                
                function verificarStatusExclusao(disciplinaId) {{
                    if (!disciplinaId) {{
                        document.getElementById('status_exclusao').style.display = 'none';
                        return;
                    }}
                    
                    disciplinaSelecionada = disciplinaId;
                    document.getElementById('final_disciplina_id').value = disciplinaId;
                    document.getElementById('status_exclusao').style.display = 'block';
                    
                    // Reset estados
                    statusEtapas = {{1: false, 2: false, 3: false, 4: false}};
                    resetarEtapas();
                    
                    // Verifica status da disciplina
                    verificarEtapa1(disciplinaId);
                }}
                
                function resetarEtapas() {{
                    for (let i = 1; i <= 4; i++) {{
                        document.getElementById(`step${{i}}`).classList.remove('completed', 'active', 'blocked');
                        document.getElementById(`status${{i}}`).textContent = i === 1 ? ' Verificando...' : ' Aguardando';
                        document.getElementById(`btn${{i}}`).disabled = true;
                    }}
                }}
                
                function verificarEtapa1(disciplinaId) {{
                    // Tenta fazer um DELETE para verificar se há notas (404 = sem notas, 200 = há notas)
                    // Mas melhor: tenta buscar notas através de uma query indireta
                    // Como não há rota GET direta, vamos tentar uma abordagem diferente:
                    // Buscar todas as turmas e verificar se há notas em alguma delas
                    
                    fetch(`${{apiBaseUrl}}/academico/turmas`, {{
                        headers: {{'Authorization': 'Bearer ' + getToken()}}
                    }})
                    .then(res => res.json())
                    .then(data => {{
                        const turmas = data.turmas || [];
                        let verificacoes = 0;
                        let temNotas = false;
                        
                        if (turmas.length === 0) {{
                            document.getElementById('details1').innerHTML = '<p> Nenhuma turma encontrada. Nenhuma nota.</p>';
                            marcarEtapaComoConcluida(1, 'Sem notas');
                            verificarEtapa2(disciplinaId);
                            return;
                        }}
                        
                        // Verifica se há notas em alguma turma/disciplina
                        turmas.forEach(turma => {{
                            // Tenta buscar alunos (se conseguir, pode ter notas)
                            fetch(`${{apiBaseUrl}}/academico/turmas/${{turma.turma_id}}/disciplinas/${{disciplinaId}}/alunos`, {{
                                headers: {{'Authorization': 'Bearer ' + getToken()}}
                            }})
                            .then(res => {{
                                verificacoes++;
                                if (res.status === 200) {{
                                    return res.json().then(alunosData => {{
                                        const alunos = alunosData.alunos || [];
                                        // Se algum aluno tiver notas (nota_np1, nota_np2, etc.), tem notas
                                        alunos.forEach(aluno => {{
                                            if (aluno.nota_np1 || aluno.nota_np2 || aluno.nota_exame) {{
                                                temNotas = true;
                                            }}
                                        }});
                                        
                                        if (verificacoes === turmas.length) {{
                                            if (temNotas) {{
                                                document.getElementById('details1').innerHTML = '<p><strong>Notas encontradas.</strong> Precisa limpar antes de excluir.</p>';
                                                habilitarEtapa(1);
                                            }} else {{
                                                document.getElementById('details1').innerHTML = '<p> Nenhuma nota encontrada.</p>';
                                                marcarEtapaComoConcluida(1, 'Sem notas');
                                                verificarEtapa2(disciplinaId);
                                            }}
                                        }}
                                    }});
                                }} else {{
                                    // Turma não tem essa disciplina ou não há alunos
                                    if (verificacoes === turmas.length && !temNotas) {{
                                        document.getElementById('details1').innerHTML = '<p> Nenhuma nota encontrada.</p>';
                                        marcarEtapaComoConcluida(1, 'Sem notas');
                                        verificarEtapa2(disciplinaId);
                                    }}
                                }}
                            }})
                            .catch(() => {{
                                verificacoes++;
                                if (verificacoes === turmas.length && !temNotas) {{
                                    document.getElementById('details1').innerHTML = '<p> Nenhuma nota encontrada.</p>';
                                    marcarEtapaComoConcluida(1, 'Sem notas');
                                    verificarEtapa2(disciplinaId);
                                }}
                            }});
                        }});
                    }})
                    .catch(err => {{
                        console.error('Erro:', err);
                        // Em caso de erro, permite tentar limpar notas manualmente
                        document.getElementById('details1').innerHTML = '<p>Clique em "Executar" para limpar as notas (se houver).</p>';
                        habilitarEtapa(1);
                    }});
                }}
                
                function verificarEtapa2(disciplinaId) {{
                    // Busca matrículas verificando em todas as turmas
                    fetch(`${{apiBaseUrl}}/academico/disciplinas/${{disciplinaId}}`, {{
                        headers: {{'Authorization': 'Bearer ' + getToken()}}
                    }})
                    .then(res => res.json())
                    .then(data => {{
                        // Tenta verificar se há matrículas através de uma busca
                        document.getElementById('details2').innerHTML = '<p>Clique em "Verificar" para buscar matrículas.</p>';
                        habilitarEtapa(2);
                    }})
                    .catch(err => {{
                        document.getElementById('details2').innerHTML = '<p>Clique em "Verificar" para buscar matrículas.</p>';
                        habilitarEtapa(2);
                    }});
                }}
                
                function executarEtapa(numero) {{
                    if (!disciplinaSelecionada) return;
                    
                    const disciplinaId = disciplinaSelecionada;
                    
                    if (numero === 1) {{
                        // Limpar notas
                        if (!confirm('Tem certeza que deseja excluir TODAS as notas desta disciplina? Esta ação não pode ser desfeita!')) {{
                            return;
                        }}
                        
                        document.getElementById(`step${{numero}}`).classList.add('active');
                        document.getElementById(`status${{numero}}`).textContent = ' Executando...';
                        
                        fetch(`${{apiBaseUrl}}/academico/disciplinas/${{disciplinaId}}/notas`, {{
                            method: 'DELETE',
                            headers: {{'Authorization': 'Bearer ' + getToken()}}
                        }})
                        .then(res => {{
                            if (res.status === 200) {{
                                return res.json().then(data => {{
                                    marcarEtapaComoConcluida(1, 'Notas excluídas com sucesso');
                                    habilitarEtapa(2);
                                    verificarEtapa2(disciplinaId);
                                    return data;
                                }});
                            }} else {{
                                return res.json().then(data => {{
                                    document.getElementById('details1').innerHTML = `<p style="color: #d32f2f;">Erro: ${{data.message || 'Erro ao excluir notas'}}</p>`;
                                    throw new Error(data.message || 'Erro ao excluir notas');
                                }});
                            }}
                        }})
                        .catch(err => {{
                            document.getElementById('details1').innerHTML = '<p style="color: #d32f2f;">Erro ao executar.</p>';
                        }});
                    }} else if (numero === 2) {{
                        // Verificar matrículas
                        document.getElementById(`step${{numero}}`).classList.add('active');
                        document.getElementById(`status${{numero}}`).textContent = '🔄 Verificando...';
                        document.getElementById('details2').innerHTML = '<p>Buscando matrículas...</p>';
                        
                        // Como não há rota direta, verificamos tentando buscar alunos
                        // Se conseguirmos listar turmas, verificamos se há matrículas
                        fetch(`${{apiBaseUrl}}/academico/turmas`, {{
                            headers: {{'Authorization': 'Bearer ' + getToken()}}
                        }})
                        .then(res => res.json())
                        .then(data => {{
                            const turmas = data.turmas || [];
                            let totalMatriculas = 0;
                            let verificacoes = 0;
                            
                            if (turmas.length === 0) {{
                                document.getElementById('details2').innerHTML = '<p> Nenhuma turma encontrada. Nenhuma matrícula.</p>';
                                marcarEtapaComoConcluida(2, 'Sem matrículas');
                                habilitarEtapa(3);
                                return;
                            }}
                            
                            turmas.forEach(turma => {{
                                fetch(`${{apiBaseUrl}}/academico/turmas/${{turma.turma_id}}/disciplinas/${{disciplinaId}}/alunos`, {{
                                    headers: {{'Authorization': 'Bearer ' + getToken()}}
                                }})
                                .then(res => {{
                                    if (res.status === 200) {{
                                        return res.json();
                                    }}
                                    return {{alunos: []}};
                                }})
                                .then(data => {{
                                    verificacoes++;
                                    const alunos = data.alunos || [];
                                    totalMatriculas += alunos.length;
                                    
                                    if (verificacoes === turmas.length) {{
                                        if (totalMatriculas === 0) {{
                                            document.getElementById('details2').innerHTML = '<p> Nenhuma matrícula encontrada.</p>';
                                            marcarEtapaComoConcluida(2, 'Sem matrículas');
                                            habilitarEtapa(3);
                                        }} else {{
                                            document.getElementById('details2').innerHTML = `<p style="color: #856404;"><strong>${{totalMatriculas}}</strong> matrícula(s) encontrada(s).<br>Você precisa remover todas as matrículas manualmente antes de continuar.</p>`;
                                            document.getElementById('status2').textContent = ' Requer ação manual';
                                        }}
                                    }}
                                }})
                                .catch(() => {{
                                    verificacoes++;
                                    if (verificacoes === turmas.length && totalMatriculas === 0) {{
                                        document.getElementById('details2').innerHTML = '<p> Nenhuma matrícula encontrada.</p>';
                                        marcarEtapaComoConcluida(2, 'Sem matrículas');
                                        habilitarEtapa(3);
                                    }}
                                }});
                            }});
                        }})
                        .catch(err => {{
                            document.getElementById('details2').innerHTML = '<p style="color: #d32f2f;">Erro ao verificar. Tente novamente.</p>';
                        }});
                    }} else if (numero === 3) {{
                        // Desassociar de turmas
                        if (!confirm('Tem certeza que deseja desassociar esta disciplina de TODAS as turmas?')) {{
                            return;
                        }}
                        
                        document.getElementById(`step${{numero}}`).classList.add('active');
                        document.getElementById(`status${{numero}}`).textContent = ' Executando...';
                        
                        // Busca todas as turmas e desassocia
                        fetch(`${{apiBaseUrl}}/academico/turmas`, {{
                            headers: {{'Authorization': 'Bearer ' + getToken()}}
                        }})
                        .then(res => res.json())
                        .then(data => {{
                            const turmas = data.turmas || [];
                            if (turmas.length === 0) {{
                                document.getElementById('details3').innerHTML = '<p> Nenhuma turma associada.</p>';
                                marcarEtapaComoConcluida(3, 'Nenhuma associação');
                                habilitarEtapa(4);
                                return;
                            }}
                            
                            let desassociacoes = 0;
                            let total = turmas.length;
                            
                            turmas.forEach(turma => {{
                                fetch(`${{apiBaseUrl}}/academico/turmas/remover-disciplina`, {{
                                    method: 'POST',
                                    headers: {{
                                        'Authorization': 'Bearer ' + getToken(),
                                        'Content-Type': 'application/json'
                                    }},
                                    body: JSON.stringify({{
                                        turma_id: parseInt(turma.turma_id),
                                        disciplina_id: parseInt(disciplinaId)
                                    }})
                                }})
                                .then(res => {{
                                    desassociacoes++;
                                    if (desassociacoes === total) {{
                                        document.getElementById('details3').innerHTML = `<p> Desassociação concluída.</p>`;
                                        marcarEtapaComoConcluida(3, 'Concluído');
                                        habilitarEtapa(4);
                                    }}
                                }})
                                .catch(() => {{
                                    desassociacoes++;
                                    if (desassociacoes === total) {{
                                        document.getElementById('details3').innerHTML = `<p> Processo concluído.</p>`;
                                        marcarEtapaComoConcluida(3, 'Concluído');
                                        habilitarEtapa(4);
                                    }}
                                }});
                            }});
                        }})
                        .catch(err => {{
                            document.getElementById('details3').innerHTML = '<p style="color: #d32f2f;">Erro ao executar.</p>';
                        }});
                    }}
                }}
                
                function marcarEtapaComoConcluida(numero, mensagem) {{
                    statusEtapas[numero] = true;
                    const step = document.getElementById(`step${{numero}}`);
                    step.classList.remove('active', 'blocked');
                    step.classList.add('completed');
                    document.getElementById(`status${{numero}}`).textContent = ` ${{mensagem}}`;
                    document.getElementById(`btn${{numero}}`).disabled = true;
                    
                    // Se não for a última etapa, habilita a próxima
                    if (numero < 4) {{
                        habilitarEtapa(numero + 1);
                    }} else {{
                        // Se for a última etapa, verifica se todas estão concluídas
                        verificarSePodeExcluir();
                    }}
                }}
                
                function verificarSePodeExcluir() {{
                    if (statusEtapas[1] && statusEtapas[2] && statusEtapas[3]) {{
                        const btn4 = document.getElementById('btn4');
                        btn4.disabled = false;
                        btn4.classList.add('enabled');
                        document.getElementById('status4').textContent = ' Pronto para excluir';
                        document.getElementById('details4').innerHTML = '<p style="color: #d32f2f;"><strong>Todas as etapas concluídas!</strong><br>Você pode excluir a disciplina permanentemente.</p>';
                    }}
                }}
                
                function habilitarEtapa(numero) {{
                    if (numero > 1 && !statusEtapas[numero - 1]) {{
                        return; // Só habilita se a etapa anterior estiver concluída
                    }}
                    
                    const step = document.getElementById(`step${{numero}}`);
                    step.classList.remove('blocked');
                    step.classList.add('active');
                    document.getElementById(`btn${{numero}}`).disabled = false;
                    document.getElementById(`btn${{numero}}`).classList.add('enabled');
                    
                    if (numero === 2) {{
                        document.getElementById(`btn${{numero}}`).classList.add('warning');
                    }}
                    
                    // Verifica se pode habilitar etapa 4
                    if (numero === 3) {{
                        verificarSePodeExcluir();
                    }}
                }}
                </script>
            </div>
        </div>
    </div>
    """
    
    # === SEÇÃO 5: VISÃO GERAL DO SISTEMA ===
    # Busca estrutura completa: turmas -> disciplinas -> alunos
    estrutura_completa = buscar_estrutura_completa(token)
    secao_visao_geral = construir_visao_geral_html(estrutura_completa)
    
    # === SEÇÃO 6: LISTAS DE REFERÊNCIA ===
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
    {secao_visao_geral}
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
    Rota de autenticação (login) de usuários.
    
    Esta rota gerencia o processo de login no sistema. Autentica o usuário
    através da API Node.js e armazena o token JWT na sessão.
    
    Métodos HTTP:
    - GET: Exibe o formulário de login
    - POST: Processa o login e autentica o usuário
    
    Fluxo de autenticação:
    1. Usuário envia email e senha
    2. Sistema envia credenciais para API Node.js
    3. API valida e retorna token JWT + dados do usuário
    4. Sistema armazena token e tipo de usuário na sessão
    5. Redireciona para dashboard apropriado
    
    Dados do formulário:
    - email: Email do usuário (usado como login)
    - senha: Senha do usuário
    
    Returns:
        GET: HTML do formulário de login
        POST: Redirecionamento para dashboard ou exibição de erro
    """
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
    """
    Rota para encerrar sessão do usuário (logout).
    
    Esta rota limpa os dados da sessão e redireciona o usuário
    para a página de login.
    
    Processo:
    1. Remove o token JWT da sessão
    2. Remove o tipo de usuário da sessão
    3. Redireciona para a página de login
    
    Returns:
        redirect: Redirecionamento para /login
    """
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
    
    conteudo_admin_html = render_admin_content(user_type, recursos, feedback_msg, feedback_cls, token)
    
    # Adiciona botão de sair no topo
    btn_sair = f'''
    <div class="nav-buttons-container">
        <a href="{url_for('logout')}" class="btn-sair">
             Sair
        </a>
    </div>
    '''
    
    conteudo_completo = f'{btn_sair}{conteudo_admin_html}'
    
    return render_base(conteudo_completo, "Painel do Administrador")
# ============================================================================
# FUNÇÕES AUXILIARES DO ADMINISTRADOR
# ============================================================================

def listar_recursos_para_admin(token):
    """
    Busca recursos básicos (turmas e disciplinas) para o painel administrativo.
    
    Esta função realiza requisições à API Node.js para obter listas de
    turmas e disciplinas que serão usadas em formulários e seleções.
    
    Args:
        token (str): Token JWT para autenticação na API
    
    Returns:
        dict: Dicionário com chaves 'turmas' e 'disciplinas', cada uma
              contendo uma lista de dicionários com os dados
    """
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
    """
    Processa ações administrativas enviadas via formulários POST.
    
    Esta função centraliza o processamento de todas as ações administrativas,
    como criação, edição e remoção de turmas, disciplinas, professores e alunos.
    
    Ações suportadas:
    - create_turma: Criar nova turma
    - create_disciplina: Criar nova disciplina
    - create_professor: Criar novo professor
    - create_aluno: Criar novo aluno
    - matricular_aluno: Matricular aluno em turma/disciplina
    - remove_disciplina_from_turma: Remover disciplina de uma turma
    - E outras ações administrativas...
    
    Args:
        action (str): Tipo de ação a ser processada
        form_data (dict): Dados do formulário enviado
        token (str): Token JWT para autenticação na API
    
    Returns:
        dict: Dicionário com 'msg' (mensagem) e 'cls' (classe CSS: 'success' ou 'error')
    
    Raises:
        Exception: Se a ação não for reconhecida ou houver erro na API
    """
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
        
    # (FUTURO) Caso para Associar Disciplinas
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

            # DEBUG LOGS (Manter por enquanto)
            print(f"\n--- [Flask POST Debug - Assign Disciplinas] ---")
            print(f"URL Alvo: {url}")
            print(f"Payload Enviado: {payload}")
            print(f"Token (primeiros 10 chars): Bearer {token[:10]}...")
            print(f"---------------------------------------------\n")
            
            # --- CÓDIGO FALTANTE: EXECUTAR A REQUISIÇÃO E PROCESSAR RESPOSTA ---
            try:
                response = method(url, json=payload, headers={"Authorization": f"Bearer {token}"})
                
                # LOG ANTES DO JSON PARSE
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

    # BLOCO FALTANTE 2: Excluir Disciplina (Global)
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

# --- AUXILIAR: BUSCAR ESTRUTURA COMPLETA DO SISTEMA ---
def buscar_estrutura_completa(token):
    """Busca a estrutura completa: turmas, disciplinas por turma, alunos por turma/disciplina."""
    headers = {"Authorization": f"Bearer {token}"}
    estrutura = {}
    
    try:
        # Busca todas as turmas
        turmas_res = requests.get(f"{API_BASE_URL}/academico/turmas", headers=headers, timeout=5)
        if turmas_res.status_code == 200:
            turmas = turmas_res.json().get('turmas', [])
        else:
            print(f"[buscar_estrutura_completa] Erro ao buscar turmas: {turmas_res.status_code}")
            return estrutura
            
        if not turmas:
            print("[buscar_estrutura_completa] Nenhuma turma encontrada")
            return estrutura
            
        # Busca todas as disciplinas uma vez (para otimizar)
        todas_disciplinas = []
        try:
            todas_disc_res = requests.get(f"{API_BASE_URL}/academico/disciplinas", headers=headers, timeout=5)
            if todas_disc_res.status_code == 200:
                todas_disciplinas = todas_disc_res.json().get('disciplinas', [])
        except Exception as e:
            print(f"[buscar_estrutura_completa] Erro ao buscar todas as disciplinas: {e}")
        
        # Busca todos os professores uma vez (para otimizar)
        professores_dict = {}
        try:
            prof_res = requests.get(f"{API_BASE_URL}/academico/professores", headers=headers, timeout=5)
            if prof_res.status_code == 200:
                professores = prof_res.json().get('professores', [])
                professores_dict = {p.get('id_usuario'): p for p in professores}
        except Exception as e:
            print(f"[buscar_estrutura_completa] Erro ao buscar professores: {e}")
            
        for turma in turmas:
                turma_id = turma['turma_id']
                professor_id_turma = turma.get('professor_id')
                professor_turma_info = professores_dict.get(professor_id_turma) if professor_id_turma else None
                
                estrutura[turma_id] = {
                    'info': turma,
                    'professor_turma': professor_turma_info,  # Professor responsável pela turma
                    'disciplinas': {},
                    'alunos_por_turma': []
                }
                
                # Busca disciplinas desta turma
                # Estratégia: para cada disciplina, tenta buscar alunos na turma
                # Se a chamada for bem-sucedida (mesmo sem alunos), a disciplina está associada à turma
                disciplinas_encontradas = {}
                
                # Para cada disciplina disponível, verifica se está na turma
                for disc in todas_disciplinas:
                    disciplina_id = disc.get('disciplina_id')
                    if not disciplina_id:
                        continue
                    
                    try:
                        # Tenta buscar alunos desta turma/disciplina
                        # Se retornar 200, a disciplina está na turma (mesmo sem alunos)
                        alunos_res = requests.get(
                            f"{API_BASE_URL}/academico/turmas/{turma_id}/disciplinas/{disciplina_id}/alunos",
                            headers=headers,
                            timeout=3  # Timeout curto
                        )
                        
                        # Se a chamada foi bem-sucedida, a disciplina está na turma
                        if alunos_res.status_code == 200:
                            alunos = alunos_res.json().get('alunos', [])
                            
                            # Por enquanto, usa o professor da turma como professor da disciplina
                            # (Futuramente pode buscar professor_id específico de turma_disciplinas)
                            professor_disc_info = professor_turma_info
                            
                            disciplinas_encontradas[disciplina_id] = {
                                'info': disc,
                                'alunos': alunos,
                                'professor': professor_disc_info
                            }
                    except requests.exceptions.Timeout:
                        # Timeout - disciplina provavelmente não está na turma
                        continue
                    except requests.exceptions.RequestException as e:
                        # 404 ou outro erro HTTP - disciplina não está na turma
                        continue
                    except Exception as e:
                        # Outro tipo de erro
                        print(f"[buscar_estrutura_completa] Erro ao buscar alunos para turma {turma_id}, disciplina {disciplina_id}: {e}")
                        continue
                
                # Armazena as disciplinas encontradas
                estrutura[turma_id]['disciplinas'] = disciplinas_encontradas
                
                # Busca todos os alunos da turma (agrupado de todas as disciplinas)
                try:
                    # Coleta alunos únicos de todas as disciplinas
                    alunos_turma = set()
                    for disc_id, disc_data in estrutura[turma_id]['disciplinas'].items():
                        for aluno in disc_data['alunos']:
                            alunos_turma.add((aluno.get('aluno_id'), aluno.get('nome', ''), aluno.get('sobrenome', '')))
                    estrutura[turma_id]['alunos_por_turma'] = list(alunos_turma)
                except:
                    pass
                    
    except Exception as e:
        print(f"[buscar_estrutura_completa] Erro: {e}")
    
    return estrutura

def construir_visao_geral_html(estrutura):
    """Constrói HTML hierárquico para visualização da estrutura completa."""
    
    visao_css = """
    <style>
        .visao-geral-section {
            background: #fff;
            padding: 30px;
            border-radius: 16px;
            margin-bottom: 40px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .visao-geral-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid #1b55f8;
        }
        .visao-geral-header h2 {
            margin: 0;
            color: #1b55f8;
            font-size: 1.8rem;
        }
        .turma-card-overview {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        .turma-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .turma-header h3 {
            margin: 0;
            font-size: 1.5rem;
            font-weight: 700;
        }
        .turma-stats {
            display: flex;
            gap: 20px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        .stat-badge {
            background: rgba(255, 255, 255, 0.2);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            backdrop-filter: blur(10px);
        }
        .professor-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.15);
            padding: 8px 12px;
            border-radius: 8px;
            margin-top: 10px;
            font-size: 0.9rem;
        }
        .professor-icon {
            width: 20px;
            height: 20px;
            background: #ff9800;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 0.75rem;
        }
        .professor-info {
            margin-top: 10px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            font-size: 0.9rem;
        }
        .disciplinas-container {
            margin-top: 20px;
        }
        .disciplina-card {
            background: white;
            color: #333;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            border-left: 4px solid #4CAF50;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .disciplina-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .disciplina-header h4 {
            margin: 0;
            color: #4CAF50;
            font-size: 1.2rem;
        }
        .alunos-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }
        .aluno-badge {
            background: #f0f0f0;
            padding: 10px 15px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
            transition: transform 0.2s;
        }
        .aluno-badge:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .aluno-icon {
            width: 24px;
            height: 24px;
            background: #4CAF50;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 0.8rem;
        }
        .alunos-turma-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 10px;
            margin-top: 15px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
        }
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #999;
            font-style: italic;
        }
        .toggle-disciplinas {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.3s;
        }
        .toggle-disciplinas:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        .collapsed {
            display: none;
        }
    </style>
    """
    
    html = f"""
    {visao_css}
    <div class="visao-geral-section">
        <div class="visao-geral-header">
            <h2> Visão Geral do Sistema</h2>
            <span style="color: #666; font-size: 0.9rem;">Total de Turmas: {len(estrutura)}</span>
        </div>
    """
    
    if not estrutura:
        html += """
        <div class="empty-state">
            <p>Nenhuma turma cadastrada no sistema.</p>
        </div>
        </div>
        """
        return html
    
    for turma_id, turma_data in estrutura.items():
        turma_info = turma_data['info']
        disciplinas = turma_data['disciplinas']
        alunos_turma = turma_data.get('alunos_por_turma', [])
        
        nome_turma = escape(turma_info.get('nome_turma', 'Sem nome'))
        ano = turma_info.get('ano', 'N/A')
        professor_turma = turma_data.get('professor_turma')
        total_disciplinas = len(disciplinas)
        total_alunos_turma = len(alunos_turma)
        
        # Conta professores únicos das disciplinas
        professores_disciplinas = set()
        for disc_data in disciplinas.values():
            prof_disc = disc_data.get('professor')
            if prof_disc and prof_disc.get('id_usuario'):
                professores_disciplinas.add((prof_disc.get('id_usuario'), prof_disc.get('email', 'N/A')))
        
        html += f"""
        <div class="turma-card-overview">
            <div class="turma-header">
                <div>
                    <h3>{nome_turma}</h3>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">Ano: {ano} • ID: {turma_id}</p>
                </div>
            </div>
            
            <div class="turma-stats">
                <div class="stat-badge">
                    <strong>{total_disciplinas}</strong> Disciplina{'s' if total_disciplinas != 1 else ''}
                </div>
                <div class="stat-badge">
                    <strong>{total_alunos_turma}</strong> Aluno{'s' if total_alunos_turma != 1 else ''} na Turma
                </div>
                <div class="stat-badge">
                    <strong>{len(professores_disciplinas) if professores_disciplinas else (1 if professor_turma else 0)}</strong> Professor{'es' if (len(professores_disciplinas) if professores_disciplinas else (1 if professor_turma else 0)) != 1 else ''}
                </div>
            </div>
            
            {"<!-- Professor Responsável pela Turma -->" if professor_turma else ""}
            {f'''
            <div class="professor-info">
                <strong> Professor Responsável:</strong><br>
                <div class="professor-badge">
                    <div class="professor-icon">P</div>
                    <span>{escape(professor_turma.get("email", "N/A"))} (ID: {professor_turma.get("id_usuario", "N/A")})</span>
                </div>
            </div>
            ''' if professor_turma else '<div class="professor-info"><em>Nenhum professor atribuído à turma</em></div>'}
            
            <button class="toggle-disciplinas" onclick="toggleDisciplinas('disc_{turma_id}', this)">
                {'▼ Ver Disciplinas e Alunos' if total_disciplinas > 0 else '─ Nenhuma disciplina'}
            </button>
            
            <div id="disc_{turma_id}" class="disciplinas-container" style="{'display: none;' if total_disciplinas > 0 else 'display: block;'}">
        """
        
        if total_disciplinas == 0:
            html += '<div class="empty-state"><p>Nenhuma disciplina associada a esta turma.</p></div>'
        else:
            for disc_id, disc_data in disciplinas.items():
                disc_info = disc_data['info']
                alunos_disc = disc_data['alunos']
                professor_disc = disc_data.get('professor')
                nome_disc = escape(disc_info.get('nome_disciplina', 'Sem nome'))
                total_alunos_disc = len(alunos_disc)
                
                html += f"""
                <div class="disciplina-card">
                    <div class="disciplina-header">
                        <h4> {nome_disc}</h4>
                        <span style="color: #666; font-size: 0.9rem;">ID: {disc_id} • {total_alunos_disc} Aluno{'s' if total_alunos_disc != 1 else ''}</span>
                    </div>
                    
                    {f'''
                    <div style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 6px;">
                        <strong> Professor:</strong> {escape(professor_disc.get("email", "N/A")) if professor_disc else "Não atribuído"}
                        {f' (ID: {professor_disc.get("id_usuario")})' if professor_disc and professor_disc.get("id_usuario") else ''}
                    </div>
                    ''' if professor_disc else '<div style="margin-bottom: 15px; padding: 10px; background: #fff3cd; border-radius: 6px; color: #856404;"><em>Nenhum professor atribuído a esta disciplina</em></div>'}
                    
                    <div class="alunos-list">
                """
                
                if total_alunos_disc == 0:
                    html += '<div class="empty-state"><p style="grid-column: 1/-1;">Nenhum aluno matriculado nesta disciplina.</p></div>'
                else:
                    for aluno in alunos_disc:
                        aluno_id = aluno.get('aluno_id', 'N/A')
                        nome = escape(aluno.get('nome', ''))
                        sobrenome = escape(aluno.get('sobrenome', ''))
                        nome_completo = f"{nome} {sobrenome}".strip() or f"Aluno ID: {aluno_id}"
                        iniciais = f"{nome[0] if nome else ''}{sobrenome[0] if sobrenome else ''}".upper() or "??"
                        
                        html += f"""
                        <div class="aluno-badge">
                            <div class="aluno-icon">{iniciais[:2]}</div>
                            <div>
                                <strong>{nome_completo}</strong>
                                <div style="font-size: 0.8rem; color: #666;">ID: {aluno_id}</div>
                            </div>
                        </div>
                        """
                
                html += """
                    </div>
                </div>
                """
        
        # Mostra lista de todos os alunos da turma (se houver)
        if total_alunos_turma > 0:
            html += """
            <div style="margin-top: 20px; padding-top: 20px; border-top: 2px solid rgba(255,255,255,0.3);">
                <h4 style="margin-bottom: 15px; color: white;"> Todos os Alunos da Turma</h4>
                <div class="alunos-turma-list">
            """
            for aluno_tuple in alunos_turma:
                aluno_id, nome, sobrenome = aluno_tuple
                nome_completo = f"{escape(nome)} {escape(sobrenome)}".strip() or f"Aluno ID: {aluno_id}"
                iniciais = f"{nome[0] if nome else ''}{sobrenome[0] if sobrenome else ''}".upper() or "??"
                html += f"""
                <div class="aluno-badge" style="background: rgba(255,255,255,0.15); color: white;">
                    <div class="aluno-icon" style="background: rgba(255,255,255,0.3);">{iniciais[:2]}</div>
                    <div>
                        <strong>{nome_completo}</strong>
                        <div style="font-size: 0.8rem; opacity: 0.8;">ID: {aluno_id}</div>
                    </div>
                </div>
                """
            html += """
                </div>
            </div>
            """
        
        html += """
            </div>
        </div>
        """
    
    html += """
        <script>
        function toggleDisciplinas(id, button) {
            const element = document.getElementById(id);
            if (element.style.display === 'none' || element.style.display === '') {
                element.style.display = 'block';
                button.textContent = '▲ Ocultar Disciplinas e Alunos';
            } else {
                element.style.display = 'none';
                button.textContent = '▼ Ver Disciplinas e Alunos';
            }
        }
        </script>
    </div>
    """
    
    return html

# --- AUXILIAR: BUSCAR RECURSOS PARA SELECTS ---
def fetch_admin_resources(token):
    """
    Busca todos os recursos necessários para o painel administrativo.
    
    Esta função realiza múltiplas requisições à API Node.js para obter
    todas as listas necessárias para o painel do administrador:
    - Turmas
    - Disciplinas
    - Professores
    - Alunos
    
    Args:
        token (str): Token JWT para autenticação na API
    
    Returns:
        dict: Dicionário com as seguintes chaves:
            - 'turmas': Lista de turmas
            - 'disciplinas': Lista de disciplinas
            - 'professores': Lista de professores
            - 'alunos': Lista de alunos
    
    Nota:
        Se alguma requisição falhar, a lista correspondente será vazia,
        mas a função não interrompe a execução.
    """
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
            
    # Busca Professores
        professores_res = requests.get(f"{API_BASE_URL}/academico/professores", headers=headers)
        if professores_res.status_code == 200:
            resources['professores'] = professores_res.json().get('professores', [])

            

    # Busca Alunos
        alunos_res = requests.get(f"{API_BASE_URL}/academico/alunos", headers=headers)
        if alunos_res.status_code == 200:
            resources['alunos'] = alunos_res.json().get('alunos', [])
        

    except requests.exceptions.RequestException as e:
        print(f"[FETCH RESOURCES ERROR]: {e}") 

    # LOG FINAL DA FUNÇÃO
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
    ia_url = url_for('chat_ia')
    quick_actions_html = f"""
    <div class="quick-actions">
        <h3>Ações Rápidas</h3>
        <div class="action-buttons">
            <a href="{boletim_url}" class="action-btn">
                Ver Boletim Completo
            </a>
            <a href="{ia_url}" class="action-btn" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                 Assistente de IA
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
    
    # 5. Adiciona botão de sair no topo
    btn_sair = f'''
    <div class="nav-buttons-container">
        <a href="{url_for('logout')}" class="btn-sair">
             Sair
        </a>
    </div>
    '''
    
    conteudo_completo = f'{btn_sair}{conteudo_aluno_html}'
    
    # 6. Renderiza usando a base
    return render_base(conteudo_completo, "Painel do Aluno")

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
@require_login
def boletim():
    """
    Rota para exibir o boletim completo do aluno.
    
    Esta rota busca e exibe todas as notas do aluno em formato de tabela,
    incluindo NP1, NP2, média final e faltas por disciplina.
    
    Processo:
    1. Verifica se o usuário é aluno
    2. Busca dados do boletim na API Node.js usando o token JWT
    3. Formata as notas e médias
    4. Renderiza tabela HTML com os dados
    
    Dados exibidos:
    - Nome da disciplina
    - Nota NP1
    - Nota NP2
    - Média final (calculada automaticamente)
    - Total de faltas
    
    Proteção:
    - Requer autenticação (@require_login)
    - Apenas alunos podem acessar
    
    Returns:
        HTML renderizado do boletim do aluno
    """
    
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
    
    # Botões de navegação
    botoes_nav = f'''
    <div class="nav-buttons-container">
        <a href="{url_for('painel_aluno')}" class="btn-voltar">
            ← Voltar para o Dashboard
        </a>
        <a href="{url_for('logout')}" class="btn-sair">
            🚪 Sair
        </a>
    </div>
    '''
    
    conteudo_completo = f'{botoes_nav}{tabela_html}'
    
    # Renderiza usando o layout
    return render_base(conteudo_completo, page_title="Meu Boletim")


# ----------------------------------------------------------------------
# FUNÇÃO AUXILIAR: FORMATAR MARKDOWN PARA HTML
# ----------------------------------------------------------------------

def formatar_markdown_para_html(texto):
    """
    Converte markdown para HTML usando a biblioteca markdown.
    Suporta todos os recursos padrão do markdown de forma segura.
    """
    if not texto:
        return ""
    
    try:
        # Converte markdown para HTML
        # Extensão 'extra' adiciona suporte para tabelas, fenced code blocks, etc.
        html = markdown.markdown(
            texto,
            extensions=['extra'],  # Suporta tabelas, fenced code, abbr, attr_list, etc.
            output_format='html5'
        )
        
        # A biblioteca markdown já escapa o conteúdo automaticamente para segurança
        # Retorna o HTML gerado
        return html
        
    except Exception as e:
        # Em caso de erro, retorna o texto escapado como fallback
        return f'<p>{escape(texto)}</p>'

# ============================================================================
# ROTA DE CHAT COM IA (GEMINI) PARA ALUNOS
# ============================================================================

@app.route('/aluno/ia', methods=['GET', 'POST'])
@require_login
def chat_ia():
    """
    Interface de chat interativa com Inteligência Artificial para alunos.
    
    Esta rota implementa um assistente acadêmico baseado em IA (Google Gemini)
    que fornece orientações personalizadas aos alunos baseadas em seu
    desempenho acadêmico.
    
    Funcionalidades:
    - Chat em tempo real com IA
    - Análise personalizada do boletim do aluno
    - Dicas de estudo e organização
    - Sugestões para melhoria de notas
    - Respostas formatadas em Markdown
    
    Métodos HTTP:
    - GET: Exibe a interface de chat vazia
    - POST: Processa mensagem do aluno e retorna resposta da IA
    
    Processo de geração de resposta:
    1. Recebe mensagem do aluno
    2. Busca dados do boletim do aluno na API
    3. Monta contexto acadêmico (notas, médias, faltas)
    4. Envia prompt contextualizado para Google Gemini
    5. Recebe resposta da IA
    6. Formata resposta Markdown para HTML
    7. Exibe no chat
    
    Proteção:
    - Requer autenticação (@require_login)
    - Apenas alunos podem acessar
    
    Dependências:
    - GEMINI_API_KEY configurada no .env
    - Biblioteca google-generativeai instalada
    
    Returns:
        HTML renderizado da interface de chat com IA
    """
    
    # Verifica se é aluno
    if session.get(SESSION_KEY_TYPE) != 'aluno':
        return render_base("<h1>Acesso Negado</h1><p>Apenas alunos podem acessar o assistente de IA.</p>", "Acesso Negado")
    
    # Verifica se a chave da API está configurada
    if not GEMINI_API_KEY:
        error_html = """
        <div style="max-width: 800px; margin: 50px auto; padding: 30px; background: #fff; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h1 style="color: #dc3545; margin-bottom: 20px;">⚠️ Chave de API não configurada</h1>
            <p style="color: #666; line-height: 1.6;">
                A chave da API do Gemini não foi configurada. Por favor, adicione a variável de ambiente 
                <code style="background: #f4f4f4; padding: 2px 6px; border-radius: 4px;">GEMINI_API_KEY</code> 
                no arquivo <code style="background: #f4f4f4; padding: 2px 6px; border-radius: 4px;">.env</code>.
            </p>
        </div>
        """
        return render_base(error_html, "Erro de Configuração")
    
    # Processa mensagens POST
    resposta_ia = None
    mensagem_usuario = None
    erro = None
    
    if request.method == 'POST':
        mensagem_usuario = request.form.get('mensagem', '').strip()
        
        if mensagem_usuario:
            try:
                # Busca dados do boletim para contexto
                token = session.get(SESSION_KEY_TOKEN)
                boletim_contexto = ""
                
                try:
                    response = requests.get(
                        f"{API_BASE_URL}/academico/boletim",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=5
                    )
                    if response.status_code == 200:
                        boletim_data = response.json().get('boletim', [])
                        if boletim_data:
                            boletim_contexto = "\n\nContexto acadêmico do aluno:\n"
                            for item in boletim_data:
                                disciplina = item.get('nome_disciplina', 'N/A')
                                nota_np1 = item.get('nota_np1', 'N/A')
                                nota_np2 = item.get('nota_np2', 'N/A')
                                media = item.get('media_final', 'N/A')
                                faltas = item.get('total_faltas', 0)
                                boletim_contexto += f"- {disciplina}: NP1={nota_np1}, NP2={nota_np2}, Média={media}, Faltas={faltas}\n"
                except:
                    pass  # Se não conseguir buscar boletim, continua sem contexto
                
                # Configura o modelo Gemini com fallback para compatibilidade
                # Tenta usar o modelo mais recente disponível primeiro
                # Se falhar, tenta modelos alternativos em ordem de preferência
                try:
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                except:
                    # Fallback 1: Tenta gemini-1.5-pro (mais poderoso)
                    try:
                        model = genai.GenerativeModel('gemini-1.5-pro')
                    except:
                        # Fallback 2: Usa gemini-1.5-flash (mais rápido e compatível)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Monta o prompt completo com contexto acadêmico do aluno
                # O contexto inclui notas, médias e faltas para personalizar a resposta
                prompt_completo = f"""Você é um assistente acadêmico inteligente e prestativo para alunos. 
Sua função é ajudar estudantes com dúvidas sobre estudos, organização, técnicas de aprendizado, e questões relacionadas ao desempenho acadêmico.

{boletim_contexto}

Responda de forma clara, amigável e educativa. Se o aluno perguntar sobre suas notas ou desempenho, use o contexto fornecido acima.

Pergunta do aluno: {mensagem_usuario}

Resposta:"""
                
                # Gera resposta da IA usando o modelo configurado
                # O modelo processa o prompt e retorna uma resposta contextualizada
                response_ia = model.generate_content(prompt_completo)
                resposta_ia = response_ia.text  # Extrai o texto da resposta
                
            except Exception as e:
                erro = f"Erro ao processar sua mensagem: {str(e)}"
    
    # CSS para a interface de chat
    chat_css = """
    <style>
        .chat-container {
            max-width: 900px;
            margin: 0 auto;
            background: #fff;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: calc(100vh - 200px);
            min-height: 600px;
        }
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px 30px;
            text-align: center;
        }
        .chat-header h1 {
            margin: 0 0 10px 0;
            font-size: 1.8rem;
        }
        .chat-header p {
            margin: 0;
            opacity: 0.9;
            font-size: 0.95rem;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 25px;
            background: #f8f9fa;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .message {
            max-width: 75%;
            padding: 15px 20px;
            border-radius: 18px;
            word-wrap: break-word;
            line-height: 1.5;
        }
        .message.user {
            align-self: flex-end;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom-right-radius: 4px;
        }
        .message.ia {
            align-self: flex-start;
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
            border-bottom-left-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .message.ia strong {
            color: #667eea;
            font-weight: 600;
        }
        .message.ia em {
            font-style: italic;
            color: #555;
        }
        .message.ia p {
            margin: 0 0 10px 0;
        }
        .message.ia p:last-child {
            margin-bottom: 0;
        }
        .message.ia ul {
            margin: 10px 0;
            padding-left: 25px;
            list-style-type: disc;
        }
        .message.ia li {
            margin: 5px 0;
            line-height: 1.6;
        }
        .message.ia br {
            line-height: 1.8;
        }
        .message.ia h3,
        .message.ia h4,
        .message.ia h5,
        .message.ia h6 {
            margin: 15px 0 10px 0;
            font-weight: 600;
            color: #333;
            line-height: 1.4;
        }
        .message.ia h3 {
            font-size: 1.3rem;
            border-bottom: 2px solid #667eea;
            padding-bottom: 5px;
        }
        .message.ia h4 {
            font-size: 1.15rem;
            color: #667eea;
        }
        .message.ia h5 {
            font-size: 1.05rem;
        }
        .message.ia h6 {
            font-size: 1rem;
        }
        .chat-input-container {
            padding: 20px 25px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }
        .chat-form {
            display: flex;
            gap: 10px;
        }
        .chat-input {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.3s;
        }
        .chat-input:focus {
            border-color: #667eea;
        }
        .chat-submit {
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .chat-submit:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        .chat-submit:active {
            transform: translateY(0);
        }
        .error-message {
            background: #f8d7da;
            color: #721c24;
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 4px solid #dc3545;
        }
        .empty-chat {
            text-align: center;
            color: #999;
            padding: 40px 20px;
        }
        .empty-chat-icon {
            font-size: 4rem;
            margin-bottom: 15px;
            opacity: 0.5;
        }
        .empty-chat p {
            margin: 0;
            font-size: 1.1rem;
        }
        .suggestions {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 15px;
        }
        .suggestion-btn {
            padding: 8px 16px;
            background: #f0f0f0;
            border: 1px solid #ddd;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s;
        }
        .suggestion-btn:hover {
            background: #e0e0e0;
            border-color: #667eea;
        }
    </style>
    """
    
    # HTML do chat
    mensagens_html = ""
    
    if mensagem_usuario:
        mensagens_html += f'<div class="message user">{escape(mensagem_usuario)}</div>'
    
    if erro:
        mensagens_html += f'<div class="error-message">{escape(erro)}</div>'
    elif resposta_ia:
        # Formata a resposta da IA convertendo markdown para HTML
        resposta_formatada = formatar_markdown_para_html(resposta_ia)
        mensagens_html += f'<div class="message ia">{Markup(resposta_formatada)}</div>'
    
    if not mensagens_html:
        mensagens_html = """
        <div class="empty-chat">
            <div class="empty-chat-icon"></div>
            <p>Olá! Sou seu assistente acadêmico. Como posso ajudá-lo hoje?</p>
            <div class="suggestions">
                <button class="suggestion-btn" onclick="document.querySelector('.chat-input').value='Como posso melhorar minhas notas?'; document.querySelector('.chat-form').submit();">Como melhorar minhas notas?</button>
                <button class="suggestion-btn" onclick="document.querySelector('.chat-input').value='Dicas de organização de estudos'; document.querySelector('.chat-form').submit();">Dicas de organização</button>
                <button class="suggestion-btn" onclick="document.querySelector('.chat-input').value='Como estudar para provas?'; document.querySelector('.chat-form').submit();">Como estudar para provas?</button>
            </div>
        </div>
        """
    
    # Botões de navegação
    botoes_nav = f'''
    <div class="nav-buttons-container">
        <a href="{url_for('painel_aluno')}" class="btn-voltar">
            ← Voltar para o Dashboard
        </a>
        <a href="{url_for('logout')}" class="btn-sair">
             Sair
        </a>
    </div>
    '''
    
    chat_html = f"""
    {botoes_nav}
    {chat_css}
    <div class="chat-container">
        <div class="chat-header">
            <h1> Assistente de IA Acadêmico</h1>
            <p>Seu assistente pessoal para dúvidas e orientações acadêmicas</p>
        </div>
        <div class="chat-messages" id="chatMessages">
            {mensagens_html}
        </div>
        <div class="chat-input-container">
            <form method="POST" class="chat-form" onsubmit="setTimeout(() => {{ document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight; }}, 100);">
                <input 
                    type="text" 
                    name="mensagem" 
                    class="chat-input" 
                    placeholder="Digite sua pergunta aqui..." 
                    required
                    autocomplete="off"
                    value=""
                >
                <button type="submit" class="chat-submit">Enviar</button>
            </form>
        </div>
    </div>
    <script>
        // Auto-scroll para a última mensagem
        window.addEventListener('load', function() {{
            const chatMessages = document.getElementById('chatMessages');
            if (chatMessages) {{
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }}
        }});
    </script>
    """
    
    return render_base(chat_html, "Assistente de IA")


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
    
    # Adiciona botão de sair no topo
    btn_sair = f'''
    <div class="nav-buttons-container">
        <a href="{url_for('logout')}" class="btn-sair">
             Sair
        </a>
    </div>
    '''
    
    conteudo_completo = f'{btn_sair}{conteudo_professor_html}'
    
    return render_base(conteudo_completo, "Painel do Professor")

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
    
    # Adiciona botão de sair no topo
    btn_sair = f'''
    <div class="nav-buttons-container">
        <a href="{url_for('logout')}" class="btn-sair">
             Sair
        </a>
    </div>
    '''
    
    conteudo_completo = f'{btn_sair}{tabela_alunos_html}'
    
    return render_base(conteudo_completo, f"Gerenciar Turma {turma_id}")

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
    tipo_avaliacao = request.form.get('tipo_avaliacao') #  Pega o tipo
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
                "tipo_avaliacao": tipo_avaliacao #  Envia o tipo para a API
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
        nota_exame = aluno.get('nota_exame')
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
        # Lógica: Se média >= 7: aprovado direto
        #         Se média >= 5 e existe exame: aprovado após exame
        #         Se média >= 5 e não existe exame: recuperação (precisa fazer exame)
        #         Se média < 5: reprovado
        def formatar_media_badge(media, tem_exame=False):
            if media is None:
                return '<span class="media-badge empty">N/D</span>'
            try:
                media_float = float(media)
                if media_float >= 7:
                    classe = 'aprovado'
                    texto = f'{media_float:.1f}'
                elif media_float >= 5:
                    if tem_exame:
                        # Aprovado após exame (média >= 5 com exame)
                        classe = 'aprovado'
                        texto = f'{media_float:.1f}'
                    else:
                        # Precisa fazer exame (média entre 5 e 7, sem exame ainda)
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
        # Verifica se existe nota de exame
        tem_exame = nota_exame is not None
        media_html = formatar_media_badge(media_final, tem_exame=tem_exame)
        
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
    
    lib_c.ordenar_por_desempenho(array_c, count) #  CHAMADA CRÍTICA AO C
    
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

# Adicione uma rota dummy para o FORM POST (lancar_nota_form) para que os links funcionem.

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