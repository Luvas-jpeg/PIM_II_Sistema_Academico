// routes/academicRoutes.js

const express = require('express');
const router = express.Router();
const academicController = require('../controllers/academicController');

// Importa o middleware de autenticação
const academicMiddleware = require('../middlewares/academicMiddleware');

// Acesso restrito a usuários autenticados e com a permissão correta
router.post(
    '/turmas',
    academicMiddleware.isAuthenticated,
    academicMiddleware.isProfessorOrAdmin,
    academicController.createTurma
);

// Acesso restrito a usuários autenticados e com a permissão correta
router.get(
    '/turmas',
    academicMiddleware.isAuthenticated,
    academicMiddleware.isProfessorOrAdmin,
    academicController.getAllTurmas
);

// Rota para criar uma nova disciplina
router.post(
    '/disciplinas',
    academicMiddleware.isAuthenticated,
    academicController.createDisciplina
);

// Rota para listar todas as disciplinas
router.get(
    '/disciplinas',
    academicMiddleware.isAuthenticated,
    academicController.getAllDisciplinas
);

//Rota para criar o perfil detalhado de um aluno
router.post(
    '/alunos',
    academicMiddleware.isAuthenticated,
    academicMiddleware.isProfessorOrAdmin,
    academicController.createAlunoPerfil
);

//Rota para matricular um aluno
router.post(
    '/matriculas',
    academicMiddleware.isAuthenticated,
    academicMiddleware.isProfessorOrAdmin,
    academicController.matricularAluno
);

module.exports = {
    createTurma: exports.createTurma,
    getAllTurmas: exports.getAllTurmas,
    createDisciplina: exports.createDisciplina,
    getAllDisciplinas: exports.getAllDisciplinas,
    matricularAluno: exports.matricularAluno,
    createAlunoProfile: exports.createAlunoPerfil,
};

module.exports = router