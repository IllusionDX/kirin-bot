#Imports the necessary libraries
from nextcord.ext import commands

#Imports the bot's configuration and custom functions
from config import *
from defs import *

client = commands.Bot(command_prefix=prefix)

@client.event
async def on_ready():
    print_frame(f"Logged in as {client.user}\nwith the following ID: {client.user.id}")

print("Loading extensions, please wait...")
for ext in ext_lst:
    try:
        client.load_extension(ext)
        print(f" + ¡The extension {ext} has been successfully loaded!")
    except Exception as e:
        print(f" - ¡The extension {ext} couldn't be loaded! - Error: {e}")
print("¡Finished loading extensions!\n")

client.run(token)