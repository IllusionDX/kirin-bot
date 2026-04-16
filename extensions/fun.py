import discord
import asyncio
import re
from discord import app_commands
from discord.ext import commands
import random
import io
from config import PREFIX
from defs import create_error_embed
from classes.duel import DuelGame, WeaponSelectView
from classes.akinator_game import AkinatorGame, AkinatorStartView, AkinatorGameView, AkinatorGuessView
from classes.dice_roller import DiceRoller, DiceRollView
from PIL import Image, ImageFont, ImageDraw
import textwrap
from i18n import t
from database import get_language

responses_8ball = {
    "positive": [
        "Yes", "Definitely", "Without a doubt", "That's right",
        "As I see it, yes", "You can bet on it", "Fortune smiles upon you",
        "It's very likely yes", "Don't give up your smile because something might hurt~",
        "I have a good prognosis for you", "The signs point to yes",
        "The answer is obvious", "In my opinion, yes", "Well, hope is the last thing to die",
        "Today is your lucky day"
    ],
    "neutral": [
        "I'm not certain, but possibly", "Do you ask that often?",
        "I think someone doesn't get out much", "Good question", "I still miss that chair...",
        "It's possible", "La la la la la la la la~", "Ask again later",
        "Sorry, I can't understand your question", "Perhaps",
        "I have no idea", "( ͡° ͜ʖ ͡°)", "Thank you, come again",
        "Has anyone seen a magic ball around here?", "Ah, ok. Take care"
    ],
    "negative": [
        "Don't even dream about it", "My sources say no", "Don't do it, buddy",
        "Very doubtful", "In a prison I was with a thousand voices in my soul",
        "I don't think so", "Don't get your hopes up", "Oh no, I think I left the oven on",
        "Don't count on it", "No way", "Not possible",
        "Not in a million years", "Go home and reflect on your life",
        "There's no possibility of that", "A red flame burned and our bread burned~"
    ],
    "emoji_positive": "🟢",
    "emoji_neutral": "🟡",
    "emoji_negative": "🔴"
}

responses_8ball_lang = {
    "en": responses_8ball,
    "es": {
        "positive": [
            "Claro que si", "Si, definitivamente", "Sin duda", "Así es",
            "Como yo lo veo, sí", "Tenlo por seguro", "El destino te sonríe",
            "Es muy probable que si", "No abandones tu sonrisa porque algo pueda doler~",
            "Tengo un buen pronostico para ti", "Las señales apuntan a que sí",
            "La respuesta es obvia", "En mi opinion, si", "Bueno, la esperanza es lo último que muere",
            "Hoy es tu dia de suerte"
        ],
        "neutral": [
            "No lo se con certeza, pero puede que si", "¿Eso lo preguntas mucho?",
            "Creo que alguien no sale mucho", "Buena pregunta", "Aun extraño ese sillón...",
            "Es posible", "La, la la la la la, la la la~", "Vuelve a pregunta mas tarde",
            "Lo siento, no puedo entender tu pregunta", "Quizas",
            "No tengo la mas minima idea", "( ͡° ͜ʖ ͡°)", "Gracias, vuelva pronto",
            "¿Alguien ha visto una bola mágica por aquí?", "Ah, ok. Te me cuidas"
        ],
        "negative": [
            "Ni lo sueñes", "Mis fuentes dicen que no", "No lo haga compa",
            "Es muy dudoso", "En una prisión estaba con mil voces en mi ser",
            "No lo creo", "No te hagas ilusiones", "Oh no, creo que deje el horno encendido",
            "No cuentes con ello", "De ninguna forma", "No es posible",
            "Ni en un millon de años", "Ve a casa y reflexiona sobre tu vida",
            "No hay ninguna posibilidad de eso", "Una flama roja ardió y nuestro pan quemo~"
        ]
    }
}

class Fun(commands.Cog, name="🎮 Fun"):
    def __init__(self, client):
        self.client = client
        self.active_duels = {}
        self.akinator = AkinatorGame()
    
    def get_responses(self, guild_id: int):
        lang = get_language(guild_id)
        lang_responses = responses_8ball_lang.get(lang, responses_8ball_lang["en"])
        return {
            "positive": {"answers": lang_responses["positive"], "emoji": responses_8ball["emoji_positive"]},
            "neutral": {"answers": lang_responses["neutral"], "emoji": responses_8ball["emoji_neutral"]},
            "negative": {"answers": lang_responses["negative"], "emoji": responses_8ball["emoji_negative"]}
        }
    
    @app_commands.command(
        name=app_commands.locale_str("akinator"),
        description=app_commands.locale_str("akinator_description")
    )
    async def akinator_cmd(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id if interaction.guild else 0
        
        if self.akinator.get_game(user_id):
            await interaction.response.send_message(t(guild_id, "already_active_game"), ephemeral=True)
            return
        
        start_view = AkinatorStartView(self, user_id, guild_id)
        await interaction.response.send_message(
            embed=discord.Embed(
                title=t(guild_id, "akinator_title"),
                description=t(guild_id, "akinator_intro"),
                color=discord.Color.from_rgb(33, 150, 243)
            ),
            view=start_view
        )
        start_view.message = await interaction.original_response()
    
    @app_commands.command(
        name=app_commands.locale_str("8ball"),
        description=app_commands.locale_str("8ball_description")
    )
    async def ball(self, interaction: discord.Interaction, pregunta: str):
        guild_id = interaction.guild.id if interaction.guild else 0

        responses = self.get_responses(guild_id)
        choice = random.choice(list(responses.values()))
        answer = random.choice(choice["answers"])

        embed = discord.Embed(color=discord.Color.orange())
        embed.set_author(name=t(guild_id, "magic_ball_title"), icon_url="https://twemoji.maxcdn.com/2/72x72/1f3b1.png")
        embed.add_field(name=t(guild_id, "field_question"), value=pregunta, inline=False)
        embed.add_field(name=t(guild_id, "field_answer"), value=f"{choice['emoji']} | `{answer}`", inline=False)
        embed.set_footer(text=t(guild_id, "search_requested_by", user=interaction.user.display_name), icon_url=interaction.user.display_avatar)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name=app_commands.locale_str("rip"),
        description=app_commands.locale_str("rip_description")
    )
    async def rip(self, interaction: discord.Interaction, usuario: str = None, *, inscripcion: str = None):
        def get_center(box):
            return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)

        await interaction.response.defer()

        img = Image.open("./images/rip.png")
        draw = ImageDraw.Draw(img)
        temp = io.BytesIO()

        font_top = ImageFont.truetype("./fonts/librefranklin-bold.ttf", 18)
        font = ImageFont.truetype("./fonts/Roboto-Bold.ttf", 16)

        if usuario is None:
            top = interaction.user.display_name
        elif interaction.data.get("resolved"):
            top = usuario
        else:
            top = usuario

        top_box = [85, 180, 210, 220]
        bottom_box = [80, 220, 220, 300]

        name = textwrap.shorten(top, width=15, placeholder=top[:12]+"...")
        draw.text(get_center(top_box), name, fill="black", font=font_top, anchor="mm")

        if inscripcion is not None:
            field = "\n".join(textwrap.wrap(inscripcion, 17, max_lines=4, placeholder="..."))
            draw.multiline_text(get_center(bottom_box), field, fill="black", font=font, anchor="mm", align="center")

        img.save(temp, "png")
        temp.seek(0)

        await interaction.followup.send(file=discord.File(filename="rip.png", fp=temp))

    @app_commands.command(
        name=app_commands.locale_str("coinflip"),
        description=app_commands.locale_str("coinflip_description")
    )
    async def coinflip(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id if interaction.guild else 0
        result = random.choice([t(guild_id, "coinflip_heads"), t(guild_id, "coinflip_tails")])
        emoji = "🪙" if result == t(guild_id, "coinflip_heads") else "📀"

        embed = discord.Embed(
            title=t(guild_id, "coinflip_title"),
            description=t(guild_id, "coinflip_result", emoji=emoji, result=result.capitalize()),
            color=discord.Color.gold()
        )
        embed.set_footer(text=t(guild_id, "search_requested_by", user=interaction.user.display_name), icon_url=interaction.user.display_avatar)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name=app_commands.locale_str("challenge"),
        description=app_commands.locale_str("challenge_description")
    )
    async def challenge(self, interaction: discord.Interaction, miembro: discord.Member):
        guild_id = interaction.guild.id if interaction.guild else 0
        
        if miembro == interaction.user:
            await interaction.response.send_message(t(guild_id, "self_challenge_error"))
            return

        is_bot = miembro.id == self.client.user.id
        
        key = tuple(sorted([interaction.user.id, miembro.id]))
        if key in self.active_duels:
            await interaction.response.send_message(t(guild_id, "already_active_duel"))
            return

        game = DuelGame(interaction.user, miembro, is_bot)
        self.active_duels[key] = game

        embed = discord.Embed(
            title=t(guild_id, "challenge_title"),
            description=t(guild_id, "challenge_start", player1=interaction.user.display_name, player2=miembro.display_name, player=interaction.user.display_name),
            color=discord.Color.orange()
        )
        embed.add_field(
            name=t(guild_id, "hp_label", player=interaction.user.display_name),
            value=t(guild_id, "hp_value"),
            inline=True
        )
        embed.add_field(
            name=t(guild_id, "hp_label", player=miembro.display_name),
            value=t(guild_id, "hp_value"),
            inline=True
        )
        embed.add_field(
            name=t(guild_id, "weapon_select_title"),
            value=f"{t(guild_id, 'weapon_dagger')} | {t(guild_id, 'weapon_crossbow')} | {t(guild_id, 'weapon_net')}",
            inline=False
        )
        embed.set_footer(text=t(guild_id, "search_requested_by", user=interaction.user.display_name), icon_url=interaction.user.display_avatar)

        view = WeaponSelectView(game, None, self, guild_id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(
        name=app_commands.locale_str("roll"),
        description=app_commands.locale_str("roll_description")
    )
    async def roll(self, interaction: discord.Interaction, expresion: str):
        guild_id = interaction.guild.id if interaction.guild else 0
        try:
            roller = DiceRoller(expresion, guild_id)
            total = roller.roll()

            simple_result = roller.get_simple_result()

            embed = discord.Embed(
                title=t(guild_id, "roll_title"),
                description=simple_result,
                color=discord.Color.blue()
            )
            embed.set_footer(text=t(guild_id, "search_requested_by", user=interaction.user.display_name), icon_url=interaction.user.display_avatar)

            view = DiceRollView(roller, interaction.user.id, guild_id)

            await interaction.response.send_message(embed=embed, view=view)

        except ValueError as e:
            await interaction.response.send_message(
                embed=create_error_embed(f"{e}\n\n{t(guild_id, 'roll_examples')}", t(guild_id, "error_title")),
                ephemeral=True
            )
        except Exception:
            await interaction.response.send_message(
                embed=create_error_embed(t(guild_id, "roll_invalid_expression"), t(guild_id, "error_title")),
                ephemeral=True
            )
            embed.set_footer(text=t(guild_id, "search_requested_by", user=interaction.user.display_name), icon_url=interaction.user.display_avatar)

            view = DiceRollView(roller, interaction.user.id)

            await interaction.response.send_message(embed=embed, view=view)

        except ValueError as e:
            await interaction.response.send_message(
                embed=create_error_embed(f"{e}\n\n{t(guild_id, 'roll_examples')}"),
                ephemeral=True
            )
        except Exception:
            await interaction.response.send_message(
                embed=create_error_embed(t(guild_id, "roll_invalid_expression")),
                ephemeral=True
            )

async def setup(client):
    await client.add_cog(Fun(client))