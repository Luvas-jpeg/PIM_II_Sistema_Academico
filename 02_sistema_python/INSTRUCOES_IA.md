# Instruções para Configurar a IA do Gemini

## 📋 Pré-requisitos

1. **Chave de API do Gemini**: Você precisa de uma chave de API do Google Gemini
   - Acesse: https://aistudio.google.com/app/apikey
   - Faça login com sua conta Google
   - Clique em "Create API Key" para gerar uma nova chave
   - Copie a chave gerada

## 🔧 Configuração

### 1. Instalar Dependências

Primeiro, instale a biblioteca do Gemini:

```bash
cd 02_sistema_python
pip install -r requirements.txt
```

Ou instale diretamente:

```bash
pip install google-generativeai
```

### 2. Configurar a Chave de API

Crie um arquivo `.env` na pasta `02_sistema_python` (se ainda não existir) e adicione:

```env
GEMINI_API_KEY=sua_chave_api_aqui
```

**Importante**: Substitua `sua_chave_api_aqui` pela chave real que você obteve do Google AI Studio.

### 3. Estrutura do arquivo .env

Seu arquivo `.env` deve ter pelo menos estas variáveis:

```env
# API Node.js
API_URL=http://127.0.0.1:3000/api

# Flask Secret Key
FLASK_SECRET_KEY=sua_chave_secreta_aqui

# Gemini API Key
c=sua_chave_gemini_aqui
```

## 🚀 Como Usar

1. **Inicie o servidor Flask**:
   ```bash
   python main.py
   ```

2. **Acesse o sistema como aluno**:
   - Faça login com uma conta de aluno
   - No painel do aluno, clique no botão "🤖 Assistente de IA"
   - Ou acesse diretamente: `http://localhost:5000/aluno/ia`

3. **Use o chat**:
   - Digite suas perguntas no campo de texto
   - O assistente responderá com base no seu desempenho acadêmico
   - Você pode fazer perguntas sobre:
     - Como melhorar suas notas
     - Dicas de estudo
     - Organização acadêmica
     - Análise do seu desempenho

## ✨ Funcionalidades

- **Contexto Acadêmico**: A IA tem acesso ao seu boletim e pode dar conselhos personalizados
- **Interface Moderna**: Chat com design responsivo e intuitivo
- **Sugestões Rápidas**: Botões com perguntas frequentes para começar
- **Respostas Inteligentes**: Usa o modelo Gemini 1.5 Flash para respostas rápidas e precisas

## ⚠️ Troubleshooting

### Erro: "Chave de API não configurada"
- Verifique se o arquivo `.env` existe na pasta `02_sistema_python`
- Confirme que a variável `GEMINI_API_KEY` está definida corretamente
- Reinicie o servidor Flask após adicionar a chave

### Erro: "Erro ao processar sua mensagem"
- Verifique se sua chave de API é válida
- Confirme que você tem créditos/quota disponível no Google AI Studio
- Verifique sua conexão com a internet

### A IA não está respondendo
- Verifique os logs do servidor para mensagens de erro
- Confirme que a biblioteca `google-generativeai` está instalada corretamente
- Tente usar `gemini-1.5-pro` em vez de `gemini-1.5-flash` no código (linha 3135)

## 📝 Notas

- A chave de API é sensível e não deve ser compartilhada
- Não commite o arquivo `.env` no Git (adicione ao `.gitignore`)
- O modelo usado é `gemini-1.5-flash` que é rápido e eficiente para chat
- As respostas são geradas em tempo real e podem levar alguns segundos

