import discord
from discord.ext import commands
from modules import chatbot

class GPT(commands.Cog):
	completion = chatbot.Completion()

	def __init__(self, bot):
		self.bot = bot

	@commands.group(name="chat", invoke_without_command=True, aliases=["c"])
	async def chat(self, ctx, *, message:str = None):
		prompt = message
		response = ""

		async with ctx.typing():
			response = await self.completion.get_response(prompt)

		# Do something with the message ID
		await ctx.send(f"{response}")

	@chat.command(name="reset")
	async def reset(self, ctx):
		# Reset the persistent message_id
		self.completion.reset()

		# Send a message to the user
		await ctx.send("El contexto ha sido reseteado.")

async def setup(bot):
	await bot.add_cog(GPT(bot))