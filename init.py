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
async def on_command_error(ctx, error):
	if hasattr(ctx.command, 'on_error'):
		return
	elif isinstance(error, commands.CommandNotFound):
		return

	print(f"Error in command {ctx.command}: {error}")

print("Loading extensions, please wait...\n")

for ext in ext_lst:
	try:
		Bot.load_extension(ext)
		print(f" + ¡The extension {ext} has been successfully loaded!")
	except Exception as e:
		print(f" - ¡The extension {ext} couldn't be loaded! - Error: {e}")

print("\n¡Finished loading extensions!\n")

Bot.run(TOKEN)