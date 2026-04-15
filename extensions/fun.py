import discord
import asyncio
import re
from discord import app_commands
from discord.ext import commands
import random
import io
from config import PREFIX
from defs import replace_mentions, create_error_embed
from classes.duel import DuelGame, WeaponSelectView
from classes.akinator_game import AkinatorGame, AkinatorStartView, AkinatorGameView, AkinatorGuessView
from PIL import Image, ImageFont, ImageDraw
import textwrap

class Fun(commands.Cog, name="🎮 Diversión"):
    def __init__(self, client):
        self.client = client
        self.active_duels = {}
        self.akinator = AkinatorGame()
    
    @app_commands.command(name="akinator", description="Juega al Akinator")
    async def akinator_cmd(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        if self.akinator.get_game(user_id):
            await interaction.response.send_message("Ya tienes una partida activa. Responde a las preguntas anteriores.", ephemeral=True)
            return
        
        start_view = AkinatorStartView(self, user_id)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🎯 Akinator",
                description="Piensa en un personaje (real o ficticio) y responde a mis preguntas.",
                color=discord.Color.from_rgb(33, 150, 243)
            ),
            view=start_view
        )
        start_view.message = await interaction.original_response()
    
    @app_commands.command(name="8ball", description="Haz una pregunta de si o no y recibe una respuesta potencialmente absurda.")
    async def ball(self, interaction: discord.Interaction, pregunta: str):
        responses = {
            "positive": {
                "answers": [
                    "Claro que si", "Si, definitivamente", "Sin duda", "Así es",
                    "Como yo lo veo, sí", "Tenlo por seguro", "El destino te sonríe",
                    "Es muy probable que si", "No abandones tu sonrisa porque algo pueda doler~",
                    "Tengo un buen pronostico para ti", "Las señales apuntan a que sí",
                    "La respuesta es obvia", "En mi opinion, si", "Bueno, la esperanza es lo último que muere",
                    "Hoy es tu dia de suerte"
                ],
                "emoji": "🟢"
            },
            "neutral": {
                "answers": [
                    "No lo se con certeza, pero puede que si", "¿Eso lo preguntas mucho?",
                    "Creo que alguien no sale mucho", "Buena pregunta", "Aun extraño ese sillón...",
                    "Es posible", "La, la la la la la, la la la~", "Vuelve a pregunta mas tarde",
                    "Lo siento, no puedo entender tu pregunta", "Quizas",
                    "No tengo la mas minima idea", "( ͡° ͜ʖ ͡°)", "Gracias, vuelva pronto",
                    "¿Alguien ha visto una bola mágica por aquí?", "Ah, ok. Te me cuidas"
                ],
                "emoji": "🟡"
            },
            "negative": {
                "answers": [
                    "Ni lo sueñes", "Mis fuentes dicen que no", "No lo haga compa",
                    "Es muy dudoso", "En una prisión estaba con mil voces en mi ser",
                    "No lo creo", "No te hagas ilusiones", "Oh no, creo que deje el horno encendido",
                    "No cuentes con ello", "De ninguna forma", "No es posible",
                    "Ni en un millon de años", "Ve a casa y reflexiona sobre tu vida",
                    "No hay ninguna posibilidad de eso", "Una flama roja ardió y nuestro pan quemo~"
                ],
                "emoji": "🔴"
            }
        }

        choice = random.choice(list(responses.values()))
        answer = random.choice(choice["answers"])

        embed = discord.Embed(color=discord.Color.orange())
        embed.set_author(name="Bola mágica", icon_url="https://twemoji.maxcdn.com/2/72x72/1f3b1.png")
        embed.add_field(name="Pregunta:", value=pregunta, inline=False)
        embed.add_field(name="Respuesta:", value=f"{choice['emoji']} | `{answer}`", inline=False)
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}", icon_url=interaction.user.display_avatar)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rip", description="Crea una tumba con dedicatoria.")
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

    @app_commands.command(name="coinflip", description="Lanza una moneda y mira qué sale.")
    async def coinflip(self, interaction: discord.Interaction):
        result = random.choice(["cara", "cruz"])
        emoji = "🪙" if result == "cara" else "📀"

        embed = discord.Embed(
            title="🪙 Tirada de Moneda",
            description=f"{emoji} ¡Ha salido **{result.capitalize()}**!",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}", icon_url=interaction.user.display_avatar)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="challenge", description="Desafia a tus amigos a un duelo a muerte con cuchillos.")
    async def challenge(self, interaction: discord.Interaction, miembro: discord.Member):
        if miembro == interaction.user:
            await interaction.response.send_message("¡No puedes desafiarte a ti mismo!")
            return

        is_bot = miembro.id == self.client.user.id
        
        key = tuple(sorted([interaction.user.id, miembro.id]))
        if key in self.active_duels:
            await interaction.response.send_message("¡Ya hay un duelo activo entre estos usuarios!")
            return

        game = DuelGame(interaction.user, miembro, is_bot)
        self.active_duels[key] = game

        embed = discord.Embed(
            title="⚔️ ¡Duelo!",
            description=f"**{interaction.user.display_name}** vs **{miembro.display_name}**\n\n"
                       f"❤️ Cada jugador tiene **100 HP**\n"
                       f"🎯 **Ronda 1** - Le toca a **{interaction.user.display_name}**",
            color=discord.Color.orange()
        )
        embed.add_field(
            name=f"❤️ {interaction.user.display_name}",
            value="**100** HP",
            inline=True
        )
        embed.add_field(
            name=f"❤️ {miembro.display_name}",
            value="**100** HP",
            inline=True
        )
        embed.add_field(
            name="🎯 Elige tu arma",
            value="🗡️ Daga (80%) | 🏹 Ballesta (60%) | 🕸️ Red (20%)",
            inline=False
        )
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}", icon_url=interaction.user.display_avatar)

        view = WeaponSelectView(game, None, self)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="roll", description="Lanza dados. Usa '2d6' para 2 dados de 6 caras o solo '20' para un d20.")
    async def roll(self, interaction: discord.Interaction, dados: str):
        # Parse the input: can be "2d6", "d20", or just "6"
        dados = dados.lower().strip()

        # Pattern: optional number, d, number (e.g., "2d6", "d20", "3d8")
        match = re.match(r'^(\d*)d?(\d+)$', dados)

        if not match:
            await interaction.response.send_message(
                embed=create_error_embed("Formato inválido. Usa: `20` (dado de 20), `2d6` (2 dados de 6), `d8` (dado de 8)"),
                ephemeral=True
            )
            return

        num_dice_str, sides_str = match.groups()
        num_dice = int(num_dice_str) if num_dice_str else 1
        sides = int(sides_str)

        # Limits
        if num_dice < 1 or num_dice > 100:
            await interaction.response.send_message(
                embed=create_error_embed("Solo puedo lanzar entre 1 y 100 dados."),
                ephemeral=True
            )
            return

        if sides < 2 or sides > 1000:
            await interaction.response.send_message(
                embed=create_error_embed("Los dados deben tener entre 2 y 1000 caras."),
                ephemeral=True
            )
            return

        # Roll the dice
        rolls = [random.randint(1, sides) for _ in range(num_dice)]
        total = sum(rolls)

        # Build the result message
        if num_dice == 1:
            description = f"🎲 ¡Sacaste **{rolls[0]}**!"
        else:
            rolls_str = " + ".join(str(r) for r in rolls)
            if len(rolls_str) > 1000:
                # Too many rolls to display individually
                description = f"🎲 Lanzaste **{num_dice}d{sides}**\n📊 Total: **{total}**"
            else:
                description = f"🎲 Lanzaste **{num_dice}d{sides}**\n🎯 Resultados: {rolls_str}\n📊 Total: **{total}**"

        embed = discord.Embed(
            title="🎲 Lanzamiento de Dados",
            description=description,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}", icon_url=interaction.user.display_avatar)

        await interaction.response.send_message(embed=embed)


async def setup(client):
    await client.add_cog(Fun(client))
