import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from i18n import t
from database import get_language

class Weather(commands.Cog, name="🌤️ Weather"):
    def __init__(self, client):
        self.client = client

    @app_commands.command(
        name=app_commands.locale_str("weather"),
        description=app_commands.locale_str("weather_description")
    )
    async def weather(self, interaction: discord.Interaction, ciudad: str):
        await interaction.response.defer()
        guild_id = interaction.guild.id if interaction.guild else 0
        lang = get_language(guild_id)

        headers = {"User-Agent": "KirinBot/1.0 (Discord Bot)"}

        async with aiohttp.ClientSession() as session:
            geo_url = f"https://nominatim.openstreetmap.org/search?q={ciudad}&format=json&limit=1&accept-language={lang}"
            async with session.get(geo_url, headers=headers) as r:
                if r.status != 200:
                    await interaction.followup.send(t(guild_id, "error_searching_city"))
                    return
                geo_data = await r.json()

            if not geo_data:
                await interaction.followup.send(t(guild_id, "city_not_found", city=ciudad))
                return

            location = geo_data[0]
            lat = float(location["lat"])
            lon = float(location["lon"])
            name = location.get("display_name", ciudad)
            country = location.get("display_name", "").split(",")[-1].strip() if "," in location.get("display_name", "") else ""

            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&timezone=auto"
            async with session.get(weather_url) as r:
                if r.status != 200:
                    await interaction.followup.send(t(guild_id, "error_fetching_weather"))
                    return
                weather_data = await r.json()

            current = weather_data.get("current", {})
            temp = current.get("temperature_2m", "N/A")
            humidity = current.get("relative_humidity_2m", "N/A")
            wind = current.get("wind_speed_10m", "N/A")
            code = current.get("weather_code", 0)

            weather_conditions = {
                0: t(guild_id, "weather_clear"),
                1: t(guild_id, "weather_mainly_clear"),
                2: t(guild_id, "weather_partly_cloudy"),
                3: t(guild_id, "weather_overcast"),
                45: t(guild_id, "weather_fog"),
                48: t(guild_id, "weather_fog"),
                51: t(guild_id, "weather_drizzle_light"),
                53: t(guild_id, "weather_drizzle_moderate"),
                55: t(guild_id, "weather_drizzle_dense"),
                61: t(guild_id, "weather_rain_slight"),
                63: t(guild_id, "weather_rain_moderate"),
                65: t(guild_id, "weather_rain_heavy"),
                71: t(guild_id, "weather_snow_slight"),
                73: t(guild_id, "weather_snow_moderate"),
                75: t(guild_id, "weather_snow_heavy"),
                80: t(guild_id, "weather_showers_slight"),
                81: t(guild_id, "weather_showers_moderate"),
                82: t(guild_id, "weather_showers_violent"),
                95: t(guild_id, "weather_thunderstorm"),
                96: t(guild_id, "weather_thunderstorm_hail"),
                99: t(guild_id, "weather_thunderstorm_heavy")
            }
            condition = weather_conditions.get(code, f"Code: {code}")

        name_short = name.split(",")[0] if "," in name else name
        
        embed = discord.Embed(title=t(guild_id, "weather_title", city=name_short, country=country), color=discord.Color.blue())
        embed.add_field(name=t(guild_id, "field_temperature"), value=f"{temp}°C", inline=True)
        embed.add_field(name=t(guild_id, "field_humidity"), value=f"{humidity}%", inline=True)
        embed.add_field(name=t(guild_id, "field_wind"), value=f"{wind} km/h", inline=True)
        embed.add_field(name=t(guild_id, "field_condition"), value=condition, inline=False)
        embed.set_footer(text=t(guild_id, "weather_footer"))

        await interaction.followup.send(embed=embed)

async def setup(client):
    await client.add_cog(Weather(client))