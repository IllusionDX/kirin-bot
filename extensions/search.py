import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import random
import re
from defs import get_json_api
from config import filters

class Search(commands.Cog, name="🔍 Busqueda"):
	def __init__(self, client):
		self.client = client

	@app_commands.command(name="derpibooru", description="Busca imágenes en Derpibooru")
	async def derpibooru(self, interaction: discord.Interaction, busqueda: str = None):
		await interaction.response.defer()

		if busqueda is None:
			query = "*"
		elif busqueda.isdigit():
			query = f"id:{busqueda}"
		else:
			query = busqueda

		embed = discord.Embed(color=discord.Color.orange())
		url = "https://derpibooru.org/api/v1/json/search/images"
		params = {
			"filter_id": filters["safe"],
			"q": query,
			"per_page": 1,
			"page": 1
		}

		db_json = await get_json_api(url, params)
		if not db_json or "images" not in db_json:
			await interaction.followup.send("No se han encontrado imágenes")
			return

		total_images = db_json.get("total", 0)

		if total_images < 1:
			await interaction.followup.send("No se han encontrado imágenes")
			return

		rand_page = random.randint(1, max(1, total_images))
		params["page"] = rand_page

		if total_images > 1:
			embed.add_field(name="Búsqueda", value=f"Se han encontrado **{total_images}** imágenes. [{rand_page}/{total_images}]", inline=False)

		db_json = await get_json_api(url, params)
		if not db_json.get("images"):
			await interaction.followup.send("No se han encontrado imágenes")
			return

		data = db_json["images"][0]

		artist = [tag[7:] for tag in data.get("tags", []) if tag.startswith("artist:")]

		if not artist:
			artist = "Anónimo"
		elif len(artist) > 5:
			artist = "Demasiados"
		else:
			artist = ", ".join(artist)

		uploader = data.get("uploader", "Anónimo")
		source_url = data.get("source_url", "Ninguna")

		embed.set_author(name="Derpibooru", url=f"https://www.derpibooru.org/images/{data['id']}", icon_url="https://i.imgur.com/K311uwc.png")
		embed.add_field(name="Favoritos", value=f"⭐ {data.get('faves', 0)}", inline=True)
		embed.add_field(name="Upvotes", value=f"👍 {data.get('upvotes', 0)}", inline=True)
		embed.add_field(name="Downvotes", value=f"👎 {data.get('downvotes', 0)}", inline=True)
		embed.add_field(name="Artista", value=f"🎨 {artist}", inline=True)
		embed.add_field(name="Puntaje", value=f"📊 {data.get('score', 0)}", inline=True)
		embed.add_field(name="Subido por", value=f"👤 {uploader}", inline=True)
		embed.add_field(name="Fuente", value=source_url, inline=False)
		embed.set_footer(text=f"Solicitado por {interaction.user.display_name}", icon_url=interaction.user.display_avatar)
		embed.set_image(url=data["representations"]["full"])

		await interaction.followup.send(embed=embed)

		if data.get("format") == "webm":
			await interaction.followup.send(data.get("view_url", ""))

async def setup(client):
	await client.add_cog(Search(client))