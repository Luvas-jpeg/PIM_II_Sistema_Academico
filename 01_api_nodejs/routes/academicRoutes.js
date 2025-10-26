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

router.get(
    '/professor/turmas',
    academicMiddleware.isAuthenticated, 
    academicMiddleware.isProfessorOrAdmin, 
    academicController.getProfessorTurmas
);

// Suporta PUT (usado pelo frontend) e POST - mantemos PUT para compatibilidade
router.put(
    '/turmas/atribuir-professor',
    academicMiddleware.isAuthenticated,
    academicMiddleware.isAdmin,
    academicController.assignProfessorToTurma
);
router.post(
    '/turmas/atribuir-professor',
    academicMiddleware.isAuthenticated,
    academicMiddleware.isAdmin,
    academicController.assignProfessorToTurma
);

// Rota para criar uma nova disciplina
router.post(
    '/disciplinas',
    academicMiddleware.isAuthenticated,
    academicController.createDisciplina
);

// Rota para criar turma com disciplinas (admin)
router.post(
    '/turmas/with-disciplinas',
    academicMiddleware.isAuthenticated,
    academicMiddleware.isAdmin,
    academicController.createTurmaWithDisciplinas
);

// Rota para listar todas as disciplinas
router.get(
    '/disciplinas',
    academicMiddleware.isAuthenticated,
    academicController.getAllDisciplinas
);

router.get(
    '/boletim',
    academicMiddleware.isAuthenticated,
    academicController.getAlunoBoletim
);

router.post(
    '/notas',
    academicMiddleware.isAuthenticated,
    academicMiddleware.isProfessorOrAdmin,
    academicController.lancarNota
)

router.get(
    '/turmas/:turma_id/disciplinas/:disciplina_id/alunos',
    academicMiddleware.isAuthenticated,
    academicMiddleware.isProfessorOrAdmin,
    academicController.getAlunosPorTurmaDisciplina
);

//Rota para criar o perfil detalhado de um aluno
router.post(
    '/alunos',
    academicMiddleware.isAuthenticated,
    academicMiddleware.isProfessorOrAdmin,
    academicController.createAlunoProfile
);

//Rota para matricular um aluno
router.post(
    '/matriculas',
    academicMiddleware.isAuthenticated,
    academicMiddleware.isProfessorOrAdmin,
    academicController.matricularAluno
);

module.exports = router;