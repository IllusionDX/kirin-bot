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
