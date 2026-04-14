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
