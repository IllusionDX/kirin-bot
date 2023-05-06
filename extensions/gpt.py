import discord
from discord.ext import commands
from modules import chatbot
import asyncio

class GPT(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.completion = chatbot.Completion()
		self.queue = asyncio.Queue()
		self.lock = asyncio.Lock()

	@commands.group(name="chat", invoke_without_command=True, aliases=["c"])
	async def chat(self, ctx, *, message: str = None):
		if not message:
			await ctx.send("Por favor escribe algo para poder responder!")
			return

		prompt = message
		response = ""

		# Add the message to the queue
		await self.queue.put((ctx.channel.id, ctx.author.id))

		async with self.lock:
			# Wait for the previous order to finish executing
			while not self.queue.empty() and self.queue._queue[0] != (ctx.channel.id, ctx.author.id):
				await asyncio.sleep(2)

			# Execute the current order
			async with ctx.typing():
				try:
					response = await asyncio.to_thread(self.completion.get_response, prompt)
				except Exception as e:
					print(f"An error occurred while generating response: {e}")
					response = "Ha ocurrido un error al generar la respuesta."

			# Remove the current order from the queue
			await self.queue.get()

		# Send the response
		if len(response) > 2000:
			# Find the last space character in the response before the limit
			last_space_index = response[:2000].rfind(' ')
			if last_space_index == -1:
				# If no space is found, cut at the character limit anyway
				last_space_index = 2000
			response_chunks = [response[i:i+last_space_index].strip() for i in range(0, len(response), last_space_index)]
			for chunk in response_chunks:
				await ctx.send(chunk.strip())
		else:
			await ctx.send(response.strip())

	@chat.command(name="reset")
	async def reset(self, ctx):
		async with self.lock:
			# Add the reset order to the queue
			await self.queue.put((ctx.channel.id, ctx.author.id))

			# Wait for the previous order to finish executing
			while not self.queue.empty() and self.queue._queue[0] != (ctx.channel.id, ctx.author.id):
				await asyncio.sleep(2)

			# Execute the reset order
			try:
				self.completion.reset()
			except Exception as e:
				print(f"An error occurred while resetting context: {e}")

			# Remove the reset order from the queue
			await self.queue.get()

		async with ctx.typing():
			# Send a message to the user
			await ctx.send("El contexto ha sido reseteado.")

async def setup(bot):
	await bot.add_cog(GPT(bot))