# Sistema Acadêmico PIM - Projeto Integrador Multidisciplinar

## Sumário

1. [Introdução](#introdução)
2. [Objetivos](#objetivos)
3. [Arquitetura do Sistema](#arquitetura-do-sistema)
4. [Tecnologias Utilizadas](#tecnologias-utilizadas)
5. [Estrutura do Projeto](#estrutura-do-projeto)
6. [Funcionalidades](#funcionalidades)
7. [Instalação e Configuração](#instalação-e-configuração)
8. [Como Utilizar](#como-utilizar)
9. [Documentação Técnica](#documentação-técnica)
10. [Contribuições](#contribuições)
11. [Referências](#referências)

---

##  Introdução

O **Sistema Acadêmico PIM** é uma aplicação web completa desenvolvida como Projeto Integrador Multidisciplinar (PIM), que visa modernizar e automatizar o gerenciamento acadêmico de instituições de ensino. O sistema oferece uma plataforma integrada para gestão de alunos, professores, turmas, disciplinas, notas e relatórios acadêmicos.

O projeto implementa uma arquitetura moderna baseada em microserviços, utilizando tecnologias de ponta como **Node.js** para a API backend, **Python Flask** para a interface web, **PostgreSQL** para persistência de dados, e integração com **Inteligência Artificial** (Google Gemini) para fornecer assistência acadêmica personalizada aos alunos.

### Características Principais

-  **Multi-usuário**: Suporte para três perfis distintos (Aluno, Professor, Administrador)
-  **Interface Moderna**: Design responsivo e intuitivo
-  **Assistente de IA**: Integração com Google Gemini para orientação acadêmica
-  **Algoritmos Otimizados**: Biblioteca C para processamento eficiente de dados
-  **API RESTful**: Arquitetura escalável e desacoplada
-  **Segurança**: Autenticação JWT e proteção contra vulnerabilidades web

---

##  Objetivos

### Objetivo Geral

Desenvolver um sistema acadêmico completo e moderno que automatize processos de gestão educacional, proporcionando uma experiência eficiente e intuitiva para alunos, professores e administradores.

### Objetivos Específicos

1. **Gestão Acadêmica**
   - Implementar controle completo de turmas, disciplinas e matrículas
   - Gerenciar lançamento de notas e frequência de alunos
   - Gerar relatórios acadêmicos e rankings de desempenho

2. **Experiência do Usuário**
   - Desenvolver interfaces intuitivas e responsivas
   - Implementar dashboards personalizados por perfil de usuário
   - Oferecer feedback visual sobre desempenho acadêmico

3. **Inovação Tecnológica**
   - Integrar Inteligência Artificial para assistência acadêmica
   - Otimizar algoritmos de processamento com linguagem C
   - Implementar arquitetura de microserviços escalável

4. **Segurança e Confiabilidade**
   - Garantir autenticação segura com tokens JWT
   - Implementar proteções contra vulnerabilidades web (XSS, CSRF)
   - Validar e sanitizar todas as entradas do usuário

---

##  Arquitetura do Sistema

O sistema adota uma arquitetura em camadas com separação clara de responsabilidades:

```
┌─────────────────────────────────────────────────────────┐
│                    CAMADA DE APRESENTAÇÃO               │
│              (Python Flask - Frontend Web)              │
│  - Interface do Usuário                                 │
│  - Renderização de Templates                            |
│  - Gerenciamento de Sessões                             |
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP/REST
┌──────────────────▼──────────────────────────────────────┐
│                    CAMADA DE APLICAÇÃO                  │
│              (Node.js - API Backend)                    |
│  - Lógica de Negócio                                    │
│  - Autenticação e Autorização                           |
│  - Validação de Dados                                   |
└──────────────────┬──────────────────────────────────────┘
                   │ SQL
┌──────────────────▼──────────────────────────────────────┐
│                    CAMADA DE DADOS                      |
│              (PostgreSQL - Banco de Dados)              │
│  - Persistência de Dados                                │
│  - Relacionamentos e Integridade                        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              SERVIÇOS EXTERNOS                          │
│  - Google Gemini API (IA)                               │
│  - Biblioteca C (Algoritmos Otimizados)                 │
└─────────────────────────────────────────────────────────┘
```

### Componentes Principais

1. **Frontend (Flask)**
   - Renderização server-side de templates HTML
   - Gerenciamento de sessões e autenticação
   - Integração com API backend via HTTP

2. **Backend (Node.js)**
   - API RESTful completa
   - Autenticação JWT
   - Validação e processamento de dados

3. **Banco de Dados (PostgreSQL)**
   - Armazenamento relacional de dados
   - Integridade referencial
   - Transações ACID

4. **Serviços Auxiliares**
   - Biblioteca C para algoritmos de ordenação
   - Integração com Google Gemini para IA

---

##  Tecnologias Utilizadas

### Backend

- **Node.js** (v18+): Runtime JavaScript para servidor
- **Express.js**: Framework web para Node.js
- **PostgreSQL**: Sistema de gerenciamento de banco de dados relacional
- **JWT (JSON Web Tokens)**: Autenticação stateless
- **bcrypt**: Hash de senhas

### Frontend

- **Python 3.11+**: Linguagem de programação
- **Flask 3.1.2**: Framework web minimalista
- **Jinja2**: Motor de templates
- **MarkupSafe**: Proteção contra XSS
- **Requests**: Cliente HTTP para comunicação com API

### Inteligência Artificial

- **Google Generative AI (Gemini)**: Modelo de linguagem para assistência acadêmica
- **Markdown**: Processamento de texto formatado

### Algoritmos

- **C (GCC)**: Linguagem para algoritmos de baixo nível
- **ctypes**: Interface Python para bibliotecas C

### Ferramentas de Desenvolvimento

- **Git**: Controle de versão
- **dotenv**: Gerenciamento de variáveis de ambiente
- **pip**: Gerenciador de pacotes Python
- **npm**: Gerenciador de pacotes Node.js

---

##  Estrutura do Projeto

```
PIM_II_Sistema_Academico/
│
├── 01_api_nodejs/              # API Backend (Node.js/Express)
│   ├── config/                  # Configurações do banco de dados
│   ├── controllers/             # Lógica de negócio
│   │   ├── academicController.js
│   │   └── authController.js
│   ├── middlewares/             # Middlewares de autenticação
│   ├── models/                  # Modelos de dados
│   ├── routes/                  # Definição de rotas
│   └── server.js                # Servidor principal
│
├── 02_sistema_python/           # Frontend Web (Flask)
│   ├── main.py                  # Aplicação Flask principal
│   ├── static/                  # Arquivos estáticos (CSS, imagens)
│   ├── venv/                    # Ambiente virtual Python
│   └── requirements.txt         # Dependências Python
│
├── 03_algorithms_c/             # Biblioteca C para algoritmos
│   ├── algorithms.c             # Código fonte C
│   ├── algorithms.dll/.so       # Biblioteca compilada
│   └── README_C.md              # Documentação da biblioteca
│
├── 04_documentacao/             # Documentação completa
│   ├── diagramas_uml/           # Diagramas de arquitetura
│   ├── manuais/                 # Manuais técnico e de usuário
│   └── evidencias_ia/           # Documentação da IA
│
├── 05_testes/                   # Testes automatizados
│   └── test_*.py                # Scripts de teste
│
├── 06_apresentacao/             # Materiais de apresentação
│   ├── apresentacao_pim.pptx
│   └── screenshots/            # Capturas de tela
│
└── README.md                     # Este arquivo
```

---

##  Funcionalidades

###  Módulo do Aluno

- **Dashboard Personalizado**
  - Visualização de média geral
  - Contagem de disciplinas matriculadas
  - Total de faltas registradas
  - Cards visuais com estatísticas

- **Boletim Acadêmico**
  - Consulta de notas (NP1, NP2, Exame)
  - Visualização de médias finais
  - Registro de faltas por disciplina
  - Formatação visual com badges de status

- **Assistente de IA**
  - Chat interativo com Google Gemini
  - Análise personalizada do desempenho acadêmico
  - Dicas de estudo e organização
  - Sugestões para melhoria de notas
  - Respostas formatadas em Markdown

###  Módulo do Professor

- **Painel de Controle**
  - Listagem de turmas atribuídas
  - Acesso rápido a disciplinas lecionadas
  - Mensagens de feedback de operações

- **Gestão de Notas**
  - Lançamento de notas (NP1, NP2, Exame)
  - Registro de presença/falta
  - Visualização de alunos por turma/disciplina
  - Cálculo automático de médias

- **Relatórios**
  - Geração de relatórios de desempenho
  - Rankings de alunos por média
  - Análise de frequência

###  Módulo do Administrador

- **Gestão Completa**
  - CRUD de turmas
  - CRUD de disciplinas
  - CRUD de professores
  - CRUD de alunos
  - Gerenciamento de matrículas

- **Relatórios Avançados**
  - Relatórios de desempenho por turma/disciplina
  - Rankings ordenados (usando biblioteca C)
  - Estatísticas gerais do sistema

---

##  Instalação e Configuração

### Pré-requisitos

- **Node.js** 18+ e npm
- **Python** 3.11+
- **PostgreSQL** 14+
- **Git** (opcional, para clonar o repositório)

### Passo 1: Configurar o Banco de Dados

1. Crie um banco de dados PostgreSQL:
```sql
CREATE DATABASE sistema_academico;
```

2. Execute os scripts SQL necessários (consulte a documentação em `04_documentacao/`)

### Passo 2: Configurar a API Node.js

1. Navegue até a pasta da API:
```bash
cd 01_api_nodejs
```

2. Instale as dependências:
```bash
npm install
```

3. Inicie o servidor:
```bash
npm start
```

A API estará disponível em `http://localhost:3000`

### Passo 3: Configurar o Frontend Flask

1. Navegue até a pasta do sistema Python:
```bash
cd 02_sistema_python
```

2. Crie um ambiente virtual (recomendado):
```bash
python -m venv venv
```

3. Ative o ambiente virtual:
   - **Windows**: `venv\Scripts\activate`
   - **Linux/Mac**: `source venv/bin/activate`

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

5. Configure as variáveis de ambiente (crie um arquivo `.env`):
```env
API_URL=http://127.0.0.1:3000/api
FLASK_SECRET_KEY=sua_chave_secreta_flask
GEMINI_API_KEY=sua_chave_api_gemini
```

6. Inicie o servidor Flask:
```bash
python main.py
```

O sistema estará disponível em `http://localhost:5000`

### Passo 4: Configurar a Biblioteca C (Opcional)

1. Navegue até a pasta de algoritmos:
```bash
cd 03_algorithms_c
```

2. Compile a biblioteca:
   - **Windows**: Execute `compile.bat`
   - **Linux/Mac**: Execute `./compile.sh`

A biblioteca será gerada automaticamente e carregada pelo Flask.

### Passo 5: Configurar a IA (Opcional)

1. Obtenha uma chave de API do Google Gemini:
   - Acesse: https://aistudio.google.com/app/apikey
   - Crie uma nova chave de API

2. Adicione a chave no arquivo `.env` do Flask:
```env
GEMINI_API_KEY=sua_chave_aqui
```

---

##  Como Utilizar

### Primeiro Acesso

1. Acesse `http://localhost:5000`
2. Clique em "Registrar" para criar uma conta de aluno
3. Faça login com suas credenciais

### Para Alunos

1. **Visualizar Dashboard**: Após login, você será redirecionado automaticamente
2. **Consultar Boletim**: Clique em " Boletim" no dashboard
3. **Usar Assistente de IA**: Clique em " Assistente de IA" e faça perguntas sobre seu desempenho

### Para Professores

1. Faça login com credenciais de professor
2. Acesse o painel do professor
3. Selecione uma turma/disciplina para gerenciar
4. Lance notas e registre presenças

### Para Administradores

1. Faça login com credenciais de administrador
2. Acesse o painel administrativo
3. Gerencie turmas, disciplinas, professores e alunos
4. Gere relatórios de desempenho

---

##  Documentação Técnica

### API Endpoints

A documentação completa da API está disponível em `04_documentacao/manuais/manual_tecnico.pdf`.

#### Principais Endpoints:

**Autenticação:**
- `POST /api/auth/register` - Registrar novo usuário
- `POST /api/auth/login` - Fazer login
- `GET /api/auth/me` - Obter dados do usuário logado

**Acadêmico:**
- `GET /api/academico/boletim` - Obter boletim do aluno
- `GET /api/academico/turmas` - Listar turmas
- `GET /api/academico/disciplinas` - Listar disciplinas
- `POST /api/academico/notas` - Lançar nota
- `POST /api/academico/presenca` - Registrar presença

### Estrutura do Banco de Dados

O banco de dados possui as seguintes tabelas principais:

- `usuarios`: Armazena dados de autenticação
- `alunos`: Perfis acadêmicos de alunos
- `professores`: Perfis de professores
- `turmas`: Turmas do sistema
- `disciplinas`: Disciplinas oferecidas
- `matriculas`: Relacionamento aluno-turma-disciplina
- `notas`: Registro de notas dos alunos
- `presencas`: Registro de frequência

### Segurança

- **Autenticação JWT**: Tokens seguros para autenticação
- **Hash de Senhas**: Senhas armazenadas com bcrypt
- **Proteção XSS**: Escape automático de conteúdo HTML
- **Validação de Entrada**: Todas as entradas são validadas
- **CORS**: Configurado para permitir apenas origens confiáveis

---

##  Contribuições

Este é um projeto acadêmico desenvolvido como PIM. Para contribuições:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request

---

##  Referências

### Documentação Oficial

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Express.js Documentation](https://expressjs.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Google Gemini API](https://ai.google.dev/docs)

### Artigos e Tutoriais

- RESTful API Design Best Practices
- JWT Authentication Best Practices
- Flask Security Best Practices
- PostgreSQL Performance Optimization

### Bibliotecas e Frameworks

- Flask: https://flask.palletsprojects.com/
- Express.js: https://expressjs.com/
- Markdown: https://python-markdown.github.io/
- Google Generative AI: https://ai.google.dev/

---

##  Licença

Este projeto foi desenvolvido para fins acadêmicos como parte do Projeto Integrador Multidisciplinar (PIM).

---

##  Autores

- **Desenvolvedores**: 
- Lucas Vinícios Martins Alves - R6602G9
- Letícia Mocci Dezanete R.A H765GB8
- Arthur Lucio Parmezan - H70FDH6
- Luis Otávio Freitas Faria - R8651C0
- Luan Alves Magalhães - H659IA0
- **Instituição**: UNIP - Universidade Paulista
- **Ano**: 2025