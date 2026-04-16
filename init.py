import discord
import asyncio
from discord.ext import commands
from i18n import KirinTranslator
from config import *
from defs import *
from database import *

intents = discord.Intents.default()
intents.message_content = True

Bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

@Bot.event
async def setup_hook():
    await Bot.tree.set_translator(KirinTranslator())

@Bot.event
async def on_ready():
	print("\n")
	print_frame(f"Logged in as {Bot.user}\nwith the following ID: {Bot.user.id}")
	
	# Sync slash commands
	try:
		synced = await Bot.tree.sync()
		print(f"Synced {len(synced)} slash commands")
	except Exception as e:
		print(f"Error syncing slash commands: {e}")

# Global command error handler
@Bot.event
async def on_command_error(ctx, error):
	if hasattr(ctx.command, 'on_error'):
		return
	elif isinstance(error, commands.CommandNotFound):
		return

	print(f"Error in command {ctx.command}: {error}")

print("Loading extensions, please wait...\n")

async def load_extensions(ext_lst):
    for ext in ext_lst:
        try:
            await Bot.load_extension(ext)
            print(f" + The extension {ext} has been successfully loaded!")
        except Exception as e:
            print(f" - The extension {ext} couldn't be loaded! - Error: {e}")

# To call the function:
asyncio.run(load_extensions(ext_lst))
print("\nFinished loading extensions!\n")

Bot.run(TOKEN)