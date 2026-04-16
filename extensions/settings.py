import discord
from discord import app_commands
from discord.ext import commands
from database import get_language, set_language
from i18n import t
from defs import create_success_embed, create_error_embed

class Settings(commands.Cog, name="🛠️ Settings"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name=app_commands.locale_str("language"),
        description=app_commands.locale_str("language_description")
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(language="The language to set")
    @app_commands.choices(language=[
        discord.app_commands.Choice(name="English", value="en"),
        discord.app_commands.Choice(name="Español", value="es")
    ])
    async def language(self, interaction: discord.Interaction, language: str):
        guild = interaction.guild
        if not guild:
            embed = create_error_embed(t(0, "error_server_only"), t(0, "error_title"))
            await interaction.response.send_message(embed=embed)
            return

        # Save language preference (this updates t() to use new language)
        set_language(guild.id, language)

        # Show success message (no re-sync needed with Discord native localization)
        embed = create_success_embed(t(guild.id, "language_set"), t(guild.id, "success_title"))
        await interaction.response.send_message(embed=embed)

    @language.error
    async def language_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            embed = create_error_embed(t(interaction.guild.id if interaction.guild else 0, "error_no_permissions"), t(interaction.guild.id if interaction.guild else 0, "error_title"))
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Settings(bot))