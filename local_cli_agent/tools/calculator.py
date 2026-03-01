"""
Tool: calculator

Safely evaluates mathematical expressions.
Supports basic arithmetic, exponentiation, and common math functions.
No use of eval() - only whitelisted operations are allowed.
"""

import ast
import math
import operator

from .base import BaseTool

_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "ceil": math.ceil,
    "floor": math.floor,
    "factorial": math.factorial,
}

_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


class CalculatorTool(BaseTool):

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return (
            "Evaluate a mathematical expression and return the numeric result. "
            "Supports: +, -, *, /, //, %, ** and functions: "
            "sqrt, sin, cos, tan, log, log10, log2, abs, round, ceil, floor, factorial. "
            "Constants: pi, e, tau."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": (
                        "The math expression to evaluate, e.g. "
                        "'2 ** 10', 'sqrt(144)', '(3 + 5) * 2'."
                    ),
                },
            },
            "required": ["expression"],
        }

    def execute(self, **kwargs) -> str:
        expression: str = kwargs["expression"]

        try:
            tree = ast.parse(expression, mode="eval")
            result = self._eval_node(tree.body)
        except (ValueError, TypeError, ZeroDivisionError) as exc:
            return f"Math error: {exc}"
        except Exception:
            return (
                f"Error: could not evaluate '{expression}'. "
                "Use standard math notation (e.g. '2 * 3 + 1')."
            )

        if isinstance(result, float) and result.is_integer():
            result = int(result)

        return f"{expression} = {result}"

    def _eval_node(self, node: ast.AST):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Unsupported constant: {node.value!r}")

        if isinstance(node, ast.UnaryOp):
            op = _UNARY_OPS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return op(self._eval_node(node.operand))

        if isinstance(node, ast.BinOp):
            op = _BINARY_OPS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op(self._eval_node(node.left), self._eval_node(node.right))

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls are supported.")
            func = _FUNCTIONS.get(node.func.id)
            if func is None:
                raise ValueError(f"Unknown function: '{node.func.id}'")
            args = [self._eval_node(arg) for arg in node.args]
            return func(*args)

        if isinstance(node, ast.Name):
            val = _CONSTANTS.get(node.id)
            if val is None:
                raise ValueError(f"Unknown variable: '{node.id}'")
            return val

        raise ValueError(f"Unsupported expression element: {type(node).__name__}")
