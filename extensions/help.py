import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog, name="Ayuda"):
	def __init__(self, Bot):
		self.Bot = Bot

	@app_commands.command(name="help", description="Muestra la lista de comandos disponibles")
	async def help_command(self, interaction: discord.Interaction):
		embed = discord.Embed(title="Comandos del Bot", color=discord.Color.orange())
		embed.description = "Usa los comandos de barra (/) para interactuar con el bot"

		cogs = [
			("Diversión", "8ball, rip, challenge, accept, reject"),
			("Miscelaneos", "say"),
			("Busqueda", "derpibooru")
		]

		for cog_name, commands in cogs:
			embed.add_field(name=cog_name, value=commands, inline=False)

		await interaction.response.send_message(embed=embed)

async def setup(Bot):
	await Bot.add_cog(Help(Bot))