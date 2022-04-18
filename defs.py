from nextcord.ext import commands
import aiohttp
import re

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

async def replace_mentions(input_str, ctx):
			async def get_name(mention):
				member = await commands.MemberConverter().convert(ctx, mention)
				name = member.display_name
				return name
			
			dictionary = {}
			new_str = ""
			m_pattern = "([<@!]+[0-9]+[>])"

			for match in re.finditer(m_pattern, input_str):
				m = match.string[match.start():match.end()]
				dictionary[f"{m}"] = await get_name(m)

			def repl(match):
				m = match.string[match.start():match.end()]
				return dictionary[f"{m}"]

			new_str = re.sub(m_pattern, repl, input_str)
			return new_str

weapons = [
				{
					"name": "Daga",
					"command": "k",
					"damage": 20,
					"chance": 80,
					"icon": "🗡"
				},
				{
					"name": "Ballesta",
					"command": "b",
					"damage": 40,
					"chance": 60,
					"icon": "🏹"
				},
				{
					"name": "Red",
					"command": "r",
					"damage": 80,
					"chance": 20,
					"icon": "🕸"
				}
			]