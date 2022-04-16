from nextcord.ext import commands

class Misc(commands.Cog, name="Miscelaneos"):
    def __init__(self, Bot):
        self.Bot = Bot

    @commands.command()
    @commands.bot_has_permissions(manage_messages=True)
    async def say(self, ctx, *, to_say):
        await ctx.trigger_typing()
        await ctx.message.delete()
        await ctx.send(to_say)

    @say.error
    async def say_error(self, ctx, error):
        await ctx.send(f"{error}")

def setup(Bot):
    Bot.add_cog(Misc(Bot))