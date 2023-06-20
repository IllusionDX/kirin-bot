import discord
from discord.ext import commands
import asyncio
from modules import chatbot

class GPT(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.message_id = ""
		self.system_message = "You'll be playing the role of Autumn Blaze, the cheerful and talkative female kirin from My Little Pony: Friendship is Magic. As Autumn Blaze, you'll talk to the user in their language and assist them with any request."
		self.command_queue = asyncio.Queue()

	@commands.group(name="chat", invoke_without_command=True, aliases=["c"])
	async def chat(self, ctx, *, message: str = None):
		if not message:
			await ctx.send("Por favor escribe algo para poder responder!")
			return

		prompt = message
		await self.command_queue.put((ctx, prompt))  # Enqueue the command

	@chat.command(name="reset")
	async def reset(self, ctx):
		self.message_id = ""

		# Send a message to the user
		async with ctx.typing(): 
			await ctx.send("La conversación ha sido reiniciada.")

	async def process_command_queue(self):
		while True:
			ctx, prompt = await self.command_queue.get()  # Dequeue the command

			try:
				async with ctx.typing():
					resp = await chatbot.Completion.create(prompt=prompt, parentMessageId=self.message_id, systemMessage=self.system_message)

				answer = resp["text"]
				self.message_id = resp["id"]

				# Split the response if it exceeds 2000 characters
				chunks = []
				while len(answer) > 2000:
					last_space_index = answer[:2000].rfind(" ")
					if last_space_index == -1:
						last_space_index = 2000
					chunks.append(answer[:last_space_index])
					answer = answer[last_space_index:].lstrip()
				chunks.append(answer)

				# Check if the original message exists
				try:
					original_message = await ctx.fetch_message(ctx.message.id)
				except discord.NotFound:
					original_message = None

				# Send the chunks as messages
				for i, chunk in enumerate(chunks):
					if original_message is not None:
						if i == 0:
							await original_message.reply(chunk)  # Send the first chunk as a reply to the original message
						else:
							await ctx.send(chunk)  # Send the remaining chunks as regular messages
					else:
						await ctx.send(chunk)  # Send all chunks as regular messages if the original message is deleted

				await asyncio.sleep(3)  # Delay of 3 seconds between commands

			except Exception as e:
				await ctx.send(f"Ha ocurrido un error: {e}")
				# Handle the exception as per your requirement

	@commands.Cog.listener()
	async def on_ready(self):
		self.bot.loop.create_task(self.process_command_queue())

async def setup(bot):
	await bot.add_cog(GPT(bot))