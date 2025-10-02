// routes/academicRoutes.js

const express = require('express');
const router = express.Router();
const academicController = require('../controllers/academicController');

// Importa o middleware de autenticação
const academicMiddleware = require('../middlewares/academicMiddleware');

// Rota para criar uma nova turma (requer autenticação e permissão de professor/admin)
router.post('/turmas', academicMiddleware.isAuthenticated, academicMiddleware.isProfessorOrAdmin, academicController.createTurma);

// Rota para listar todas as turmas (requer autenticação e permissão de professor/admin)
router.get('/turmas', academicMiddleware.isAuthenticated, academicMiddleware.isProfessorOrAdmin, academicController.getAllTurmas);

module.exports = router;