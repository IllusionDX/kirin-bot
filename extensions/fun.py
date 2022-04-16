import discord
from discord.ext import commands

#Imports de módulos integrados
import random
import asyncio
import io

#Imports miscelaneos
from config import PREFIX
from defs import replace_mentions, weapons
from PIL import Image, ImageFont, ImageDraw
import textwrap

class Fun(commands.Cog, name="Diversión"):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, 'on_error'):
            return
        elif ctx.command is None:
            return

    @commands.command(name="8ball", aliases=["caracola"])
    async def ball(self, ctx, *, q:str = None):
        if q is None:
            await ctx.send("¡No has hecho una pregunta!")
            return

        responses = {
            "positive" : {
                "answer" : [
                    "Claro que si",
                    "Si, definitivamente",
                    "Sin duda",
                    "Así es",
                    "Como yo lo veo, sí",
                    "Tenlo por seguro",
                    "El destino te sonríe",
                    "Es muy probable que si",
                    "No abandones tu sonrisa porque algo pueda doler~",
                    "Tengo un buen pronostico para ti",
                    "Las señales apuntan a que sí",
                    "La respuesta es obvia",
                    "En mi opinion, si",
                    "Bueno, la esperanza es lo último que muere",
                    "Hoy es tu dia de suerte"
                ],
                "emote" : ":green_circle:"
            },
            "neutral" : {
                "answer" : [
                    "No lo se con certeza, pero puede que si",
                    "¿Eso lo preguntas mucho?",
                    "Creo que alguien no sale mucho",
                    "Buena pregunta",
                    "Aun extraño ese sillón...",
                    "Es posible",
                    "La, la la la la la, la la la~",
                    "Vuelve a preguntar mas tarde",
                    "Lo siento, no puedo entender tu pregunta",
                    "Quizas",
                    "No tengo la mas minima idea",
                    "( ͡° ͜ʖ ͡°)",
                    "Gracias, vuelva pronto",
                    "¿Alguien ha visto una bola mágica por aquí?",
                    "Ah, ok. Te me cuidas"
                ],
                "emote" : ":yellow_circle:"
            },
            "negative" : {
                "answer" : [
                    "Ni lo sueñes",
                    "Mis fuentes dicen que no",
                    "No lo haga compa",
                    "Es muy dudoso",
                    "En una prisión estaba con mil voces en mi ser",
                    "No lo creo",
                    "No te hagas ilusiones",
                    "Oh no, creo que deje el horno encendido antes de salir",
                    "No cuentes con ello",
                    "De ninguna forma",
                    "No es posible",
                    "Ni en un millon de años",
                    "Ve a casa y reflexiona sobre tu vida",
                    "No hay ninguna posibilidad de eso",
                    "Una flama roja ardió y nuestro pan quemo~"
                ],
                "emote" : ":red_circle:" 
            }
        }

        async with ctx.typing():
            choice = random.choice(list(responses.values()))
            answer = random.choice(choice["answer"])

            embed = discord.Embed(color=discord.Color.orange())
            embed.set_author(name="Bola mágica", icon_url="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/72/twitter/247/pool-8-ball_1f3b1.png")
            embed.add_field(name="Pregunta:", value=f"{q}", inline=False)
            embed.add_field(name="Respuesta:", value=f"{choice['emote']} | `{answer}`", inline=False)
            embed.set_footer(text=f"Solicitado por {ctx.author.display_name}",icon_url=ctx.author.display_avatar)
        
        try:
            await ctx.send(embed=embed)
        except Exception as ex:
            await ctx.send(f"Ha ocurrido un error! - Error {ex}")

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
        
        async with ctx.typing():
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

    @commands.command(aliases=["retar", "coliseo"])
    async def challenge(self, ctx, member: discord.Member = None):
        flavorText = {
            "onHit" : [
                "{0} arremete contra {1} y le da un golpe certero. ¡Ouch!, eso debe doler.",
                "¡{0} toma una posición de ventaja y se abalanza contra su rival, {1} recibe de lleno el impacto!",
                "¡{1} se da la vuelta y {0} aprovecha la oportunidad para atacarle por la espalda!",
                "¡{0} sostiene firmemente a su rival y le lanza por los aires, {1} cae de lleno al suelo!",
                "¡{0} supera los esfuerzos de {1} y le asesta un golpe sin pensarlo dos veces!"
            ],
            "onMiss" : [
                "{0} se arroja sobre {1}, pero este le tiende un trampa, y logra escabullirse en el ultimo momento.",
                "{0} subestima la agilidad de {1}, y este logra esquivar fácilmente el ataque.",
                "¡{0} intenta dar un golpe, pero se resbala y cae al suelo en su lugar!",
                "¡{0} ha rozado por poco a {1}, pero no ha dado en el blanco!",
                "{0} duda un momento al realizar su ataque y este no alcanza su objetivo."
            ]
        }

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
                        return ("¡Ha acertado! " + random.choice(flavorText['onHit']).format(self.member.mention, Player.member.mention) +
                        f"\nLanzo: (**{roll}** < {chance}). ")

                    else:
                        return ("¡Ha fallado! " + random.choice(flavorText['onMiss']).format(self.member.mention, Player.member.mention) +
                        f"\nLanzo: (**{roll}** > {chance}). ")

            pOrder = [Player(author), Player(member)]
            random.shuffle(pOrder)

            data = []
            isOver = False

            def weapon(m):
                return m.content.startswith(prefix) and any(d["command"] == m.content[len(prefix):] for d in weapons) and m.author == Player.member

            while not isOver:
                    for i, Player in enumerate(pOrder):
                        Next = pOrder[i - 1]

                        if Player.hp > 0 and Next.hp > 0:
                            await ctx.send(f"Es tu turno {Player.member.mention}, tienes 30 segundos, usa " +
                            ", ".join([f"{prefix}{li['command']}" for li in weapons[:-1]]) + f" o {prefix}{weapons[-1]['command']}" + " para atacar.")

                            try:
                                msg = await self.client.wait_for("message", check=weapon, timeout=30)
                            except:
                                await ctx.send(f"Al parecer {Player.member.mention} no esta ahi.")
                                isOver = True
                                return

                            com = msg.content[len(prefix):]
                            
                            for item in weapons:
                                if item["command"] == com:
                                    data.append(f"¡{Player.member.mention} ha atacado a {Next.member.mention} " +
                                    f"con una {item['name']} {item['icon']}!... " + Player.attack(Next, item))

                                    data[-1] += (f"Salud de los contrincantes: {pOrder[0].member.display_name}: {max(0, pOrder[0].hp)}. " +
                                    f"{pOrder[1].member.display_name}: {max(0, pOrder[1].hp)}")

                                    await ctx.send("\n".join(data))
                                    data = []
                        else:
                            if Player.hp < Next.hp:
                                await ctx.send(f"¡{Next.member.mention} es el vencedor!")
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
                return

def setup(client):
    client.add_cog(Fun(client))