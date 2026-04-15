import discord
import random

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


class DuelGame:
    weapons = [
        {"name": "Daga", "damage": 20, "chance": 80, "icon": "🗡"},
        {"name": "Ballesta", "damage": 40, "chance": 60, "icon": "🏹"},
        {"name": "Red", "damage": 80, "chance": 20, "icon": "🕸"}
    ]
    
    def __init__(self, p1, p2, is_bot=False):
        self.p1 = p1
        self.p2 = p2
        self.p1_hp = 100
        self.p2_hp = 100
        self.is_bot = is_bot
        self.round = 1
        self.current_turn = p1
        self.p1_weapon = None
        self.p2_weapon = None
    
    def next_turn(self):
        self.current_turn = self.p2 if self.current_turn == self.p1 else self.p1
        self.round += 1
    
    def is_over(self):
        return self.p1_hp <= 0 or self.p2_hp <= 0
    
    def get_winner(self):
        if self.p1_hp <= 0 and self.p2_hp <= 0:
            return None
        elif self.p1_hp <= 0:
            return self.p2
        elif self.p2_hp <= 0:
            return self.p1
        return None
    
    def get_key(self):
        return tuple(sorted([self.p1.id, self.p2.id]))


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
