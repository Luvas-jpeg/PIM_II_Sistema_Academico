from flask import Flask, render_template_string, request, redirect, url_for
from markupsafe import escape

# Para usar uma imagem local como fundo, coloque o arquivo em 02_sistema_python/static/
# por exemplo: 02_sistema_python/static/tech-bg.jpg
# e altere a url do background no CSS para: url('/static/tech-bg.jpg')
# No PowerShell, crie a pasta static com:
#   New-Item -ItemType Directory -Path .\static

app = Flask(__name__)

def render_base(content_html, page_title="Pagina De Login"):
    base_html = f'''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{page_title}</title>
        <style>
            :root {{
                --bg: #f4f6fa;
                --card: #ffffff;
                --accent: #1b55f8; /* COR SOLICITADA */
                --accent-hover: #133fe0;
                --muted: #6b7280;
            }}
            * {{ box-sizing: border-box; }}
            body {{
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
                     /* imagem de fundo local (coloque a sua imagem em static/tech-bg.jpg)
                         Se quiser usar a imagem remota como fallback, descomente a segunda linha abaixo. */
                     background-image: linear-gradient(rgba(12,18,32,0.45), rgba(12,18,32,0.45)), url('/static/tech-bg.jpg');
                     /* fallback remote:
                     background-image: linear-gradient(rgba(12,18,32,0.45), rgba(12,18,32,0.45)), url('https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=1950&q=80');
                     */
                background-size: cover;
                background-position: center center;
                background-attachment: fixed;
                color: #111827;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 24px;
            }}
            .login-card {{
                width: 100%;
                max-width: 420px;
                background: var(--card);
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(16,24,40,0.08);
                padding: 28px;
                border: 1px solid rgba(16,24,40,0.04);
            }}
            .brand {{
                text-align: center;
                margin-bottom: 18px;
            }}
            .brand h2 {{ margin: 0; color: var(--accent); letter-spacing: 0.4px; }}
            label {{ display:block; font-size:0.9rem; color:var(--muted); margin-bottom:6px; }}
            input[type="text"], input[type="password"] {{
                width: 100%;
                padding: 10px 12px;
                border-radius: 8px;
                border: 1px solid #e6e9ef;
                background: #fbfdff;
                margin-bottom: 14px;
                font-size: 1rem;
            }}
            button[type="submit"] {{
                width: 100%;
                padding: 12px 14px;
                border-radius: 8px;
                border: none;
                background: var(--accent);
                color: #fff;
                font-weight: 600;
                cursor: pointer;
                font-size: 1rem;
                transition: background-color .15s ease;
            }}
            button[type="submit"]:hover {{
                background: var(--accent-hover);
            }}
            .help {{ text-align:center; margin-top:12px; color:var(--muted); font-size:0.9rem; }}
            @media (max-width:420px) {{
                .login-card {{ padding: 20px; border-radius:10px; }}
            }}
        </style>
    </head>
    <body>
        {content_html}
    </body>
    </html>
    '''
    return base_html


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        # Aqui você pode validar o login
        usuario_seguro = escape(usuario) if usuario is not None else ''
        mensagem = f"<div class=\"login-card\"><div class=\"brand\"><h2>Bem-vindo</h2></div><p>Olá, <strong>{usuario_seguro}</strong>! Login realizado.</p></div>"
        return render_base(mensagem, "Login Realizado")
    
    # Formulário de login
    form_html = '''
    <div class="login-card">
        <div class="brand"><h2>Sistema Acadêmico PIM</h2></div>
        <form method="POST">
            <label for="usuario">Usuário</label>
            <input id="usuario" type="text" name="usuario" placeholder="seu.usuario" required>

            <label for="senha">Senha</label>
            <input id="senha" type="password" name="senha" placeholder="••••••••" required>

            <button type="submit">Entrar</button>
        </form>
        <div class="help">Esqueceu a senha? Fale com o administrador.</div>
    </div>
    '''
    return render_base(form_html, "Página de Login")


# Redireciona a raiz para /login para evitar página "Not Found" ao acessar /
@app.route('/')
def index():
    return redirect(url_for('login'))


# 🔥 Adicione isso no final
if __name__ == '__main__':
    # Explicit host/port makes local testing predictable
    app.run(debug=True, host='127.0.0.1', port=5000)
