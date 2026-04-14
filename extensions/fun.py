import discord
import asyncio
from discord import app_commands
from discord.ext import commands
import random
import io
from config import PREFIX
from defs import replace_mentions
from classes.duel import DuelGame
from classes.akinator_game import AkinatorGame
from PIL import Image, ImageFont, ImageDraw
import textwrap


class WeaponSelectView(discord.ui.View):
    def __init__(self, game: DuelGame, message: discord.Message, cog):
        super().__init__(timeout=60)
        self.game = game
        self.message = message
        self.cog = cog
        
        for weapon in DuelGame.weapons:
            button = discord.ui.Button(
                label=f"{weapon['icon']} {weapon['name']}",
                style=discord.ButtonStyle.primary
            )
            button.callback = self.make_callback(weapon)
            self.add_item(button)
    
    def make_callback(self, weapon):
        async def callback(interaction: discord.Interaction):
            if self.game.is_bot:
                if interaction.user.id != self.game.p1.id:
                    await interaction.response.send_message("¡No es tu turno!", ephemeral=True)
                    return
                await self.handle_bot_turn(interaction, weapon)
            else:
                if interaction.user.id != self.game.current_turn.id:
                    await interaction.response.send_message("¡No es tu turno!", ephemeral=True)
                    return
                await self.handle_pvp_turn(interaction, weapon)
            
            self.stop()
        return callback
    
    async def handle_bot_turn(self, interaction: discord.Interaction, player_weapon):
        p1_weapon = player_weapon
        p2_weapon = random.choice(DuelGame.weapons)
        
        p1_hit = random.random() * 100 < p1_weapon['chance']
        p2_hit = random.random() * 100 < p2_weapon['chance']
        
        p1_damage = p1_weapon['damage'] if p1_hit else 0
        p2_damage = p2_weapon['damage'] if p2_hit else 0
        
        self.game.p2_hp -= p1_damage
        self.game.p1_hp -= p2_damage
        
        embed = self.build_round_embed(
            p1_weapon, p2_weapon,
            p1_hit, p2_hit,
            p1_damage, p2_damage
        )
        
        if self.game.is_over():
            await self.end_duel(interaction, embed, self.cog)
        else:
            self.game.round += 1
            embed.description += f"\n\n🎯 **Ronda {self.game.round}** - ¡Elige tu arma, **{self.game.p1.display_name}**!"
            view = WeaponSelectView(self.game, self.message, self.cog)
            await interaction.response.edit_message(embed=embed, view=view)
    
    async def handle_pvp_turn(self, interaction: discord.Interaction, weapon):
        is_p1_turn = self.game.current_turn.id == self.game.p1.id
        
        if not hasattr(self.game, 'p1_weapon'):
            self.game.p1_weapon = None
        if not hasattr(self.game, 'p2_weapon'):
            self.game.p2_weapon = None
        
        if is_p1_turn:
            self.game.p1_weapon = weapon
        else:
            self.game.p2_weapon = weapon
        
        if self.game.p1_weapon and self.game.p2_weapon:
            p1_hit = random.random() * 100 < self.game.p1_weapon['chance']
            p2_hit = random.random() * 100 < self.game.p2_weapon['chance']
            
            p1_damage = self.game.p1_weapon['damage'] if p1_hit else 0
            p2_damage = self.game.p2_weapon['damage'] if p2_hit else 0
            
            self.game.p2_hp -= p1_damage
            self.game.p1_hp -= p2_damage
            
            embed = self.build_round_embed(
                self.game.p1_weapon, self.game.p2_weapon,
                p1_hit, p2_hit,
                p1_damage, p2_damage
            )
            
            self.game.p1_weapon = None
            self.game.p2_weapon = None
            
            if self.game.is_over():
                await self.end_duel(interaction, embed, self.cog)
            else:
                self.game.next_turn()
                self.game.round += 1
                embed.description += f"\n\n🎯 **Ronda {self.game.round}** - Le toca a **{self.game.current_turn.display_name}**"
                view = WeaponSelectView(self.game, self.message, self.cog)
                await interaction.response.edit_message(embed=embed, view=view)
        else:
            self.game.next_turn()
            embed = self.build_status_embed()
            view = WeaponSelectView(self.game, self.message, self.cog)
            await interaction.response.edit_message(embed=embed, view=view)
    
    def build_status_embed(self, is_bot=False):
        if is_bot:
            next_turn = "🎯 **Tu turno** - ¡Elige tu arma!"
            turn_num = self.game.round
        else:
            next_turn = f"🎯 Le toca a **{self.game.current_turn.display_name}**"
            turn_num = self.game.round
        
        embed = discord.Embed(
            title="⚔️ ¡Duelo!",
            description=f"**Ronda {turn_num}** | {next_turn}",
            color=discord.Color.orange()
        )
        embed.add_field(
            name=f"❤️ {self.game.p1.display_name}",
            value=f"**{self.game.p1_hp}** HP",
            inline=True
        )
        embed.add_field(
            name=f"❤️ {self.game.p2.display_name}",
            value=f"**{self.game.p2_hp}** HP",
            inline=True
        )
        embed.add_field(
            name="🎯 Elige tu arma",
            value="🗡️ Daga (80%) | 🏹 Ballesta (60%) | 🕸️ Red (20%)",
            inline=False
        )
        return embed
    
    def build_round_embed(self, w1, w2, h1, h2, d1, d2):
        p1_name = self.game.p1.display_name
        p2_name = self.game.p2.display_name
        
        log_p1 = f"**{p1_name}** atacó con {w1['icon']} **{w1['name']}** "
        if h1:
            log_p1 += f"e hizo **{d1}** de daño. 💥"
        else:
            log_p1 += f"y falló! ❌"
            
        log_p2 = f"**{p2_name}** atacó con {w2['icon']} **{w2['name']}** "
        if h2:
            log_p2 += f"e hizo **{d2}** de daño. 💥"
        else:
            log_p2 += f"y falló! ❌"
            
        embed = discord.Embed(
            title=f"⚔️ Resultados de la Ronda {self.game.round}",
            description=f"{log_p1}\n{log_p2}",
            color=discord.Color.red()
        )
        embed.add_field(
            name=f"❤️ {p1_name}",
            value=f"**{max(0, self.game.p1_hp)}** HP",
            inline=True
        )
        embed.add_field(
            name=f"❤️ {p2_name}",
            value=f"**{max(0, self.game.p2_hp)}** HP",
            inline=True
        )
        return embed
    
    async def end_duel(self, interaction, embed, cog):
        winner = self.game.get_winner()
        if winner:
            embed.description += f"\n\n🏆 **{winner.display_name} GANA! 🎉**"
            embed.color = discord.Color.green()
        else:
            embed.description += "\n\n🤝 **EMPATE!**"
            embed.color = discord.Color.gold()
        
        key = self.game.get_key()
        if key in cog.active_duels:
            del cog.active_duels[key]
        
        await interaction.response.edit_message(embed=embed, view=None)


class AkinatorStartView(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
    
    @discord.ui.button(label="Comenzar", custom_id="aki_start", emoji="▶️", style=discord.ButtonStyle.success)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Este botón no es para ti.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            await self.cog.akinator.start(self.user_id)
            
            view = AkinatorGameView(self.cog, self.user_id)
            view.update_question()
            
            await interaction.edit_original_response(
                content=None,
                embed=view.get_question_embed(),
                view=view
            )
        except Exception as e:
            import traceback
            await interaction.edit_original_response(
                content=f"Error al iniciar: {e}\n\n```\n{traceback.format_exc()[:500]}\n```",
                view=None
            )


class AkinatorGameView(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=120)
        self.cog = cog
        self.user_id = user_id
    
    def update_question(self):
        self.current_question = self.cog.akinator.get_question(self.user_id)
    
    def get_question_embed(self):
        prog = round(self.cog.akinator.get_progress(self.user_id))
        step = self.cog.akinator.get_step(self.user_id)
        
        r = min(255, int(prog * 2.55))
        g = min(165, int(prog * 1.2))
        b = max(0, 255 - int(prog * 2.55))
        color = discord.Color.from_rgb(r, g, b)
        
        filled = int(prog / 10)
        bar = "🟧" * filled + "⬛" * (10 - filled)
        
        embed = discord.Embed(
            title=f"🎯 Pregunta #{step + 1}",
            description=f"### {self.current_question}",
            color=color
        )
        embed.add_field(name="Progresión", value=f"{bar} **{prog}%**", inline=False)
        embed.set_footer(text="Responde con los botones de abajo")
        return embed
    
    @discord.ui.button(label="Sí", custom_id="aki_yes", emoji="✅", style=discord.ButtonStyle.success)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._answer(interaction, "yes")
    
    @discord.ui.button(label="No", custom_id="aki_no", emoji="❌", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._answer(interaction, "no")
    
    @discord.ui.button(label="Probablemente", custom_id="aki_probably", emoji="🤔", style=discord.ButtonStyle.secondary)
    async def probably(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._answer(interaction, "probably")
    
    @discord.ui.button(label="No sé", custom_id="aki_dont_know", emoji="❓", style=discord.ButtonStyle.secondary)
    async def dont_know(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._answer(interaction, "i don't know")
    
    @discord.ui.button(label="Atrás", custom_id="aki_back", emoji="🔙", style=discord.ButtonStyle.primary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Este no es tu juego.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            await self.cog.akinator.back(self.user_id)
            self.update_question()
            await interaction.edit_original_response(
                content=None,
                embed=self.get_question_embed(),
                view=self
            )
        except Exception as e:
            await interaction.followup.send(f"No puedes volver más atrás: {e}", ephemeral=True)
    
    async def _answer(self, interaction: discord.Interaction, answer: str):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Este no es tu juego.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            await self.cog.akinator.answer(self.user_id, answer)
            self.update_question()
            
            if self.cog.akinator.is_win(self.user_id):
                guess = self.cog.akinator.get_guess(self.user_id)
                embed = discord.Embed(
                    title="🤔 ¿Es este tu personaje?",
                    description=f"¿Es **{guess['name']}**?",
                    color=discord.Color.yellow()
                )
                if guess['description']:
                    embed.add_field(name="Descripción:", value=guess['description'][:500], inline=False)
                if guess['photo']:
                    embed.set_image(url=guess['photo'])
                
                guess_view = AkinatorGuessView(self.cog, self.user_id)
                await interaction.edit_original_response(content=None, embed=embed, view=guess_view)
                return
            
            if self.cog.akinator.is_finished(self.user_id):
                embed = discord.Embed(
                    title="🏆 ¡Me rindo!",
                    description="Has ganado.",
                    color=discord.Color.red()
                )
                await interaction.edit_original_response(content=None, embed=embed, view=None)
                self.cog.akinator.remove_game(self.user_id)
                return
            
            await interaction.edit_original_response(
                content=None,
                embed=self.get_question_embed(),
                view=self
            )
        except Exception as e:
            import traceback
            await interaction.edit_original_response(
                content=f"Error: {e}\n\n```\n{traceback.format_exc()[:500]}\n```",
                embed=None,
                view=None
            )
            self.cog.akinator.remove_game(self.user_id)


class AkinatorGuessView(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
    
    @discord.ui.button(label="¡Sí!", custom_id="guess_yes", emoji="✅", style=discord.ButtonStyle.success)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Este no es tu juego.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            await self.cog.akinator.choose(self.user_id)
            game = self.cog.akinator.get_game(self.user_id)
            embed = discord.Embed(
                title="🎉 ¡Sabía que lo adivinaría!",
                description="¡Gracias por jugar!",
                color=discord.Color.gold()
            )
            embed.add_field(name="Personaje:", value=f"**{game.name_proposition}**", inline=False)
            if getattr(game, 'photo', None):
                embed.set_image(url=game.photo)
            
            await interaction.edit_original_response(content=None, embed=embed, view=None)
            self.cog.akinator.remove_game(self.user_id)
        except Exception as e:
            await interaction.edit_original_response(content=f"Error: {e}", embed=None, view=None)
            self.cog.akinator.remove_game(self.user_id)
    
    @discord.ui.button(label="No", custom_id="guess_no", emoji="❌", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Este no es tu juego.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            await self.cog.akinator.exclude(self.user_id)
            
            if self.cog.akinator.is_finished(self.user_id):
                embed = discord.Embed(
                    title="🏆 ¡Me rindo!",
                    description="Has ganado.",
                    color=discord.Color.red()
                )
                await interaction.edit_original_response(content=None, embed=embed, view=None)
                self.cog.akinator.remove_game(self.user_id)
                return
            
            view = AkinatorGameView(self.cog, self.user_id)
            view.update_question()
            
            await interaction.edit_original_response(
                content=None,
                embed=view.get_question_embed(),
                view=view
            )
        except Exception as e:
            await interaction.edit_original_response(content=f"Error: {e}", embed=None, view=None)
            self.cog.akinator.remove_game(self.user_id)


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
        
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🎯 Akinator",
                description="Piensa en un personaje (real o ficticio) y responde a mis preguntas.",
                color=discord.Color.from_rgb(33, 150, 243)
            ),
            view=AkinatorStartView(self, user_id),
            ephemeral=True
        )
    
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
        def rect_text(box, text, font):
            x1, y1, x2, y2 = box[0], box[1], box[2], box[3]
            w = font.getlength(text)
            bbox = font.getbbox(text)
            h = bbox[3] - bbox[1]
            x = (x2 - x1 - w)/2 + x1
            y = (y2 - y1 - h)/2 + y1
            return (x, y)

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
        draw.text((rect_text(top_box, name, font_top)), name, fill="black", align="center", font=font_top)

        if inscripcion is not None:
            field = "\n".join(textwrap.wrap(inscripcion, 17, max_lines=4, placeholder="..."))
            draw.multiline_text((rect_text(bottom_box, field, font)), field, fill="black", align="center", font=font)

        img.save(temp, "png")
        temp.seek(0)

        await interaction.followup.send(file=discord.File(filename="rip.png", fp=temp))

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


async def setup(client):
    await client.add_cog(Fun(client))
