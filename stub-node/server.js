
const express = require('express');
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const path = require('path');
const swaggerUi = require('swagger-ui-express');
const swaggerJSDoc = require('swagger-jsdoc');

const swaggerDefinition = {
  openapi: '3.0.0',
  info: {
    title: 'Bingo API Gateway',
    version: '1.0.0',
    description: 'Gateway HTTP que encaminha requisições REST para o servidor gRPC Python',
  },
  servers: [
    { url: 'http://localhost:8080', description: 'Servidor local' },
    { url: 'http://bingo-api:80', description: 'Ingress' },
  ],
};

const options = {
  swaggerDefinition,
  apis: ['./server.js'], // Arquivo com as anotações dos endpoints
};

const swaggerSpec = swaggerJSDoc(options);

const PROTO_PATH = path.join(__dirname, './proto/bingo.proto');

const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
});

const bingoProto = grpc.loadPackageDefinition(packageDefinition).bingo;

// Cria os stubs gRPC (clientes)
const gameClient = new bingoProto.GameService('game-server-service:50051', grpc.credentials.createInsecure());
const validationClient = new bingoProto.ValidationService('validation-server-service:50052', grpc.credentials.createInsecure());

// ======================
// CONFIGURAÇÃO DO SERVIDOR HTTP
// ======================
const app = express();
app.use(express.json());

app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// ======================
// ENDPOINTS HTTP → CHAMADAS gRPC
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
app.post('/create-game', (req, res) => {
  const { game_name } = req.body;

  gameClient.CreateGame({ game_name }, (err, response) => {
    if (err) {
      console.error('Erro no gRPC:', err);
      return res.status(500).json({ error: err.message });
    }
    res.json(response);
  });
});

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
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 player_id:
 *                   type: string
 *                   example: "p1"
 *                 card_numbers:
 *                   type: array
 *                   items:
 *                     type: integer
 *                   example: [5, 12, 34, 48, 71]
 *                 success:
 *                   type: boolean
 *                   example: true
 */
app.post('/register-player', (req, res) => {
  const { game_id, player_name } = req.body;

  gameClient.RegisterPlayer({ game_id, player_name }, (err, response) => {
    if (err) {
      console.error('Erro no gRPC:', err);
      return res.status(500).json({ error: err.message });
    }
    res.json(response);
  });
});

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
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 player_id:
 *                   type: string
 *                   example: "p1"
 *                 card_numbers:
 *                   type: array
 *                   items:
 *                     type: integer
 *                   example: [5, 12, 34, 48, 71]
 *                 success:
 *                   type: boolean
 *                   example: true
 */

/**
 * @openapi
 * /draw-number:
 *   post:
 *     summary: Sorteia um número no jogo de bingo
 *     description: Solicita ao servidor gRPC o sorteio de um novo número.
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
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 number:
 *                   type: integer
 *                   example: 42
 *                 success:
 *                   type: boolean
 *                   example: true
 */

app.post('/draw-number', (req, res) => {
  const { game_id } = req.body;

  gameClient.DrawNumber({ game_id }, (err, response) => {
    if (err) {
      console.error('Erro no gRPC:', err);
      return res.status(500).json({ error: err.message });
    }
    res.json(response);
  });
});

/**
 * @openapi
 * /mark-number:
 *   post:
 *     summary: Marca um número no cartão do jogador
 *     description: Marca um número sorteado no cartão do jogador específico.
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
 *               player_id:
 *                 type: string
 *                 example: "p1"
 *               number:
 *                 type: integer
 *                 example: 42
 *     responses:
 *       200:
 *         description: Número marcado com sucesso
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                   example: true
 */
app.post('/mark-number', (req, res) => {
  const { game_id, player_id, number } = req.body;

  gameClient.MarkNumber({ game_id, player_id, number }, (err, response) => {
    if (err) {
      console.error('Erro no gRPC:', err);
      return res.status(500).json({ error: err.message });
    }
    res.json(response);
  });
});

/**
 * @openapi
 * /check-bingo:
 *   post:
 *     summary: Verifica se o jogador completou um bingo
 *     description: Retorna verdadeiro caso o jogador tenha completado um bingo válido.
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
 *               player_id:
 *                 type: string
 *                 example: "p1"
 *     responses:
 *       200:
 *         description: Resultado da verificação de bingo
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 bingo:
 *                   type: boolean
 *                   example: false
 */
app.post('/check-bingo', (req, res) => {
  const { game_id, player_id } = req.body;

  gameClient.CheckBingo({ game_id, player_id }, (err, response) => {
    if (err) {
      console.error('Erro no gRPC:', err);
      return res.status(500).json({ error: err.message });
    }
    res.json(response);
  });
});

/**
 * @openapi
 * /validate-number:
 *   post:
 *     summary: Valida se um número pertence ao cartão do jogador
 *     description: Verifica se o número informado existe no cartão do jogador.
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
 *         description: Resultado da validação do número
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                   example: true
 */
app.post('/validate-number', (req, res) => {
  const { player_id, number } = req.body;

  validationClient.ValidateNumber({ player_id, number }, (err, response) => {
    if (err) {
      console.error('Erro no gRPC:', err);
      return res.status(500).json({ error: err.message });
    }
    res.json(response);
  });
});

/**
 * @openapi
 * /validate-bingo:
 *   post:
 *     summary: Valida se a combinação de números constitui um bingo
 *     description: Recebe uma lista de números e valida se representam um bingo válido.
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
 *               numbers:
 *                 type: array
 *                 items:
 *                   type: integer
 *                 example: [5, 12, 34, 48, 71]
 *     responses:
 *       200:
 *         description: Resultado da validação do bingo
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 bingo:
 *                   type: boolean
 *                   example: true
 */
app.post('/validate-bingo', (req, res) => {
  const { player_id, numbers } = req.body;

  validationClient.ValidateBingo({ player_id, numbers }, (err, response) => {
    if (err) {
      console.error('Erro no gRPC:', err);
      return res.status(500).json({ error: err.message });
    }
    res.json(response);
  });
});

/**
 * @openapi
 * /get-card:
 *   post:
 *     summary: Obtém o cartão do jogador
 *     description: Retorna os números atuais do cartão de bingo do jogador.
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
 *     responses:
 *       200:
 *         description: Cartão retornado com sucesso
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 card_numbers:
 *                   type: array
 *                   items:
 *                     type: integer
 *                   example: [1, 12, 34, 48, 70]
 */

app.post('/get-card', (req, res) => {
  const { player_id } = req.body;

  validationClient.GetCard({ player_id }, (err, response) => {
    if (err) {
      console.error('Erro no gRPC:', err);
      return res.status(500).json({ error: err.message });
    }
    res.json(response);
  });
});

/**
 * @openapi
 * /register-card:
 *   post:
 *     summary: Registra manualmente um cartão de bingo
 *     description: Permite associar um cartão personalizado a um jogador existente.
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
 *               card_numbers:
 *                 type: array
 *                 items:
 *                   type: integer
 *                 example: [3, 8, 19, 44, 67]
 *     responses:
 *       200:
 *         description: Cartão registrado com sucesso
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                   example: true
 */
app.post('/register-card', (req, res) => {
  const { player_id, card_numbers } = req.body;

  validationClient.RegisterCard({ player_id, card_numbers }, (err, response) => {
    if (err) {
      console.error('Erro no gRPC:', err);
      return res.status(500).json({ error: err.message });
    }
    res.json(response);
  });
});

// ======================
// INICIA O SERVIDOR
// ======================
const PORT = 8080;
app.listen(PORT, () => {
  console.log(`🌐 Servidor HTTP rodando em http://localhost:${PORT}`);
  console.log(`→ Encaminhando requisições para servidores gRPC Python`);
});
