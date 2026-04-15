import random
import re
from typing import List, Tuple, Union
import discord


class DiceRoller:
    """
    Advanced dice roller supporting RPG-style notation.
    Supports: 2d6, d20, 2d6+1, (1d20+5)*2, 3d8+2d4-1, etc.
    """

    def __init__(self, expression: str):
        self.expression = expression.lower().replace(' ', '')
        self.tokens: List[Union[int, str, Tuple[int, int]]] = []
        self.output_queue: List[Union[int, str, Tuple[int, int]]] = []
        self.operator_stack: List[str] = []
        self.roll_results: List[Tuple[str, List[int], int]] = []
        self.total = 0

    def _tokenize(self) -> bool:
        """Tokenize the expression into dice rolls, numbers and operators."""
        i = 0
        while i < len(self.expression):
            char = self.expression[i]

            # Dice notation: NdM or dM
            if char == 'd' or (char.isdigit() and i + 1 < len(self.expression) and self.expression[i + 1] == 'd'):
                # Match dice pattern: NdM or dM
                match = re.match(r'(\d*)d(\d+)', self.expression[i:])
                if match:
                    num_str, sides_str = match.groups()
                    num_dice = int(num_str) if num_str else 1
                    sides = int(sides_str)

                    # Limits
                    if num_dice < 1 or num_dice > 100:
                        raise ValueError("Solo puedo lanzar entre 1 y 100 dados.")
                    if sides < 2 or sides > 1000:
                        raise ValueError("Los dados deben tener entre 2 y 1000 caras.")

                    self.tokens.append((num_dice, sides))
                    i += match.end()
                    continue

            # Number
            if char.isdigit():
                match = re.match(r'\d+', self.expression[i:])
                if match:
                    num = int(match.group())
                    if num > 1000000:
                        raise ValueError("Números demasiado grandes.")
                    self.tokens.append(num)
                    i += match.end()
                    continue

            # Operators
            if char in '+-*/()':
                self.tokens.append(char)
                i += 1
                continue

            # Unknown character
            raise ValueError(f"Carácter inválido: '{char}'")

        # If only one token and it's a number, treat it as a die (e.g., "20" -> "1d20")
        if len(self.tokens) == 1 and isinstance(self.tokens[0], int):
            num = self.tokens[0]
            if num >= 2 and num <= 1000:
                self.tokens[0] = (1, num)
            else:
                raise ValueError("Los dados deben tener entre 2 y 1000 caras.")

        return True

    def _get_precedence(self, op: str) -> int:
        """Get operator precedence. Higher = evaluated first."""
        precedence = {'+': 1, '-': 1, '*': 2, '/': 2}
        return precedence.get(op, 0)

    def _is_left_associative(self, op: str) -> bool:
        """Check if operator is left-associative."""
        return op in '+-*/'

    def _shunting_yard(self) -> bool:
        """Convert infix notation to postfix using Shunting Yard algorithm."""
        i = 0
        while i < len(self.tokens):
            token = self.tokens[i]

            # Dice or number: add to output
            if isinstance(token, tuple) or isinstance(token, int):
                self.output_queue.append(token)
                i += 1
                continue

            # Operator
            if token in '+-*/':
                while (self.operator_stack and
                       self.operator_stack[-1] != '(' and
                       ((self._is_left_associative(token) and
                         self._get_precedence(self.operator_stack[-1]) >= self._get_precedence(token)) or
                        (not self._is_left_associative(token) and
                         self._get_precedence(self.operator_stack[-1]) > self._get_precedence(token)))):
                    self.output_queue.append(self.operator_stack.pop())
                self.operator_stack.append(token)
                i += 1
                continue

            # Left parenthesis
            if token == '(':
                self.operator_stack.append(token)
                i += 1
                continue

            # Right parenthesis
            if token == ')':
                while self.operator_stack and self.operator_stack[-1] != '(':
                    self.output_queue.append(self.operator_stack.pop())
                if not self.operator_stack:
                    raise ValueError("Paréntesis desbalanceados.")
                self.operator_stack.pop()  # Remove '('
                i += 1
                continue

            i += 1

        # Pop remaining operators
        while self.operator_stack:
            op = self.operator_stack.pop()
            if op == '(':
                raise ValueError("Paréntesis desbalanceados.")
            self.output_queue.append(op)

        return True

    def _roll_dice(self, num_dice: int, sides: int) -> Tuple[List[int], int]:
        """Roll dice and return individual results and total."""
        results = [random.randint(1, sides) for _ in range(num_dice)]
        return results, sum(results)

    def _evaluate_postfix(self) -> int:
        """Evaluate the postfix expression."""
        stack = []
        self.roll_results = []

        for token in self.output_queue:
            # Dice roll
            if isinstance(token, tuple):
                num_dice, sides = token
                results, total = self._roll_dice(num_dice, sides)
                dice_notation = f"{num_dice}d{sides}" if num_dice > 1 else f"d{sides}"
                self.roll_results.append((dice_notation, results, total))
                stack.append(total)
                continue

            # Number
            if isinstance(token, int):
                stack.append(token)
                continue

            # Operator
            if token in '+-*/':
                if len(stack) < 2:
                    raise ValueError("Expresión inválida.")
                b = stack.pop()
                a = stack.pop()

                if token == '+':
                    result = a + b
                elif token == '-':
                    result = a - b
                elif token == '*':
                    result = a * b
                elif token == '/':
                    if b == 0:
                        raise ValueError("División por cero.")
                    result = a // b  # Integer division

                stack.append(result)

        if len(stack) != 1:
            raise ValueError("Expresión inválida.")

        self.total = stack[0]
        return self.total

    def roll(self) -> int:
        """Parse and roll the dice expression."""
        self._tokenize()
        self._shunting_yard()
        return self._evaluate_postfix()

    def get_breakdown(self) -> str:
        """Get a detailed breakdown of the roll for verbose mode (without result header)."""
        if not self.roll_results:
            return ""

        # Rebuild expression substituting each dice token with its rolled value(s)
        dice_iter = iter(self.roll_results)
        parts = []
        for token in self.tokens:
            if isinstance(token, tuple):
                # Replace dice token with the actual rolls
                notation, results, total = next(dice_iter)
                if len(results) == 1:
                    parts.append(str(results[0]))
                else:
                    # Wrap multi-die sum in parens so it reads cleanly
                    parts.append(f"({'+'.join(map(str, results))})")
            elif isinstance(token, int):
                parts.append(str(token))
            else:
                # Operator or parenthesis — keep as-is with spacing
                if token in '+-':
                    parts.append(f" {token} ")
                elif token in '*/':
                    parts.append(f" {token} ")
                else:
                    parts.append(token)

        expression_with_values = "".join(parts)

        # Build per-die detail line
        dice_details = []
        for notation, results, total in self.roll_results:
            if len(results) == 1:
                dice_details.append(f"🎲 {notation}: **{results[0]}**")
            else:
                dice_details.append(f"🎲 {notation}: {' + '.join(map(str, results))} = **{total}**")

        detail_str = "\n".join(dice_details)
        return (
            f"`{expression_with_values}` = **{self.total}**\n\n"
            f"{detail_str}"
        )

    def get_simple_result(self) -> str:
        """Get simple result showing just the total."""
        return f"🎲 ¡Sacaste **{self.total}**!"


def validate_dice_expression(expression: str) -> Tuple[bool, str]:
    """Validate a dice expression and return (is_valid, error_message)."""
    try:
        roller = DiceRoller(expression)
        roller._tokenize()
        return True, ""
    except ValueError as e:
        return False, str(e)
    except Exception:
        return False, "Expresión inválida."


class DiceRollView(discord.ui.View):
    """View for dice roll with reveal button for detailed breakdown."""

    def __init__(self, roller: DiceRoller, original_user_id: int):
        super().__init__(timeout=300)  # 5 minute timeout
        self.roller = roller
        self.original_user_id = original_user_id
        self.revealed = False

    @discord.ui.button(label="Ver desglose", style=discord.ButtonStyle.secondary, emoji="📋")
    async def reveal_breakdown(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Only the original user can reveal
        if interaction.user.id != self.original_user_id:
            await interaction.response.send_message(
                "Solo el jugador que hizo la tirada puede ver el desglose.",
                ephemeral=True
            )
            return

        if self.revealed:
            await interaction.response.send_message(
                "El desglose ya está visible.",
                ephemeral=True
            )
            return

        self.revealed = True
        button.disabled = True
        button.label = "Desglose visible"

        # Get detailed breakdown (without result, just dice details)
        breakdown = self.roller.get_breakdown()

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="🎲 Tirada de Dados",
                description=f"🎲 ¡Sacaste **{self.roller.total}**!\n\n{breakdown}",
                color=discord.Color.blue()
            ).set_footer(
                text=f"Solicitado por {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar
            ),
            view=self
        )
