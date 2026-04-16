import discord
import akinator
import akinator.async_client as _aki_async_client
from i18n import t
from database import get_language

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


def akinator_expired_embed(guild_id=0):
    return discord.Embed(
        title=t(guild_id, "akinator_expired_title"),
        description=t(guild_id, "akinator_expired_desc"),
        color=discord.Color.red()
    )


class AkinatorGame:
    def __init__(self):
        _patch_async_handler()
        self.games = {}

    async def start(self, user_id: int, language: str = "en"):
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
    def __init__(self, cog, user_id, guild_id=0):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        self.guild_id = guild_id
        for item in self.children:
            if item.custom_id == "aki_start":
                item.label = t(guild_id, "akinator_start")

    async def on_timeout(self):
        try:
            await self.message.edit(embed=akinator_expired_embed(self.guild_id), view=None)
        except:
            pass

    @discord.ui.button(label="Start", custom_id="aki_start", emoji="▶️", style=discord.ButtonStyle.success)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.guild_id = interaction.guild.id if interaction.guild else 0
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(t(self.guild_id, "akinator_not_your_button"), ephemeral=True)
            return

        await interaction.response.defer()
        self.stop()

        try:
            lang = get_language(self.guild_id)
            await self.cog.akinator.start(self.user_id, language=lang)

            view = AkinatorGameView(self.cog, self.user_id, self.guild_id)
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
                content=t(self.guild_id, "akinator_error_start", error=f"{e}\n\n```\n{traceback.format_exc()[:500]}\n```"),
                view=None
            )


class AkinatorGameView(discord.ui.View):
    def __init__(self, cog, user_id, guild_id=0):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        self.guild_id = guild_id
        self._update_button_labels()

    def _update_button_labels(self):
        for item in self.children:
            if item.custom_id == "aki_yes":
                item.label = t(self.guild_id, "akinator_yes")
            elif item.custom_id == "aki_no":
                item.label = t(self.guild_id, "akinator_no")
            elif item.custom_id == "aki_probably":
                item.label = t(self.guild_id, "akinator_probably")
            elif item.custom_id == "aki_dont_know":
                item.label = t(self.guild_id, "akinator_dont_know")
            elif item.custom_id == "aki_back":
                item.label = t(self.guild_id, "akinator_back")

    async def on_timeout(self):
        if self.cog.akinator.get_game(self.user_id):
            if not self.cog.akinator.is_win(self.user_id) and not self.cog.akinator.is_finished(self.user_id):
                self.cog.akinator.remove_game(self.user_id)
                await self.message.edit(embed=akinator_expired_embed(self.guild_id), view=None)

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
            title=t(self.guild_id, "akinator_question", step=step + 1),
            description=f"### {self.current_question}",
            color=color
        )
        embed.add_field(name=t(self.guild_id, "akinator_progression"), value=f"{bar} **{prog}%**", inline=False)
        embed.set_footer(text=t(self.guild_id, "akinator_answer_below"))
        return embed

    @discord.ui.button(label="Yes", custom_id="aki_yes", emoji="✅", style=discord.ButtonStyle.success)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._answer(interaction, "yes")

    @discord.ui.button(label="No", custom_id="aki_no", emoji="❌", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._answer(interaction, "no")

    @discord.ui.button(label="Probably", custom_id="aki_probably", emoji="🤔", style=discord.ButtonStyle.secondary)
    async def probably(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._answer(interaction, "probably")

    @discord.ui.button(label="Don't know", custom_id="aki_dont_know", emoji="❓", style=discord.ButtonStyle.secondary)
    async def dont_know(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._answer(interaction, "i don't know")

    @discord.ui.button(label="Back", custom_id="aki_back", emoji="🔙", style=discord.ButtonStyle.primary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.guild_id = interaction.guild.id if interaction.guild else 0
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(t(self.guild_id, "akinator_not_your_game"), ephemeral=True)
            return

        await interaction.response.defer()
        self.stop()

        if not self.cog.akinator.get_game(self.user_id):
            await interaction.edit_original_response(
                embed=akinator_expired_embed(self.guild_id),
                view=None
            )
            return

        try:
            await self.cog.akinator.back(self.user_id)
            view = AkinatorGameView(self.cog, self.user_id, self.guild_id)
            view.update_question()
            view.message = await interaction.original_response()
            await interaction.edit_original_response(
                content=None,
                embed=view.get_question_embed(),
                view=view
            )
        except Exception as e:
            await interaction.followup.send(t(self.guild_id, "akinator_cant_go_back", error=e), ephemeral=True)

    async def _answer(self, interaction: discord.Interaction, answer: str):
        self.guild_id = interaction.guild.id if interaction.guild else 0
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(t(self.guild_id, "akinator_not_your_game"), ephemeral=True)
            return

        await interaction.response.defer()
        self.stop()

        if not self.cog.akinator.get_game(self.user_id):
            await interaction.edit_original_response(
                embed=akinator_expired_embed(self.guild_id),
                view=None
            )
            return

        try:
            await self.cog.akinator.answer(self.user_id, answer)
            self.update_question()

            if self.cog.akinator.is_win(self.user_id):
                guess = self.cog.akinator.get_guess(self.user_id)
                embed = discord.Embed(
                    title=t(self.guild_id, "akinator_is_this"),
                    description=t(self.guild_id, "akinator_is_name", name=guess['name']),
                    color=discord.Color.yellow()
                )
                if guess['description']:
                    embed.add_field(name=t(self.guild_id, "akinator_guess_description"), value=guess['description'][:500], inline=False)
                if guess['photo']:
                    embed.set_image(url=guess['photo'])

                guess_view = AkinatorGuessView(self.cog, self.user_id, self.guild_id)
                await interaction.edit_original_response(content=None, embed=embed, view=guess_view)
                guess_view.message = await interaction.original_response()
                return

            if self.cog.akinator.is_finished(self.user_id):
                embed = discord.Embed(
                    title=t(self.guild_id, "akinator_give_up_title"),
                    description=t(self.guild_id, "akinator_you_won"),
                    color=discord.Color.red()
                )
                await interaction.edit_original_response(content=None, embed=embed, view=None)
                return

            view = AkinatorGameView(self.cog, self.user_id, self.guild_id)
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
                content=t(self.guild_id, "error_prefix", error=f"{e}\n\n```\n{traceback.format_exc()[:500]}\n```"),
                embed=None,
                view=None
            )
            self.cog.akinator.remove_game(self.user_id)


class AkinatorGuessView(discord.ui.View):
    def __init__(self, cog, user_id, guild_id=0):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        self.guild_id = guild_id
        self.message = None
        for item in self.children:
            if item.custom_id == "guess_yes":
                item.label = t(guild_id, "akinator_guess_yes")
            elif item.custom_id == "guess_no":
                item.label = t(guild_id, "akinator_no")

    async def on_timeout(self):
        self.cog.akinator.remove_game(self.user_id)
        try:
            if self.message:
                await self.message.edit(embed=akinator_expired_embed(self.guild_id), view=None)
        except:
            pass

    @discord.ui.button(label="Yes!", custom_id="guess_yes", emoji="✅", style=discord.ButtonStyle.success)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.guild_id = interaction.guild.id if interaction.guild else 0
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(t(self.guild_id, "akinator_not_your_game"), ephemeral=True)
            return

        await interaction.response.defer()
        self.stop()

        if not self.cog.akinator.get_game(self.user_id):
            await interaction.edit_original_response(
                embed=akinator_expired_embed(self.guild_id),
                view=None
            )
            return

        try:
            await self.cog.akinator.choose(self.user_id)
            game = self.cog.akinator.get_game(self.user_id)
            embed = discord.Embed(
                title=t(self.guild_id, "akinator_knew_it"),
                description=game.question.replace(" !", "!"),
                color=discord.Color.gold()
            )
            embed.add_field(name=t(self.guild_id, "akinator_character"), value=f"**{game.name_proposition}**", inline=False)
            if getattr(game, 'photo', None):
                embed.set_image(url=game.photo)

            await interaction.edit_original_response(content=None, embed=embed, view=None)
            self.cog.akinator.remove_game(self.user_id)
        except Exception as e:
            await interaction.edit_original_response(content=t(self.guild_id, "error_prefix", error=e), embed=None, view=None)
            self.cog.akinator.remove_game(self.user_id)

    @discord.ui.button(label="No", custom_id="guess_no", emoji="❌", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.guild_id = interaction.guild.id if interaction.guild else 0
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(t(self.guild_id, "akinator_not_your_game"), ephemeral=True)
            return

        await interaction.response.defer()
        self.stop()

        if not self.cog.akinator.get_game(self.user_id):
            await interaction.edit_original_response(
                embed=akinator_expired_embed(self.guild_id),
                view=None
            )
            return

        try:
            await self.cog.akinator.exclude(self.user_id)

            if self.cog.akinator.is_finished(self.user_id):
                embed = discord.Embed(
                    title=t(self.guild_id, "akinator_give_up_title"),
                    description=t(self.guild_id, "akinator_you_won"),
                    color=discord.Color.red()
                )
                await interaction.edit_original_response(content=None, embed=embed, view=None)
                self.cog.akinator.remove_game(self.user_id)
                return

            view = AkinatorGameView(self.cog, self.user_id, self.guild_id)
            view.update_question()
            view.message = await interaction.original_response()

            await interaction.edit_original_response(
                content=None,
                embed=view.get_question_embed(),
                view=view
            )
        except Exception as e:
            await interaction.edit_original_response(content=t(self.guild_id, "error_prefix", error=e), embed=None, view=None)
            self.cog.akinator.remove_game(self.user_id)
