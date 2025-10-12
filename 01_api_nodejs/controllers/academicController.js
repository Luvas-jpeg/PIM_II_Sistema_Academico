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
    if (req.user.tipo_usuario !== "admin") {
        return res.status(403).json({ message: "Acesson negado. Apenas administradores!" });
    }

    const { nome_disciplina, descricao } = req.body;

    if (!nome_disciplina) {
        return res.status(400).json({ message: "O nome da disciplina é obrigatório." });
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
            return res.status(409).json({ message: "A disciplina já existe" });
        }
        console.error("Erro ao criar disciplina:", error);
        res.status(500).json({ message: "Erro no servidor", error: error.message });
    }
};

// Funcao para listar todas as disciplinas
exports.getAllDisciplinas = async (req, res) => {
    try {
        const sql = 'SELECT * FROM disciplinas ORDER BY nome_disciplina ASC';
        const resultado = await db.query(sql);

        res.status(200).json({
            message: 'Lista de disciplinas',
            disciplinas: resultado.rows
        });
    } catch (error) {
        console.error('Erro ao listar disciplinas:', error);
        res.status(500).json({ message: 'erro no servidor', error: error.message });
    }
};
// Função para criar o perfil acadêmico de um aluno na tabela 'alunos'
exports.createAlunoPerfil = async (req, res) => {
    // Permissão: Apenas Professores ou Administradores podem criar perfis de aluno
    if (req.user.tipo_usuario !== 'professor' && req.user.tipo_usuario !== 'admin') {
        return res.status(403).json({ message: 'Acesso negado. Apenas gestores podem criar perfis de aluno.' });
    }

    // Espera dados completos do aluno, e o ID do usuário já existente
    const { nome, sobrenome, email, data_nascimento, usuario_id } = req.body;

    if (!nome || !email || !usuario_id) {
        return res.status(400).json({ message: 'Nome, E-mail e ID do Usuário são obrigatórios.' });
    }

    try {
        // Verifica se o usuário_id existe na tabela 'usuarios' e se o tipo_usuario é 'aluno'
        const userCheck = await db.query('SELECT tipo_usuario FROM usuarios WHERE id_usuario = $1', [usuario_id]);
        if (userCheck.rows.length === 0 || userCheck.rows[0].tipo_usuario !== 'aluno') {
            return res.status(404).json({ message: 'Usuário não encontrado ou não está categorizado como ALUNO.' });
        }

        // Insere o perfil na tabela 'alunos'
        const sql = `
            INSERT INTO alunos (nome, sobrenome, email, data_nascimento, usuario_id)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *;
        `;
        const params = [nome, sobrenome, email, data_nascimento || null, usuario_id];

        const result = await db.query(sql, params);
        const novoAluno = result.rows[0];

        res.status(201).json({
            message: 'Perfil de aluno criado com sucesso!',
            aluno: novoAluno
        });

    } catch (error) {
        // 23505 para o campo 'email' ou 'usuario_id' duplicado
        if (error.code === '23505') {
            return res.status(409).json({ message: 'Já existe um perfil de aluno ligado a este usuário ou e-mail.' });
        }
        console.error('Erro ao criar perfil de aluno:', error);
        res.status(500).json({ message: 'Erro no servidor', error: error.message });
    }
};

//Função para matricular um aluno em uma turma/disciplina
exports.matricularAluno = async (req, res) => {
    // Apenas professoresou admins podem matricular
    if (req.user.tipo_usuario !== 'professor' && req.user.tipo_usuario !== "admin") {
        return res.status(403).json({ message: "Acesso negado, apenas professores ou administradores podem realizar essa ação" });
    }

    const { aluno_id, turma_id, disciplina_id } = req.body;

    if (!aluno_id || !turma_id || !disciplina_id) {
        return res.status(400).json({ message: 'Aluno, turma e disciplina são obrigatórios' });

    }

    try {
        // Verfica se o aluno existe na tabela alunos
        const aluno = await db.query('SELECT aluno_id FROM alunos WHERE aluno_id = $1', [aluno_id])
        if (aluno.rows.length === 0) {
            return res.status(404).json({ message: "Aluno não encontrado" });
        }

        //Verifica se a disciplina existe
        const disciplina = await db.query('SELECT disciplina_id FROM disciplinas WHERE disciplina_id = 1$', [disciplina_id]);
        if (disciplina.rows.length === 0) {
            return res.status(404).json({ message: 'Disciplina não encntrado' })
        }

        // Realiza a matricula
        const slq = `
        INSERT INTO matriculas (aluno_id, turma_id, disciplina_id)
        VALUES (1$, 2$, 3$)
        RETURNING *;
        `;
        const parametros = [aluno_id, turma_id, disciplina_id];

        const resultado = await db.query(sql, parametros);
        const novaMatricula = resultado.rows[0];

        res.status(201).json({
            message: 'Matricula realizada com sucesso!',
            matricula: novaMatricula
        });
    } catch (error) {
        // 23505 é o copdio do PostgreSQL para  matricula duplicada
        if (error.code === "23505") {
            return res.status(409).json({ message: 'O aluno já está matriculado nesta turma/disciplina' })
        }
        console.error('Erro ao matricular aluno', error);
        res.status(500).json({ message: "erro no servidor", error: error.message })
    }
};

