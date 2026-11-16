# spec: PLS-315 29.9.1, 7.8.1
# description: The first generic alias a program makes, by a builtin
# class subscripted by an instance inside a function whose body loops,
# is the class's alias with the instance as its argument, as every later
# one is.
from harness import *
class O:
    def __repr__(self): return "O"
def first():
    for _ in (): pass
    L, o = list, O()
    return L[o]
alias = first()
assert_eq((repr(alias), alias.__origin__, len(alias.__args__)), ("list[O]", list, 1))
assert_eq(repr(first()), "list[O]")
