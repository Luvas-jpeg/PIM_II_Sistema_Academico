const db = require("../models/db");


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
};

// Funcao para criar disciplinas
exports.createDisciplina = async (req, res) => {
    // Apemas admins devem criar disciplinas
    if(req.user.tipo_usuario !== "admin") {
        return res.status(403).json({message: "Acesson negado. Apenas administradores!"});
    }

    const { nome_disciplina, descricao } = req.body;

    if(!nome_disciplina) {
        return res.status(400).json ({message: "O nome da disciplina é obrigatório."});
    }

    try {
        const sql = 'INSERT INTO disciplinas (nome_disciplina, descricao) VALUES($1, $2) RETURNING *';
        const params = [nome_disciplina, descricao];

        const resultado = await db.query(sql, params);
        const novaDisciplina = resultado.rows[0];

        res.status(201).json({
            message: "Disciplina corada com sucesso!",
            disciplina: novaDisciplina
        });
    } catch (error) {
        // Erro de disciplina duplicada no SQl é 23505
        if (error.code === '23505') {
            return res.status(409).json({message: "A disciplina já existe"});
        }
        console.error("Erro ao criar disciplina:", error);
        res.status(500).json({message: "Erro no servidor", error: error.message});
    }
};

// Funcao para listar todas as disciplinas
exports.getAllDisciplinas = async (req, res) => {
    try{
        const sql = 'SELECT * FROM disciplinas ORDER BY nome_disciplina ASC';
        const resultado = await db.query(sql);

        res.status(200).json({
            message: 'Lista de disciplinas',
            disciplinas: resultado.rows
        });
    } catch (error) {
        console.error('Erro ao listar disciplinas:', error);
        res.status(500).json({message: 'erro no servidor', error: error.message});
    }
};

//Função para matricular um aluno em uma turma/disciplina
exports.matricularAluno = async (req, res) => {
    // Apenas professoresou admins podem matricular
    if (req.user.tipo_usuario !== 'professro' && req.user.tipo_usuario !== "admin") {
        return res.status(403).json({message: "Acesso negado, apenas professores ou administradores podem realizar essa ação"});
    }

    const { aluno_id, turma_id, disciplina_id} = req.body;

    if (!aluno_id || !turma_id || !disciplina_id) {
        return res.status(400).json({message: 'Aluno, turma e disciplina são obrigatórios'});

    }

    try {
        // Verfica se o aluno existe na tabela alunos
        const aluno = await db.query('SELECT aluno_id FROM alunos WHERE aluno_id = 1$', [aluno_id])
        if (aluno.rows.length === 0) {
            return res.status(404).json ({message : "Aluno não encontrado"});
        }

        //Verifica se a disciplina existe
        const disciplina = await db.query('SELECT disciplina_id FROM disciplinas WHERE disciplina_id = 1$', [disciplina_id]);
        if(disciplina.rows.length === 0) {
            return res.status(404).json({message: 'Disciplina não encntrado'})
        }
    }   
}