import discord
from discord.ext import commands

class Misc(commands.Cog, name="Miscelaneos"):
	def __init__(self, Bot):
		self.Bot = Bot

	@commands.command(name = "say", description = "Autumn repite lo que dices.", usage = f"say [mensaje]")
	async def say(self, ctx, *, to_say):
		await ctx.typing()

		if ctx.channel.permissions_for(ctx.me).manage_messages:
			await ctx.message.delete()
		
		await ctx.send(to_say)

async def setup(Bot):
	await Bot.add_cog(Misc(Bot))