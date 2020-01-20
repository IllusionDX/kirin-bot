import discord
from discord.ext import commands

#Imports de modulos integrados
import random
import asyncio
import io

#Imports miscelaneos
import textwrap
from misc import replace_mentions
from PIL import Image, ImageFont, ImageDraw
from config import prefix

class Fun(commands.Cog, name="Diversión"):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def rip(self, ctx, a:str = None, *, arg:str = None):
        def rect_text(self, box, text, font):
            x1, y1, x2, y2 = box[0], box[1], box[2], box[3]

            w, h = draw.textsize(text, font=font)
            x = (x2 - x1 - w)/2 + x1
            y = (y2 - y1 - h)/2 + y1

            return (x, y)

        img = Image.open("./images/rip.png")
        draw = ImageDraw.Draw(img)
        temp = io.BytesIO()

        #Carga las definiciones de fuentes para el nombre y el texto de abajo
        font_top = ImageFont.truetype("./fonts/librefranklin-bold.ttf", 18)
        font = ImageFont.truetype("./fonts/Roboto-Bold.ttf", 16)
        
        async with ctx.channel.typing():
            if a is None:
                top = ctx.author.display_name
            elif ctx.message.mentions:
                top = await replace_mentions(a, ctx)
            else:
                top = a

            top_box = [85, 180, 210, 220]
            bottom_box = [80, 220, 220, 300]

            name = textwrap.shorten(top, width=15, placeholder=top[:12]+"...")

            draw.text((rect_text(self, top_box, name, font_top)), name, fill="black", align="center", font=font_top)

            if arg is None:
                pass
            else:
                if ctx.message.mentions:
                    body = await replace_mentions(arg, ctx)
                else:
                    body = arg

                field = "\n".join(textwrap.wrap(body, 17, max_lines=4, placeholder="..."))
                draw.multiline_text((rect_text(self, bottom_box, field, font)), field, fill="black", align="center", font=font)

            #Guarda la imagen dentro del buffer de BytesIO, y lo devuelve al principio del stream para ser usado.
            img.save(temp, "png")
            temp.seek(0)

        #Crea y enviá la imagen final usando el buffer temporal
        await ctx.send(file=discord.File(filename="rip.png", fp=temp))

    @commands.command(aliases=["retar"])
    async def challenge(self, ctx, member: discord.Member = None):
        async def gameloop(self, ctx, author:discord.Member, member:discord.Member):
            class Player():
                def __init__(self, member):
                    self.member = member
                    self.hp = 100

                def attack(self, Player, weapons):
                    roll = random.randint(0, 100)
                    chance = weapons["chance"]

                    if roll <= chance:
                        setattr(Player, "hp", Player.hp - weapons["damage"])
                        return (f"¡Ha acertado! Lanzo: (**{roll}** < {chance})")

                    else:
                        return (f"¡Ha fallado! Lanzo: (**{roll}** > {chance})")

            pOrder = [Player(author), Player(member)]
            random.shuffle(pOrder)

            data = []
            isOver = False

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

            def weapon(m):
                return m.content.startswith(prefix) and any(d["command"] == m.content[len(prefix):] for d in weapons) and m.author == Player.member

            while not isOver:
                    for i, Player in enumerate(pOrder):
                        Previous = pOrder[i - 1]

                        if Player.hp > 0 and Previous.hp > 0:
                            await ctx.send(f"Es tu turno {Player.member.mention}, tienes 30 segundos, usa " +
                            ", ".join([f"{prefix}{li['command']}" for li in weapons]) + " para atacar.")

                            try:
                                msg = await self.client.wait_for("message", check=weapon, timeout=30)
                            except:
                                await ctx.send(f"Al parecer {Player.member.mention} no esta ahi.")
                                isOver = True
                                return

                            com = msg.content[len(prefix):]
                            
                            for item in weapons:
                                if item["command"] == com:
                                    data.append(f"¡{Player.member.mention} ha atacado a {Previous.member.mention} " +
                                    f"con una {item['name']} {item['icon']}!... " + Player.attack(Previous, item))

                                    data.append(f"Salud de los contrincantes: {pOrder[0].member.display_name}: {max(0, pOrder[0].hp)}. " +
                                    f"{pOrder[1].member.display_name}: {max(0, pOrder[1].hp)}")

                                    await ctx.send("\n".join(data))
                                    data = []
                        else:
                            if Player.hp < Previous.hp:
                                await ctx.send(f"¡{Previous.member.mention} es el vencedor!")
                            else:
                                await ctx.send(f"¡{Player.member.mention} es el vencedor!")

                            isOver = True
                            break

        if member is None:
            await ctx.send("¡Debes mencionar a otro usuario para comenzar el reto!")
            return
        elif len(ctx.message.mentions) > 1:
            await ctx.send("Solo puedes desafiar a un usuario a la vez.")
            return
        elif (member == ctx.message.author):
            await ctx.send("Ten cuidado con eso, no te hagas daño.")
            return

        author = ctx.message.author

        await ctx.send(f"{member.mention}, {author.mention} desea desafiarte a un duelo a muerte con cuchillos, aceptas el reto?" +
        "\nResponde con 1 para aceptar o 2 para rechazar el reto, esta invitación expirara en 30 segundos.")

        def accept(m):
            return (m.content == "1" or m.content == "2") and m.channel == ctx.channel and m.author == member

        try:
            msg = await self.client.wait_for("message", check=accept, timeout=30)
        except:
            await ctx.send(f"Al parecer {member.mention} no esta ahi.")
            return
        else:
            if msg.content == "1":
                await ctx.send("Desafió aceptado")
                await gameloop(self, ctx, author, member)
            elif msg.content == "2":
                await ctx.send("Desafió rechazado")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        pass

def setup(client):
    client.add_cog(Fun(client))