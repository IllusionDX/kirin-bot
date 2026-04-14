import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

class Weather(commands.Cog, name="Clima"):
	def __init__(self, client):
		self.client = client

	@app_commands.command(name="weather", description="Consulta el clima de una ciudad")
	async def weather(self, interaction: discord.Interaction, ciudad: str):
		await interaction.response.defer()

		headers = {"User-Agent": "KirinBot/1.0 (Discord Bot)"}

		async with aiohttp.ClientSession() as session:
			# Geocoding with Nominatim (better for "city country" queries)
			geo_url = f"https://nominatim.openstreetmap.org/search?q={ciudad}&format=json&limit=1"
			async with session.get(geo_url, headers=headers) as r:
				if r.status != 200:
					await interaction.followup.send("Error al buscar la ciudad.")
					return
				geo_data = await r.json()

			if not geo_data:
				await interaction.followup.send(f"No se encontró la ciudad: {ciudad}")
				return

			location = geo_data[0]
			lat = float(location["lat"])
			lon = float(location["lon"])
			name = location.get("display_name", ciudad)
			# Extract country from display_name
			country = location.get("display_name", "").split(",")[-1].strip() if "," in location.get("display_name", "") else ""

			# Weather: get current weather
			weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&timezone=auto"
			async with session.get(weather_url) as r:
				if r.status != 200:
					await interaction.followup.send("Error al obtener el clima.")
					return
				weather_data = await r.json()

			current = weather_data.get("current", {})
			temp = current.get("temperature_2m", "N/A")
			humidity = current.get("relative_humidity_2m", "N/A")
			wind = current.get("wind_speed_10m", "N/A")
			code = current.get("weather_code", 0)

			weather_conditions = {
				0: "Cielo despejado ☀️",
				1: "Mayormente despejado 🌤️",
				2: "Parcialmente nublado ⛅",
				3: "Nublado ☁️",
				45: "Niebla 🌫️",
				48: "Niebla 🌫️",
				51: "Lluvia ligera 🌧️",
				53: "Lluvia moderada 🌧️",
				55: "Lluvia intensa 🌧️",
				61: "Lluvia 🌧️",
				63: "Lluvia 🌧️",
				65: "Lluvia intensa 🌧️",
				71: "Nieve 🌨️",
				73: "Nieve 🌨️",
				75: "Nieve intensa 🌨️",
				80: "Chubascos 🌦️",
				81: "Chubascos 🌦️",
				82: "Chubascos fuertes 🌦️",
				95: "Tormenta ⛈️",
				96: "Tormenta con granizo ⛈️",
				99: "Tormenta intensa ⛈️"
			}
			condition = weather_conditions.get(code, f"Código: {code}")

		# Shorten name to just city
		name_short = name.split(",")[0] if "," in name else name
		
		embed = discord.Embed(title=f"Clima en {name_short}, {country}", color=discord.Color.blue())
		embed.add_field(name="🌡️ Temperatura", value=f"{temp}°C", inline=True)
		embed.add_field(name="💧 Humedad", value=f"{humidity}%", inline=True)
		embed.add_field(name="💨 Viento", value=f"{wind} km/h", inline=True)
		embed.add_field(name="☁️ Condición", value=condition, inline=False)
		embed.set_footer(text="Datos de Open-Meteo | Geocodificación por OpenStreetMap")

		await interaction.followup.send(embed=embed)

async def setup(client):
	await client.add_cog(Weather(client))