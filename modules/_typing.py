"""Primitives and accelerators for the typing module.

Small Python builds this module into the engine, following CPython 3.15's _typing
module. Its types are the engine's own objects for PEP 695 type parameters,
type aliases, generics, and unions, taken from the language constructs that
create them.
"""


# A builtin function in CPython: it does not bind when typing stores it as
# NewType.__call__, which a callable staticmethod reproduces.
@staticmethod
def _idfunc(x, /):
    return x


def _parameters[T, *Ts, **P]():
    pass


TypeVar, TypeVarTuple, ParamSpec = map(type, _parameters.__type_params__)
_P = _parameters.__type_params__[2]
ParamSpecArgs = type(_P.args)
ParamSpecKwargs = type(_P.kwargs)
NoDefault = _parameters.__type_params__[0].__default__

type _Alias = None
TypeAliasType = type(_Alias)


class _Generic[T]:
    pass


Generic = _Generic.__mro__[1]
Union = type(int | str)

del _parameters, _P, _Alias, _Generic
