const db = require('../models/db');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');

// Funcção de registro para criar novos usuários
exports.register = async (req, res) =>{
    const {email, senha, tipo_usuario} = 
    req.body;

    if(!email || !senha) {
        return res.status(400).json({message: 'Email e senha inválidos'})
    }
    try {
        const senhaCripto = await bcrypt.hash(senha,10);

        // consulta SQL para inserir usuario, incluindo o tipo_usuario
        const resultado = await db.query(
            'INSERT INTO usuario(email,senha,tipo_usuario) VALUES (1$, 2$, 3$) RETURNING *',
            [email, senhaCripto, tipo_usuario || 'comum']
        );

        const novoUsuario = resultado.rows[0];
        res.status(201).json({
            message: "Usuario registrado!",
            usuario: {
                id_usuario: novoUsuario.id_usuario,
                email: novoUsuario.email,
                tipo_usuario: novoUsuario.tipo_usuario
            }
        });
    } catch (error){
        console.log('Erro ao registrar usuario:', error);
        res.status(500).json({message: 'Erro no servidor', error: error.message});

    }
};

// Funcção de login para autenticar e retornar o tipo de usuário
exports.login = async(req, res) => {
    const {email, senha} = req.body;

    if(!email || !senha) {
        return res.status(400).json({message: "Email e senha obrigatórios."});
    }
    try{
        const resultado = await db.query('SELECT * FROM usuario WHERE   EMAIL = $1', [email]);
        const user = resultado.row[0];

        if(!usuario) {
            return res.status(401).json({message:'Credenciais inválidas.'});
        }

        const token = jwt.sign(
            {id: user.id_usuario, tipo_usuario: user.tipo_usuario},
            process.env.JWT_SECRET,
            {expiresIn: "1h"}
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
    } catch(error){
        console.log('Erro no login:', error);
        res.status(500).json({message: 'Erro no servidor', error: error.message});
    }
}