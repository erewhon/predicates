import yaml

from predicates import Expr

# Create test objects for evaluation
test_objects = {
    "simple": {
        "name": "John Doe",
        "age": 30,
        "active": True,
        "tags": ["developer", "python"]
    },
    "nested": {
        "user": {
            "profile": {
                "name": "Jane Smith",
                "age": 25,
                "preferences": {
                    "theme": "dark",
                    "notifications": True
                }
            },
            "permissions": ["read", "write", "admin"]
        },
        "metadata": {
            "created": "2023-01-15",
            "modified": "2023-05-20"
        }
    },
    "array_test": {
        "items": [
            {"id": 1, "value": "first"},
            {"id": 2, "value": "second"}
        ],
        "counts": [5, 10, 15, 20],
        "flags": [True, False, True]
    },
    "string_test": {
        "message": "Hello World",
        "description": "This is a test"
    }
}

# Basic comparison tests
print("BASIC COMPARISON TESTS")
print("----------------------")

basic_tests = [
    ("$.name == 'John Doe'", test_objects["simple"]),
    ("$.age > 25", test_objects["simple"]),
    ("$.active == True", test_objects["simple"]),
    ("$.user.profile.name == 'Jane Smith'", test_objects["nested"]),
    ("$.user.profile.age < 30", test_objects["nested"]),
    ("$.user.profile.preferences.theme == 'dark'", test_objects["nested"]),
    ("$.metadata.created != 'unknown'", test_objects["nested"]),
]

for expr_str, obj in basic_tests:
    expr = Expr(args=expr_str)
    result = expr.test(obj)
    print(f"Expression: {expr_str}")
    print(f"Result: {result}")
    print()

# AND operator tests
print("\nAND OPERATOR TESTS")
print("----------------")

and_tests = [
    ("$.name == 'John Doe' AND $.age > 25", test_objects["simple"]),  # True AND True = True
    ("$.name == 'John Doe' AND $.age < 25", test_objects["simple"]),  # True AND False = False
    ("$.age > 20 AND $.active == True AND $.tags[0] == 'developer'", test_objects["simple"]),  # Multiple ANDs
    ("$.user.profile.age < 30 AND $.user.permissions[2] == 'admin'", test_objects["nested"]),  # Nested properties
]

for expr_str, obj in and_tests:
    expr = Expr(args=expr_str)
    result = expr.test(obj)
    print(f"Expression: {expr_str}")
    print(f"Result: {result}")
    print()

# OR operator tests
print("\nOR OPERATOR TESTS")
print("---------------")

or_tests = [
    ("$.name == 'John Smith' OR $.age > 25", test_objects["simple"]),  # False OR True = True
    ("$.name == 'John Smith' OR $.age < 25", test_objects["simple"]),  # False OR False = False
    ("$.age < 20 OR $.active == False OR $.tags[0] == 'developer'", test_objects["simple"]),  # Multiple ORs
    ("$.user.profile.age > 30 OR $.user.permissions[2] == 'admin'", test_objects["nested"]),  # Nested properties
]

for expr_str, obj in or_tests:
    expr = Expr(args=expr_str)
    result = expr.test(obj)
    print(f"Expression: {expr_str}")
    print(f"Result: {result}")
    print()

# IN operator tests
print("\nIN OPERATOR TESTS")
print("---------------")

in_tests = [
    ("'python' IN $.tags", test_objects["simple"]),  # Should be True
    ("'java' IN $.tags", test_objects["simple"]),  # Should be False
    ("'admin' IN $.user.permissions", test_objects["nested"]),  # Should be True
    ("'delete' IN $.user.permissions", test_objects["nested"]),  # Should be False
    ("5 IN $.counts", test_objects["array_test"]),  # Should be True
    ("100 IN $.counts", test_objects["array_test"]),  # Should be False
    ("True IN $.flags", test_objects["array_test"]),  # Should be True
    # Testing IN with string containment
    ("'World' IN $.message", test_objects["string_test"]),  # Should be True - substring match
    ("'Test' IN $.message", test_objects["string_test"]),  # Should be False - case sensitive
]

for expr_str, obj in in_tests:
    expr = Expr(args=expr_str)
    result = expr.test(obj)
    print(f"Expression: {expr_str}")
    print(f"Result: {result}")
    print()

# NOT IN operator tests
print("\nNOT IN OPERATOR TESTS")
print("-------------------")

not_in_tests = [
    ("'java' NOT IN $.tags", test_objects["simple"]),  # Should be True
    ("'python' NOT IN $.tags", test_objects["simple"]),  # Should be False
    ("'delete' NOT IN $.user.permissions", test_objects["nested"]),  # Should be True
    ("'admin' NOT IN $.user.permissions", test_objects["nested"]),  # Should be False
    ("100 NOT IN $.counts", test_objects["array_test"]),  # Should be True
    ("5 NOT IN $.counts", test_objects["array_test"]),  # Should be False
    # Testing NOT IN with string containment
    ("'Test' NOT IN $.message", test_objects["string_test"]),  # Should be True - case sensitive
    ("'World' NOT IN $.message", test_objects["string_test"]),  # Should be False
]

for expr_str, obj in not_in_tests:
    expr = Expr(args=expr_str)
    result = expr.test(obj)
    print(f"Expression: {expr_str}")
    print(f"Result: {result}")
    print()

# Combined tests with AND, OR, IN and NOT IN
print("\nCOMBINED OPERATOR TESTS")
print("---------------------")

combined_tests = [
    ("'python' IN $.tags AND $.age > 25", test_objects["simple"]),  # True AND True = True
    ("'java' IN $.tags OR $.age > 25", test_objects["simple"]),  # False OR True = True
    ("'admin' IN $.user.permissions AND 'delete' NOT IN $.user.permissions", test_objects["nested"]),
    # True AND True = True
    ("'python' IN $.tags AND 'java' NOT IN $.tags AND $.active == True", test_objects["simple"]),  # Multiple operators
    ("'admin' NOT IN $.user.permissions OR $.user.profile.age > 30", test_objects["nested"]),  # False OR False = False
]

for expr_str, obj in combined_tests:
    expr = Expr(args=expr_str)
    result = expr.test(obj)
    print(f"Expression: {expr_str}")
    print(f"Result: {result}")
    print()

# YAML integration tests
print("\nYAML INTEGRATION TESTS")
print("--------------------")

yaml_exprs = [
    """
    rule:
      op: expr
      args: "'python' IN $.tags AND $.age > 25"
    """,
    """
    rule:
      op: expr
      args: "'admin' IN $.user.permissions AND 'delete' NOT IN $.user.permissions"
    """,
    """
    rule:
      op: expr
      args: "'admin' NOT IN $.user.permissions OR $.user.profile.age > 30"
    """
]

for yaml_expr_str in yaml_exprs:
    yaml_data = yaml.safe_load(yaml_expr_str)
    expr = Expr(args=yaml_data["rule"]["args"])

    # Determine which test object to use based on the expression
    if "tags" in yaml_data["rule"]["args"]:
        obj = test_objects["simple"]
        obj_name = "simple"
    else:
        obj = test_objects["nested"]
        obj_name = "nested"

    result = expr.test(obj)
    print(f"YAML Expression: {yaml_data['rule']['args']}")
    print(f"Test Object: {obj_name}")
    print(f"Result: {result}")
    print()

# Edge cases
print("\nEDGE CASE TESTS")
print("--------------")

edge_case_tests = [
    # Empty collections
    ("'something' IN $.empty_list", {"empty_list": []}),  # Should be False
    ("'something' NOT IN $.empty_list", {"empty_list": []}),  # Should be True
    # Non-existent fields
    ("'something' IN $.nonexistent", {}),  # Should be False
    ("'something' NOT IN $.nonexistent", {}),  # Should be True
    # None values
    ("'something' IN $.null_value", {"null_value": None}),  # Should be False
    ("'something' NOT IN $.null_value", {"null_value": None}),  # Should be True
    # IN with non-iterable values
    ("'a' IN $.number", {"number": 123}),  # Should be False (numbers aren't iterable)
    ("'a' NOT IN $.number", {"number": 123}),  # Should be True
    # Complex nested case
    ("5 IN $.nested.array AND 'x' NOT IN $.nested.string",
     {"nested": {"array": [1, 5, 10], "string": "test"}}),  # True AND True = True
]

for expr_str, obj in edge_case_tests:
    expr = Expr(args=expr_str)
    result = expr.test(obj)
    print(f"Expression: {expr_str}")
    print(f"Object: {obj}")
    print(f"Result: {result}")
    print()
