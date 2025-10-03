from flask import Flask, render_template_string, request

app = Flask(__name__)

def render_base(content_html, page_title="Pagina De Login"):
    base_html = f'''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>{page_title}</title>
        <style>
            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f4f6fa;
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
        mensagem = f"<p>Bem-vindo, <strong>{usuario}</strong>!</p>"
        return render_base(mensagem, "Login Realizado")
    
    # Formulário de login
    form_html = '''
    <div style="max-width:400px;margin:50px auto;padding:20px;background:#fff;border-radius:8px;box-shadow:0 0 10px rgba(0,0,0,0.1);">
        <h2>Login</h2>
        <form method="POST">
            <label>Usuário:</label><br>
            <input type="text" name="usuario" required><br><br>
            <label>Senha:</label><br>
            <input type="password" name="senha" required><br><br>
            <button type="submit">Entrar</button>
        </form>
    </div>
    '''
    return render_base(form_html, "Página de Login")


# 🔥 Adicione isso no final
if __name__ == '__main__':
    app.run(debug=True)
