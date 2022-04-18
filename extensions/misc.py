from nextcord.ext import commands

class Misc(commands.Cog, name="Miscelaneos"):
	def __init__(self, Bot):
		self.Bot = Bot

	@commands.command()
	async def say(self, ctx, *, to_say):
		await ctx.trigger_typing()

		if ctx.channel.permissions_for(ctx.me).manage_messages:
			await ctx.message.delete()
		
		await ctx.send(to_say)

def setup(Bot):
	Bot.add_cog(Misc(Bot))