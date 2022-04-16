from nextcord.ext import commands

#Imports the bot's configuration and custom functions
from config import *
from defs import *

Bot = commands.Bot(command_prefix=PREFIX)

@Bot.event
async def on_ready():
    print_frame(f"Logged in as {Bot.user}\nwith the following ID: {Bot.user.id}")

# Shitty global command error handling
@Bot.event
async def on_command_error(ctx, err):
    if hasattr(ctx.command, 'on_error'):
        return

    print(f"Command {ctx.command} has raised an exception: {err}")

print("Loading extensions, please wait...\n")

for ext in ext_lst:
    try:
        Bot.load_extension(ext)
        print(f" + ¡The extension {ext} has been successfully loaded!")
    except Exception as e:
        print(f" - ¡The extension {ext} couldn't be loaded! - Error: {e}")

print("\n¡Finished loading extensions!\n")

Bot.run(TOKEN)