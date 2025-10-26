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
				:root {{ --accent: #1b55f8; --accent-hover: #133fe0; --sidebar-bg: var(--accent); --muted: #6b7280; }}
				body {{
					margin: 0;
					font-family: Arial, sans-serif;
					background: #f4f6fa;
				}}
				.sidebar {{
					position: fixed;
					top: 0;
					left: 0;
					width: 180px;
					height: 100vh;
					/* imagem de fundo local com overlay escuro para legibilidade */
					background-image: linear-gradient(rgba(7,18,48,0.45), rgba(7,18,48,0.45)), url('/static/tech-bg2.jpg');
					background-size: cover;
					background-position: center center;
					background-attachment: fixed;
					color: #fff;
					display: flex;
					flex-direction: column;
					padding-top: 30px;
					box-shadow: 2px 0 8px rgba(0,0,0,0.07);
				}}
				.sidebar h2 {{
					text-align: center;
					margin: 12px 0;
					font-size: 1rem;
					letter-spacing: 0.6px;
				}}
				.sidebar-search {{ padding: 8px 10px; }}
				.sidebar-search input {{
					width: 100%;
					height: 40px;
					padding: 8px 12px 8px 36px; /* espaço para o ícone, menor para mover à esquerda */
					border-radius: 999px; /* pill */
					border: none;
					background: rgba(255,255,255,0.06);
					color: #ffffff; /* texto branco */
					font-size: 0.95rem;
					outline: none;
					box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
					background-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23ffffff' d='M21 20l-5.6-5.6a7 7 0 10-1.4 1.4L20 21zM11 18a7 7 0 110-14 7 7 0 010 14z'/%3E%3C/svg%3E");
					background-repeat: no-repeat;
					background-position: 10px center; /* mover ícone mais para a esquerda */
					background-size: 18px 18px; /* tamanho proporcional do ícone */
				}}
				.sidebar-search input::placeholder {{ color: #ffffff; opacity: 0.85; }}
				.sidebar a {{
					color: #fff;
					text-decoration: none;
					padding: 10px 18px;
					font-size: 1.05em; /* fonte reduzida */
					transition: background 0.2s;
				}}
				.sidebar a:hover {{
					background: var(--accent-hover);
				}}
				.main-content {{
					margin-left: 220px;
					padding: 40px;
				}}
				.main-content h1 {{
					color: var(--sidebar-bg);
					font-size: 2.2em;
					margin-bottom: 8px;
				}}
				.main-content p {{
					margin-top: 6px; 
					color: #222; 
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
					background: var(--sidebar-bg);
					color: #fff;
				}}
		</style>
	</head>
		<body>
			<div class="sidebar">
				<div class="sidebar-search">
					<input id="sidebarSearch" type="text" placeholder="Pesquisar menu...">
				</div>
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
			<script>
			// Script simples para filtrar links na sidebar
			(function(){{
				const input = document.getElementById('sidebarSearch');
				if(!input) return;
				const links = Array.from(document.querySelectorAll('.sidebar a'));
				input.addEventListener('input', function(){{
					const q = this.value.trim().toLowerCase();
					links.forEach(a => {{
						const txt = a.textContent.trim().toLowerCase();
						a.style.display = txt.includes(q) ? 'block' : 'none';
					}});
				}});
				input.addEventListener('keydown', function(e){{
					if(e.key === 'Enter'){{
						e.preventDefault();
						const first = links.find(a => a.style.display !== 'none');
						if(first) window.location.href = first.href;
					}}
				}});
			}})();
			</script>
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
				:root {{ --accent: #1b55f8; --accent-hover: #133fe0; --sidebar-bg: var(--accent); --muted: #6b7280; }}
				body {{ margin: 0; font-family: Arial, sans-serif; background: #f4f6fa; }}
				.sidebar {{ position: fixed; top: 0; left: 0; width: 180px; height: 100vh; background-image: linear-gradient(rgba(7,18,48,0.45), rgba(7,18,48,0.45)), url('/static/tech-bg2.jpg'); background-size: cover; background-position: center center; background-attachment: fixed; color: #fff; display: flex; flex-direction: column; padding-top: 30px; box-shadow: 2px 0 8px rgba(0,0,0,0.07); }}
				.sidebar h2 {{ text-align: center; margin-bottom: 40px; font-size: 1.3em; letter-spacing: 1px; }}
				.sidebar-search {{ padding: 8px 10px; }}
				.sidebar-search input {{ width: 100%; height: 40px; padding: 8px 12px 8px 36px; border-radius: 999px; border: none; background: rgba(255,255,255,0.06); color: #ffffff; font-size: 0.95rem; outline: none; box-shadow: inset 0 1px 0 rgba(255,255,255,0.02); background-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23ffffff' d='M21 20l-5.6-5.6a7 7 0 10-1.4 1.4L20 21zM11 18a7 7 0 110-14 7 7 0 010 14z'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: 10px center; background-size: 18px 18px; }}
				.sidebar a {{ color: #fff; text-decoration: none; padding: 10px 18px; font-size: 1.05em; transition: background 0.2s; }}
				.sidebar a:hover {{ background: var(--accent-hover); }}
				.main-content {{ margin-left: 180px; padding: 40px; }}
				.main-content h1 {{ color: var(--sidebar-bg); font-size: 2.2em; margin-bottom: 8px; }}
				.main-content p {{ margin-top: 6px; color: #222; }}
				table.boletim {{ border-collapse: collapse; width: 100%; background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }}
				table.boletim th, table.boletim td {{ border: 1px solid #ddd; padding: 10px 16px; text-align: center; }}
				table.boletim th {{ background: var(--sidebar-bg); color: #fff; }}
			</style>
		</head>
		<body>
			<div class="sidebar">
				<div class="sidebar-search">
					<input id="sidebarSearch" type="text" placeholder="Pesquisar menu...">
				</div>
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
			<script>
			// Script simples para filtrar links na sidebar
			(function(){{
				const input = document.getElementById('sidebarSearch');
				if(!input) return;
				const links = Array.from(document.querySelectorAll('.sidebar a'));
				input.addEventListener('input', function(){{
					const q = this.value.trim().toLowerCase();
					links.forEach(a => {{
						const txt = a.textContent.trim().toLowerCase();
						a.style.display = txt.includes(q) ? 'block' : 'none';
					}});
				}});
				// quando apertar Enter, navega para o primeiro link visível
				input.addEventListener('keydown', function(e){{
					if(e.key === 'Enter'){{
						e.preventDefault();
						const first = links.find(a => a.style.display !== 'none');
						if(first) window.location.href = first.href;
					}}
				}});
			}})();
			</script>
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
				<button style="padding: 14px 32px; font-size: 1.1em; background: var(--accent); color: #fff; border: none; border-radius: 6px; cursor: pointer;">História</button>
				<button style="padding: 14px 32px; font-size: 1.1em; background: var(--accent); color: #fff; border: none; border-radius: 6px; cursor: pointer;">Matemática</button>
				<button style="padding: 14px 32px; font-size: 1.1em; background: var(--accent); color: #fff; border: none; border-radius: 6px; cursor: pointer;">Português</button>
				<button style="padding: 14px 32px; font-size: 1.1em; background: var(--accent); color: #fff; border: none; border-radius: 6px; cursor: pointer;">Geografia</button>
				<button style="padding: 14px 32px; font-size: 1.1em; background: var(--accent); color: #fff; border: none; border-radius: 6px; cursor: pointer;">Ciências</button>
				<button style="padding: 14px 32px; font-size: 1.1em; background: var(--accent); color: #fff; border: none; border-radius: 6px; cursor: pointer;">Inglês</button>
	</div>
	'''
	return render_base(content, page_title="Selecionar Aulas")








if __name__ == '__main__':
	app.run(debug=True)