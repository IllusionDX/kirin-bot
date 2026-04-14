import discord
from discord import app_commands
from discord.ext import commands
from discord import ui

class Help(commands.Cog, name="Ayuda"):
	def __init__(self, Bot):
		self.Bot = Bot

	@app_commands.command(name="help", description="Muestra la lista de comandos disponibles")
	async def help_command(self, interaction: discord.Interaction):
		view = HelpView(self.Bot)
		await interaction.response.send_message(embed=view.get_main_embed(), view=view)

class HelpView(ui.View):
	def __init__(self, bot):
		super().__init__(timeout=300)
		self.bot = bot
		self.update_select()
	
	def update_select(self):
		self.clear_items()
		
		options = [discord.SelectOption(label="🏠 Principal", value="Ayuda")]
		for cog in self.bot.cogs.values():
			if cog.qualified_name != "Ayuda":
				options.append(discord.SelectOption(label=cog.qualified_name, value=cog.qualified_name))
		
		select = ui.Select(
			custom_id="help_category",
			placeholder="Navega por categorías",
			options=options
		)
		self.add_item(select)
	
	def get_commands_for_cog(self, cog_name):
		commands = []
		cog = self.bot.cogs.get(cog_name)
		if cog:
			for attr_name in dir(cog):
				attr = getattr(cog, attr_name)
				if isinstance(attr, app_commands.Command):
					commands.append((attr.name, attr.description or "Sin descripción"))
		return commands
	
	def get_main_embed(self):
		embed = discord.Embed(
			title="📚 Centro de Ayuda de Autumn",
			description="Selecciona una categoría del menú para ver sus comandos.",
			color=discord.Color.orange()
		)
		
		# Dynamically build category list
		categories = []
		for cog in self.bot.cogs.values():
			if cog.qualified_name != "Ayuda":
				cmds = self.get_commands_for_cog(cog.qualified_name)
				if cmds:
					categories.append(f"📁 {cog.qualified_name} ({len(cmds)} comandos)")
		
		if categories:
			embed.add_field(name="Categorías Disponibles", value="\n".join(categories), inline=False)
		
		embed.set_footer(text="KirinBot | Autumn Blaze")
		return embed
	
	def get_category_embed(self, category):
		if category == "Ayuda":
			return self.get_main_embed()
		
		embed = discord.Embed(
			title=f"📁 {category}",
			color=discord.Color.orange()
		)
		
		commands = self.get_commands_for_cog(category)
		
		if commands:
			cmd_list = [f"**/{name}** - {desc}" for name, desc in commands]
			embed.description = "\n".join(cmd_list)
		else:
			embed.description = "No hay comandos en esta categoría."
		
		embed.set_footer(text="KirinBot | Autumn Blaze")
		return embed
	
	async def interaction_check(self, interaction: discord.Interaction) -> bool:
		if interaction.data.get("component_type") == 3:
			category = interaction.data["values"][0]
			await interaction.response.edit_message(embed=self.get_category_embed(category), view=self)
			return True
		return True

async def setup(Bot):
	await Bot.add_cog(Help(Bot))