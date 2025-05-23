from __future__ import annotations

import yaml

from predicates import RuleContainer

rules1 = yaml.safe_load("""
---
rule:
  op: in
  args:
    - foo.bar
    - World
""")

rules2 = yaml.safe_load("""
---
rule:
  op: equals
  args:
    - foo.bar
    - Hello World
""")

rules3 = yaml.safe_load("""
---
rule:
  op: and
  args:
    - op: in
      args: [ foo.bar, World ]
    - op: and
      args:
        - op: in
          args:
            - foo.bar
            - Hel
        - op: in
          args:
            - foo.bar
            - ell
""")

r1 = RuleContainer(**rules1)
r2 = RuleContainer(**rules2)
r3 = RuleContainer(**rules3)
print(r1.model_dump_json(indent=2))
print(yaml.dump(r1.model_dump()))
print(yaml.dump(r3.model_dump()))
# print(yaml.dump(p1.model_dump_json(), Dumper=yaml.Dumper, sort_keys=False, default_flow_style=False))

test1 = {'foo': {'bar': 'World'}}
test2 = {'foo': {'bar': 'Hello World'}}
test3 = {'foo': {'foo': 'Hello World'}}

for o in test1, test2, test3:
    print(o, r1.rule, r1.rule.test(o))
    print(o, r2.rule, r2.rule.test(o))
    print(o, r3.rule, r3.rule.test(o))
    print("")

#print(r1.rule.test({'foo': {'bar': 'Hello World'}}))

#print(r1.rule.test({'foo': {'foo': 'Hello World'}}))

#print(p1)
#print(p1.model_dump_json())

# try:
#     Model(p=('1.3', '2'))
# except ValidationError as e:
#     print(e)