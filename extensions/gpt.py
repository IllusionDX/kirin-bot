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
        await ctx.send("El contexto ha sido reiniciado.")

    async def process_command_queue(self):
        while True:
            ctx, prompt = await self.command_queue.get()  # Dequeue the command

            async with ctx.typing():
                resp = await chatbot.Completion.create(prompt=prompt, parentMessageId=self.message_id, systemMessage=self.system_message)

            answer = resp["text"]
            self.message_id = resp["id"]

            # Split the response if it exceeds 2000 characters
            chunks = [answer[i:i+2000] for i in range(0, len(answer), 2000)]

            # Send the chunks as messages
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await ctx.reply(chunk)  # Send the first chunk as a reply
                else:
                    await ctx.send(chunk)  # Send the remaining chunks as regular messages

            await asyncio.sleep(3)  # Delay of 3 seconds between commands

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(self.process_command_queue())

async def setup(bot):
    await bot.add_cog(GPT(bot))