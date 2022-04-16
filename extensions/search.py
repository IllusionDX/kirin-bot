import discord
import aiohttp
import random
import math
import re

from discord.ext import commands
from defs import *
from config import filters

class Search(commands.Cog, name = "Busqueda"):
    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["derpi", "derpy", "db"])
    async def derpibooru(self, ctx, *, arg:str = None):

        def get_db_id(q):
            prog = re.compile("(?<=[images/])([0-9]+)")
            m = re.search(prog, q)
            if m is not None:
                return m[0]
            else:
                pass

        m = get_db_id(arg)
        if m:
            arg = m
            if ctx.me.permissions_in(ctx.channel).manage_messages:
                await ctx.message.delete()
            else:
                await ctx.send("¡No tengo permisos para reemplazar tu mensaje!")
                return

        if arg is None:
            query = "*"
        elif len(arg.split(",")) == 1 and arg.isdigit():
            query = "id:" + arg
        else:
            query = arg

                
        embed = discord.Embed(color=discord.Color.orange())
        url = "https://derpibooru.org/api/v1/json/search/images"
        params = {
            "filter_id" : filters["safe"],
            "q" : query,
            "per_page" : 1,
            "page" : 1
        }

        await ctx.trigger_typing()

        db_json = await get_json_api(url, params)
        total_images = db_json["total"]

        rand_img = random.randint(0, total_images)
        params["page"] = rand_img

        if total_images < 1:
            await ctx.send("No se han encontrado imágenes")
        elif total_images == 1:
            pass
        else:
            embed.add_field(name="Busqueda", value=f"Se han encontrado **{total_images}** imágenes. [{rand_img}/{total_images}]", inline=False)
        
        db_json = await get_json_api(url, params)
        data = db_json['images'][0]

        artist = [i[7:] for i in data['tags'] if i.startswith("artist:")]

        if not artist:
            artist = "Anonimo"
        elif len(artist) > 5:
            artist = "Demasiados"
        else:
            artist = ", ".join(artist)

        if not data['uploader']:
            data['uploader'] = "Anónimo"

        if not data['source_url']:
            data['source_url'] = "Ninguna"

        embed.set_author(name="Derpibooru", url=f"https://www.derpibooru.org/images/{data['id']}",icon_url="https://i.imgur.com/K311uwc.png")

        embed.add_field(name="Favoritos", value=f"<:favorite:964725356697378828> {data['faves']}", inline=True)
        embed.add_field(name="Upvotes", value=f"<:upvote:964725345750237194> {data['upvotes']}", inline=True)
        embed.add_field(name="Downvotes", value=f"<:downvote:964725367191519252> {data['downvotes']}", inline=True)
     
        embed.add_field(name="Artista", value=artist, inline=True)

        embed.add_field(name="Puntaje", value=f"{data['score']}", inline=True)

        embed.add_field(name="Subido por", value=f"{data['uploader']}", inline=True)

        embed.add_field(name="Fuente", value=f"{data['source_url']}", inline=False)

        embed.set_footer(text=f"Solicitado por {ctx.author.display_name}\nUsando la API de Derpibooru: https://www.derpibooru.org/pages/api", icon_url=ctx.author.display_avatar)

        embed.set_image(url=data['representations']['full'])

        try:
            await ctx.send(embed=embed)
        except discord.HTTPException as e:
            print(e)

        if data['format'] == "webm":
            await ctx.send(data['view_url']) 

        return

def setup(client):
    client.add_cog(Search(client))