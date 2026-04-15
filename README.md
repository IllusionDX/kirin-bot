# Kirin Bot

Un bot de Discord para mi servidor, principalmente para divertirse.

Está en desarrollo activo. Actualmente tiene:

### 🎮 Diversión
- **/akinator** - Juega al Akinator (adivina tu personaje)
- **/8ball** - Haz una pregunta sí/no a la bola mágica
- **/challenge** - Desafía a otros jugadores a un duelo
- **/coinflip** - Lanza una moneda (cara o cruz)
- **/rip** - Crea una tumba con dedicatoria
- **/roll** - Lanza dados. Soporta formatos: `20`, `2d6`, `d8`

### 🔍 Búsqueda
- **/derpibooru** - Busca imágenes en Derpibooru

### 🌤️ Utilidad
- **/weather** - Consulta el clima de una ciudad
- **/say** - Haz que el bot diga algo
- **/help** - Muestra la ayuda

## Requisitos

- Python 3.10+
- discord.py >= 2.7.0
- python-dotenv >= 1.0.0
- Pillow >= 10.0.0
- aiohttp >= 3.9.0
- akinator >= 2.0.0

## Instalación

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Crear archivo `.env`:
```
TOKEN=tu_token_del_bot
```

3. Ejecutar el bot:
```bash
python init.py
```

## Despliegue

### Docker
```bash
docker build -t kirin-bot .
docker run -d --env TOKEN=tu_token kirin-bot
```

### Fly.io
```bash
fly deploy
```

## Licencia

CC0 1.0 Universal
