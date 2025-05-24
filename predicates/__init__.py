"""Simple predictates using Pydantic.

Suitable for use in JSON, YAML, or TOML files."""

from __future__ import annotations

from typing import NamedTuple, Any, Literal, Annotated

import pydash
from pydantic import BaseModel, Field


class PredicateValues(NamedTuple):
    field: str
    value: Any


class BaseOperator(BaseModel):
    op: Literal['equals', 'in', 'and', 'or', 'expr']

    def test(self, o: dict[str, Any]) -> bool:
        """Applies the operator to the arguments."""


class Equals(BaseOperator):
    op: Literal['equals'] = 'equals'
    args: PredicateValues

    def test(self, o: dict[str, Any]) -> bool:
        return pydash.get(o, self.args.field) == self.args.value


class In(BaseOperator):
    op: Literal['in'] = 'in'
    args: PredicateValues

    def test(self, o: dict[str, Any]) -> bool:
        v = pydash.get(o, self.args.field)
        return v is not None and self.args.value in v


class And(BaseOperator):
    op: Literal['and'] = 'and'
    args: list[In | Equals | And | Or]

    def test(self, o: dict[str, Any]) -> bool:
        return all(arg.test(o) for arg in self.args)


class Or(BaseOperator):
    op: Literal['or'] = 'or'
    args: list[In | Equals | And | Or]

    def test(self, o: dict[str, Any]) -> bool:
        return any(arg.test(o) for arg in self.args)


class Expr(BaseOperator):
    op: Literal['expr'] = 'expr'
    args: str

    def test(self, o: dict[str, Any]) -> bool:
        """
        Evaluates expressions like '$.foo == "some value"' against the provided object.
        Also supports logical operators AND and OR for combining conditions:
        '$.foo == "value" AND $.count > 5'
        '$.status == "active" OR $.role == "admin"'

        The $ symbol represents the root of the object being tested.
        Supported comparison operators: ==, !=, >, <, >=, <=
        Supported logical operators: AND, OR (case insensitive)
        """
        import re

        # Split on AND/OR (but not inside quotes)
        def split_on_logical_ops(expr):
            parts = []
            operators = []
            last_pos = 0
            in_quotes = False

            for i, char in enumerate(expr):
                if char in ['"', "'"]:
                    in_quotes = not in_quotes

                if not in_quotes and i + 5 <= len(expr):
                    if expr[i:i + 5].upper() == ' AND ':
                        parts.append(expr[last_pos:i])
                        operators.append('AND')
                        last_pos = i + 5
                    elif expr[i:i + 4].upper() == ' OR ':
                        parts.append(expr[last_pos:i])
                        operators.append('OR')
                        last_pos = i + 4

            parts.append(expr[last_pos:])
            return parts, operators

        # Evaluate a single comparison expression
        def evaluate_comparison(expr):
            # Parse expression: $.fieldpath operator value
            pattern = r'\$\.([\w\.]+)\s*(==|!=|>|<|>=|<=)\s*(.+)'
            match = re.match(pattern, expr.strip())

            if not match:
                raise ValueError(f"Invalid expression format: {expr}")

            field, operator, value = match.groups()

            # Try to evaluate the value part (handles quoted strings, numbers, etc.)
            try:
                evaluated_value = eval(value, {"__builtins__": {}}, {})
            except:
                evaluated_value = value  # Keep as string if eval fails

            # Get the field value from the object
            field_value = pydash.get(o, field)

            # Apply the operator
            if operator == "==":
                return field_value == evaluated_value
            elif operator == "!=":
                return field_value != evaluated_value
            elif operator == ">":
                return field_value > evaluated_value
            elif operator == "<":
                return field_value < evaluated_value
            elif operator == ">=":
                return field_value >= evaluated_value
            elif operator == "<=":
                return field_value <= evaluated_value
            else:
                raise ValueError(f"Unsupported operator: {operator}")

        # If there are no logical operators, evaluate as a simple expression
        if ' AND ' not in self.args.upper() and ' OR ' not in self.args.upper():
            return evaluate_comparison(self.args)

        # Split the expression by logical operators
        parts, operators = split_on_logical_ops(self.args)

        # Evaluate the first part
        result = evaluate_comparison(parts[0])

        # Apply each logical operator in sequence
        for i, op in enumerate(operators):
            if op == 'AND':
                result = result and evaluate_comparison(parts[i + 1])
                # Short-circuit evaluation - if already False, no need to continue with AND
                if not result:
                    break
            elif op == 'OR':
                result = result or evaluate_comparison(parts[i + 1])
                # Short-circuit evaluation - if already True, no need to continue with OR
                if result and (i + 1 < len(operators) and operators[i + 1] == 'OR'):
                    continue

        return result


OperatorRule = Annotated[Equals | In | And | Or | Expr, Field(discriminator='op')]


class RuleContainer(BaseModel):
    rule: OperatorRule
