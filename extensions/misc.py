import discord
from discord.ext import commands

class Misc(commands.Cog, name="Miscelaneos"):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def say(self, ctx, *, to_say):
        await ctx.trigger_typing()
        if ctx.me.permissions_in(ctx.channel).manage_messages:
            await ctx.message.delete()
        await ctx.send(to_say)

def setup(client):
    client.add_cog(Misc(client))