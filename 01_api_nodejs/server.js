const express = require('express');
const cors = require('cors');
require('dotenv').config();

const db = require('./models/db');

const app = express();

app.use(express.json());
app.use(cors());

db.query('SELECT 1 + 1 AS solution')
    .then(res => {
        console.log("Conexão com o PostgreSQL bem-sucedida");
        console.log("Resultado da consulta:", res)
    })
    .catch(err => {
        console.error("Erro de conexão com o PostgreSQL:", err.stack);
    });

app.get('/health', (req, res) => {
    res.status(200).json({status: "ok", message: "API is running"});
});

const authRoutes = require('./routes/academicRoutes');

const PORT = process.env.PORT || 3000;
app.listen(PORT, () =>{
    console.log(`Servidor rodando na porta ${PORT}`);
});