// Игра "Змейка"
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// Константы
const GRID_SIZE = 20;
const CELL_SIZE = canvas.width / GRID_SIZE;
const INITIAL_SPEED = 150;
const SPEED_INCREASE = 5;

// Цвета (из палитры сайта)
const COLORS = {
    snake: '#667eea',
    snakeHead: '#764ba2',
    food: '#ff6b6b',
    grid: '#e0e0e0',
    background: '#f5f5f5'
};

// Состояние игры
let snake = [];
let food = {};
let direction = { x: 1, y: 0 };
let nextDirection = { x: 1, y: 0 };
let score = 0;
let highScore = localStorage.getItem('snakeHighScore') || 0;
let gameLoop = null;
let isPlaying = false;
let isPaused = false;
let speed = INITIAL_SPEED;

// Элементы DOM
const scoreElement = document.getElementById('score');
const highScoreElement = document.getElementById('highScore');
const finalScoreElement = document.getElementById('finalScore');
const gameOverElement = document.getElementById('gameOver');
const startBtn = document.getElementById('startBtn');
const pauseBtn = document.getElementById('pauseBtn');
const restartBtn = document.getElementById('restartBtn');

// Инициализация
function init() {
    // Начальная позиция змейки
    snake = [
        { x: 10, y: 10 },
        { x: 9, y: 10 },
        { x: 8, y: 10 }
    ];
    
    direction = { x: 1, y: 0 };
    nextDirection = { x: 1, y: 0 };
    score = 0;
    speed = INITIAL_SPEED;
    
    updateScore();
    spawnFood();
    draw();
}

// Генерация еды
function spawnFood() {
    let validPosition = false;
    
    while (!validPosition) {
        food = {
            x: Math.floor(Math.random() * GRID_SIZE),
            y: Math.floor(Math.random() * GRID_SIZE)
        };
        
        // Проверяем что еда не на змейке
        validPosition = !snake.some(segment => 
            segment.x === food.x && segment.y === food.y
        );
    }
}

// Отрисовка
function draw() {
    // Очистка canvas
    ctx.fillStyle = COLORS.background;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Сетка
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth = 1;
    for (let i = 0; i <= GRID_SIZE; i++) {
        ctx.beginPath();
        ctx.moveTo(i * CELL_SIZE, 0);
        ctx.lineTo(i * CELL_SIZE, canvas.height);
        ctx.stroke();
        
        ctx.beginPath();
        ctx.moveTo(0, i * CELL_SIZE);
        ctx.lineTo(canvas.width, i * CELL_SIZE);
        ctx.stroke();
    }
    
    // Змейка
    snake.forEach((segment, index) => {
        ctx.fillStyle = index === 0 ? COLORS.snakeHead : COLORS.snake;
        ctx.fillRect(
            segment.x * CELL_SIZE + 1,
            segment.y * CELL_SIZE + 1,
            CELL_SIZE - 2,
            CELL_SIZE - 2
        );
        
        // Глаза для головы
        if (index === 0) {
            ctx.fillStyle = 'white';
            const eyeSize = CELL_SIZE / 6;
            const eyeOffset = CELL_SIZE / 4;
            
            if (direction.x !== 0) {
                // Горизонтальное движение
                ctx.fillRect(
                    segment.x * CELL_SIZE + eyeOffset,
                    segment.y * CELL_SIZE + eyeOffset,
                    eyeSize, eyeSize
                );
                ctx.fillRect(
                    segment.x * CELL_SIZE + eyeOffset,
                    segment.y * CELL_SIZE + CELL_SIZE - eyeOffset - eyeSize,
                    eyeSize, eyeSize
                );
            } else {
                // Вертикальное движение
                ctx.fillRect(
                    segment.x * CELL_SIZE + eyeOffset,
                    segment.y * CELL_SIZE + eyeOffset,
                    eyeSize, eyeSize
                );
                ctx.fillRect(
                    segment.x * CELL_SIZE + CELL_SIZE - eyeOffset - eyeSize,
                    segment.y * CELL_SIZE + eyeOffset,
                    eyeSize, eyeSize
                );
            }
        }
    });
    
    // Еда
    ctx.fillStyle = COLORS.food;
    ctx.beginPath();
    ctx.arc(
        food.x * CELL_SIZE + CELL_SIZE / 2,
        food.y * CELL_SIZE + CELL_SIZE / 2,
        CELL_SIZE / 2 - 2,
        0,
        Math.PI * 2
    );
    ctx.fill();
    
    // Блик на еде
    ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
    ctx.beginPath();
    ctx.arc(
        food.x * CELL_SIZE + CELL_SIZE / 2 - CELL_SIZE / 6,
        food.y * CELL_SIZE + CELL_SIZE / 2 - CELL_SIZE / 6,
        CELL_SIZE / 6,
        0,
        Math.PI * 2
    );
    ctx.fill();
}

// Обновление игры
function update() {
    if (!isPlaying || isPaused) return;
    
    // Применяем следующее направление
    direction = { ...nextDirection };
    
    // Новая позиция головы
    const head = {
        x: snake[0].x + direction.x,
        y: snake[0].y + direction.y
    };
    
    // Проверка столкновения со стенами
    if (head.x < 0 || head.x >= GRID_SIZE || head.y < 0 || head.y >= GRID_SIZE) {
        gameOver();
        return;
    }
    
    // Проверка столкновения с собой
    if (snake.some(segment => segment.x === head.x && segment.y === head.y)) {
        gameOver();
        return;
    }
    
    // Добавляем новую голову
    snake.unshift(head);
    
    // Проверка поедания еды
    if (head.x === food.x && head.y === food.y) {
        score += 10;
        updateScore();
        spawnFood();
        
        // Увеличиваем скорость
        if (speed > 50) {
            speed -= SPEED_INCREASE;
            clearInterval(gameLoop);
            gameLoop = setInterval(update, speed);
        }
    } else {
        // Убираем хвост
        snake.pop();
    }
    
    draw();
}

// Обновление счёта
function updateScore() {
    scoreElement.textContent = score;
    highScoreElement.textContent = highScore;
    
    if (score > highScore) {
        highScore = score;
        localStorage.setItem('snakeHighScore', highScore);
        highScoreElement.textContent = highScore;
    }
}

// Конец игры
function gameOver() {
    isPlaying = false;
    clearInterval(gameLoop);
    
    finalScoreElement.textContent = score;
    gameOverElement.classList.remove('hidden');
    startBtn.classList.remove('hidden');
    pauseBtn.classList.add('hidden');
}

// Начать игру
function startGame() {
    if (isPlaying) return;
    
    init();
    isPlaying = true;
    isPaused = false;
    gameOverElement.classList.add('hidden');
    startBtn.classList.add('hidden');
    pauseBtn.classList.remove('hidden');
    
    gameLoop = setInterval(update, speed);
}

// Пауза
function togglePause() {
    if (!isPlaying) return;
    
    isPaused = !isPaused;
    pauseBtn.textContent = isPaused ? '▶️ Продолжить' : '⏸️ Пауза';
}

// Управление
function handleKeyPress(e) {
    // Предотвращаем прокрутку страницы
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'w', 'a', 's', 'd'].includes(e.key)) {
        e.preventDefault();
    }
    
    if (!isPlaying || isPaused) return;
    
    switch(e.key) {
        case 'ArrowUp':
        case 'w':
        case 'W':
            if (direction.y === 0) {
                nextDirection = { x: 0, y: -1 };
            }
            break;
        case 'ArrowDown':
        case 's':
        case 'S':
            if (direction.y === 0) {
                nextDirection = { x: 0, y: 1 };
            }
            break;
        case 'ArrowLeft':
        case 'a':
        case 'A':
            if (direction.x === 0) {
                nextDirection = { x: -1, y: 0 };
            }
            break;
        case 'ArrowRight':
        case 'd':
        case 'D':
            if (direction.x === 0) {
                nextDirection = { x: 1, y: 0 };
            }
            break;
        case ' ':
            togglePause();
            break;
    }
}

// Обработчики событий
startBtn.addEventListener('click', startGame);
pauseBtn.addEventListener('click', togglePause);
restartBtn.addEventListener('click', startGame);
document.addEventListener('keydown', handleKeyPress);

// Инициализация при загрузке
highScoreElement.textContent = highScore;
init();
