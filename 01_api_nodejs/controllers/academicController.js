const db = require("../models/db");


// Função para criar uma nova turma
const createTurma = async (req, res) => {
    const { nome_turma, ano } = req.body;
    // Use the authenticated user's id as the professor_id (route requires isProfessorOrAdmin)
    const professor_id = req.user && req.user.id ? req.user.id : null;

    if (!professor_id) {
        return res.status(401).json({ message: 'Usuário não autenticado.' });
    }

    if (!nome_turma || !ano) {
        return res.status(400).json({ message: 'nome_turma e ano são obrigatórios.' });
    }

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

const assignProfessorToTurma = async (req, res) => {
    // Permissão: Apenas Administradores podem atribuir turmas a professores.
    if (req.user.tipo_usuario !== 'admin') {
        return res.status(403).json({ message: 'Acesso negado. Apenas administradores podem atribuir turmas.' });
    }

    // Parâmetros do corpo (vindos do frontend do Admin)
    const { turma_id, professor_id } = req.body;

    if (!turma_id || !professor_id) {
        return res.status(400).json({ message: 'IDs de Turma e Professor são obrigatórios.' });
    }

    try {
        // 1. Opcional: Verificar se o professor_id existe e é 'professor' (Boa Prática)
        const professorCheck = await db.query(
            'SELECT tipo_usuario FROM usuarios WHERE id_usuario = $1', [professor_id]
        );
        // DEBUG: se não encontrar, incluir informação útil para troubleshooting
        if (professorCheck.rows.length === 0 || professorCheck.rows[0].tipo_usuario !== 'professor') {
            console.warn('assignProfessorToTurma: professor lookup failed', { professor_id, found: professorCheck.rows });
            return res.status(404).json({ 
                message: 'ID do Professor não encontrado ou usuário não é do tipo "professor".',
                debug: { received_professor_id: professor_id, query_result: professorCheck.rows }
            });
        }
        
        // 2. Atualiza a turma com o professor_id
        const sql = 'UPDATE turmas SET professor_id = $1 WHERE turma_id = $2 RETURNING *';
        const params = [professor_id, turma_id];
        
        const result = await db.query(sql, params);

        if (result.rows.length === 0) {
            return res.status(404).json({ message: 'Turma não encontrada para atribuição.' });
        }

        res.status(200).json({
            message: 'Professor atribuído à turma com sucesso!',
            turma: result.rows[0]
        });
    } catch (error) {
        console.error('Erro ao atribuir professor:', error);
        res.status(500).json({ message: 'Erro no servidor', error: error.message });
    }
};

// Funcao para listar todas as turmas
const getAllTurmas = async (req, res) => {
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

const getProfessorTurmas = async (req, res) => {
    // O ID do professor vem do token JWT decodificado pelo middleware
    const professor_id = req.user.id; 

    try {
        // ⚠️ CORREÇÃO SQL: Usamos um JOIN para buscar as disciplinas ligadas
        const sql = `
            SELECT 
                t.turma_id, t.nome_turma, t.ano, 
                d.disciplina_id, d.nome_disciplina
            FROM 
                turmas t
            JOIN 
                matriculas m ON t.turma_id = m.turma_id
            JOIN 
                disciplinas d ON m.disciplina_id = d.disciplina_id
            WHERE 
                t.professor_id = $1
            GROUP BY 
                t.turma_id, t.nome_turma, t.ano, d.disciplina_id, d.nome_disciplina
            ORDER BY 
                t.ano DESC, t.nome_turma ASC;
        `;
        const params = [professor_id];
        
        const result = await db.query(sql, params);

        res.status(200).json({
            message: 'Turmas do professor carregadas com sucesso!',
            turmas: result.rows
        });
    } catch (error) {
        console.error('Erro ao listar turmas do professor:', error);
        res.status(500).json({ message: 'Erro no servidor', error: error.message });
    }
};

// Funcao para criar disciplinas
const createDisciplina = async (req, res) => {
    // Apemas admins devem criar disciplinas
    if (req.user.tipo_usuario !== "admin") {
        return res.status(403).json({ message: "Acesso negado. Apenas administradores!" });
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

        // ⚠️ CORREÇÃO: "criada"
        res.status(201).json({
            message: "Disciplina criada com sucesso!",
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
const getAllDisciplinas = async (req, res) => {
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
const createAlunoProfile = async (req, res) => {
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

// Função para matricular um aluno em uma turma/disciplina
const matricularAluno = async (req, res) => {
    // ⚠️ CORREÇÃO: Removido erro de digitação ('professoresou')
    if (req.user.tipo_usuario !== 'professor' && req.user.tipo_usuario !== "admin") {
        return res.status(403).json({ message: "Acesso negado, apenas professores ou administradores podem realizar essa ação" });
    }

    const { aluno_id, turma_id, disciplina_id } = req.body;

    if (!aluno_id || !turma_id || !disciplina_id) {
        return res.status(400).json({ message: 'Aluno, turma e disciplina são obrigatórios' });

    }

    try {
        // Verfica se o aluno existe na tabela alunos
        const aluno = await db.query('SELECT aluno_id FROM alunos WHERE aluno_id = $1', [aluno_id]) // ⚠️ CORREÇÃO: Sintaxe $1
        if (aluno.rows.length === 0) {
            return res.status(404).json({ message: "Aluno não encontrado" });
        }

        //Verifica se a disciplina existe
        const disciplina = await db.query('SELECT disciplina_id FROM disciplinas WHERE disciplina_id = $1', [disciplina_id]); // ⚠️ CORREÇÃO: Sintaxe $1
        // ⚠️ CORREÇÃO: Digitação de 'encontrado'
        if (disciplina.rows.length === 0) {
            return res.status(404).json({ message: 'Disciplina não encontrada' }) 
        }

        // Realiza a matricula
        const sql = `
        INSERT INTO matriculas (aluno_id, turma_id, disciplina_id)
        VALUES ($1, $2, $3)
        RETURNING *;
        `;
        const params = [aluno_id, turma_id, disciplina_id]; // ⚠️ CORREÇÃO: Variável 'parametros' para 'params'
        
        const resultado = await db.query(sql, params); // ⚠️ CORREÇÃO: Variável 'sql' não 'slq'
        const novaMatricula = resultado.rows[0];

        res.status(201).json({
            message: 'Matricula realizada com sucesso!',
            matricula: novaMatricula
        });
    } catch (error) {
        // 23505 é o código do PostgreSQL para matricula duplicada
        if (error.code === "23505") {
            return res.status(409).json({ message: 'O aluno já está matriculado nesta turma/disciplina' })
        }
        console.error('Erro ao matricular aluno', error);
        res.status(500).json({ message: "erro no servidor", error: error.message })
    }
};

const getAlunoBoletim = async (req, res) => {
    const usuario_id = req.user.id; 

    try {
        // Consulta SQL complexa para ligar usuários -> alunos -> matrículas -> notas/disciplinas
        const sql = `
            SELECT
                d.nome_disciplina,
                n.valor_nota,
                m.turma_id,
                a.aluno_id
            FROM 
                usuarios u
            JOIN 
                alunos a ON u.id_usuario = a.usuario_id
            LEFT JOIN
                matriculas m ON a.aluno_id = m.aluno_id
            LEFT JOIN
                notas n ON m.aluno_id = n.aluno_id AND m.disciplina_id = n.disciplina_id
            LEFT JOIN
                disciplinas d ON m.disciplina_id = d.disciplina_id
            WHERE 
                u.id_usuario = $1
            ORDER BY 
                d.nome_disciplina;
        `;
        const params = [usuario_id];
        
        const result = await db.query(sql, params);

        res.status(200).json({
            message: 'Boletim do aluno carregado com sucesso!',
            boletim: result.rows
        });

    } catch (error) {
        console.error('Erro ao buscar boletim:', error);
        res.status(500).json({ message: 'Erro no servidor', error: error.message });
    }
};

const lancarNota = async (req, res) => {
    if (req.user.tipo_usuario !== 'professor' && req.user.tipo_usuario !== 'admin') {
        return res.status(403).json({ message: "Acesso negado. Apenas pessoa autorizadas!" })
    }

    const { aluno_id, disciplina_id, valor_nota, tipo_avaliacao } = req.body;

    if (!aluno_id || !disciplina_id || valor_nota === undefined) {
        return res.status(400).json({ message: "Aluno, disciplina e valor da nota são obrigatórios" })
    }

    try {
        // 1. Verifica se a matrícula existe
        const matriculaCheck = await db.query(
            'SELECT * FROM matriculas WHERE aluno_id = $1 AND disciplina_id = $2',
            [aluno_id, disciplina_id]
        );

        if (matriculaCheck.rows.length === 0) {
            return res.status(404).json({ message: 'Aluno não está matriculado nesta disciplina!' })
        }
        
        // 2. Insere a Nota
        const sql = `
        INSERT INTO notas (aluno_id, disciplina_id, valor_nota, tipo_avaliacao)
        VALUES ($1, $2, $3, $4)
        RETURNING *;
        `;
        const params = [aluno_id, disciplina_id, valor_nota, tipo_avaliacao || 'Prova Final'];

        const resultado = await db.query(sql, params);
        const novaNota = resultado.rows[0];

        res.status(201).json({
            message: "Nota lançada com sucesso!",
            nota: novaNota
        });
    } catch (error) {
        // Se a nota for duplicada (UNIQUE constraint no DB), retorna 409
        if (error.code === '23505') {
            return res.status(409).json({ message: 'Nota para esta avalização ja foi lançada' });
        }
        console.error('Erro ao lançar nota:', error);
        res.status(500).json({ message: 'erro no servidor', error: error.message })
    }
};

// Função para buscar alunos matriculados em uma turma e disciplina específicas
const getAlunosPorTurmaDisciplina = async (req, res) => {
    // ⚠️ CORREÇÃO: req.params
    const { turma_id, disciplina_id } = req.params; 
    
    // O ID do professor vem do token para checagem de permissão (não usado diretamente no GET, mas para segurança)
    const professor_id = req.user.id; 

    try {
        // 2. Consulta para buscar os alunos e a nota atual
        const sql = `
            SELECT
                a.aluno_id,
                a.nome,
                a.sobrenome,
                n.valor_nota AS nota_atual
            FROM 
                matriculas m
            JOIN 
                alunos a ON m.aluno_id = a.aluno_id
            LEFT JOIN 
                notas n ON m.aluno_id = n.aluno_id AND m.disciplina_id = n.disciplina_id
            WHERE 
                m.turma_id = $1 AND m.disciplina_id = $2
            ORDER BY 
                a.nome;
        `;
        const params = [turma_id, disciplina_id];
        
        const result = await db.query(sql, params);

        res.status(200).json({
            message: 'Alunos carregados com sucesso!',
            alunos: result.rows
        });

    } catch (error) {
        console.error('Erro ao listar alunos por turma/disciplina:', error);
        res.status(500).json({ message: 'Erro no servidor', error: error.message });
    }
};

// ⚠️ CORREÇÃO: Exportar todas as novas funções
// Exportar funções de forma consistente
// (module.exports moved to end of file to include all declared functions)

// Cria uma turma e associa disciplinas a ela (rota pensada para Admin)
const createTurmaWithDisciplinas = async (req, res) => {
    // Permissão: apenas admin pode criar turmas já vinculadas com disciplinas
    if (!req.user || req.user.tipo_usuario !== 'admin') {
        return res.status(403).json({ message: 'Acesso negado. Apenas administradores podem realizar esta ação.' });
    }

    const { nome_turma, ano, disciplinas, professor_id } = req.body;

    if (!nome_turma || !ano) {
        return res.status(400).json({ message: 'nome_turma e ano são obrigatórios.' });
    }

    // disciplinas é opcional, mas quando presente deve ser array de ids
    const listaDisciplinas = Array.isArray(disciplinas) ? disciplinas : (disciplinas ? [disciplinas] : []);

    try {
        // 1) Inserir turma (pode incluir professor_id opcional)
        const sqlInsertTurma = 'INSERT INTO turmas (nome_turma, ano, professor_id) VALUES ($1, $2, $3) RETURNING *';
        const paramsTurma = [nome_turma, ano, professor_id || null];
        const resultTurma = await db.query(sqlInsertTurma, paramsTurma);
        const novaTurma = resultTurma.rows[0];

        // 2) Para cada disciplina, validar existência e inserir na tabela de relação
        const associated = [];
        for (const d of listaDisciplinas) {
            // Valida se a disciplina existe
            const check = await db.query('SELECT disciplina_id, nome_disciplina FROM disciplinas WHERE disciplina_id = $1', [d]);
            if (check.rows.length === 0) {
                // pular disciplina inválida (ou poderíamos abortar com 400)
                console.warn('createTurmaWithDisciplinas: disciplina não encontrada, pulando', d);
                continue;
            }

            // Insere na tabela de relação turmas_disciplinas (precisa existir no DB)
            // Usamos INSERT ... ON CONFLICT DO NOTHING para evitar duplicatas
            const relSql = 'INSERT INTO turma_disciplinas (turma_id, disciplina_id) VALUES ($1, $2) ON CONFLICT DO NOTHING RETURNING *';
            try {
                const relRes = await db.query(relSql, [novaTurma.turma_id, d]);
                associated.push({ disciplina_id: d, nome: check.rows[0].nome_disciplina, inserted: relRes.rows.length > 0 });
            } catch (err) {
                // Se a tabela não existir, retornamos aviso claro
                if (err.code === '42P01') { // undefined_table
                    console.error('Tabela turma_disciplinas inexistente:', err.message);
                    return res.status(500).json({ message: 'Tabela de relação turma_disciplinas não encontrada no banco. Crie a tabela ou informe o administrador.' });
                }
                throw err;
            }
        }

        res.status(201).json({ message: 'Turma criada e disciplinas associadas (quando válidas).', turma: novaTurma, disciplinas_associadas: associated });

    } catch (error) {
        console.error('Erro em createTurmaWithDisciplinas:', error);
        res.status(500).json({ message: 'Erro no servidor', error: error.message });
    }
};

// Export all controller functions
module.exports = {
    createTurma,
    createTurmaWithDisciplinas,
    assignProfessorToTurma,
    getAllTurmas,
    getProfessorTurmas,
    createDisciplina,
    getAllDisciplinas,
    createAlunoProfile,
    matricularAluno,
    getAlunoBoletim,
    lancarNota,
    getAlunosPorTurmaDisciplina
};