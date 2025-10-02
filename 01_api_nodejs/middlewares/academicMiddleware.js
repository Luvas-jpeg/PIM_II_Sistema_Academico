// middlewares/academicMiddleware.js

const jwt = require('jsonwebtoken');

// Middleware para verificar se o usuário está autenticado
exports.isAuthenticated = (req, res, next) => {
    // 1. Obter o token do cabeçalho da requisição
    const authHeader = req.headers.authorization;

    if (!authHeader) {
        return res.status(401).json({ message: 'Acesso negado. Token não fornecido.' });
    }

    const token = authHeader.split(' ')[1]; // Formato: "Bearer TOKEN"
    if (!token) {
        return res.status(401).json({ message: 'Acesso negado. Formato de token inválido.' });
    }

    // 2. Verificar a validade do token
    try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        
        // 3. Adicionar as informações do usuário à requisição
        req.user = decoded; 
        next(); // Continua para a próxima função (o controlador)
    } catch (error) {
        return res.status(401).json({ message: 'Token inválido.' });
    }
};

// Middleware para verificar se o usuário é um professor ou administrador
exports.isProfessorOrAdmin = (req, res, next) => {
    // Requer o middleware 'isAuthenticated' antes deste
    if (!req.user || (req.user.tipo_usuario !== 'professor' && req.user.tipo_usuario !== 'admin')) {
        return res.status(403).json({ message: 'Acesso negado. Apenas professores ou administradores podem acessar.' });
    }
    next(); // Continua para a próxima função
};