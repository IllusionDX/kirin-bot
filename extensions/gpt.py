import discord
from discord.ext import commands
from modules import chatbot
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

class GPT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.completion = chatbot.Completion()
        self.queue = asyncio.Queue()
        self.lock = asyncio.Lock()
        self.executor = ThreadPoolExecutor()
        self.last_completion_time = time.monotonic()

    @commands.group(name="chat", invoke_without_command=True, aliases=["c"])
    async def chat(self, ctx, *, message: str = None):
        if not message:
            await ctx.send("Please provide a message to respond to!")
            return

        prompt = message

        # Add the message to the queue
        await self.queue.put((ctx.channel.id, ctx.author.id))

        async with self.lock:
            # Wait until it's been at least 2 seconds since the last order completed
            await asyncio.sleep(max(0, 2 - (time.monotonic() - self.last_completion_time)))

            # Execute the current order
            async with ctx.typing():
                try:
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(self.executor, self.completion.get_response, prompt)
                except Exception as e:
                    print(f"Error generating response: {e}")
                    response = "An error occurred while generating the response."

            # Update the last completion time
            self.last_completion_time = time.monotonic()

            # Remove the current order from the queue
            await self.queue.get()

        # Send the response
        if len(response) > 2000:
            # Split long responses into chunks and send each chunk separately
            response_chunks = [response[i:i+2000].strip() for i in range(0, len(response), 2000)]
            for chunk in response_chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(response.strip())

    @chat.command(name="reset")
    async def reset(self, ctx):
        # Add the reset order to the queue
        await self.queue.put((ctx.channel.id, ctx.author.id))

        async with self.lock:
            # Wait until it's been at least 2 seconds since the last order completed
            await asyncio.sleep(max(0, 2 - (time.monotonic() - self.last_completion_time)))

            # Execute the reset order
            try:
                self.completion.reset()
            except Exception as e:
                print(f"Error resetting context: {e}")

            # Update the last completion time
            self.last_completion_time = time.monotonic()

            # Remove the reset order from the queue
            await self.queue.get()

        async with ctx.typing():
            # Send a message to the user
            await ctx.send("Context has been reset.")

async def setup(bot):
    await bot.add_cog(GPT(bot))