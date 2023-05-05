import discord
from discord.ext import commands

class EmbedHelpCommand(commands.HelpCommand):		
	COLOR = discord.Color.orange()

	def get_ending_note(self):
		return f"Usa {self.context.clean_prefix}{self.invoked_with} [comando] para obtener mas información"

	async def send_bot_help(self, mapping):
		embed = discord.Embed(title="Comandos", color=self.COLOR)
		embed.description = "Aqui puedes ver los comandos del bot"
		
		for cog, command in mapping.items():
			if cog is None:
				continue
			
			name = cog.qualified_name
			filtered = await self.filter_commands(command, sort=True)
			
			if filtered:
				value = "\u2002".join(c.name for c in command)
				if cog.description:
					value = f"{cog.description}\n{value}"

				embed.add_field(name=name, value=value, inline=False)

		embed.set_footer(text=self.get_ending_note())
		await self.get_destination().send(embed=embed)

	async def send_command_help(self, command):
		embed = discord.Embed(title=command, color=self.COLOR)
		embed.add_field(name="Descripción", value=command.description, inline=False)
		embed.add_field(name="Uso", value=f"{self.context.clean_prefix}{command.usage}", inline=False)
		await self.get_destination().send(embed=embed)

	
class Help(commands.Cog, name="Ayuda"):
	def __init__(self, Bot):
		self.Bot = Bot

		EmbedHelpCommand().cog = self
		Bot.help_command = EmbedHelpCommand()

async def setup(Bot):
	await Bot.add_cog(Help(Bot))
