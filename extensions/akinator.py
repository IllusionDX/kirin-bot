import discord
from discord import app_commands
from discord.ext import commands
from discord import ui
import akinator
import asyncio

# Patch the client module to handle missing 'akitude' key
import akinator.async_client as _aki_async_client

async def _patched_async_handler(self, response):
    response.raise_for_status()
    try:
        data = response.json()
    except Exception as e:
        if "A technical problem has ocurred." in response.text:
            raise RuntimeError("A technical problem has occurred. Please try again later.") from e
        raise RuntimeError("Failed to parse the response as JSON.") from e

    if "completion" not in data:
        data["completion"] = getattr(self, "completion", None)
    if data["completion"] == "KO - TIMEOUT":
        raise RuntimeError("The session has timed out. Please start a new game.")
    if data["completion"] == "SOUNDLIKE":
        self.finished = True
        self.win = True
        if not getattr(self, "id_proposition", None):
            await self.defeat()
    elif "id_proposition" in data:
        self.win = True
        self.id_proposition = data["id_proposition"]
        self.name_proposition = data["name_proposition"]
        self.description_proposition = data["description_proposition"]
        self.step_last_proposition = self.step
        self.pseudo = data["pseudo"]
        self.flag_photo = data["flag_photo"]
        self.photo = data["photo"]
    else:
        self.akitude = data.get("akitude", None)
        self.step = int(data.get("step", getattr(self, "step", 0) + 1))
        self.progression = float(data.get("progression", getattr(self, "progression", 0.0)))
        self.question = data.get("question", getattr(self, "question", ""))
    self.completion = data["completion"]

_aki_async_client.AsyncClient._AsyncClient__handler = _patched_async_handler

class Akinator(commands.Cog, name="🎯 Akinator"):
	def __init__(self, Bot):
		self.Bot = Bot
		self.active_games = {}
	
	@app_commands.command(name="akinator", description="Juega al Akinator")
	async def akinator_cmd(self, interaction: discord.Interaction):
		user_id = interaction.user.id
		
		if user_id in self.active_games:
			await interaction.response.send_message("Ya tienes una partida activa. Responde a las preguntas anteriores.", ephemeral=True)
			return
		
		await interaction.response.send_message(
			embed=discord.Embed(
				title="🎯 Akinator",
				description="Piensa en un personaje (real o ficticio) y responde a mis preguntas.",
				color=discord.Color.from_rgb(33, 150, 243)
			),
			view=AkinatorStartView(self, user_id),
			ephemeral=True
		)

class AkinatorStartView(ui.View):
	def __init__(self, cog, user_id):
		super().__init__(timeout=60)
		self.cog = cog
		self.user_id = user_id
	
	@ui.button(label="Comenzar", custom_id="aki_start", emoji="▶️", style=discord.ButtonStyle.success)
	async def start(self, interaction: discord.Interaction, button: ui.Button):
		if interaction.user.id != self.user_id:
			await interaction.response.send_message("Este botón no es para ti.", ephemeral=True)
			return
		
		await interaction.response.defer()
		
		try:
			game = akinator.AsyncAkinator()
			await game.start_game(language="es")
			
			self.cog.active_games[self.user_id] = game
			
			view = AkinatorGameView(self.cog, self.user_id, game)
			view.update_question()
			
			await interaction.edit_original_response(
				content=None,
				embed=view.get_question_embed(),
				view=view
			)
		except Exception as e:
			import traceback
			await interaction.edit_original_response(
				content=f"Error al iniciar: {e}\n\n```\n{traceback.format_exc()[:500]}\n```",
				view=None
			)

class AkinatorGameView(ui.View):
	def __init__(self, cog, user_id, game):
		super().__init__(timeout=120)
		self.cog = cog
		self.user_id = user_id
		self.game = game
	
	def update_question(self):
		self.current_question = str(self.game).strip()
	
	def get_question_embed(self):
		prog = round(self.game.progression)
		step = getattr(self.game, 'step', 0)
		
		# Color shifts from blue -> orange as progression increases
		r = min(255, int(prog * 2.55))
		g = min(165, int(prog * 1.2))
		b = max(0, 255 - int(prog * 2.55))
		color = discord.Color.from_rgb(r, g, b)
		
		# Visual progress bar
		filled = int(prog / 10)
		bar = "🟧" * filled + "⬛" * (10 - filled)
		
		embed = discord.Embed(
			title=f"🎯 Pregunta #{step + 1}",
			description=f"### {self.current_question}",
			color=color
		)
		embed.add_field(name="Progresión", value=f"{bar} **{prog}%**", inline=False)
		
		embed.set_footer(text="Responde con los botones de abajo")
		return embed
	
	@ui.button(label="Sí", custom_id="aki_yes", emoji="✅", style=discord.ButtonStyle.success)
	async def yes(self, interaction: discord.Interaction, button: ui.Button):
		await self._answer(interaction, "yes")
	
	@ui.button(label="No", custom_id="aki_no", emoji="❌", style=discord.ButtonStyle.danger)
	async def no(self, interaction: discord.Interaction, button: ui.Button):
		await self._answer(interaction, "no")
	
	@ui.button(label="Probablemente", custom_id="aki_probably", emoji="🤔", style=discord.ButtonStyle.secondary)
	async def probably(self, interaction: discord.Interaction, button: ui.Button):
		await self._answer(interaction, "probably")
	
	@ui.button(label="No sé", custom_id="aki_dont_know", emoji="❓", style=discord.ButtonStyle.secondary)
	async def dont_know(self, interaction: discord.Interaction, button: ui.Button):
		await self._answer(interaction, "i don't know")
	
	@ui.button(label="Atrás", custom_id="aki_back", emoji="🔙", style=discord.ButtonStyle.primary)
	async def back(self, interaction: discord.Interaction, button: ui.Button):
		if interaction.user.id != self.user_id:
			await interaction.response.send_message("Este no es tu juego.", ephemeral=True)
			return
		
		await interaction.response.defer()
		
		try:
			await self.game.back()
			self.update_question()
			await interaction.edit_original_response(
				content=None,
				embed=self.get_question_embed(),
				view=self
			)
		except Exception as e:
			await interaction.followup.send(f"No puedes volver más atrás: {e}", ephemeral=True)
	
	async def _answer(self, interaction: discord.Interaction, answer: str):
		if interaction.user.id != self.user_id:
			await interaction.response.send_message("Este no es tu juego.", ephemeral=True)
			return
		
		await interaction.response.defer()
		
		try:
			await self.game.answer(answer)
			self.update_question()
			
			if getattr(self.game, 'win', False) and not getattr(self.game, 'finished', False):
				guess_name = getattr(self.game, 'name_proposition', 'Unknown')
				embed = discord.Embed(
					title="🤔 ¿Es este tu personaje?",
					description=f"¿Es **{guess_name}**?",
					color=discord.Color.yellow()
				)
				if getattr(self.game, 'description_proposition', None):
					embed.add_field(name="Descripción:", value=self.game.description_proposition[:500], inline=False)
				if getattr(self.game, 'photo', None):
					embed.set_image(url=self.game.photo)
				
				# Add Yes/No buttons for the guess
				guess_view = AkinatorGuessView(self.cog, self.user_id, self.game)
				await interaction.edit_original_response(content=None, embed=embed, view=guess_view)
				return
			
			if getattr(self.game, 'finished', False):
				embed = discord.Embed(
					title="🏆 ¡Me rindo!",
					description=str(getattr(self.game, 'question', 'Has ganado.')).strip(),
					color=discord.Color.red()
				)
				await interaction.edit_original_response(content=None, embed=embed, view=None)
				if self.user_id in self.cog.active_games:
					del self.cog.active_games[self.user_id]
				return
			
			await interaction.edit_original_response(
				content=None,
				embed=self.get_question_embed(),
				view=self
			)
		except Exception as e:
			import traceback
			await interaction.edit_original_response(
				content=f"Error: {e}\n\n```\n{traceback.format_exc()[:500]}\n```",
				embed=None,
				view=None
			)
			if self.user_id in self.cog.active_games:
				del self.cog.active_games[self.user_id]

class AkinatorGuessView(ui.View):
	def __init__(self, cog, user_id, game):
		super().__init__(timeout=60)
		self.cog = cog
		self.user_id = user_id
		self.game = game
	
	@ui.button(label="¡Sí!", custom_id="guess_yes", emoji="✅", style=discord.ButtonStyle.success)
	async def yes(self, interaction: discord.Interaction, button: ui.Button):
		if interaction.user.id != self.user_id:
			await interaction.response.send_message("Este no es tu juego.", ephemeral=True)
			return
		
		await interaction.response.defer()
		
		try:
			await self.game.choose()
			embed = discord.Embed(
				title="🎉 ¡Sabía que lo adivinaría!",
				description=str(getattr(self.game, 'question', "¡Gracias por jugar!")).replace(" !", "!").strip(),
				color=discord.Color.gold()
			)
			embed.add_field(name="Personaje:", value=f"**{self.game.name_proposition}**", inline=False)
			if getattr(self.game, 'photo', None):
				embed.set_image(url=self.game.photo)
			
			await interaction.edit_original_response(content=None, embed=embed, view=None)
			if self.user_id in self.cog.active_games:
				del self.cog.active_games[self.user_id]
		except Exception as e:
			await interaction.edit_original_response(content=f"Error: {e}", embed=None, view=None)
			if self.user_id in self.cog.active_games:
				del self.cog.active_games[self.user_id]
	
	@ui.button(label="No", custom_id="guess_no", emoji="❌", style=discord.ButtonStyle.danger)
	async def no(self, interaction: discord.Interaction, button: ui.Button):
		if interaction.user.id != self.user_id:
			await interaction.response.send_message("Este no es tu juego.", ephemeral=True)
			return
		
		await interaction.response.defer()
		
		try:
			await self.game.exclude()
			
			if getattr(self.game, 'finished', False):
				embed = discord.Embed(
					title="🏆 ¡Me rindo!",
					description=str(getattr(self.game, 'question', 'Has ganado.')).strip(),
					color=discord.Color.red()
				)
				await interaction.edit_original_response(content=None, embed=embed, view=None)
				if self.user_id in self.cog.active_games:
					del self.cog.active_games[self.user_id]
				return
			
			view = AkinatorGameView(self.cog, self.user_id, self.game)
			view.update_question()
			
			await interaction.edit_original_response(
				content=None,
				embed=view.get_question_embed(),
				view=view
			)
		except Exception as e:
			await interaction.edit_original_response(content=f"Error: {e}", embed=None, view=None)
			if self.user_id in self.cog.active_games:
				del self.cog.active_games[self.user_id]

async def setup(Bot):
	await Bot.add_cog(Akinator(Bot))