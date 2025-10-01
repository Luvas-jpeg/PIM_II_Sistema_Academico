const express = require('express');
const router = express.Router();
const academicController = require('../controllers/academicController');

// Rota para criar uma nova turma
router.post('/turmas', academicController.createTurma);

//Rota para listar todas as turmas
router.get('/turmas', academicController.getAllTurmas);

module.exports = router