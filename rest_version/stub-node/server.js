// Express API Gateway that talks to REST FastAPI backends (no gRPC)
// -----------------------------------------------------------------
// Replaces @grpc/* stubs with HTTP calls to the REST GameService and
// ValidationService you already have running in Python.
//
// ENV VARS (with sensible defaults):
//   GAME_BASE=http://game-server-service:50051
//   VALIDATION_BASE=http://validation-server-service:50052
//   PORT=8080
//
// Run:
//   npm i express cors swagger-ui-express swagger-jsdoc axios
//   node server.rest.js

const express = require('express');
const path = require('path');
const swaggerUi = require('swagger-ui-express');
const swaggerJSDoc = require('swagger-jsdoc');
const cors = require('cors');
const axios = require('axios');

const GAME_BASE = process.env.GAME_BASE || 'http://game-server-service:50051';
const VALIDATION_BASE = process.env.VALIDATION_BASE || 'http://validation-server-service:50052';
const PORT = process.env.PORT || 8080;

const swaggerDefinition = {
  openapi: '3.0.0',
  info: {
    title: 'Bingo API Gateway (REST → REST)',
    version: '1.0.0',
    description: 'Gateway HTTP que encaminha requisições REST para os serviços REST Python (FastAPI).',
  },
  servers: [
    { url: `http://localhost:${PORT}`, description: 'Servidor local' },
    { url: 'http://bingo-api:80', description: 'Ingress' },
  ],
};

const options = {
  swaggerDefinition,
  apis: [path.join(__dirname, './server.rest.js')],
};

const swaggerSpec = swaggerJSDoc(options);

// ======================
// CONFIGURAÇÃO DO SERVIDOR HTTP
// ======================
const app = express();

const corsOptions = {
  origin: '*',
  methods: 'GET,POST,DELETE',
  allowedHeaders: ['Content-Type', 'Authorization'],
};

app.use(cors(corsOptions));
app.use(express.json());
app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// Small helper for forwarding
async function forward(method, url, payload, res) {
  try {
    const r = await axios({ method, url, data: payload, validateStatus: () => true });
    // Pass through status and data
    return res.status(r.status || 200).json(r.data);
  } catch (err) {
    console.error('Erro ao encaminhar requisição:', err.message);
    return res.status(502).json({ error: 'Bad gateway', detail: err.message });
  }
}

// ======================
// ENDPOINTS HTTP → REST PYTHON SERVICES
// ======================

// Criar jogo
/**
 * @openapi
 * /create-game:
 *   post:
 *     summary: Cria um novo jogo de bingo
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               game_name:
 *                 type: string
 *                 example: "Bingo do Da UnB"
 *     responses:
 *       200:
 *         description: Jogo criado com sucesso
 */
app.post('/create-game', async (req, res) => {
  const { game_name } = req.body || {};
  return forward('post', `${GAME_BASE}/games`, { game_name }, res);
});

// Registrar jogador
/**
 * @openapi
 * /register-player:
 *   post:
 *     summary: Registra um jogador em um jogo existente
 *     description: Cria um jogador vinculado a um jogo existente, gerando seu cartão de bingo.
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               game_id:
 *                 type: string
 *                 example: "abc123"
 *               player_name:
 *                 type: string
 *                 example: "Pedro"
 *     responses:
 *       200:
 *         description: Jogador registrado com sucesso
 */
app.post('/register-player', async (req, res) => {
  const { game_id, player_name } = req.body || {};
  if (!game_id) return res.status(400).json({ error: 'game_id é obrigatório' });
  return forward('post', `${GAME_BASE}/games/${encodeURIComponent(game_id)}/players`, { player_name }, res);
});

// Sortear número
/**
 * @openapi
 * /draw-number:
 *   post:
 *     summary: Sorteia um número no jogo de bingo
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               game_id:
 *                 type: string
 *                 example: "abc123"
 *     responses:
 *       200:
 *         description: Número sorteado com sucesso
 */
app.post('/draw-number', async (req, res) => {
  const { game_id } = req.body || {};
  if (!game_id) return res.status(400).json({ error: 'game_id é obrigatório' });
  return forward('post', `${GAME_BASE}/games/${encodeURIComponent(game_id)}/draw`, {}, res);
});

// Marcar número
/**
 * @openapi
 * /mark-number:
 *   post:
 *     summary: Marca um número no cartão do jogador
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               player_id:
 *                 type: string
 *                 example: "p1"
 *               number:
 *                 type: integer
 *                 example: 42
 *     responses:
 *       200:
 *         description: Número marcado com sucesso
 */
app.post('/mark-number', async (req, res) => {
  const { player_id, number } = req.body || {};
  if (!player_id) return res.status(400).json({ error: 'player_id é obrigatório' });
  return forward('post', `${GAME_BASE}/players/${encodeURIComponent(player_id)}/mark`, { number }, res);
});

// Verificar bingo
/**
 * @openapi
 * /check-bingo:
 *   post:
 *     summary: Verifica se o jogador completou um bingo
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               game_id:
 *                 type: string
 *               player_id:
 *                 type: string
 *     responses:
 *       200:
 *         description: Resultado da verificação de bingo
 */
app.post('/check-bingo', async (req, res) => {
  const { game_id, player_id } = req.body || {};
  if (!game_id) return res.status(400).json({ error: 'game_id é obrigatório' });
  if (!player_id) return res.status(400).json({ error: 'player_id é obrigatório' });
  const url = `${GAME_BASE}/games/${encodeURIComponent(game_id)}/bingo?player_id=${encodeURIComponent(player_id)}`;
  return forward('get', url, undefined, res);
});

// Validation: validate-number
/**
 * @openapi
 * /validate-number:
 *   post:
 *     summary: Valida se um número pertence ao cartão do jogador
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               player_id:
 *                 type: string
 *               number:
 *                 type: integer
 *     responses:
 *       200:
 *         description: Resultado da validação do número
 */
app.post('/validate-number', async (req, res) => {
  const { player_id, number } = req.body || {};
  return forward('post', `${VALIDATION_BASE}/validate-number`, { player_id, number }, res);
});

// Validation: validate-bingo
/**
 * @openapi
 * /validate-bingo:
 *   post:
 *     summary: Valida se a combinação de números constitui um bingo
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               player_id:
 *                 type: string
 *               numbers:
 *                 type: array
 *                 items:
 *                   type: integer
 *     responses:
 *       200:
 *         description: Resultado da validação do bingo
 */
app.post('/validate-bingo', async (req, res) => {
  const { player_id, numbers } = req.body || {};
  return forward('post', `${VALIDATION_BASE}/validate-bingo`, { player_id, numbers }, res);
});

// Validation: get-card
/**
 * @openapi
 * /get-card:
 *   post:
 *     summary: Obtém o cartão do jogador
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               player_id:
 *                 type: string
 *     responses:
 *       200:
 *         description: Cartão retornado com sucesso
 */
app.post('/get-card', async (req, res) => {
  const { player_id } = req.body || {};
  if (!player_id) return res.status(400).json({ error: 'player_id é obrigatório' });
  return forward('get', `${VALIDATION_BASE}/card/${encodeURIComponent(player_id)}`, undefined, res);
});

// Validation: register-card
/**
 * @openapi
 * /register-card:
 *   post:
 *     summary: Registra manualmente um cartão de bingo
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               player_id:
 *                 type: string
 *               card_numbers:
 *                 type: array
 *                 items:
 *                   type: integer
 *     responses:
 *       200:
 *         description: Cartão registrado com sucesso
 */
app.post('/register-card', async (req, res) => {
  const { player_id, card_numbers } = req.body || {};
  return forward('post', `${VALIDATION_BASE}/register-card`, { player_id, card_numbers }, res);
});

// Health of gateway (and optional pass-through checks)
app.get('/healthz', async (req, res) => {
  try {
    const [game, val] = await Promise.all([
      axios.get(`${GAME_BASE}/healthz`).catch(() => ({ data: { status: 'down' } })),
      axios.get(`${VALIDATION_BASE}/healthz`).catch(() => ({ data: { status: 'down' } })),
    ]);
    res.json({ gateway: 'ok', game: game.data, validation: val.data });
  } catch (e) {
    res.json({ gateway: 'ok' });
  }
});

// ======================
// INICIA O SERVIDOR
// ======================
app.listen(PORT, () => {
  console.log(`🌐 Servidor HTTP rodando em http://localhost:${PORT}`);
  console.log(`→ Encaminhando requisições REST para GAME_BASE=${GAME_BASE} e VALIDATION_BASE=${VALIDATION_BASE}`);
});

