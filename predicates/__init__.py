"""Simple predicates using Pydantic.

Suitable for use in JSON, YAML, or TOML files."""

from __future__ import annotations

from typing import NamedTuple, Any, Literal, Annotated

import re
from jsonpath_ng import parse
from pydantic import BaseModel, Field


class PredicateValues(NamedTuple):
    field: str
    value: Any


class BaseOperator(BaseModel):
    """
    Represents a base operator used for logical operations.

    This class serves as a base for implementing logical operators like 'equals',
    'in', 'and', 'or', and 'expr'. It provides a structure for defining specific
    operations and applying them to provided arguments.

    :ivar op: Specifies the type of operation. Valid values are 'equals', 'in',
        'and', 'or', and 'expr'.
    :type op: Literal['equals', 'in', 'and', 'or', 'expr']
    """
    op: Literal['equals', 'in', 'and', 'or', 'expr']

    def test(self, o: dict[str, Any]) -> bool:
        """Applies the operator to the arguments."""


class Equals(BaseOperator):
    """
    Represents an equality operator used for evaluating specific conditions.

    The Equals operator is a subclass of BaseOperator. This operator compares
    a specified field's value in an input object against a predefined value.
    It is designed for use cases where such equality checks are needed. The
    comparison logic is encapsulated in the `test` method, which performs the
    field extraction and value comparison using the given PredicateValues.

    :ivar op: The operator type, which is statically set to "equals".
    :type op: Literal['equals']
    :ivar args: The predicate values, containing the field to be compared and
                the value for comparison.
    :type args: PredicateValues
    """
    op: Literal['equals'] = 'equals'
    args: PredicateValues

    def test(self, o: dict[str, Any]) -> bool:
        matches = parse('$.' + self.args.field).find(o)
        return matches and matches[0].value == self.args.value


class In(BaseOperator):
    """
    Represents an "in" operation used for testing whether a specified value exists
    within a collection or result of a parsed JSON path.

    This class is used for evaluating predicates where an operation checks if a value
    (`args.value`) exists in the collection obtained by resolving a specific field
    (`args.field`) in a given object.

    :ivar op: Literal string identifier for the "in" operation.
    :type op: Literal['in']
    :ivar args: Encapsulates the field to be parsed and the value to be checked.
    :type args: PredicateValues
    """
    op: Literal['in'] = 'in'
    args: PredicateValues

    def test(self, o: dict[str, Any]) -> bool:
        matches = parse('$.' + self.args.field).find(o)
        return matches and self.args.value in matches[0].value


class And(BaseOperator):
    """
    Represents a logical AND operation for combining multiple conditions.

    This class is used to test whether all the provided conditions in the
    ``args`` attribute evaluate to true based on the input dictionary.
    It serves as a composite operator that allows using multiple nested
    conditions such as ``In``, ``Equals``, other ``And`` operations, or
    ``Or`` operations.

    :ivar op: A literal indicating the type of logical operator,
        which is always 'and' for this class.
    :type op: Literal['and']
    :ivar args: A list of conditions to be tested. Each item in the list
        must be an instance of `In`, `Equals`, `And`, or `Or`.
    :type args: list[In | Equals | And | Or]
    """
    op: Literal['and'] = 'and'
    args: list[In | Equals | And | Or]

    def test(self, o: dict[str, Any]) -> bool:
        return all(arg.test(o) for arg in self.args)


class Or(BaseOperator):
    """
    Represents a logical OR operator used to evaluate a set of conditions.

    The class is designed to evaluate multiple conditions and return True
    if any of the conditions evaluate to True. It serves as a composite
    logical operator that can aggregate various conditions, including
    other composite conditions, for complex logical evaluations.

    :ivar op: Identifier for the OR operator.
    :type op: Literal['or']
    :ivar args: A list of conditions that this operator evaluates,
        which can include instances of `In`, `Equals`, `And`, or other `Or` operators.
    :type args: list[In | Equals | And | Or]
    """
    op: Literal['or'] = 'or'
    args: list[In | Equals | And | Or]

    def test(self, o: dict[str, Any]) -> bool:
        return any(arg.test(o) for arg in self.args)


class Expr(BaseOperator):
    """
    Represents an operator for evaluating logical and comparison expressions against an object.

    This class allows the evaluation of complex expressions such as logical
    and comparison operators, as well as containment checks on attributes of a
    given object. The expressions support features such as:
    - Logical operators: AND, OR (case insensitive)
    - Comparison operators: ==, !=, >, <, >=, <=
    - Containment operators: IN, NOT IN (case insensitive)

    Expressions are evaluated in the context of a root object, denoted by
    the `$` symbol, and support path querying using `jsonpath-ng`.

    Examples of valid expressions:
    - '$.foo == "value" AND $.count > 5'
    - '$.status == "active" OR $.role == "admin"'
    - '"World" IN $.tags'
    - '"admin" NOT IN $.permissions'

    :ivar op: The operator type, always set to 'expr'.
    :type op: Literal['expr']
    :ivar args: The logical or comparison expression to be evaluated.
    :type args: str
    """
    op: Literal['expr'] = 'expr'
    args: str

    def test(self, o: dict[str, Any]) -> bool:
        """
        Evaluates expressions like '$.foo == "some value"' against the provided object.
        Also supports:
        - Logical operators: AND, OR (case insensitive)
        - Comparison operators: ==, !=, >, <, >=, <=
        - Containment operators: IN, NOT IN (case insensitive)

        Examples:
        - '$.foo == "value" AND $.count > 5'
        - '$.status == "active" OR $.role == "admin"'
        - '"World" IN $.tags'
        - '"admin" NOT IN $.permissions'

        The $ symbol represents the root of the object being tested.
        """

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
            expr = expr.strip()

            # Check for "value IN $.field" pattern
            in_pattern = r'(.+?)\s+(IN|NOT\s+IN)\s+\$\.([\w\.]+)'
            in_match = re.match(in_pattern, expr, re.IGNORECASE)

            if in_match:
                value_str, operator, field = in_match.groups()

                # Try to evaluate the value part
                try:
                    value = eval(value_str, {"__builtins__": {}}, {})
                except:
                    value = value_str  # Keep as string if eval fails

                # Get the field value from the object using jsonpath-ng
                matches = parse('$.' + field).find(o)
                field_value = matches[0].value if matches else None

                # Apply the IN or NOT IN operator
                operator = operator.upper()
                if operator == "IN":
                    # Check if field_value is iterable and value is in it
                    if field_value is not None:
                        try:
                            return value in field_value
                        except TypeError:
                            # If field_value isn't iterable or doesn't support 'in'
                            return False
                    return False
                elif operator == "NOT IN":
                    # Check if field_value is iterable and value is not in it
                    if field_value is not None:
                        try:
                            return value not in field_value
                        except TypeError:
                            # If field_value isn't iterable or doesn't support 'in'
                            return True
                    return True

            # Traditional pattern: $.fieldpath operator value
            pattern = r'\$\.([\S\.]+)\s*(==|!=|>|<|>=|<=)\s*(.+)'
            match = re.match(pattern, expr)

            if not match:
                raise ValueError(f"Invalid expression format: {expr}")

            field, operator, value = match.groups()

            # Try to evaluate the value part (handles quoted strings, numbers, etc.)
            try:
                evaluated_value = eval(value, {"__builtins__": {}}, {})
            except:
                evaluated_value = value  # Keep as string if eval fails

            # Get the field value from the object using jsonpath-ng
            matches = parse('$.' + field).find(o)
            field_value = matches[0].value if matches else None

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
    """
    Container class for holding and managing a single rule.

    This class is designed to encapsulate an operator rule and provide a structured
    way to manage and integrate rules into various systems or workflows.

    :ivar rule: The operator rule being stored and managed in the container.
    :type rule: OperatorRule
    """
    rule: OperatorRule