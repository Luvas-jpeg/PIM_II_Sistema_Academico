const db = require('../models/db');
const bcrypt = require('bcryptjs'); // Correção: 'bcryptjs' é a biblioteca correta
const jwt = require('jsonwebtoken');

// Função de registro para criar novos usuários
exports.register = async (req, res) => {
    // Agora esperamos todos os dados do formulário
    const { email, senha, nome, sobrenome, data_nascimento, tipo_usuario } = req.body;

    // Validações básicas
    if (!email || !senha || !nome) {
        return res.status(400).json({ message: 'E-mail, Senha e Nome são obrigatórios.' });
    }

    // Garante que o tipo seja 'aluno' se for registro completo
    const final_tipo_usuario = tipo_usuario === 'aluno' ? 'aluno' : 'comum'; 

    // --- INÍCIO DA TRANSAÇÃO ---
    const client = await db.getClient(); // Obtém um cliente do pool para transação

    try {
        await client.query('BEGIN'); // Começa a transação

        // 1. Criptografa a senha
        const senhaCripto = await bcrypt.hash(senha, 10);

        // 2. Insere na tabela 'usuarios'
        const userSql = 'INSERT INTO usuarios (email, senha, tipo_usuario) VALUES ($1, $2, $3) RETURNING id_usuario';
        const userParams = [email, senhaCripto, final_tipo_usuario];
        const userResult = await client.query(userSql, userParams);
        
        const novoUsuarioId = userResult.rows[0].id_usuario;

        // 3. Se for um aluno, insere na tabela 'alunos'
        let novoAluno = null;
        if (final_tipo_usuario === 'aluno') {
            const alunoSql = `
                INSERT INTO alunos (nome, sobrenome, email, data_nascimento, usuario_id)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *;
            `;
            const alunoParams = [nome, sobrenome, email, data_nascimento || null, novoUsuarioId];
            const alunoResult = await client.query(alunoSql, alunoParams);
            novoAluno = alunoResult.rows[0];
        }

        await client.query('COMMIT'); // Confirma a transação se tudo deu certo

        // Retorna a resposta de sucesso
        res.status(201).json({
            message: "Usuário registrado com sucesso!",
            usuario: {
                id_usuario: novoUsuarioId,
                email: email,
                tipo_usuario: final_tipo_usuario
            },
            // Inclui o perfil do aluno se foi criado
            aluno: novoAluno 
        });

    } catch (error) {
        await client.query('ROLLBACK'); // Desfaz a transação em caso de erro
        
        console.error('Erro ao registrar usuário (transação):', error);
        // Trata erros comuns (ex: e-mail duplicado)
        if (error.code === '23505') { // UNIQUE constraint violation
             return res.status(409).json({ message: 'Este e-mail já está registrado.' });
        }
        res.status(500).json({ message: 'Erro no servidor durante o registro.', error: error.message });
        
    } finally {
        client.release(); // Libera o cliente de volta para o pool
    }
};

// Função de login para autenticar e retornar o tipo de usuário
exports.login = async (req, res) => {
    const { email, senha } = req.body;

    if (!email || !senha) {
        return res.status(400).json({ message: "Email e senha obrigatórios." });
    }
    try {
        // Correção do espaço em branco na consulta
        const resultado = await db.query('SELECT * FROM usuarios WHERE email = $1', [email]);
        // Correção: 'rows' no lugar de 'row'
        const user = resultado.rows[0];

        if (!user) {
            return res.status(401).json({ message: 'Credenciais inválidas.' });
        }

        // Adiciona a verificação da senha com bcrypt
        const isMatch = await bcrypt.compare(senha, user.senha);
        if (!isMatch) {
            return res.status(401).json({ message: 'Credenciais inválidas.' });
        }

        const token = jwt.sign(
            { id: user.id_usuario, tipo_usuario: user.tipo_usuario },
            process.env.JWT_SECRET,
            { expiresIn: "1h" }
        );
        res.status(200).json({
            message: 'Login realizado!',
            token,
            usuario: {
                id_usuario: user.id_usuario,
                email: user.email,
                tipo_usuario: user.tipo_usuario // Retorna o tipo de usuario
            }
        });
    } catch (error) {
        console.log('Erro no login:', error);
        res.status(500).json({ message: 'Erro no servidor', error: error.message });
    }
};

// Correção: Garante que o objeto está sendo exportado
module.exports = {
    register: exports.register,
    login: exports.login,
};