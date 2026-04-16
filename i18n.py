import json
import os
from pathlib import Path
from discord import app_commands, Locale
from database import get_language

TRANSLATIONS = {}
LOCALES_DIR = Path(__file__).parent / "locales"


def load_translations():
    global TRANSLATIONS
    TRANSLATIONS = {}

    if not LOCALES_DIR.exists():
        return

    for file in LOCALES_DIR.glob("*.json"):
        lang_code = file.stem
        try:
            with open(file, "r", encoding="utf-8") as f:
                TRANSLATIONS[lang_code] = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error loading {file}: {e}")


def t(guild_id: int, key: str, **kwargs) -> str:
    lang = get_language(guild_id)
    text = TRANSLATIONS.get(lang, TRANSLATIONS.get("en", {})).get(key, key)

    if kwargs:
        text = text.format(**kwargs)

    return text


class KirinTranslator(app_commands.Translator):
    async def load(self):
        pass

    async def unload(self):
        pass

    async def translate(self, string: app_commands.locale_str, locale: Locale, context: app_commands.TranslationContext):
        locale_str = str(string)

        translations = TRANSLATIONS.get(locale.value, TRANSLATIONS.get("en", {}))

        if context.location == app_commands.TranslationContextLocation.command_name:
            return translations.get(locale_str)
        elif context.location == app_commands.TranslationContextLocation.command_description:
            return translations.get(locale_str)

        return None


load_translations()
