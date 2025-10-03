// middlewares/academicMiddleware.js

const jwt = require('jsonwebtoken');

// 1. Middleware para verificar se o usuário está autenticado
exports.isAuthenticated = (req, res, next) => {
    // Obtém o token do cabeçalho de autorização (formato: "Bearer TOKEN")
    const authHeader = req.headers.authorization;

    if (!authHeader) {
        return res.status(401).json({ message: 'Acesso negado. Token não fornecido.' });
    }

    const token = authHeader.split(' ')[1]; 
    if (!token) {
        return res.status(401).json({ message: 'Acesso negado. Formato de token inválido.' });
    }

    // 2. Verifica a validade do token
    try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        
        // Adiciona as informações do usuário (ID e tipo) à requisição
        req.user = decoded; 
        next(); // Permite que a requisição siga para a próxima função
    } catch (error) {
        return res.status(401).json({ message: 'Token inválido ou expirado.' });
    }
};

// 2. Middleware para verificar se o usuário é um Professor ou Administrador
exports.isProfessorOrAdmin = (req, res, next) => {
    // Verifica o tipo_usuario que foi decodificado e adicionado por isAuthenticated
    if (!req.user || (req.user.tipo_usuario !== 'professor' && req.user.tipo_usuario !== 'admin')) {
        return res.status(403).json({ message: 'Acesso negado. Apenas professores ou administradores podem realizar esta ação.' });
    }
    next();
};