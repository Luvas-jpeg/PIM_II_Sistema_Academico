const db = require("../models/db");

//Funcao para criar nova turma
exports.createTurma = async (req, res) =>{
    const {nome_turma, ano} = req.body;
    // req.user futuro!
    const professor_id = 1;

    try{
        const sql = 'INSERT INTO turmas (nome_turma, ano, professor_id) VALUES (1$, 2$, 3$) RETURNING *';
        const parametro = [nome_turma, ano, professor_id];

        const resultado = await db.query(sql, parametro);
        const novaTurma = resultado.rows[0];

        res.status(201).json({
            mssage: 'Turma criada!',
            turma: novaTurma
        });
    } catch (error) {
        console.error('Erro ao criar turmar:', error);
        res.status(500).json({message: 'Erro no servidor', error: error.message});
    }
};

// Funcao para listar todas as turmas
exports.getAllTurmas = async (req, res) => {
    try {
        const sql = 'SELECT * FROM turmas ORDER BY ano DESC, nome_turma ASC';
        const resultado = await db.query(sql);

        res.status(200).json({
            message: 'Lista de turmas',
            turmas: resultado,rows
        });
    } catch (error) {
        console.error('Erro ao listar turmas:', error);
        res.status(500).json({ message: 'Erro no servidor', error: error.message });
    }
}