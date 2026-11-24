# spec: PLS-315 29.2.1, 29.3, 29.4, 29.6
# description: TypeVar, TypeVarTuple, ParamSpec and TypeAliasType bind
# their arguments as Argument Clinic does, naming typevar(),
# typevartuple(), paramspec() and typealias(): too many positional
# arguments, then one given by name and position, then a missing one,
# then an unexpected keyword, with its suggestion; the at-most count first
# when there is no variadic parameter.
from harness import *
def f[T, *Ts, **P](): pass
T, Ts, P = f.__type_params__
type X = int
TV, TVT, PS, TAT = type(T), type(Ts), type(P), type(X)
def errors():
    out = []
    for c in (lambda: TV(foo=1), lambda: TV("T", name="T", foo=1), lambda: TV("T", int, name="T"), lambda: TV(default=1),
              lambda: TVT(), lambda: TVT("a", "b"), lambda: TVT(name="a", foo=1), lambda: PS("a", "b"), lambda: PS("a", foo=1),
              lambda: PS("a", name="a"), lambda: TAT(), lambda: TAT("a", 1, 2), lambda: TAT(foo=1), lambda: TAT("a", 1, name="a")):
        try: c()
        except TypeError as e: out.append(str(e))
    return out
assert_eq(errors(), ["typevar() missing required argument 'name' (pos 1)", "argument for typevar() given by name ('name') and position (1)",
                     "argument for typevar() given by name ('name') and position (1)", "typevar() missing required argument 'name' (pos 1)",
                     "typevartuple() missing required argument 'name' (pos 1)", "typevartuple() takes exactly 1 positional argument (2 given)",
                     "typevartuple() got an unexpected keyword argument 'foo'", "paramspec() takes exactly 1 positional argument (2 given)",
                     "paramspec() got an unexpected keyword argument 'foo'", "argument for paramspec() given by name ('name') and position (1)",
                     "typealias() missing required argument 'name' (pos 1)", "typealias() takes exactly 2 positional arguments (3 given)",
                     "typealias() missing required argument 'name' (pos 1)", "argument for typealias() given by name ('name') and position (1)"])
k6 = dict(bound=None, covariant=False, contravariant=False, infer_variance=False, default=int)
def counts():
    out = []
    for c in (lambda: TVT("a", foo=1, **k6), lambda: TVT(name="a", foo=1, **k6), lambda: PS("a", "b", "c", foo=1, **k6),
              lambda: TV("a", 1, 2, foo=1, **k6), lambda: TAT("a", 1, type_params=(), qualname="q", foo=1), lambda: TVT("a", dfault=1),
              lambda: TAT("a", name="a"), lambda: TAT(value=1, name="a", foo=2)):
        try: c()
        except TypeError as e: out.append(str(e))
    return out
assert_eq(counts(), ["typevartuple() takes at most 6 arguments (7 given)", "typevartuple() takes at most 6 keyword arguments (7 given)",
                     "paramspec() takes at most 6 arguments (9 given)", "typevar() got an unexpected keyword argument 'foo'",
                     "typealias() takes at most 4 arguments (5 given)",
                     "typevartuple() got an unexpected keyword argument 'dfault'. Did you mean 'default'?",
                     "typealias() missing required argument 'value' (pos 2)", "typealias() got an unexpected keyword argument 'foo'"])
def values():
    return [TV(name="T", bound=int).__bound__, TV("T", int, str).__constraints__, TV("T", covariant=[]).__covariant__,
            TVT(name="Ts", default=int).__default__, repr(TVT("a", contravariant=1)), PS(name="P", bound=int).__bound__,
            TAT(name="Y", value=int, qualname="Q").__qualname__]
assert_eq(values(), [int, (int, str), False, int, "-a", int, "Q"])
