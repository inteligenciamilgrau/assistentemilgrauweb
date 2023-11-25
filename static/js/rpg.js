const TILESIZE = 32;
const PLAYER_SPEED = 4;
const TILE_SPEED = TILESIZE;
const FPS = 60;
const keys = {};

const tilemap = [
    'BBBBBBBBBBBBBBBBBBBB',
    'B..............B...B',
    'B..............B...B',
    'B.......BB........MB',
    'B..................B',
    'B..............B...B',
    'B.........BB...BBBBB',
    'B..................B',
    'B...BBBB...........B',
    'B..................B',
    'B...........B......B',
    'BB..BB......B......B',
    'B....B.............B',
    'B.H..B.............B',
    'BBBBBBBBBBBBBBBBBBBBXP',
];

// Encontra a coordenada de uma letra no mapa
function findPosition(tilemap, targetLetter) {
    let position = null;

    for (let i = 0; i < tilemap.length; i++) {
        for (let j = 0; j < tilemap[i].length; j++) {
            if (tilemap[i][j] === targetLetter) {
                position = { col: j, row: i };
            }
        }
    }

    return position;
}

const casaPosition = findPosition(tilemap, "H");
const mercadoPosition = findPosition(tilemap, "M");

// para randomizar posicao de um elemento no mapa
function getRandomPosition() {
    let x, y;
    do {
        x = Math.floor(Math.random() * tilemap[0].length);
        y = Math.floor(Math.random() * tilemap.length);
    } while (tilemap[y][x] === 'B'); // para evitar de criar um objeto em cima de uma parede ("B" de block)
    return { x, y };
}

function getRandomDirection() {
        const directions = ['left', 'right', 'up', 'down'];
        const randomIndex = Math.floor(Math.random() * directions.length);
        return directions[randomIndex];
}

let playerX = 2;
let playerY = 2;

let position = getRandomPosition();
let xPosition = position.x * TILESIZE;
let yPosition = position.y * TILESIZE;

document.addEventListener('keydown', function (e) {
    keys[e.keyCode] = true;
});

document.addEventListener('keyup', function (e) {
    keys[e.keyCode] = false;
});

const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

const playerSpritesheet = new Image();
playerSpritesheet.src = "static/img/character.png";

const atendenteMercadoSpritesheet = new Image();
atendenteMercadoSpritesheet.src = "static/img/enemy.png";

const terrainSpritesheet = new Image();
terrainSpritesheet.src = "static/img/terrain.png";

const casaSpritesheet = new Image();
casaSpritesheet.src = "static/img/casa.png";

const mercadoSpritesheet = new Image();
mercadoSpritesheet.src = "static/img/mercado.png";

class Sprite {
    constructor(image, x, y, width, height) {
        this.image = image;
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
    }

    draw(ctx, x, y) {
        ctx.drawImage(this.image, this.x, this.y, this.width, this.height, x, y, TILESIZE, TILESIZE);
    }
}

class Player {
    constructor(x, y, name) {
        this.x = x * TILESIZE;
        this.y = y * TILESIZE;
        this.width = TILESIZE;
        this.height = TILESIZE;
        this.facing = 'down';
        this.animationLoop = 1;
        this.name = name;
        this.ouro_coletado = 0;
        this.playerSprite = new Sprite(playerSpritesheet, 3 + (0 * TILESIZE), 2 + (0 * TILESIZE), this.width, this.height);
        this.coordinates = {col: Math.floor(this.x/TILESIZE), row: Math.floor(this.y/TILESIZE)};
        this.local = "Origem";
    }

    animateSprite(xSprite, ySprite){
        return new Sprite(playerSpritesheet, 3 + (xSprite * TILESIZE), 2 + (ySprite * TILESIZE), this.width, this.height);
    }

    draw(ctx) {
        this.playerSprite.draw(ctx, this.x, this.y);
    }

    update() {
        this.movement();
        this.animate();
        this.coordinates = {col: Math.floor(player.x/TILESIZE), row: Math.floor(player.y/TILESIZE)};
    }

    movement() {
        const originalX = this.x;
        const originalY = this.y;

        if (keys[37]) {  // Left arrow key
            this.x -= PLAYER_SPEED;
            this.facing = 'left';
        }
        if (keys[39]) {  // Right arrow key
            this.x += PLAYER_SPEED;
            this.facing = 'right';
        }
        if (keys[38]) {  // Up arrow key
            this.y -= PLAYER_SPEED;
            this.facing = 'up';
        }
        if (keys[40]) {  // Down arrow key
            this.y += PLAYER_SPEED;
            this.facing = 'down';
        }

        //console.log(Math.floor(this.x/TILESIZE), Math.floor(this.y/TILESIZE));

        // Check for collisions with blocks after movement
        this.collideBlocks(originalX, originalY);
    }

    movement_digital(mov) {
        const originalX = this.x;
        const originalY = this.y;

        if (mov == "Left") {  // Left arrow key
            this.x -= TILE_SPEED;
            this.facing = 'left';
        }
        if (mov == "Right") {  // Right arrow key
            this.x += TILE_SPEED;
            this.facing = 'right';
        }
        if (mov == "Up") {  // Up arrow key
            this.y -= TILE_SPEED;
            this.facing = 'up';
        }
        if (mov == "Down") {  // Down arrow key
            this.y += TILE_SPEED;
            this.facing = 'down';
        }

        // Check for collisions with blocks after movement
        this.collideBlocks(originalX, originalY);
    }

    collideBlocks(originalX, originalY) {
        for (let i = 0; i < tilemap.length; i++) {
            for (let j = 0; j < tilemap[i].length; j++) {
                const tile = tilemap[i][j];
                const x = j * TILESIZE;
                const y = i * TILESIZE;

                if (tile === 'B') {
                    if (
                        this.x < x + TILESIZE &&
                        this.x + this.width > x &&
                        this.y < y + TILESIZE &&
                        this.y + this.height > y
                    ) {
                        this.x = originalX;
                        this.y = originalY;
                    }
                } else if (tile === 'X') {
                    if (
                        this.x < xPosition + TILESIZE &&
                        this.x + this.width > xPosition &&
                        this.y < yPosition + TILESIZE &&
                        this.y + this.height > yPosition
                    ) {
                        // Respawn 'X' to a new random position
                        position = position = getRandomPosition();
                        xPosition = position.x * TILESIZE;
                        yPosition = position.y * TILESIZE;
                        gold.x = xPosition;
                        gold.y = yPosition;
                        //console.log(tilemap);
                        this.ouro_coletado += 1;
                        //console.log("ORO");
                    }
                }
            }
        }
    }
    animate(){
        let up_animations = [];
        let down_animations = [];
        let left_animations = [];
        let right_animations = [];

        if(this.facing == "up"){
            this.playerSprite = this.animateSprite(0, 1);
        }
        else if(this.facing == "down"){
            this.playerSprite = this.animateSprite(0, 0);
        }
        else if(this.facing == "left"){
            this.playerSprite = this.animateSprite(0, 3);
        }
        else if(this.facing == "right"){
            this.playerSprite = this.animateSprite(0, 2);
        }
    }
}

const player = new Player(playerX, playerY, "Maria");

class Gold {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.width = TILESIZE;
        this.height = TILESIZE;
    }

    draw() {
        const groundSprite = new Sprite(terrainSpritesheet, 18 * TILESIZE, 13 * TILESIZE, this.width, this.height);
        groundSprite.draw(ctx, this.x, this.y);
    }
}

const gold = new Gold(xPosition, yPosition);

class Lugares {
    constructor(x, y, lugarSpritesheet) {
        this.x = x;
        this.y = y;
        this.width = TILESIZE;
        this.height = TILESIZE;
        this.lugarSpritesheet = lugarSpritesheet;
    }

    draw() {
        ctx.drawImage(this.lugarSpritesheet, 0, 0, 64, 64, this.x, this.y, 64, 64);
    }
}

const casa = new Lugares(1 * 32, 9 * 32, casaSpritesheet);
const mercadinho = new Lugares(13 * 32, 1 * 32, mercadoSpritesheet);

class Personagens {
    constructor(nome, x, y, personagemSpritesheet) {
        this.nome = nome;
        this.x = x;
        this.y = y;
        this.width = TILESIZE;
        this.height = TILESIZE;
        this.spriteSheet = personagemSpritesheet;
        this.facing = "down";
        this.personagemSprite = new Sprite(this.spriteSheet, 0 * TILESIZE, 0 * TILESIZE, 32, 32);
        this.colidiu = false;
    }

    draw() {
        //const personagemSprite = new Sprite(this.spriteSheet, 0 * TILESIZE, 0 * TILESIZE, 32, 32);
        //personagemSprite.draw(ctx, 17 * TILESIZE, 1 * TILESIZE);
        this.personagemSprite.draw(ctx, this.x, this.y);
    }

    update() {
        this.movement_digital(getRandomDirection());
    }

    movement_digital(mov) {
        const originalX = this.x;
        const originalY = this.y;

        if (mov == "left") {  // Left arrow key
            this.x -= TILE_SPEED;
            this.facing = 'left';
        }
        if (mov == "right") {  // Right arrow key
            this.x += TILE_SPEED;
            this.facing = 'right';
        }
        if (mov == "up") {  // Up arrow key
            this.y -= TILE_SPEED;
            this.facing = 'up';
        }
        if (mov == "down") {  // Down arrow key
            this.y += TILE_SPEED;
            this.facing = 'down';
        }

        // Check for collisions with blocks after movement
        this.collideBlocks(originalX, originalY);
    }

    collideBlocks(originalX, originalY) {
        for (let i = 0; i < tilemap.length; i++) {
            for (let j = 0; j < tilemap[i].length; j++) {
                const tile = tilemap[i][j];
                const x = j * TILESIZE;
                const y = i * TILESIZE;

                if (tile === 'B') {
                    if (
                        this.x < x + TILESIZE &&
                        this.x + this.width > x &&
                        this.y < y + TILESIZE &&
                        this.y + this.height > y
                    ) {
                        this.x = originalX;
                        this.y = originalY;
                    }
                }
            }
        }
        if(originalX >= (player.x - TILESIZE) && originalX <= (player.x + TILESIZE) &&
        originalY >= (player.y - TILESIZE) && originalY <= (player.y + TILESIZE)){
            this.x = originalX;
            this.y = originalY;
            this.colidiu = true;
        }else{
            this.colidiu = false;
        }
    }
}

const atendenteMercado = new Personagens("João", 17 * TILESIZE, 1 * TILESIZE, atendenteMercadoSpritesheet);

class Block {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.width = TILESIZE;
        this.height = TILESIZE;
    }

    draw() {
        const blockSprite = new Sprite(terrainSpritesheet, 30 * TILESIZE, 14 * TILESIZE, this.width, this.height);
        blockSprite.draw(ctx, this.x, this.y);
    }
}

class Ground {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.width = TILESIZE;
        this.height = TILESIZE;
    }

    draw() {
        const groundSprite = new Sprite(terrainSpritesheet, 2 * TILESIZE, 11 * TILESIZE, this.width, this.height);
        groundSprite.draw(ctx, this.x, this.y);
    }
}

function drawTilemap() {
    for (let i = 0; i < tilemap.length; i++) {
        for (let j = 0; j < tilemap[i].length; j++) {
            const tile = tilemap[i][j];
            const x = j * TILESIZE;
            const y = i * TILESIZE;

            const grass = new Ground(x, y);
            grass.draw();

            if (tile === 'B')
            {
                const block = new Block(x, y);
                block.draw();
            }
            else if (tile === 'P')
            {
                player.draw(ctx);
            }
            else if (tile === 'X')
            {
                gold.draw(ctx);
            }
            casa.draw(ctx);
            mercadinho.draw(ctx);
        }
    }
    atendenteMercado.draw(ctx);
}

function update() {
    player.update();
}

function update_personagens(){
    atendenteMercado.update();
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawTilemap();

    const objetivo_completo = document.getElementById('objetivo_completo');
    objetivo_completo.textContent = 'Coletou: ' + player.ouro_coletado;

    const conversar = document.getElementById('conversar');
    if(atendenteMercado.colidiu){
        conversar.textContent = 'Conversar: ' + atendenteMercado.nome;
    }else{
        conversar.textContent = 'Conversar: ' + "Ninguém";
    }


    const localPlayer = document.getElementById('localPlayer');
    if(player.coordinates.row >= (mercadoPosition.row - 2) && player.coordinates.row <= (mercadoPosition.row + 2) &&
    player.coordinates.col >= (mercadoPosition.col -2) && player.coordinates.col <= (mercadoPosition.col +2)){
        localPlayer.textContent = 'Local: Mercado';
        player.local = "Mercado";
    }
    else if(player.coordinates.row >= (casaPosition.row - 2) && player.coordinates.row <= (casaPosition.row + 2) &&
    player.coordinates.col >= (casaPosition.col -2) && player.coordinates.col <= (casaPosition.col +2)){
        localPlayer.textContent = 'Local: Casa';
        player.local = "Casa";
    }
    else
    {
        localPlayer.textContent = 'Local: Por aí';
        player.local = "Por aí";
    }
}

setInterval(function () {
    update();
    draw();
}, 1000 / FPS);

setInterval(function () {
    update_personagens();
}, 1000);

function sendTilemapToFlask() {
    conversar = "";
    if(atendenteMercado.colidiu){
        conversar = atendenteMercado.nome;
    }
    // Use the Fetch API to send a POST request to Flask
    fetch('/update_tilemap', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ tilemap: tilemap,
            player_coord_x: Math.floor(player.x/TILESIZE),
            player_coord_y: Math.floor(player.y/TILESIZE),
            gold_x: Math.floor(gold.x/TILESIZE),
            gold_y: Math.floor(gold.y/TILESIZE),
            atend_x: Math.floor(atendenteMercado.x/TILESIZE),
            atend_y: Math.floor(atendenteMercado.y/TILESIZE),
            local: player.local,
            ouro: player.ouro_coletado,
            conversar: conversar
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data["move"].length > 0) {
            //console.log(data["move"][0]);
            JSON.parse(data["move"]).forEach(direction => {
                player.movement_digital(direction);
                });
        }
    })
    .catch(error => console.error('Error:', error));
}

setInterval(function () {
    sendTilemapToFlask()
}, 300);

