import discord
from discord import app_commands
from discord.ext import commands
import random
import io
from config import PREFIX
from defs import replace_mentions, weapons
from PIL import Image, ImageFont, ImageDraw
import textwrap

class Fun(commands.Cog, name="Diversión"):
	def __init__(self, client):
		self.client = client

	@app_commands.command(name="8ball", description="Haz una pregunta de si o no y recibe una respuesta potencialmente absurda.")
	async def ball(self, interaction: discord.Interaction, pregunta: str):
		responses = {
			"positive": {
				"answers": [
					"Claro que si", "Si, definitivamente", "Sin duda", "Así es",
					"Como yo lo veo, sí", "Tenlo por seguro", "El destino te sonríe",
					"Es muy probable que si", "No abandones tu sonrisa porque algo pueda doler~",
					"Tengo un buen pronostico para ti", "Las señales apuntan a que sí",
					"La respuesta es obvia", "En mi opinion, si", "Bueno, la esperanza es lo último que muere",
					"Hoy es tu dia de suerte"
				],
				"emoji": "🟢"
			},
			"neutral": {
				"answers": [
					"No lo se con certeza, pero puede que si", "¿Eso lo preguntas mucho?",
					"Creo que alguien no sale mucho", "Buena pregunta", "Aun extraño ese sillón...",
					"Es posible", "La, la la la la la, la la la~", "Vuelve a pregunta mas tarde",
					"Lo siento, no puedo entender tu pregunta", "Quizas",
					"No tengo la mas minima idea", "( ͡° ͜ʖ ͡°)", "Gracias, vuelva pronto",
					"¿Alguien ha visto una bola mágica por aquí?", "Ah, ok. Te me cuidas"
				],
				"emoji": "🟡"
			},
			"negative": {
				"answers": [
					"Ni lo sueñes", "Mis fuentes dicen que no", "No lo haga compa",
					"Es muy dudoso", "En una prisión estaba con mil voces en mi ser",
					"No lo creo", "No te hagas ilusiones", "Oh no, creo que deje el horno encendido",
					"No cuentes con ello", "De ninguna forma", "No es posible",
					"Ni en un millon de años", "Ve a casa y reflexiona sobre tu vida",
					"No hay ninguna posibilidad de eso", "Una flama roja ardió y nuestro pan quemo~"
				],
				"emoji": "🔴"
			}
		}

		choice = random.choice(list(responses.values()))
		answer = random.choice(choice["answers"])

		embed = discord.Embed(color=discord.Color.orange())
		embed.set_author(name="Bola mágica", icon_url="https://twemoji.maxcdn.com/2/72x72/1f3b1.png")
		embed.add_field(name="Pregunta:", value=pregunta, inline=False)
		embed.add_field(name="Respuesta:", value=f"{choice['emoji']} | `{answer}`", inline=False)
		embed.set_footer(text=f"Solicitado por {interaction.user.display_name}", icon_url=interaction.user.display_avatar)

		await interaction.response.send_message(embed=embed)

	@app_commands.command(name="rip", description="Crea una tumba con dedicatoria para tus amigos.")
	async def rip(self, interaction: discord.Interaction, usuario: str = None, *, inscripcion: str = None):
		def rect_text(box, text, font):
			x1, y1, x2, y2 = box[0], box[1], box[2], box[3]
			w, h = font.getsize(text)
			x = (x2 - x1 - w)/2 + x1
			y = (y2 - y1 - h)/2 + y1
			return (x, y)

		await interaction.response.defer()

		img = Image.open("./images/rip.png")
		draw = ImageDraw.Draw(img)
		temp = io.BytesIO()

		font_top = ImageFont.truetype("./fonts/librefranklin-bold.ttf", 18)
		font = ImageFont.truetype("./fonts/Roboto-Bold.ttf", 16)

		if usuario is None:
			top = interaction.user.display_name
		elif interaction.data.get("resolved"):
			top = usuario
		else:
			top = usuario

		top_box = [85, 180, 210, 220]
		bottom_box = [80, 220, 220, 300]

		name = textwrap.shorten(top, width=15, placeholder=top[:12]+"...")
		draw.text((rect_text(top_box, name, font_top)), name, fill="black", align="center", font=font_top)

		if inscripcion is not None:
			field = "\n".join(textwrap.wrap(inscripcion, 17, max_lines=4, placeholder="..."))
			draw.multiline_text((rect_text(bottom_box, field, font)), field, fill="black", align="center", font=font)

		img.save(temp, "png")
		temp.seek(0)

		await interaction.followup.send(file=discord.File(filename="rip.png", fp=temp))

	@app_commands.command(name="challenge", description="Desafia a tus amigos a un duelo a muerte con cuchillos.")
	async def challenge(self, interaction: discord.Interaction, miembro: discord.Member):
		if miembro == interaction.user:
			await interaction.response.send_message("Ten cuidado con eso, no te haces daño.")
			return

		await interaction.response.send_message(
			f"{miembro.mention}, {interaction.user.mention} desea desafiarte a un duelo a muerte con cuchillos, aceptas el reto?\n"
			"Responde con /accept o /reject, esta invitación expirara en 30 segundos."
		)

		# Store challenge data for later handling
		self.client.pending_challenges = getattr(self.client, 'pending_challenges', {})
		self.client.pending_challenges[miembro.id] = {
			"challenger": interaction.user,
			"member": miembro,
			"channel": interaction.channel
		}

	@app_commands.command(name="accept", description="Acepta un desafío")
	async def accept(self, interaction: discord.Interaction):
		pending = getattr(self.client, 'pending_challenges', {})
		if interaction.user.id in pending:
			challenge = pending[interaction.user.id]
			await interaction.response.send_message("¡Desafío aceptado! Iniciando duelo...")
			# TODO: Implement game loop
		else:
			await interaction.response.send_message("No tienes ningún desafío pendiente.")

	@app_commands.command(name="reject", description="Rechaza un desafío")
	async def reject(self, interaction: discord.Interaction):
		pending = getattr(self.client, 'pending_challenges', {})
		if interaction.user.id in pending:
			challenge = pending[interaction.user.id]
			await interaction.response.send_message(f"¡Desafío rechazado! {challenge['challenger'].mention}")
			del pending[interaction.user.id]
		else:
			await interaction.response.send_message("No tienes ningún desafío pendiente.")

async def setup(client):
	await client.add_cog(Fun(client))