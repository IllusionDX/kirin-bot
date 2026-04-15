import discord
import aiohttp


def create_error_embed(message: str, title: str = "❌ Error") -> discord.Embed:
    """Create a reusable error embed with custom message."""
    return discord.Embed(
        title=title,
        description=message,
        color=discord.Color.red()
    )


def print_frame(str):
	str = str.splitlines()
	maxlen = len(max(str, key=len))
	spaces = " " * maxlen if (maxlen % 2 == 0) else " " * (maxlen + 1)
	
	l2 = "* " + spaces + " *"
	l1 = "*" * len(l2)
	print(l1 + "\n" + l2)
	for line in str:
		if len(line) % 2 != 0:
			line = line + " "
		ldiff = int((len(spaces) - len(line)) / 2)
		print ("* " + " "*ldiff + line + " "*ldiff + " *")
	print(l2 + "\n" + l1 + "\n")

async def get_json_api(url, params):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as r:
            if (r.status == 200):
                return await r.json()