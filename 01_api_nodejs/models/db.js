const { Pool, Query } = require('pg');
require('dotenv').config();

const pool = new Pool({
    user:process.env.DB_USER,
    host:process.env.DB_HOST,
    database:process.env.DB_DATABASE,
    password:process.env.DB_PASSWORD,
    port:process.env.DB_PORT // Porta do PostgreSLQ : 5432

});

module.exports ={
    query:(text, params) =>pool.query(text, params),
    getClient: () => pool.connect()
};