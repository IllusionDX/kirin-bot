# Kirin Bot

A Discord bot for my server, primarily for fun. Supports English and Spanish.

Currently in active development. Features:

### 🎮 Fun
- **/akinator** - Play Akinator (guess your character)
- **/8ball** - Ask a yes/no question to the magic ball
- **/challenge** - Challenge other players to a duel
- **/coinflip** - Flip a coin (heads or tails)
- **/rip** - Create a tombstone with a dedication
- **/roll** - Roll RPG dice. Supports: `20`, `2d6+3`, `1d20+5`, `(2d6+2d4)*2`, etc.

### 🔍 Search
- **/derpibooru** - Search images on Derpibooru

### ⛅ Weather
- **/weather** - Check the weather for a city

### ⚙️ Misc
- **/say** - Make the bot say something
- **/help** - Show help

### 🛠️ Settings
- **/language** - Set the bot's language for this server (requires Manage Server permission)

## Requirements

- Python 3.10+
- discord.py >= 2.7.0
- python-dotenv >= 1.0.0
- Pillow >= 10.0.0
- aiohttp >= 3.9.0
- akinator >= 2.0.0

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```
TOKEN=your_bot_token
```

3. Run the bot:
```bash
python init.py
```

## Deployment

### Docker
```bash
docker build -t kirin-bot .
docker run -d --env TOKEN=your_token kirin-bot
```

### Fly.io
```bash
fly deploy
```

## License

CC0 1.0 Universal
