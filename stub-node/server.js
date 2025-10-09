const express = require('express');
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const path = require('path');
const swaggerUi = require('swagger-ui-express');
const swaggerJSDoc = require('swagger-jsdoc');
const cors = require('cors');

const swaggerDefinition = {
  openapi: '3.0.0',
  info: {
    title: 'Bingo API Gateway',
    version: '1.0.0',
    description: 'Gateway HTTP que encaminha requisições REST para o servidor gRPC Python',
  },
  servers: [
    { url: 'http://localhost:8080', description: 'Servidor local' },
    { url: 'http://bingo-api', description: 'Ingress' },
  ],
};

const options = {
  swaggerDefinition,
  apis: ['./server.js'],
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

const app = express();

const corsOptions = {
  origin: '*',
  methods: 'GET,POST,DELETE',
  allowedHeaders: ['Content-Type', 'Authorization']
};

app.use(cors(corsOptions));
app.use(express.json());
app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// Health check
app.get('/', (req, res) => {
  res.json({ status: 'ok', service: 'Bingo API Gateway' });
});

// ===================================
// ENDPOINTS COMPATÍVEIS COM O TESTE
// ===================================

/**
 * @openapi
 * /game/create:
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
 *     responses:
 *       200:
 *         description: Jogo criado
 */
app.post('/game/create', (req, res) => {
  const { game_name } = req.body;
  gameClient.CreateGame({ game_name }, (err, response) => {
    if (err) {
      console.error('Erro no gRPC CreateGame:', err);
      return res.status(500).json({ success: false, error: err.message });
    }
    res.json({ success: true, game_id: response.game_id });
  });
});

/**
 * @openapi
 * /game/register:
 *   post:
 *     summary: Registra um jogador
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               game_id:
 *                 type: string
 *               player_name:
 *                 type: string
 *     responses:
 *       200:
 *         description: Jogador registrado
 */
app.post('/game/register', (req, res) => {
  const { game_id, player_name } = req.body;
  gameClient.RegisterPlayer({ game_id, player_name }, (err, response) => {
    if (err) {
      console.error('Erro no gRPC RegisterPlayer:', err);
      return res.status(500).json({ success: false, error: err.message });
    }
    res.json({
      success: response.success,
      player_id: response.player_id,
      card: response.card_numbers
    });
  });
});

/**
 * @openapi
 * /game/draw:
 *   post:
 *     summary: Sorteia um número
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               game_id:
 *                 type: string
 *     responses:
 *       200:
 *         description: Número sorteado
 */
app.post('/game/draw', (req, res) => {
  const { game_id } = req.body;
  gameClient.DrawNumber({ game_id }, (err, response) => {
    if (err) {
      console.error('Erro no gRPC DrawNumber:', err);
      return res.status(500).json({ success: false, error: err.message });
    }
    res.json({
      success: response.success,
      number: response.number
    });
  });
});

/**
 * @openapi
 * /game/mark:
 *   post:
 *     summary: Marca um número
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
 *               number:
 *                 type: integer
 *     responses:
 *       200:
 *         description: Número marcado
 */
app.post('/game/mark', (req, res) => {
  const { game_id, player_id, number } = req.body;
  gameClient.MarkNumber({ game_id, player_id, number }, (err, response) => {
    if (err) {
      console.error('Erro no gRPC MarkNumber:', err);
      return res.status(500).json({ success: false, error: err.message });
    }
    res.json({ success: response.success });
  });
});

/**
 * @openapi
 * /game/bingo:
 *   post:
 *     summary: Verifica bingo
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
 *         description: Resultado da verificação
 */
app.post('/game/bingo', (req, res) => {
  const { game_id, player_id } = req.body;
  gameClient.CheckBingo({ game_id, player_id }, (err, response) => {
    if (err) {
      console.error('Erro no gRPC CheckBingo:', err);
      return res.status(500).json({ bingo: false, error: err.message });
    }
    res.json({ bingo: response.bingo });
  });
});

/**
 * @openapi
 * /game/card:
 *   get:
 *     summary: Obtém cartela do jogador
 *     parameters:
 *       - name: player_id
 *         in: query
 *         required: true
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Cartela do jogador
 */
app.get('/game/card', (req, res) => {
  const { player_id } = req.query;
  validationClient.GetCard({ player_id }, (err, response) => {
    if (err) {
      console.error('Erro no gRPC GetCard:', err);
      return res.status(500).json({ card: [], error: err.message });
    }
    res.json({ card: response.card_numbers });
  });
});

// Mantém endpoints antigos para compatibilidade com Swagger
app.post('/create-game', (req, res) => req.app.handle({ ...req, url: '/game/create' }, res));
app.post('/register-player', (req, res) => req.app.handle({ ...req, url: '/game/register' }, res));
app.post('/draw-number', (req, res) => req.app.handle({ ...req, url: '/game/draw' }, res));
app.post('/mark-number', (req, res) => req.app.handle({ ...req, url: '/game/mark' }, res));
app.post('/check-bingo', (req, res) => req.app.handle({ ...req, url: '/game/bingo' }, res));

const PORT = 8080;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🌐 Servidor HTTP rodando em http://localhost:${PORT}`);
  console.log(`📚 Documentação disponível em http://localhost:${PORT}/docs`);
  console.log(`→ Encaminhando requisições para servidores gRPC Python`);
});
