const db = require('../models/db');
const bcrypt = require('bcryptjs'); // Correção: 'bcryptjs' é a biblioteca correta
const jwt = require('jsonwebtoken');

// Função de registro para criar novos usuários
exports.register = async (req, res) => {
    const { email, senha, tipo_usuario } = req.body;

    if (!email || !senha) {
        return res.status(400).json({ message: 'Email e senha inválidos' });
    }
    try {
        const senhaCripto = await bcrypt.hash(senha, 10);

        // Correção da sintaxe SQL e do nome da tabela
        const sql = 'INSERT INTO usuarios (email, senha, tipo_usuario) VALUES ($1, $2, $3) RETURNING *';
        const params = [email, senhaCripto, tipo_usuario || 'comum'];

        const resultado = await db.query(sql, params);

        const novoUsuario = resultado.rows[0];
        res.status(201).json({
            message: "Usuário registrado!",
            usuario: {
                id_usuario: novoUsuario.id_usuario,
                email: novoUsuario.email,
                tipo_usuario: novoUsuario.tipo_usuario
            }
        });
    } catch (error) {
        console.log('Erro ao registrar usuario:', error);
        res.status(500).json({ message: 'Erro no servidor', error: error.message });

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