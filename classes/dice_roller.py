import random
import re
from typing import List, Tuple, Union


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
        """Get a detailed breakdown of the roll."""
        if not self.roll_results:
            return str(self.total)

        # Build breakdown
        breakdown_parts = []
        dice_index = 0

        for token in self.output_queue:
            if isinstance(token, tuple):
                dice_notation, results, total = self.roll_results[dice_index]
                dice_index += 1
                if len(results) == 1:
                    breakdown_parts.append(str(results[0]))
                else:
                    breakdown_parts.append(f"({' + '.join(map(str, results))})")
            elif isinstance(token, int):
                breakdown_parts.append(str(token))
            else:
                # Operator
                if token in '+-*/':
                    # Map operators to symbols
                    op_map = {'+': '+', '-': '-', '*': '×', '/': '÷'}
                    breakdown_parts.append(op_map.get(token, token))

        # Also provide dice summary
        dice_summary = []
        for notation, results, total in self.roll_results:
            if len(results) == 1:
                dice_summary.append(f"{notation}: {results[0]}")
            else:
                dice_summary.append(f"{notation}: {' + '.join(map(str, results))} = {total}")

        if dice_summary:
            return f"**{self.total}**\n📊 {' '.join(breakdown_parts)}\n🎲 {', '.join(dice_summary)}"
        else:
            return f"**{self.total}**\n📊 {' '.join(breakdown_parts)}"

    def get_simple_result(self) -> str:
        """Get simple result for basic rolls."""
        if len(self.roll_results) == 1 and len(self.roll_results[0][1]) == 1:
            # Single die roll
            return f"¡Sacaste **{self.total}**!"

        # Multiple dice or complex expression
        return f"Resultado: **{self.total}**"


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
