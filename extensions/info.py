from discord.ext import commands

class Info(commands.Cog, name="Información"):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("pong")

def setup(client):
    client.add_cog(Info(client))