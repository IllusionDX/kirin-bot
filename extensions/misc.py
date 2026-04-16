import discord
from discord import app_commands
from discord.ext import commands


class Misc(commands.Cog, name="⚙️ Misc"):
    def __init__(self, Bot):
        self.Bot = Bot

    @app_commands.command(
        name=app_commands.locale_str("say"),
        description=app_commands.locale_str("say_description")
    )
    async def say(self, interaction: discord.Interaction, mensaje: str):
        if interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(mensaje)
        else:
            await interaction.response.send_message(mensaje)


async def setup(Bot):
    await Bot.add_cog(Misc(Bot))