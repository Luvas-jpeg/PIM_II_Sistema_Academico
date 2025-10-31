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
        // 🔥 TRATAMENTO PARA TURMA DUPLICADA 🔥
        // Código 23505 no PostgreSQL indica violação de UNIQUE constraint
        if (error.code === '23505' && error.constraint === 'unique_turma_nome_ano') {
            return res.status(409).json({ // 409 Conflict
                message: `Erro: Já existe uma turma com o nome "${nome_turma}" para o ano ${ano}.` 
            });
        }
        
        // Outros erros
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

    console.log(`[AssignProf] Recebido: turma_id=${turma_id}, professor_id=${professor_id}`);

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

        console.log(`[AssignProf] Executando SQL: ${sql} com params:`, params);
        
        const result = await db.query(sql, params);

        console.log(`[AssignProf] Resultado da Query:`, result.rows);

        if (result.rows.length === 0) {
            console.log(`[AssignProf] Turma ${turma_id} não encontrada para atualização.`);
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


exports.assignDisciplinasToTurma = async (req, res) => {
    // Permissão: Apenas Administradores
    if (req.user.tipo_usuario !== 'admin') {
        return res.status(403).json({ message: 'Acesso negado. Apenas administradores podem atribuir disciplinas.' });
    }

    const { turma_id, disciplina_ids } = req.body; // disciplina_ids é um ARRAY de IDs
    
    if (!turma_id || !disciplina_ids || !Array.isArray(disciplina_ids) || disciplina_ids.length === 0) {
        return res.status(400).json({ message: 'ID da Turma e uma lista (array) de IDs de Disciplinas são obrigatórios.' });
    }

    // Usaremos uma transação para garantir atomicidade
    const client = await db.getClient(); 

    try {
        await client.query('BEGIN'); // Inicia a transação

        // 1. Verificar se a Turma existe
        const turmaCheck = await client.query('SELECT turma_id FROM turmas WHERE turma_id = $1', [turma_id]);
        if (turmaCheck.rows.length === 0) {
            await client.query('ROLLBACK'); // Desfaz a transação
            return res.status(404).json({ message: 'Turma não encontrada.' });
        }

        let insercoesRealizadas = 0;
        let disciplinasInvalidas = [];

        // 2. Para cada disciplina_id na lista, tenta inserir na tabela de junção
        for (const disciplina_id of disciplina_ids) {
            // Opcional: Validar se a disciplina existe antes de inserir
            const discCheck = await client.query('SELECT disciplina_id FROM disciplinas WHERE disciplina_id = $1', [disciplina_id]);
            if (discCheck.rows.length === 0) {
                disciplinasInvalidas.push(disciplina_id);
                continue; // Pula para a próxima disciplina se esta não existir
            }
            
            // Tenta inserir na tabela turma_disciplinas
            // ON CONFLICT DO NOTHING: Evita erro se a associação já existir (ignora a inserção duplicada)
            const insertSql = `
                INSERT INTO turma_disciplinas (turma_id, disciplina_id) 
                VALUES ($1, $2) 
                ON CONFLICT (turma_id, disciplina_id) DO NOTHING
                RETURNING turma_disciplina_id; 
            `;
            const params = [turma_id, disciplina_id];
            console.log(`[AssignDisciplinas] PREPARANDO INSERT: turma=${params[0]}, disciplina=${params[1]}`);
            
            // Conta quantas inserções foram realmente feitas (não ignoradas pelo ON CONFLICT)
           try {
                const result = await client.query(insertSql, params);
                
                // 🔥 LOG DEPOIS DO INSERT 🔥
                console.log(`[AssignDisciplinas] RESULTADO INSERT para Disc ${disciplina_id}: RowCount=${result.rowCount}, Rows=`, result.rows);
                
                if (result.rowCount > 0) {
                    insercoesRealizadas++;
                } else {
                    console.log(`[AssignDisciplinas] Associação Turma ${turma_id} - Disc ${disciplina_id} JÁ EXISTIA (ON CONFLICT acionado).`);
                } } catch (insertError) {
                 // 🔥 LOG SE O INSERT FALHAR (mesmo com ON CONFLICT) 🔥
                 console.error(`[AssignDisciplinas] ERRO NO INSERT para Disc ${disciplina_id}:`, insertError);
                 // Decide se quer continuar ou abortar a transação
                 // throw insertError; // Descomente para abortar tudo se um INSERT falhar
            }
        }

        await client.query('COMMIT'); // Confirma a transação
        console.log(`[AssignDisciplinas] COMMIT realizado. Inserções: ${insercoesRealizadas}`);

        let finalResponseMessage = "";
        if (insercoesRealizadas > 0) {
             finalResponseMessage = `${insercoesRealizadas} nova(s) disciplina(s) associada(s) à Turma ${turma_id}.`;
        } else {
             // 👇 MENSAGEM MAIS CLARA QUANDO NADA É INSERIDO 👇
             finalResponseMessage = `Nenhuma nova disciplina foi associada. As associações selecionadas provavelmente já existiam para a Turma ${turma_id}.`;
        }
        
        if (disciplinasInvalidas.length > 0) {
            finalResponseMessage += ` IDs de disciplinas inválidos ignorados: ${disciplinasInvalidas.join(', ')}.`; 
        }

        res.status(200).json({
            message: finalResponseMessage, // Mensagem atualizada
            turma_id: turma_id,
            disciplinas_processadas: disciplina_ids
        });

    } catch (error) {
        await client.query('ROLLBACK'); // Desfaz a transação em caso de erro inesperado
        console.error('Erro ao atribuir disciplinas à turma:', error);
        res.status(500).json({ message: 'Erro no servidor durante a atribuição de disciplinas.', error: error.message });
    } finally {
        client.release(); // Libera o cliente de volta para o pool
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
                t.turma_id, 
                t.nome_turma, 
                t.ano, 
                d.disciplina_id, 
                d.nome_disciplina
            FROM 
                turmas t
            -- Usamos INNER JOIN para garantir que só turmas com matrículas apareçam
            INNER JOIN 
                matriculas m ON t.turma_id = m.turma_id
            INNER JOIN 
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

const removeDisciplinaFromTurma = async (req, res) => {
    // Permissão: Apenas Administradores
    if (req.user.tipo_usuario !== 'admin') {
        return res.status(403).json({ message: 'Acesso negado. Apenas administradores.' });
    }

    const { turma_id, disciplina_id } = req.body;

    console.log(`[RemoveDisciplina] Recebido: turma_id=${turma_id}, disciplina_id=${disciplina_id}`);

    if (!turma_id || !disciplina_id) {
        console.log("[RemoveDisciplina] Erro: IDs faltando.");
        return res.status(400).json({ message: 'ID da Turma e ID da Disciplina são obrigatórios.' });
    }

    try {
        // Deleta da tabela de junção 'turma_disciplinas'
        const sql = `
            DELETE FROM turma_disciplinas
            WHERE turma_id = $1 AND disciplina_id = $2
            RETURNING *; 
        `;
        // Nota: Se houver alunos matriculados (tabela 'matriculas'), esta ação pode ser bloqueada
        // ou causar problemas de integridade se a tabela 'matriculas' depender de 'turma_disciplinas'.
        // Por enquanto, assumimos que a remoção é permitida.
        
        const params = [turma_id, disciplina_id];
        console.log(`[RemoveDisciplina] Executando SQL: ${sql.trim().replace(/\s+/g, ' ')}`, params);
        
        const result = await db.query(sql, params);

        if (result.rowCount === 0) {
            console.log("[RemoveDisciplina] Associação não encontrada para remoção.");
            return res.status(404).json({ message: 'Associação não encontrada para remoção.' });
        }

        res.status(200).json({
            message: 'Disciplina removida da turma com sucesso!',
            associacao_removida: result.rows[0]
        });

    } catch (error) {
        // Erro 23503: Se a remoção for impedida por uma Foreign Key (ex: matrículas dependem dela)
        console.error('--- [RemoveDisciplina] ERRO CAPTURADO ---');
        console.error('Mensagem:', error.message);
        console.error('Código (code):', error.code); // ⬅️ Ex: 23503 (Foreign Key)
        console.error('Detalhe (detail):', error.detail);
        console.error('-------------------------------------------');

        if (error.code === '23503') {
            console.error('[RemoveDisciplina] Erro 23503 (Foreign Key) detectado.');
             return res.status(409).json({ 
                 message: 'Erro: Não é possível remover esta disciplina da turma pois existem matrículas de alunos ativas nela.',
                 detail: error.detail
            });
        }
        console.error('Erro ao remover disciplina da turma:', error);
        res.status(500).json({ message: 'Erro no servidor.', error: error.message });
    }
};

const deleteDisciplina = async (req, res) => {
    // Permissão: Apenas Administradores
    if (req.user.tipo_usuario !== 'admin') {
        return res.status(403).json({ message: 'Acesso negado. Apenas administradores.' });
    }

    const { disciplina_id } = req.params; // ID vem da URL

    try {
        // Deleta da tabela 'disciplinas'
        const sql = 'DELETE FROM disciplinas WHERE disciplina_id = $1 RETURNING *';
        const params = [disciplina_id];
        
        const result = await db.query(sql, params);

        if (result.rowCount === 0) {
            return res.status(404).json({ message: 'Disciplina não encontrada para exclusão.' });
        }

        res.status(200).json({
            message: 'Disciplina excluída permanentemente com sucesso!',
            disciplina_excluida: result.rows[0]
        });

    } catch (error) {
        console.error('--- [DeleteDisciplina] ERRO CAPTURADO ---');
        console.error('Mensagem:', error.message);
        console.error('Código (code):', error.code); // ⬅️ IMPORTANTE
        console.error('Detalhe (detail):', error.detail); // ⬅️ IMPORTANTE
        console.error('-------------------------------------------');
        // Erro 23503: Violação de Chave Estrangeira (a disciplina está sendo usada!)
        // Isso acontece se ela ainda estiver associada em 'turma_disciplinas' ou 'matriculas'.
        if (error.code === '23503') {
            console.error('[DeleteDisciplina] Erro 23503 (Foreign Key) detectado. Enviando 409.');
             return res.status(409).json({ // 409 Conflict
                 message: 'Erro: Não é possível excluir esta disciplina pois ela já está associada a uma ou mais turmas/matrículas.',
                 detail: 'Remova primeiro a disciplina de todas as turmas.'
            });
        }
        console.error('[DeleteDisciplina] Erro não tratado (23503 não detectado). Enviando 500.');
        console.error('Erro ao excluir disciplina:', error);
        res.status(500).json({ message: 'Erro no servidor.', error: error.message });
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

const deleteMatricula = async (req, res) => {
    // Permissão: Apenas Administradores
    if (req.user.tipo_usuario !== 'admin') {
        return res.status(403).json({ message: 'Acesso negado. Apenas administradores.' });
    }

    const { matricula_id } = req.params; // ID vem da URL

    if (!matricula_id) {
        return res.status(400).json({ message: 'ID da Matrícula é obrigatório.' });
    }

    try {
        // Deleta da tabela 'matriculas'
        const sql = 'DELETE FROM matriculas WHERE matricula_id = $1 RETURNING *';
        const params = [matricula_id];
        
        const result = await db.query(sql, params);

        if (result.rowCount === 0) {
            return res.status(404).json({ message: 'Matrícula não encontrada para exclusão.' });
        }

        // Se a exclusão funcionar, as notas e presenças associadas
        // (que dependem de matricula_id) também devem ser excluídas
        // SE você configurou "ON DELETE CASCADE" nessas tabelas (notas, presenca).
        // Se não configurou, elas ficarão órfãs (o que é ruim) ou a exclusão falhará (se houver notas).

        res.status(200).json({
            message: 'Matrícula do aluno removida com sucesso!',
            matricula_excluida: result.rows[0]
        });

    } catch (error) {
        // Erro 23503: Violação de Chave Estrangeira (Notas/Presença dependem desta matrícula)
        if (error.code === '23503') {
             return res.status(409).json({ // 409 Conflict
                 message: 'Erro: Não é possível excluir esta matrícula pois ela possui notas ou registros de presença associados.',
                 detail: error.detail 
            });
        }
        console.error('Erro ao excluir matrícula:', error);
        res.status(500).json({ message: 'Erro no servidor.', error: error.message });
    }
};

const getAlunoBoletim = async (req, res) => {
    const usuario_id = req.user.id; 

    console.log(`[GetBoletim] ID do usuário sendo usado na consulta WHERE: ${usuario_id}`);

    try {
        // Consulta SQL complexa para ligar usuários -> alunos -> matrículas -> notas/disciplinas
       const sql = `
            SELECT
                d.disciplina_id,
                d.nome_disciplina,
                m.turma_id,
                a.aluno_id,
                
                -- Subconsulta NP1
                (SELECT valor_nota FROM notas n_np1 
                 WHERE n_np1.aluno_id = a.aluno_id 
                   AND n_np1.disciplina_id = d.disciplina_id 
                   AND n_np1.tipo_avaliacao = 'NP1' LIMIT 1) AS nota_np1, 
                   
                -- Subconsulta NP2
                (SELECT valor_nota FROM notas n_np2 
                 WHERE n_np2.aluno_id = a.aluno_id 
                   AND n_np2.disciplina_id = d.disciplina_id 
                   AND n_np2.tipo_avaliacao = 'NP2' LIMIT 1) AS nota_np2, 
                   
                -- Cálculo da Média
                ROUND(
                    (
                        COALESCE((SELECT valor_nota FROM notas n_np1 WHERE n_np1.aluno_id = a.aluno_id AND n_np1.disciplina_id = d.disciplina_id AND n_np1.tipo_avaliacao = 'NP1' LIMIT 1), 0) 
                        + 
                        COALESCE((SELECT valor_nota FROM notas n_np2 WHERE n_np2.aluno_id = a.aluno_id AND n_np2.disciplina_id = d.disciplina_id AND n_np2.tipo_avaliacao = 'NP2' LIMIT 1), 0)
                    ) / 2.0, 1
                ) AS media_final,

                -- 🔥 SUBCONSULTA DE FALTAS CORRIGIDA 🔥
                (SELECT COUNT(*) 
                 FROM presenca p 
                 WHERE p.matricula_id = m.matricula_id 
                   AND p.status = 'ausente') AS total_faltas 
            
            FROM 
                usuarios u
            JOIN 
                alunos a ON u.id_usuario = a.usuario_id
            JOIN 
                matriculas m ON a.aluno_id = m.aluno_id
            JOIN 
                disciplinas d ON m.disciplina_id = d.disciplina_id
            
            -- Junta com NOTAS (LEFT JOINs para NP1 e NP2)
            LEFT JOIN notas n_np1 ON n_np1.aluno_id = a.aluno_id AND n_np1.disciplina_id = d.disciplina_id AND n_np1.tipo_avaliacao = 'NP1'
            LEFT JOIN notas n_np2 ON n_np2.aluno_id = a.aluno_id AND n_np2.disciplina_id = d.disciplina_id AND n_np2.tipo_avaliacao = 'NP2'
            
            WHERE 
                u.id_usuario = $1 -- Filtra pelo ID do usuário logado
            
            -- Agrupa para garantir UMA LINHA POR DISCIPLINA
            GROUP BY 
                d.disciplina_id, d.nome_disciplina, m.turma_id, m.matricula_id, a.aluno_id, n_np1.valor_nota, n_np2.valor_nota
            ORDER BY 
                d.nome_disciplina;
        `;
        
        const params = [usuario_id];
        
        const result = await db.query(sql, params);

        console.log(`[GetBoletim] Resultado da Query (Node.js):`, result.rows); 
        console.log(`[GetBoletim] Número de Linhas Recebidas: ${result.rowCount}`);

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

    if (!aluno_id || !disciplina_id || valor_nota === undefined || !tipo_avaliacao) {
        return res.status(400).json({ message: "Aluno, disciplina e valor da nota são obrigatórios" })
    }

    const tiposValidos = ['NP1', 'NP2', 'Exame', 'Substitutiva']; 
    if (!tiposValidos.includes(tipo_avaliacao)) {
        return res.status(400).json({ message: `Tipo de avaliação inválido. Use um de: ${tiposValidos.join(', ')}` });
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
    INSERT INTO notas (aluno_id, disciplina_id, valor_nota, tipo_avaliacao, data_lancamento)
    VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP) 

    -- Se a UNIQUE constraint (aluno_id, disciplina_id, tipo_avaliacao) falhar:
    ON CONFLICT (aluno_id, disciplina_id, tipo_avaliacao) 

    -- Então, execute um UPDATE
    DO UPDATE SET 
        valor_nota = EXCLUDED.valor_nota, -- Atualiza a nota para o novo valor
        data_lancamento = CURRENT_TIMESTAMP

    RETURNING *;`
        
        const params = [aluno_id, disciplina_id, valor_nota, tipo_avaliacao];

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

const deleteNotasPorDisciplina = async (req, res) => {
    // Permissão: Apenas Administradores (ação muito destrutiva)
    if (req.user.tipo_usuario !== 'admin') {
        return res.status(403).json({ message: 'Acesso negado. Apenas administradores.' });
    }

    // O ID da disciplina vem da URL
    const { disciplina_id } = req.params; 

    if (!disciplina_id) {
        return res.status(400).json({ message: 'ID da Disciplina é obrigatório.' });
    }

    try {
        // Deleta todos os registros da tabela 'notas' que correspondem à disciplina
        const sql = 'DELETE FROM notas WHERE disciplina_id = $1 RETURNING *';
        const params = [disciplina_id];
        
        const result = await db.query(sql, params);

        if (result.rowCount === 0) {
            return res.status(404).json({ 
                message: 'Nenhuma nota encontrada para esta disciplina (ou a disciplina não existe).',
                disciplina_id: disciplina_id
            });
        }

        res.status(200).json({
            message: `Todas as ${result.rowCount} nota(s) associada(s) à disciplina ${disciplina_id} foram excluídas.`,
            notas_excluidas: result.rows
        });

    } catch (error) {
        // Esta função não deve falhar por FK (a menos que 'presenca' dependa de 'notas', o que é raro)
        console.error('Erro ao excluir notas por disciplina:', error);
        res.status(500).json({ message: 'Erro no servidor.', error: error.message });
    }
};

const marcarPresenca = async (req, res) => {
    if (req.user.tipo_usuario !== 'professor' && req.user.tipo_usuario !== 'admin') {
        return res.status(403).json({message:'Acesso negado!'});
    }

    const {matricula_id, status} = req.body;
    const data_atual = new Date().toISOString().split('T')[0]

    if (!matricula_id || !status || !['presente', 'ausente'].includes(status)) {
        return res.status(400).json({ message: 'ID da Matrícula e Status ("presente" ou "ausente") são obrigatórios.' });
    }

    try {
        // Tenta inserir o registro de presença para HOJE
        const sql = `
            INSERT INTO presenca (matricula_id, data_presenca, status)
            VALUES ($1, $2, $3)
            RETURNING *;
        `;
        // Usamos a data atual do servidor
        const params = [matricula_id, data_atual, status];
        
        const result = await db.query(sql, params);
        const novoRegistroPresenca = result.rows[0];

        res.status(201).json({
            message: `Presença (${status}) marcada para hoje (${data_atual}) com sucesso!`,
            presenca: novoRegistroPresenca
        });

    } catch (error) {
        // 🔥 ERRO 23505: Violação da UNIQUE constraint (Já marcou hoje!)
        if (error.code === '23505') {
             return res.status(409).json({ message: `Presença para este aluno/disciplina já foi marcada hoje (${data_atual}).` });
        }
        // Erro 23503: Chave estrangeira (matricula_id não existe)
        if (error.code === '23503') {
             return res.status(404).json({ message: 'Matrícula não encontrada.' });
        }
        
        console.error('Erro ao marcar presença:', error);
        res.status(500).json({ message: 'Erro no servidor', error: error.message });
    }
};


// Função para buscar alunos matriculados em uma turma e disciplina específicas
const getAlunosPorTurmaDisciplina = async (req, res) => {
    const { turma_id, disciplina_id } = req.params; 
    const professor_id = req.user.id; // ID do professor logado (para segurança)

    try {
        // ⚠️ CONSULTA SQL COM GROUP BY CORRIGIDO ⚠️
        const sql = `
            SELECT
                a.aluno_id, a.nome, a.sobrenome, m.matricula_id,
                
                -- Subconsulta NP1
                (SELECT valor_nota FROM notas n_np1 
                 WHERE n_np1.aluno_id = a.aluno_id 
                   AND n_np1.disciplina_id = m.disciplina_id 
                   AND n_np1.tipo_avaliacao = 'NP1' LIMIT 1) AS nota_np1,
                   
                -- Subconsulta NP2
                (SELECT valor_nota FROM notas n_np2 
                 WHERE n_np2.aluno_id = a.aluno_id 
                   AND n_np2.disciplina_id = m.disciplina_id 
                   AND n_np2.tipo_avaliacao = 'NP2' LIMIT 1) AS nota_np2,
                   
                -- Cálculo da Média
                ROUND(
                    (COALESCE((SELECT valor_nota FROM notas n_np1 WHERE n_np1.aluno_id = a.aluno_id AND n_np1.disciplina_id = m.disciplina_id AND n_np1.tipo_avaliacao = 'NP1' LIMIT 1), 0) + 
                     COALESCE((SELECT valor_nota FROM notas n_np2 WHERE n_np2.aluno_id = a.aluno_id AND n_np2.disciplina_id = m.disciplina_id AND n_np2.tipo_avaliacao = 'NP2' LIMIT 1), 0)) 
                    / 2.0 
                , 1) AS media_final
            FROM 
                matriculas m
            JOIN 
                alunos a ON m.aluno_id = a.aluno_id
            
            WHERE 
                m.turma_id = $1 AND m.disciplina_id = $2 
            
            -- 👇 CORREÇÃO: GROUP BY apenas nas colunas de identificação 👇
            GROUP BY
                a.aluno_id, a.nome, a.sobrenome, m.matricula_id
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

// Função para associar disciplinas a uma turma
const assignDisciplinasToTurma = async (req, res) => {
    // Permissão: Apenas Administradores
    if (req.user.tipo_usuario !== 'admin') {
        return res.status(403).json({ message: 'Acesso negado. Apenas administradores podem atribuir disciplinas.' });
    }

    const { turma_id, disciplina_ids } = req.body; 

    if (!turma_id || !disciplina_ids || !Array.isArray(disciplina_ids) || disciplina_ids.length === 0) {
        console.log("[AssignDisciplinas] Erro: Dados inválidos recebidos."); // LOG de erro de validação
        return res.status(400).json({ message: 'ID da Turma e uma lista (array) de IDs de Disciplinas são obrigatórios.' });
    }

    const client = await db.getClient(); 

    try {
        await client.query('BEGIN'); 

        // 1. Verificar se a Turma existe
        const turmaCheck = await client.query('SELECT turma_id FROM turmas WHERE turma_id = $1', [turma_id]);

        if (turmaCheck.rows.length === 0) {
            await client.query('ROLLBACK'); 
            return res.status(404).json({ message: 'Turma não encontrada.' });
        }

        let insercoesRealizadas = 0;
        let disciplinasInvalidas = [];

        // 2. Loop para inserir cada disciplina
        for (const disciplina_id of disciplina_ids) {
            //  LOG 3: Processando cada disciplina_id

            // Validar se a disciplina existe
            const discCheck = await client.query('SELECT disciplina_id FROM disciplinas WHERE disciplina_id = $1', [disciplina_id]);
    
            if (discCheck.rows.length === 0) {
                disciplinasInvalidas.push(disciplina_id);
                continue; 
            }
            
            // Tenta inserir na tabela turma_disciplinas
            const insertSql = `
                INSERT INTO turma_disciplinas (turma_id, disciplina_id) 
                VALUES ($1, $2) 
                ON CONFLICT (turma_id, disciplina_id) DO NOTHING
                RETURNING turma_disciplina_id; 
            `;
            const result = await client.query(insertSql, [turma_id, disciplina_id]);
            
            if (result.rowCount > 0) {
                insercoesRealizadas++;
            }
        }

        await client.query('COMMIT'); 
        console.log(`[AssignDisciplinas] COMMIT realizado. Inserções: ${insercoesRealizadas}`);

        // 👇 CORREÇÃO: Defina a variável antes de usá-la 👇
        let finalResponseMessage = `${insercoesRealizadas} nova(s) disciplina(s) associada(s) à Turma ${turma_id}.`;
        if (disciplinasInvalidas.length > 0) {
            // Use a variável definida acima
            finalResponseMessage += ` IDs de disciplinas inválidos ignorados: ${disciplinasInvalidas.join(', ')}.`; 
        }

        // Use a variável correta na resposta JSON
        res.status(200).json({
            message: finalResponseMessage, // ⬅️ Variável corrigida aqui
            turma_id: turma_id,
            disciplinas_processadas: disciplina_ids
        });

    } catch (error) {
        await client.query('ROLLBACK'); 
        // 🔥 LOG 7: Erro capturado
        console.error('[AssignDisciplinas] Erro durante a transação:', error); 
        res.status(500).json({ message: 'Erro no servidor durante a atribuição.', error: error.message });
    } finally {
        client.release(); 
    }
};

const getAllProfessores = async (req, res) => {
    // Permissão: Apenas Admin pode ver a lista completa
    if (req.user.tipo_usuario !== 'admin') {
        return res.status(403).json({ message: 'Acesso negado. Apenas administradores.' });
    }

    try {
        // Busca na tabela 'usuarios' filtrando pelo tipo
        const sql = `
            SELECT 
                u.id_usuario, 
                u.email, 
                u.data_criacao
                -- Futuramente, pode fazer JOIN com uma tabela 'professores' para mais detalhes
            FROM 
                usuarios u
            WHERE 
                u.tipo_usuario = 'professor'
            ORDER BY 
                u.email;
        `;
        
        const result = await db.query(sql);

        res.status(200).json({
            message: 'Lista de professores carregada.',
            professores: result.rows
        });

    } catch (error) {
        console.error('Erro ao listar professores:', error);
        res.status(500).json({ message: 'Erro no servidor', error: error.message });
    }
};

// Função para listar todos os usuários do tipo 'aluno' (com dados do perfil)
const getAllAlunos = async (req, res) => {
    // Permissão: Apenas Admin pode ver a lista completa
    if (req.user.tipo_usuario !== 'admin') {
        return res.status(403).json({ message: 'Acesso negado. Apenas administradores.' });
    }

    try {
        // Faz JOIN com a tabela 'alunos' para pegar nome, etc.
        const sql = `
            SELECT 
                u.id_usuario, 
                a.aluno_id, 
                a.nome, 
                a.sobrenome, 
                a.email,
                a.data_nascimento
            FROM 
                usuarios u
            JOIN 
                alunos a ON u.id_usuario = a.usuario_id
            WHERE 
                u.tipo_usuario = 'aluno'
            ORDER BY 
                a.nome, a.sobrenome;
        `;
        
        const result = await db.query(sql);

        res.status(200).json({
            message: 'Lista de alunos carregada.',
            alunos: result.rows
        });

    } catch (error) {
        console.error('Erro ao listar alunos:', error);
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
    removeDisciplinaFromTurma,
    deleteDisciplina,
    getAllDisciplinas,
    createAlunoProfile,
    deleteMatricula,
    matricularAluno,
    getAlunoBoletim,
    lancarNota,
    deleteNotasPorDisciplina,
    marcarPresenca,
    getAlunosPorTurmaDisciplina,
    assignDisciplinasToTurma,
    getAllProfessores,
    getAllAlunos
};