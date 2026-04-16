import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import random
import re
from defs import get_json_api
from config import filters
from i18n import t

class Search(commands.Cog, name="🔍 Search"):
    def __init__(self, client):
        self.client = client

    @app_commands.command(
        name=app_commands.locale_str("derpibooru"),
        description=app_commands.locale_str("derpibooru_description")
    )
    async def derpibooru(self, interaction: discord.Interaction, busqueda: str = None):
        await interaction.response.defer()
        guild_id = interaction.guild.id if interaction.guild else 0

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
            await interaction.followup.send(t(guild_id, "no_images_found"))
            return

        total_images = db_json.get("total", 0)

        if total_images < 1:
            await interaction.followup.send(t(guild_id, "no_images_found"))
            return

        rand_page = random.randint(1, max(1, total_images))
        params["page"] = rand_page

        if total_images > 1:
            embed.add_field(name=t(guild_id, "search_title"), value=t(guild_id, "search_results", total=total_images, current=rand_page), inline=False)

        db_json = await get_json_api(url, params)
        if not db_json.get("images"):
            await interaction.followup.send(t(guild_id, "no_images_found"))
            return

        data = db_json["images"][0]

        artist = [tag[7:] for tag in data.get("tags", []) if tag.startswith("artist:")]

        if not artist:
            artist = t(guild_id, "field_unknown")
        elif len(artist) > 5:
            artist = t(guild_id, "field_too_many")
        else:
            artist = ", ".join(artist)

        uploader = data.get("uploader", t(guild_id, "field_unknown"))
        source_url = data.get("source_url", t(guild_id, "field_unknown"))

        embed.set_author(name="Derpibooru", url=f"https://www.derpibooru.org/images/{data['id']}", icon_url="https://i.imgur.com/K311uwc.png")
        embed.add_field(name=t(guild_id, "field_favorites"), value=f"⭐ {data.get('faves', 0)}", inline=True)
        embed.add_field(name=t(guild_id, "field_upvotes"), value=f"👍 {data.get('upvotes', 0)}", inline=True)
        embed.add_field(name=t(guild_id, "field_downvotes"), value=f"👎 {data.get('downvotes', 0)}", inline=True)
        embed.add_field(name=t(guild_id, "field_artist"), value=f"🎨 {artist}", inline=True)
        embed.add_field(name=t(guild_id, "field_score"), value=f"📊 {data.get('score', 0)}", inline=True)
        embed.add_field(name=t(guild_id, "field_uploader"), value=f"👤 {uploader}", inline=True)
        embed.add_field(name=t(guild_id, "field_source"), value=source_url, inline=False)
        embed.set_footer(text=t(guild_id, "search_requested_by", user=interaction.user.display_name), icon_url=interaction.user.display_avatar)
        embed.set_image(url=data["representations"]["full"])

        await interaction.followup.send(embed=embed)

        if data.get("format") == "webm":
            await interaction.followup.send(data.get("view_url", ""))

async def setup(client):
    await client.add_cog(Search(client))