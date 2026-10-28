"""
Some correct syntax for variable annotation here.
More examples are in test_grammar and test_parser.
"""

# (Ported) typing is not imported; its no_type_check and ClassVar
# reduce to an identity decorator and a subscriptable placeholder.
no_type_check = lambda cls: cls
class ClassVar:
    def __class_getitem__(cls, item):
        return cls

i: int = 1
j: int
x: float = i/10

def f():
    class C: ...
    return C()

f().new_attr: object = object()

class C:
    def __init__(self, x: int) -> None:
        self.x = x

c = C(5)
c.new_attr: int = 10

__annotations__ = {}


@no_type_check
class NTC:
    def meth(self, param: complex) -> None:
        ...

class CV:
    var: ClassVar['CV']

CV.var = CV()
