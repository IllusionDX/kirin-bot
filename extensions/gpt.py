import discord
from discord.ext import commands
from modules import chatbot
from queue import Queue
import concurrent.futures
import asyncio

class GPT(commands.Cog):
    completion = chatbot.Completion()
    queue = Queue()
    lock = asyncio.Lock()

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="chat", invoke_without_command=True, aliases=["c"])
    async def chat(self, ctx, *, message:str = None):
        prompt = message
        response = ""

        # Add the message to the queue
        async with self.lock:
            self.queue.put((ctx.channel.id, ctx.author.id))

        async with self.lock:
            # Wait for the previous order to finish executing
            while not self.queue.empty() and self.queue.queue[0] != (ctx.channel.id, ctx.author.id):
                await asyncio.sleep(0.1)

            # Execute the current order
            async with ctx.typing():
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    response = await self.bot.loop.run_in_executor(executor, self.completion.get_response, prompt)

            # Remove the current order from the queue
            self.queue.get()

        # Send the response
        if len(response) > 2000:
            response_list = response.split()
            response_chunks = []
            current_chunk = ""
            for word in response_list:
                if len(current_chunk + " " + word) <= 2000:
                    current_chunk += " " + word
                else:
                    response_chunks.append(current_chunk)
                    current_chunk = word
            response_chunks.append(current_chunk)

            for chunk in response_chunks:
                await ctx.send(chunk.strip())
        else:
            await ctx.send(response.strip())

    @chat.command(name="reset")
    async def reset(self, ctx):
        async with self.lock:
            # Add the reset order to the queue
            self.queue.put((ctx.channel.id, ctx.author.id))

        async with self.lock:
            # Wait for the previous order to finish executing
            while not self.queue.empty() and self.queue.queue[0] != (ctx.channel.id, ctx.author.id):
                await asyncio.sleep(0.1)

            # Execute the reset order
            self.completion.reset()

            # Remove the reset order from the queue
            self.queue.get()

        async with ctx.typing():
            # Send a message to the user
            await ctx.send("El contexto ha sido reseteado.")

async def setup(bot):
    await bot.add_cog(GPT(bot))