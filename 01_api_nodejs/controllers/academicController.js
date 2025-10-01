const db = require("../models/db");

//Funcao para criar nova turma
// Função para criar uma nova turma
exports.createTurma = async (req, res) => {
    const { nome_turma, ano } = req.body;
    const professor_id = 1; 

    try {
        const sql = 'INSERT INTO turmas (nome_turma, ano, professor_id) VALUES ($1, $2, $3) RETURNING *';
        const params = [nome_turma, ano, professor_id];
        
        const result = await db.query(sql, params);
        const novaTurma = result.rows[0];

        res.status(201).json({
            message: 'Turma criada com sucesso!',
            turma: novaTurma
        });
    } catch (error) {
        console.error('Erro ao criar turma:', error);
        res.status(500).json({ message: 'Erro no servidor', error: error.message });
    }
};

// Funcao para listar todas as turmas
exports.getAllTurmas = async (req, res) => {
    try {
        const sql = 'SELECT * FROM turmas ORDER BY ano DESC, nome_turma ASC';
        const resultado = await db.query(sql);

        res.status(200).json({
            message: 'Lista de turmas',
            turmas: resultado.rows
        });
    } catch (error) {
        console.error('Erro ao listar turmas:', error);
        res.status(500).json({ message: 'Erro no servidor', error: error.message });
    }
}