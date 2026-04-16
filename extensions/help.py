import discord
from discord import app_commands
from discord.ext import commands
from discord import ui
from i18n import t


class Help(commands.Cog, name="❓ Help"):
    def __init__(self, Bot):
        self.Bot = Bot

    @app_commands.command(
        name=app_commands.locale_str("help"),
        description=app_commands.locale_str("help_description")
    )
    async def help_command(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id if interaction.guild else 0
        view = HelpView(self.Bot, guild_id)
        embed = view.get_main_embed(guild_id)
        await interaction.response.send_message(embed=embed, view=view)


class HelpView(ui.View):
    def __init__(self, bot, guild_id=0):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.update_select(guild_id)

    def get_category_name(self, cog_name, guild_id=0):
        category_map = {
            "❓ Ayuda": "cog_ayuda",
            "❓ Help": "cog_ayuda",
            "Ayuda": "cog_ayuda",
            "Help": "cog_ayuda",
            "🔍 Busqueda": "cog_busqueda",
            "🔍 Search": "cog_busqueda",
            "🎮 Diversión": "cog_diversion",
            "🎮 Fun": "cog_diversion",
            "⛅ Clima": "cog_clima",
            "⛅ Weather": "cog_clima",
            "🌤️ Clima": "cog_clima",
            "🌤️ Weather": "cog_clima",
            "⚙️ Miscelaneos": "cog_misc",
            "⚙️ Misc": "cog_misc",
            "🛠️ Configuración": "cog_config",
            "🛠️ Settings": "cog_config",
            "Settings": "cog_config",
        }
        key = category_map.get(cog_name, cog_name)
        return t(guild_id, key) if key.startswith("cog_") else cog_name

    def update_select(self, guild_id=0):
        self.guild_id = guild_id
        self.clear_items()

        help_cog_name = t(guild_id, "cog_ayuda")
        options = [discord.SelectOption(label=t(guild_id, "principal_category"), value=help_cog_name)]
        for cog in self.bot.cogs.values():
            translated_name = self.get_category_name(cog.qualified_name, guild_id)
            if translated_name != help_cog_name:
                options.append(discord.SelectOption(label=translated_name, value=cog.qualified_name))

        select = ui.Select(
            custom_id="help_category",
            placeholder=t(guild_id, "navigate_categories"),
            options=options
        )
        self.add_item(select)

    def get_commands_for_cog(self, cog_name):
        commands = []
        cog = self.bot.cogs.get(cog_name)
        if cog:
            for attr_name in dir(cog):
                attr = getattr(cog, attr_name)
                if isinstance(attr, app_commands.Command):
                    name = str(attr.name) if isinstance(attr.name, app_commands.locale_str) else attr.name
                    desc = str(attr.description) if isinstance(attr.description, app_commands.locale_str) else attr.description
                    translated_name = t(self.guild_id, name) if name != attr.name else name
                    translated_desc = t(self.guild_id, desc) if desc else t(self.guild_id, "no_description")
                    commands.append((translated_name, translated_desc))
        return commands

    def get_main_embed(self, guild_id=0):
        self.guild_id = guild_id
        embed = discord.Embed(
            title=t(guild_id, "help_title"),
            description=t(guild_id, "select_category"),
            color=discord.Color.purple()
        )

        categories = []
        help_cog_name = t(guild_id, "cog_ayuda")
        for cog in self.bot.cogs.values():
            translated_name = self.get_category_name(cog.qualified_name, guild_id)
            if translated_name != help_cog_name:
                cmds = self.get_commands_for_cog(cog.qualified_name)
                if cmds:
                    categories.append(f"{translated_name} ({t(guild_id, 'commands_count', count=len(cmds))})")

        if categories:
            embed.add_field(name=t(guild_id, "available_categories"), value="\n".join(categories), inline=False)

        embed.set_footer(text=t(guild_id, "footer_kirin"))
        return embed

    def get_category_embed(self, category, guild_id=0):
        self.guild_id = guild_id
        help_cog_name = t(guild_id, "cog_ayuda")
        translated_name = self.get_category_name(category, guild_id)
        if translated_name == help_cog_name:
            return self.get_main_embed(guild_id)

        embed = discord.Embed(
            title=translated_name,
            color=discord.Color.purple()
        )

        commands = self.get_commands_for_cog(category)

        if commands:
            cmd_list = [f"**/{name}** - {desc}" for name, desc in commands]
            embed.description = "\n".join(cmd_list)
        else:
            embed.description = t(guild_id, "no_commands_category")

        embed.set_footer(text=t(guild_id, "footer_kirin"))
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data.get("component_type") == 3:
            category = interaction.data["values"][0]
            guild_id = interaction.guild.id if interaction.guild else 0
            self.guild_id = guild_id
            embed = self.get_category_embed(category, guild_id)
            await interaction.response.edit_message(embed=embed, view=self)
            return True
        return True


async def setup(Bot):
    await Bot.add_cog(Help(Bot))
