from discord.ext import commands
import aiohttp
import random
import math

from misc import *
from config import filters

class Search(commands.Cog, name = "Busqueda"):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["derpi", "derpy", "db"])
    async def derpibooru(self, ctx, *, arg:str = None):
        if arg is None:
            query = "*"
        elif len(arg.split(",")) == 1 and arg.isdigit():
            query = "id:" + arg
        else:
            query = arg

        data = []
        url = "https://derpibooru.org/api/v1/json/search/images"
        params = {
            "filter_id" : filters["safe"],
            "q" : query,
            "per_page" : 1,
            "page" : 1
        }

        async with ctx.channel.typing():
            db_json = await get_json_api(url, params)
            total_images = db_json["total"]

            rand_img = random.randint(0, total_images)
            params["page"] = rand_img

            if total_images < 1:
                await ctx.send("No se han encontrado imágenes")
            elif total_images == 1:
                pass
            else:
                data.append(f"Se han encontrado **{total_images}** imágenes. [{rand_img}/{total_images}]")
        
            db_json = await get_json_api(url, params)
            data.append(f"https://derpibooru.org/{db_json['images'][0]['id']}")

            await ctx.send("\n".join(data))

def setup(client):
    client.add_cog(Search(client))