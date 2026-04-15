import discord
import akinator
import akinator.async_client as _aki_async_client

_patch_done = False

def _patch_async_handler():
    global _patch_done
    if _patch_done:
        return
    
    async def _patched_async_handler(self, response):
        response.raise_for_status()
        try:
            data = response.json()
        except Exception as e:
            if "A technical problem has ocurred." in response.text:
                raise RuntimeError("A technical problem has occurred. Please try again later.") from e
            raise RuntimeError("Failed to parse the response as JSON.") from e

        if "completion" not in data:
            data["completion"] = getattr(self, "completion", None)
        if data["completion"] == "KO - TIMEOUT":
            raise RuntimeError("The session has timed out. Please start a new game.")
        if data["completion"] == "SOUNDLIKE":
            self.finished = True
            self.win = True
            if not getattr(self, "id_proposition", None):
                await self.defeat()
        elif "id_proposition" in data:
            self.win = True
            self.id_proposition = data["id_proposition"]
            self.name_proposition = data["name_proposition"]
            self.description_proposition = data["description_proposition"]
            self.step_last_proposition = self.step
            self.pseudo = data["pseudo"]
            self.flag_photo = data["flag_photo"]
            self.photo = data["photo"]
        else:
            self.akitude = data.get("akitude", None)
            self.step = int(data.get("step", getattr(self, "step", 0) + 1))
            self.progression = float(data.get("progression", getattr(self, "progression", 0.0)))
            self.question = data.get("question", getattr(self, "question", ""))
        self.completion = data["completion"]

    _aki_async_client.AsyncClient._AsyncClient__handler = _patched_async_handler
    _patch_done = True


def akinator_expired_embed():
    return discord.Embed(
        title="⏰ Sesión expirada",
        description="Tu sesión de Akinator ha expirado. Usa /akinator para jugar de nuevo.",
        color=discord.Color.red()
    )


class AkinatorGame:
    def __init__(self):
        _patch_async_handler()
        self.games = {}
    
    async def start(self, user_id: int, language: str = "es"):
        game = akinator.AsyncAkinator()
        await game.start_game(language=language)
        self.games[user_id] = game
        return game
    
    def get_game(self, user_id: int):
        return self.games.get(user_id)
    
    def remove_game(self, user_id: int):
        if user_id in self.games:
            del self.games[user_id]
    
    async def answer(self, user_id: int, answer: str):
        game = self.get_game(user_id)
        if not game:
            raise RuntimeError("No active game")
        await game.answer(answer)
        return game
    
    async def back(self, user_id: int):
        game = self.get_game(user_id)
        if not game:
            raise RuntimeError("No active game")
        await game.back()
        return game
    
    async def choose(self, user_id: int):
        game = self.get_game(user_id)
        if not game:
            raise RuntimeError("No active game")
        await game.choose()
        return game
    
    async def exclude(self, user_id: int):
        game = self.get_game(user_id)
        if not game:
            raise RuntimeError("No active game")
        await game.exclude()
        return game
    
    def get_question(self, user_id: int) -> str:
        game = self.get_game(user_id)
        if not game:
            return ""
        question = getattr(game, "question", None)
        return str(question) if question else ""
    
    def get_progress(self, user_id: int) -> float:
        game = self.get_game(user_id)
        if not game:
            return 0.0
        return getattr(game, "progression", 0.0)
    
    def get_step(self, user_id: int) -> int:
        game = self.get_game(user_id)
        if not game:
            return 0
        return getattr(game, "step", 0)
    
    def is_win(self, user_id: int) -> bool:
        game = self.get_game(user_id)
        if not game:
            return False
        return getattr(game, "win", False) and not getattr(game, "finished", False)
    
    def is_finished(self, user_id: int) -> bool:
        game = self.get_game(user_id)
        if not game:
            return False
        return getattr(game, "finished", False)
    
    def get_guess(self, user_id: int) -> dict:
        game = self.get_game(user_id)
        if not game:
            return {}
        return {
            "name": getattr(game, "name_proposition", "Unknown"),
            "description": getattr(game, "description_proposition", None),
            "photo": getattr(game, "photo", None)
        }


class AkinatorStartView(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
    
    async def on_timeout(self):
        try:
            await self.message.edit(embed=akinator_expired_embed(), view=None)
        except:
            pass
    
    @discord.ui.button(label="Comenzar", custom_id="aki_start", emoji="▶️", style=discord.ButtonStyle.success)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Este botón no es para ti.", ephemeral=True)
            return
        
        await interaction.response.defer()
        self.stop()
        
        try:
            await self.cog.akinator.start(self.user_id)
            
            view = AkinatorGameView(self.cog, self.user_id)
            view.update_question()
            view.message = await interaction.original_response()
            
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
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
    
    async def on_timeout(self):
        if self.cog.akinator.get_game(self.user_id):
            if not self.cog.akinator.is_win(self.user_id) and not self.cog.akinator.is_finished(self.user_id):
                self.cog.akinator.remove_game(self.user_id)
                await self.message.edit(embed=akinator_expired_embed(), view=None)
    
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
        self.stop()
        
        if not self.cog.akinator.get_game(self.user_id):
            await interaction.edit_original_response(
                embed=akinator_expired_embed(),
                view=None
            )
            return
        
        try:
            await self.cog.akinator.back(self.user_id)
            view = AkinatorGameView(self.cog, self.user_id)
            view.update_question()
            view.message = await interaction.original_response()
            await interaction.edit_original_response(
                content=None,
                embed=view.get_question_embed(),
                view=view
            )
        except Exception as e:
            await interaction.followup.send(f"No puedes volver más atrás: {e}", ephemeral=True)
    
    async def _answer(self, interaction: discord.Interaction, answer: str):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Este no es tu juego.", ephemeral=True)
            return
        
        await interaction.response.defer()
        self.stop()
        
        if not self.cog.akinator.get_game(self.user_id):
            await interaction.edit_original_response(
                embed=akinator_expired_embed(),
                view=None
            )
            return
        
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
                # Pass message reference for guess view timeout
                guess_view.message = await interaction.original_response()
                return
            
            if self.cog.akinator.is_finished(self.user_id):
                embed = discord.Embed(
                    title="🏆 ¡Me rindo!",
                    description="Has ganado.",
                    color=discord.Color.red()
                )
                await interaction.edit_original_response(content=None, embed=embed, view=None)
                return
            
            # Refresh view with new timeout
            view = AkinatorGameView(self.cog, self.user_id)
            view.update_question()
            view.message = await interaction.original_response()
            await interaction.edit_original_response(
                content=None,
                embed=view.get_question_embed(),
                view=view
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
        self.message = None
    
    async def on_timeout(self):
        self.cog.akinator.remove_game(self.user_id)
        try:
            if self.message:
                await self.message.edit(embed=akinator_expired_embed(), view=None)
        except:
            pass
    
    @discord.ui.button(label="¡Sí!", custom_id="guess_yes", emoji="✅", style=discord.ButtonStyle.success)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Este no es tu juego.", ephemeral=True)
            return
        
        await interaction.response.defer()
        self.stop()
        
        if not self.cog.akinator.get_game(self.user_id):
            await interaction.edit_original_response(
                embed=akinator_expired_embed(),
                view=None
            )
            return
        
        try:
            await self.cog.akinator.choose(self.user_id)
            game = self.cog.akinator.get_game(self.user_id)
            embed = discord.Embed(
                title="🎉 ¡Sabía que lo adivinaría!",
                description=game.question.replace(" !", "!"),
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
        self.stop()
        
        if not self.cog.akinator.get_game(self.user_id):
            await interaction.edit_original_response(
                embed=akinator_expired_embed(),
                view=None
            )
            return
        
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
            view.message = await interaction.original_response()
            
            await interaction.edit_original_response(
                content=None,
                embed=view.get_question_embed(),
                view=view
            )
        except Exception as e:
            await interaction.edit_original_response(content=f"Error: {e}", embed=None, view=None)
            self.cog.akinator.remove_game(self.user_id)
