document.addEventListener('DOMContentLoaded', () => {
    // Variáveis de estado global do jogo
    let GAME_ID = null;
    let PLAYER_ID = null;
    let ROUND_NUMBER = 0;
    const API_BASE_URL = 'http://bingo-api';

    // Referências aos elementos do DOM
    const startGameBtn = document.getElementById('start-game-btn');
    const drawBtn = document.getElementById('draw-btn');
    const gameIdSpan = document.getElementById('game-id');
    const playerIdSpan = document.getElementById('player-id');
    const roundNumberSpan = document.getElementById('round-number');
    const drawnNumberDiv = document.getElementById('drawn-number');
    const bingoCardBody = document.querySelector('#bingo-card tbody');
    const messageDiv = document.getElementById('message');
    const playerNameSpan = document.getElementById('player-name');

    const BINGO_COLUMNS = {
        'B': [1, 15],
        'I': [16, 30],
        'N': [31, 45],
        'G': [46, 60],
        'O': [61, 75]
    };
    const COLUMN_KEYS = ['B', 'I', 'N', 'G', 'O'];

    function displayMessage(msg, type) {
        messageDiv.textContent = msg;
        messageDiv.className = type;
        messageDiv.classList.remove('hidden');
        setTimeout(() => {
            messageDiv.classList.add('hidden');
        }, 5000);
    }

    function renderCard(cardNumbers) {
        bingoCardBody.innerHTML = '';
        
        const cardCells = cardNumbers;

        let middleIndex = Math.floor(cardNumbers.length / 2); 

        cardCells.splice(middleIndex, 0, 0);

        var freeRow = false;

        for (let i = 0; i < 5; i++) {
            const row = bingoCardBody.insertRow();
            for (let j = 0; j < 5; j++) {
                // Marcar o centro como "FREE" (3,3)
                const cell = row.insertCell();
                if (i === 2 && j === 2) {
                    cell.textContent = 'FREE';
                    cell.classList.add('marked');
                    cell.dataset.number = '0'; // Usar 0 para representar o free space
                    cell.removeEventListener('click', markNumber);
                }
                else{
                    const number = cardCells[i * 5 + j];
                    cell.textContent = number;
                    cell.dataset.number = number;
                    cell.addEventListener('click', () => markNumber(cell, number));
                }
            }
        }
    }

    async function startGame() {
        startGameBtn.disabled = true;
        displayMessage('Iniciando novo jogo...', 'success');

        try {
            // 1. Criar Jogo
            const createGameResponse = await fetch(`${API_BASE_URL}/create-game`, {
                method: 'POST',
                headers: { 
                    "accept": "*/*",
                    'Content-Type': 'application/json' 
                },
                body: JSON.stringify({ game_name: "Bingo Web" })
            });

            if (!createGameResponse.ok) throw new Error('Falha ao criar o jogo.');
            const gameData = await createGameResponse.json();
            GAME_ID = gameData.game_id;
            gameIdSpan.textContent = GAME_ID;
            
            // 2. Registrar Jogador
            const playerName = prompt('Digite seu nome para se registrar no jogo:', 'Jogador Web');
            if (!playerName) {
                gameIdSpan.textContent = 'N/A';
                startGameBtn.disabled = false;
                displayMessage('Registro cancelado.', 'error');
                return;
            }

            playerNameSpan.textContent = playerName;

            const registerResponse = await fetch(`${API_BASE_URL}/register-player`, {
                method: 'POST',
                headers: { 
                    'accept': 'application/json',
                    'Content-Type': 'application/json' 
                },
                body: JSON.stringify({ game_id: GAME_ID, player_name: playerName })
            });

            if (!registerResponse.ok) throw new Error('Falha ao registrar o jogador.');
            const playerData = await registerResponse.json();
            PLAYER_ID = playerData.player_id;
            playerIdSpan.textContent = PLAYER_ID;

            // 4. Renderizar Cartão
            renderCard(playerData.card);
            
            // 5. Atualizar UI
            drawBtn.disabled = false;
            startGameBtn.disabled = true;
            ROUND_NUMBER = 0;
            roundNumberSpan.textContent = ROUND_NUMBER;
            drawnNumberDiv.textContent = '?';
            displayMessage('Jogo iniciado! Cartão gerado com sucesso.', 'success');

        } catch (error) {
            console.error('Erro ao iniciar o jogo:', error);
            displayMessage(`Erro ao iniciar o jogo: ${error.message}`, 'error');
            startGameBtn.disabled = false;
        }
    }

    // Sorteia um novo número.
    async function drawNumber() {
        if (!GAME_ID) {
            displayMessage('Por favor, inicie um novo jogo primeiro.', 'error');
            return;
        }
        
        drawBtn.disabled = true;
        displayMessage('Sorteando número...', 'success');

        try {
            const response = await fetch(`${API_BASE_URL}/draw-number`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ game_id: GAME_ID })
            });

            if (!response.ok) throw new Error('Falha ao sortear o número.');
            const data = await response.json();
            
            if (data.success) {
                ROUND_NUMBER++;
                roundNumberSpan.textContent = ROUND_NUMBER;
                drawnNumberDiv.textContent = data.number;
                displayMessage(`Número sorteado: ${data.number}!`, 'success');
                
                // Realça o número sorteado no cartão do jogador, se existir.
                const cellToMark = document.querySelector(`td[data-number="${data.number}"]`);
                if (cellToMark && !cellToMark.classList.contains('marked')) {
                    cellToMark.classList.add('glow-on-draw'); // Adiciona classe para destaque visual temporário
                    setTimeout(() => {
                        cellToMark.classList.remove('glow-on-draw');
                    }, 1000);
                }

            } else {
                displayMessage('Erro: ' + (data.message || 'Não foi possível sortear o número.'), 'error');
            }

        } catch (error) {
            console.error('Erro ao sortear número:', error);
            displayMessage(`Erro na comunicação: ${error.message}`, 'error');
        } finally {
            drawBtn.disabled = false;
        }
    }

    async function markNumber(cell, number) {
        if (!GAME_ID || !PLAYER_ID) {
            displayMessage('Inicie um jogo antes de marcar um número.', 'error');
            return;
        }
        
        if (cell.classList.contains('marked')) {
            displayMessage('Este número já está marcado.', 'error');
            return;
        }

        if (parseInt(drawnNumberDiv.textContent) !== number) {
             displayMessage('Marque apenas o número que foi sorteado por último!', 'error');
             return;
        }

        try {
            const markResponse = await fetch(`${API_BASE_URL}/mark-number`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ game_id: GAME_ID, player_id: PLAYER_ID, number: number })
            });
            
            if (!markResponse.ok) throw new Error('Falha ao marcar o número no servidor.');
            const markData = await markResponse.json();

            if (markData.success) {
                // Marcar visualmente na UI
                cell.classList.add('marked');
                displayMessage(`Número ${number} marcado com sucesso!`, 'success');

                // Verificar Bingo
                await checkBingo();

            } else {
                 displayMessage('Erro ao marcar número: ' + (markData.message || 'Desconhecido'), 'error');
            }

        } catch (error) {
            console.error('Erro ao marcar número:', error);
            displayMessage(`Erro na comunicação: ${error.message}`, 'error');
        }
    }
    
    // Verifica se o jogador fez bingo.
    async function checkBingo() {
        try {
            const checkResponse = await fetch(`${API_BASE_URL}/check-bingo`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ game_id: GAME_ID, player_id: PLAYER_ID })
            });

            if (!checkResponse.ok) throw new Error('Falha ao verificar bingo.');
            const checkData = await checkResponse.json();
            
            if (checkData.bingo) {
                displayMessage('PARABÉNS! VOCÊ FEZ BINGO!', 'success');
                drawBtn.disabled = true;
            }

        } catch (error) {
            console.error('Erro ao verificar bingo:', error);
            displayMessage(`Erro ao verificar bingo: ${error.message}`, 'error');
        }
    }


    // Adiciona os event listeners
    startGameBtn.addEventListener('click', startGame);
    drawBtn.addEventListener('click', drawNumber);
});

// Adiciona estilos para o efeito de brilho ao sortear um número
const style = document.createElement('style');
style.textContent = `
    .glow-on-draw {
        animation: glow 0.5s 2 alternate;
    }
    @keyframes glow {
        from { box-shadow: 0 0 5px #ff8c00; }
        to { box-shadow: 0 0 20px #ff8c00, 0 0 30px #ff8c00; }
    }
`;
document.head.append(style);