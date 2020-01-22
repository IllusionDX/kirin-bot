#Librerías neceesarias
import discord
from discord.ext import commands

#Importa las funciones personalizadas y la configuración del bot
from config import *
from defs import *

client = commands.Bot(command_prefix=prefix)

@client.event
async def on_ready():
    print_frame(f"""Se ha iniciado sesion como {client.user}\nTengo la id de {client.user.id}""")

print("Cargando extensiones, por favor espere...")
for ext in ext_lst:
    try:
        client.load_extension(ext)
        print(f" + ¡La extension {ext} se ha cargado con éxito!")
    except Exception as e:
        print(f" - ¡La extension {ext} no pudo ser cargada! - Error: {e}")
print("¡Carga de extensiones finalizada!\n")

client.run(token)