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

         The $ symbol represents the root of the object being tested.
         Supported operators: ==, !=, >, <, >=, <=
         """
        import re

        # Parse expression: $.fieldpath operator value
        pattern = r'\$\.([\w\.]+)\s*(==|!=|>|<|>=|<=)\s*(.+)'
        match = re.match(pattern, self.args.strip())

        if not match:
            raise ValueError(f"Invalid expression format: {self.args}")

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


OperatorRule = Annotated[Equals | In | And | Or | Expr, Field(discriminator='op')]


class RuleContainer(BaseModel):
    rule: OperatorRule
