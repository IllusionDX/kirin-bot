import discord
from discord.ext import commands
from modules import chatbot
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import traceback

class GPT(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.completion = chatbot.Completion()
		self.queue = asyncio.Queue()
		self.lock = asyncio.Lock()
		self.executor = ThreadPoolExecutor()
		self.last_completion_time = time.monotonic()
		self.delay = 5

	@commands.group(name="chat", invoke_without_command=True, aliases=["c"])
	async def chat(self, ctx, *, message: str = None):
		if not message:
			await ctx.send("Por favor escribe algo para poder responder!")
			return

		prompt = message

		async with self.lock:
			# Wait until it's been at least 3 seconds since the last order completed
			time_since_last_completion = time.monotonic() - self.last_completion_time
			if time_since_last_completion < self.delay:
				await asyncio.sleep(self.delay - time_since_last_completion)

			# Add the message to the queue
			await self.queue.put((ctx.channel.id, ctx.author.id, prompt))

			# Execute the current order
			async with ctx.typing():
				try:
					channel_id, author_id, prompt = await self.queue.get()
					response = await self.bot.loop.run_in_executor(self.executor, self.completion.get_response, prompt)
				except Exception as e:
					traceback.print_exc()
					response = "Ocurrió un error mientras se generaba la respuesta."

			# Update the last completion time
			self.last_completion_time = time.monotonic()

		# Send the response
		if len(response) > 2000:
			# Split long responses into chunks and send each chunk separately
			response_chunks = [response[i:i+2000].strip() for i in range(0, len(response), 2000)]
			for i, chunk in enumerate(response_chunks):
				if i == 0:
					await ctx.reply(chunk.strip())
				else:
					await ctx.send(chunk.strip())
		else:
			await ctx.reply(response.strip())

	@chat.command(name="reset")
	async def reset(self, ctx):
		async with self.lock:
			# Wait until it's been at least 3 seconds since the last order completed
			time_since_last_completion = time.monotonic() - self.last_completion_time
			if time_since_last_completion < 3:
				await asyncio.sleep(3 - time_since_last_completion)

			# Add the reset order to the queue
			await self.queue.put((ctx.channel.id, ctx.author.id, None))

			# Execute the reset order
			async with ctx.typing():
				try:
					channel_id, author_id, _ = await self.queue.get()
					if not _:
						self.completion.reset()
				except Exception as e:
					traceback.print_exc()
					print(f"Error reiniciando el contexto: {e}")

			# Update the last completion time
			self.last_completion_time = time.monotonic()

		# Send a message to the user
		await ctx.send("El contexto ha sido reiniciado.")

async def setup(bot):
	await bot.add_cog(GPT(bot))