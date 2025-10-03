from flask import Flask
from flask import render_template_string

app = Flask(__name__)


def render_base(content_html, page_title="Sistema Acadêmico PIM"):
	base_html = f'''
	<!DOCTYPE html>
	<html lang="pt-br">
	<head>
		<meta charset="UTF-8">
		<title>{{page_title}}</title>
		<style>
			body {{
				margin: 0;
				font-family: Arial, sans-serif;
				background: #f4f6fa;
			}}
			.sidebar {{
				position: fixed;
				top: 0;
				left: 0;
				width: 220px;
				height: 100vh;
				background: #263159;
				color: #fff;
				display: flex;
				flex-direction: column;
				padding-top: 30px;
				box-shadow: 2px 0 8px rgba(0,0,0,0.07);
			}}
			.sidebar h2 {{
				text-align: center;
				margin-bottom: 40px;
				font-size: 1.3em;
				letter-spacing: 1px;
			}}
			.sidebar a {{
				color: #fff;
				text-decoration: none;
				padding: 15px 30px;
				font-size: 1.1em;
				transition: background 0.2s;
			}}
			.sidebar a:hover {{
				background: #435585;
			}}
			.main-content {{
				margin-left: 220px;
				padding: 40px;
			}}
			.main-content h1 {{
				color: #263159;
				font-size: 2.2em;
				margin-bottom: 20px;
			}}
			table.boletim {{
				border-collapse: collapse;
				width: 100%;
				background: #fff;
				box-shadow: 0 2px 8px rgba(0,0,0,0.04);
			}}
			table.boletim th, table.boletim td {{
				border: 1px solid #ddd;
				padding: 10px 16px;
				text-align: center;
			}}
			table.boletim th {{
				background: #263159;
				color: #fff;
			}}
		</style>
	</head>
	<body>
		<div class="sidebar">
			<h2>Menu</h2>
			<a href="/">Home</a>
			<a href="/boletim">Boletim</a>
			<a href="/aulas">Seleção de Aulas</a>
			<a href="/material">Material Didático</a>
			<a href="/mensagens">Mensagens</a>
			<a href="/horarios">Horários</a>
			<a href="/documentos">Documentos</a>
			<a href="/ai">AI</a>
			<a href="/configuracoes">Configurações</a>
		</div>
		<div class="main-content">
			{content_html}
		</div>
	</body>
	</html>
	'''
	return render_template_string(base_html, page_title=page_title)



# Página de AI
@app.route('/ai')
def ai():
	content = '''<h1>Assistente AI</h1><p>Em breve: área de Inteligência Artificial do sistema. Aqui você poderá interagir com funcionalidades inteligentes, como assistente virtual, análise de dados e recomendações personalizadas.</p>'''
	return render_base(content, page_title="Assistente AI")


# Função para renderizar a base HTML do sistema com sidebar e conteúdo principal
def render_base(content_html, page_title="Sistema Acadêmico PIM"):
	base_html = f'''
	<!DOCTYPE html>
	<html lang="pt-br">
	<head>
		<meta charset="UTF-8">
		<title>{{page_title}}</title>
		<style>
			body {{ margin: 0; font-family: Arial, sans-serif; background: #f4f6fa; }}
			.sidebar {{ position: fixed; top: 0; left: 0; width: 220px; height: 100vh; background: #263159; color: #fff; display: flex; flex-direction: column; padding-top: 30px; box-shadow: 2px 0 8px rgba(0,0,0,0.07); }}
			.sidebar h2 {{ text-align: center; margin-bottom: 40px; font-size: 1.3em; letter-spacing: 1px; }}
			.sidebar a {{ color: #fff; text-decoration: none; padding: 15px 30px; font-size: 1.1em; transition: background 0.2s; }}
			.sidebar a:hover {{ background: #435585; }}
			.main-content {{ margin-left: 220px; padding: 40px; }}
			.main-content h1 {{ color: #263159; font-size: 2.2em; margin-bottom: 20px; }}
			table.boletim {{ border-collapse: collapse; width: 100%; background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }}
			table.boletim th, table.boletim td {{ border: 1px solid #ddd; padding: 10px 16px; text-align: center; }}
			table.boletim th {{ background: #263159; color: #fff; }}
		</style>
	</head>
	<body>
		<div class="sidebar">
			<h2>Menu</h2>
			<a href="/">Home</a>
			<a href="/boletim">Boletim</a>
			<a href="/aulas">Seleção de Aulas</a>
			<a href="/material">Material Didático</a>
			<a href="/mensagens">Mensagens</a>
			<a href="/horarios">Horários</a>
			<a href="/documentos">Documentos</a>
			<a href="/configuracoes">Configurações</a>
		</div>
		<div class="main-content">
			{content_html}
		</div>
	</body>
	</html>
	'''
	return render_template_string(base_html, page_title=page_title)

# Página inicial
@app.route('/')
def index():
	content = '''<h1>Sistema Acadêmico PIM</h1><p>Bem-vindo! Use o menu lateral para navegar.</p>'''
	return render_base(content)

# Página do boletim com notas e faltas

# Página de seleção de aulas

# Página de material didático
@app.route('/material')
def material():
	content = '''<h1>Material Didático</h1><p>Acesse apostilas, livros digitais e vídeos das disciplinas.</p>'''
	return render_base(content, page_title="Material Didático")

# Página de mensagens
@app.route('/mensagens')
def mensagens():
	content = '''<h1>Mensagens</h1><p>Consulte comunicados, mensagens de professores e avisos importantes.</p>'''
	return render_base(content, page_title="Mensagens")

# Página de horários
@app.route('/horarios')
def horarios():
	content = '''<h1>Horários</h1><p>Visualize sua grade de horários e datas de provas.</p>'''
	return render_base(content, page_title="Horários")

# Página de documentos
@app.route('/documentos')
def documentos():
	content = '''<h1>Documentos</h1><p>Acesse atestados, declarações e históricos escolares.</p>'''
	return render_base(content, page_title="Documentos")

# Página de configurações
@app.route('/configuracoes')
def configuracoes():
	content = '''<h1>Configurações</h1><p>Altere informações do perfil, senha e preferências.</p>'''
	return render_base(content, page_title="Configurações")



@app.route('/boletim')
def boletim():
	tabela = '''
	<h1>Boletim</h1>
	<table class="boletim">
		<tr><th>Disciplina</th><th>Nota 1</th><th>Nota 2</th><th>Nota 3</th><th>Média</th><th>Faltas</th></tr>
		<tr><td>Matemática</td><td>8.0</td><td>7.5</td><td>9.0</td><td>8.2</td><td>2</td></tr>
		<tr><td>Português</td><td>7.0</td><td>8.0</td><td>7.5</td><td>7.5</td><td>0</td></tr>
		<tr><td>História</td><td>6.5</td><td>7.0</td><td>8.0</td><td>7.2</td><td>1</td></tr>
		<tr><td>Geografia</td><td>8.5</td><td>8.0</td><td>8.5</td><td>8.3</td><td>3</td></tr>
	</table>
	'''
	return render_base(tabela, page_title="Boletim")


@app.route('/aulas')
def aulas():
	content = '''
	<h1>Selecionar Aulas</h1>
	<p>Selecione as aulas que deseja se matricular:</p>
	<div style="display: flex; flex-wrap: wrap; gap: 16px; margin-top: 24px;">
		<button style="padding: 14px 32px; font-size: 1.1em; background: #435585; color: #fff; border: none; border-radius: 6px; cursor: pointer;">História</button>
		<button style="padding: 14px 32px; font-size: 1.1em; background: #435585; color: #fff; border: none; border-radius: 6px; cursor: pointer;">Matemática</button>
		<button style="padding: 14px 32px; font-size: 1.1em; background: #435585; color: #fff; border: none; border-radius: 6px; cursor: pointer;">Português</button>
		<button style="padding: 14px 32px; font-size: 1.1em; background: #435585; color: #fff; border: none; border-radius: 6px; cursor: pointer;">Geografia</button>
		<button style="padding: 14px 32px; font-size: 1.1em; background: #435585; color: #fff; border: none; border-radius: 6px; cursor: pointer;">Ciências</button>
		<button style="padding: 14px 32px; font-size: 1.1em; background: #435585; color: #fff; border: none; border-radius: 6px; cursor: pointer;">Inglês</button>
	</div>
	'''
	return render_base(content, page_title="Selecionar Aulas")








if __name__ == '__main__':
	app.run(debug=True)