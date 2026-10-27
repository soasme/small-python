"""Intrinsic objects for generics, unions, and type parameters.

Small Python compiles this module into the engine (see tools/build_intrinsics.py)
and runs it lazily, the first time a language construct needs one of its
objects: subscripting a builtin class, `|` between types, PEP 695 type
parameters, and the `type` statement. It is not importable. CPython exposes
these objects through `types` and `typing`, so their names, modules, reprs,
and errors follow CPython 3.15.
"""


def _final(name):
    def __init_subclass__(cls, /, *args, **kwargs):
        raise TypeError(f"type '{name}' is not an acceptable base type")
    return classmethod(__init_subclass__)


def _type_name(obj):
    module = type(obj).__module__
    name = type(obj).__qualname__
    return name if module == 'builtins' else f'{module}.{name}'


def _alias_repr_item(p):
    # types.GenericAlias and Union print classes by qualified name.
    if p is ...:
        return '...'
    if p is type(None):
        return 'None'
    if isinstance(p, GenericAlias):
        return repr(p)
    try:
        if hasattr(p, '__origin__') and hasattr(p, '__args__'):
            return repr(p)
        qualname = p.__name__ if isinstance(p, TypeAliasType) else p.__qualname__
        module = p.__module__
    except AttributeError:
        return repr(p)
    if module is None:
        return repr(p)
    if module == 'builtins':
        return str(qualname)
    return f'{module}.{qualname}'


def _type_repr(obj):
    # typing's representation of type arguments.
    if isinstance(obj, type):
        if obj.__module__ == 'builtins':
            return obj.__qualname__
        return f'{obj.__module__}.{obj.__qualname__}'
    if obj is ...:
        return '...'
    if type(obj) is type(_type_repr):
        return obj.__name__
    if isinstance(obj, tuple):
        return '[' + ', '.join(_type_repr(t) for t in obj) + ']'
    return repr(obj)


class ForwardRef:
    """A string annotation used as a type argument."""
    __module__ = 'annotationlib'

    def __init__(self, arg, *, module=None, owner=None, is_argument=True, is_class=False):
        if not isinstance(arg, str):
            raise TypeError(f"Forward reference must be a string -- got {arg!r}")
        self.__forward_arg__ = arg
        self.__forward_module__ = module
        self.__owner__ = owner
        self.__forward_is_argument__ = is_argument
        self.__forward_is_class__ = is_class

    def __eq__(self, other):
        if not isinstance(other, ForwardRef):
            return NotImplemented
        return (self.__forward_arg__ == other.__forward_arg__ and
                self.__forward_module__ == other.__forward_module__)

    def __hash__(self):
        return hash((self.__forward_arg__, self.__forward_module__))

    def __or__(self, other):
        return Union[self, other]

    def __ror__(self, other):
        return Union[other, self]

    def __repr__(self):
        extra = '' if self.__forward_module__ is None else f', module={self.__forward_module__!r}'
        return f'ForwardRef({self.__forward_arg__!r}{extra})'


def _type_convert(arg):
    if arg is None:
        return type(None)
    if isinstance(arg, str):
        return ForwardRef(arg)
    return arg


def _type_check(arg, msg):
    arg = _type_convert(arg)
    if isinstance(arg, _GenericAlias) and arg.__origin__ is Generic:
        raise TypeError(f"{arg} is not valid as type argument")
    if isinstance(arg, _SpecialForm) or arg is Generic:
        raise TypeError(f"Plain {arg} is not valid as type argument")
    if type(arg) is tuple:
        raise TypeError(f"{msg} Got {arg!r:.100}.")
    return arg


def _is_unpacked_typevartuple(x):
    return not isinstance(x, type) and getattr(x, '__typing_is_unpacked_typevartuple__', False)


def _is_typevar_like(x):
    return isinstance(x, (TypeVar, ParamSpec)) or _is_unpacked_typevartuple(x)


def _is_param_expr(arg):
    return arg is ... or isinstance(arg, (tuple, list, ParamSpec))


def _unpack_args(*args):
    newargs = []
    for arg in args:
        subargs = getattr(arg, '__typing_unpacked_tuple_args__', None)
        if subargs is not None and not (subargs and subargs[-1] is ...):
            newargs.extend(subargs)
        else:
            newargs.append(arg)
    return newargs


def _make_parameters(args):
    # The free type variables of arguments, in first-seen order.
    parameters = []
    for t in args:
        if isinstance(t, type):
            continue
        if isinstance(t, (tuple, list)):
            for x in _make_parameters(t):
                if x not in parameters:
                    parameters.append(x)
        elif hasattr(t, '__typing_subst__'):
            if t not in parameters:
                parameters.append(t)
        else:
            for x in getattr(t, '__parameters__', ()):
                if x not in parameters:
                    parameters.append(x)
    return tuple(parameters)


def _collect_type_parameters(args, *, enforce_default_ordering=True):
    default_encountered = False
    type_var_tuple_encountered = False
    parameters = []
    for t in args:
        if isinstance(t, type):
            pass
        elif isinstance(t, tuple):
            for x in t:
                for collected in _collect_type_parameters([x]):
                    if collected not in parameters:
                        parameters.append(collected)
        elif hasattr(t, '__typing_subst__'):
            if t not in parameters:
                if enforce_default_ordering:
                    if type_var_tuple_encountered and t.has_default():
                        raise TypeError('Type parameter with a default follows TypeVarTuple')
                    if t.has_default():
                        default_encountered = True
                    elif default_encountered:
                        raise TypeError(f'Type parameter {t!r} without a default'
                                        ' follows type parameter with a default')
                parameters.append(t)
        else:
            if _is_unpacked_typevartuple(t):
                type_var_tuple_encountered = True
            for x in getattr(t, '__parameters__', ()):
                if x not in parameters:
                    parameters.append(x)
    return tuple(parameters)


def _subs_tvars(obj, params, argitems):
    subparams = getattr(obj, '__parameters__', None)
    if not isinstance(subparams, tuple) or not subparams:
        return obj
    subargs = []
    for arg in subparams:
        iparam = params.index(arg)
        param = params[iparam]
        arg = argitems[iparam]
        if isinstance(param, TypeVarTuple) and isinstance(arg, tuple):
            subargs.extend(arg)
        else:
            subargs.append(arg)
    return obj[tuple(subargs)]


def _subs_parameters(alias, args, params, item):
    # Substitute type arguments for the parameters of a GenericAlias or Union.
    if not params:
        raise TypeError(f"{alias!r} is not a generic class")
    item = tuple(_unpack_args(*(item if isinstance(item, tuple) else (item,))))
    for param in params:
        prepare = getattr(param, '__typing_prepare_subst__', None)
        if prepare is not None:
            item = prepare(alias, item)
    if len(item) != len(params):
        raise TypeError(f"Too {'many' if len(item) > len(params) else 'few'} arguments for {alias!r};"
                        f" actual {len(item)}, expected {len(params)}")
    newargs = []
    for arg in args:
        if isinstance(arg, type):
            newargs.append(arg)
            continue
        if isinstance(arg, (tuple, list)):
            sub = [_subs_tvars(x, params, item) if not hasattr(x, '__typing_subst__')
                   else x.__typing_subst__(item[params.index(x)]) for x in arg]
            newargs.append(type(arg)(sub))
            continue
        unpack = _is_unpacked_typevartuple(arg)
        subst = getattr(arg, '__typing_subst__', None)
        if subst:
            arg = subst(item[params.index(arg)])
        else:
            arg = _subs_tvars(arg, params, item)
        if unpack and isinstance(arg, tuple):
            newargs.extend(arg)
        else:
            newargs.append(arg)
    return tuple(newargs)


def _unionable(obj):
    return (obj is None or isinstance(obj, (type, GenericAlias, Union, TypeAliasType, sentinel)))


def _union_from_tuple(args):
    items = []
    for arg in args:
        if arg is None:
            arg = type(None)
        members = arg.__args__ if isinstance(arg, Union) else (arg,)
        for member in members:
            for seen in items:
                if seen is member or seen == member:
                    break
            else:
                items.append(member)
    if len(items) == 1:
        return items[0]
    union = object.__new__(Union)
    object.__setattr__(union, '__args__', tuple(items))
    return union


def _union(a, b):
    # type.__or__ when both operands can form a union.
    if not _unionable(a) or not _unionable(b):
        return NotImplemented
    return _union_from_tuple((a, b))


# types.GenericAlias: list[int], dict[str, T], tuple[int, ...].

_GA_ATTRIBUTES = frozenset({
    '__class__', '__bases__', '__origin__', '__args__', '__unpacked__', '__parameters__',
    '__typing_unpacked_tuple_args__', '__mro_entries__', '__reduce_ex__', '__reduce__',
    '__copy__', '__deepcopy__'})


class GenericAlias:
    """Represent a PEP 585 generic type

    E.g. for t = list[int], t.__origin__ is list and t.__args__ is (int,)."""
    __module__ = 'types'

    def __new__(cls, *arguments, **keywords):
        if keywords:
            raise TypeError('GenericAlias() takes no keyword arguments')
        if len(arguments) != 2:
            raise TypeError(f'GenericAlias expected 2 arguments, got {len(arguments)}')
        origin, args = arguments
        self = object.__new__(cls)
        object.__setattr__(self, '__origin__', origin)
        object.__setattr__(self, '__args__', args if isinstance(args, tuple) else (args,))
        object.__setattr__(self, '__unpacked__', False)
        return self

    def __getattribute__(self, name):
        if name in _GA_ATTRIBUTES:
            if name == '__parameters__':
                args = object.__getattribute__(self, '__args__')
                return _make_parameters(args)
            if name == '__typing_unpacked_tuple_args__':
                if (object.__getattribute__(self, '__unpacked__') and
                        object.__getattribute__(self, '__origin__') is tuple):
                    return object.__getattribute__(self, '__args__')
                return None
            return object.__getattribute__(self, name)
        return getattr(object.__getattribute__(self, '__origin__'), name)

    def __setattr__(self, name, value):
        if name in _GA_ATTRIBUTES:
            raise AttributeError('readonly attribute')
        raise AttributeError(f"'types.GenericAlias' object has no attribute '{name}'"
                             " and no __dict__ for setting new attributes")

    def __delattr__(self, name):
        raise AttributeError('readonly attribute')

    def __repr__(self):
        args = self.__args__
        if not args:
            items = '()'
        else:
            items = ', '.join('[' + ', '.join(_alias_repr_item(x) for x in a) + ']'
                              if type(a) is list else _alias_repr_item(a) for a in args)
        star = '*' if self.__unpacked__ else ''
        return f'{star}{_alias_repr_item(self.__origin__)}[{items}]'

    def __eq__(self, other):
        if not isinstance(other, GenericAlias):
            return NotImplemented
        return (self.__unpacked__ == other.__unpacked__ and
                self.__origin__ == other.__origin__ and self.__args__ == other.__args__)

    def __hash__(self):
        return hash(self.__origin__) ^ hash(self.__args__)

    def __call__(self, /, *args, **kwargs):
        result = self.__origin__(*args, **kwargs)
        try:
            result.__orig_class__ = self
        except Exception:
            pass
        return result

    def __getitem__(self, item):
        args = _subs_parameters(self, self.__args__, self.__parameters__, item)
        result = GenericAlias(self.__origin__, args)
        object.__setattr__(result, '__unpacked__', self.__unpacked__)
        return result

    def __iter__(self):
        star = GenericAlias(self.__origin__, self.__args__)
        object.__setattr__(star, '__unpacked__', True)
        yield star

    def __mro_entries__(self, bases):
        return (self.__origin__,)

    def __instancecheck__(self, obj):
        raise TypeError("isinstance() argument 2 cannot be a parameterized generic")

    def __subclasscheck__(self, cls):
        raise TypeError("issubclass() argument 2 cannot be a parameterized generic")

    def __or__(self, other):
        return _union(self, other)

    def __ror__(self, other):
        return _union(other, self)

    def __dir__(self):
        return sorted(set(dir(self.__origin__)) | _GA_ATTRIBUTES)


# typing.Union: int | str, Union[int, str].

def _union_readonly(union, name):
    # A union has the member __args__, getsets, and no __dict__.
    if name == '__args__':
        raise AttributeError('readonly attribute')
    if name in ('__parameters__', '__origin__', '__name__', '__qualname__'):
        raise AttributeError(f"attribute '{name}' of 'typing.Union' objects is not writable")
    if name != '__module__' and any(name in vars(cls) for cls in type(union).__mro__):
        raise AttributeError(f"'typing.Union' object attribute '{name}' is read-only")
    raise AttributeError(f"'typing.Union' object has no attribute '{name}'"
                         " and no __dict__ for setting new attributes")


class Union:
    """Represent a union type

    E.g. for int | str"""
    __module__ = 'typing'
    __init_subclass__ = _final('typing.Union')

    def __new__(cls, *args, **kwargs):
        raise TypeError("cannot create 'typing.Union' instances")

    def __class_getitem__(cls, args):
        if not isinstance(args, tuple):
            args = (args,)
        if not args:
            raise TypeError("Cannot take a Union of no types.")
        return _union_from_tuple(args)

    def __getattribute__(self, name):
        if name == '__parameters__':
            return _make_parameters(object.__getattribute__(self, '__args__'))
        if name == '__origin__':
            return Union
        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        _union_readonly(self, name)

    def __delattr__(self, name):
        _union_readonly(self, name)

    def __repr__(self):
        return ' | '.join('None' if a is type(None) else _alias_repr_item(a) for a in self.__args__)

    def __eq__(self, other):
        if not isinstance(other, Union):
            return NotImplemented
        try:
            return frozenset(self.__args__) == frozenset(other.__args__)
        except TypeError:
            a, b = list(self.__args__), list(other.__args__)
            return len(a) == len(b) and all(x in b for x in a)

    def __hash__(self):
        return hash(frozenset(self.__args__))

    def __getitem__(self, item):
        return _union_from_tuple(_subs_parameters(self, self.__args__, self.__parameters__, item))

    def __or__(self, other):
        return _union(self, other)

    def __ror__(self, other):
        return _union(other, self)

    def __instancecheck__(self, obj):
        return isinstance(obj, self.__args__)

    def __subclasscheck__(self, cls):
        return issubclass(cls, self.__args__)

    def __mro_entries__(self, bases):
        raise TypeError(f"Cannot subclass {self!r}")


# Type parameters: TypeVar, ParamSpec, TypeVarTuple (PEP 484, 612, 646, 695, 696).

class NoDefaultType:
    """The type of the NoDefault singleton."""
    __module__ = 'typing'
    __init_subclass__ = _final('typing.NoDefaultType')

    def __new__(cls, *args, **kwargs):
        if args or kwargs:
            raise TypeError('NoDefaultType takes no arguments')
        return NoDefault

    def __repr__(self):
        return 'typing.NoDefault'

    def __reduce__(self):
        return 'NoDefault'


NoDefault = object.__new__(NoDefaultType)


class _ConstEvaluator:
    __module__ = 'annotationlib'

    def __init__(self, value):
        self._value = value

    def __call__(self, format, /):
        if format == 4:
            return _type_repr(self._value)
        return self._value

    def __repr__(self):
        return f'<constevaluator {self._value!r}>'


_UNSET = object()


def _param_init(self, name, bound, covariant, contravariant, infer_variance, default):
    if not isinstance(name, str):
        raise TypeError(f"{type(self).__name__.lower()}() argument 'name' must be str, not {_type_name(name)}")
    if covariant and contravariant:
        raise ValueError('Bivariant types are not supported.')
    if infer_variance and (covariant or contravariant):
        raise ValueError('Variance cannot be specified with infer_variance.')
    object.__setattr__(self, '_name', name)
    object.__setattr__(self, '__name__', name)
    object.__setattr__(self, '_covariant', bool(covariant))
    object.__setattr__(self, '_contravariant', bool(contravariant))
    object.__setattr__(self, '_infer_variance', bool(infer_variance))
    object.__setattr__(self, '_bound', bound)
    object.__setattr__(self, '_constraints', ())
    object.__setattr__(self, '_default', default)
    object.__setattr__(self, '_evaluate_bound', None)
    object.__setattr__(self, '_evaluate_constraints', None)
    object.__setattr__(self, '_evaluate_default', None)
    object.__setattr__(self, '__module__', 'typing')


def _lazy(self, value_name, evaluate_name, missing):
    value = object.__getattribute__(self, value_name)
    if value is _UNSET:
        evaluate = object.__getattribute__(self, evaluate_name)
        if evaluate is None:
            return missing
        value = evaluate(1)
        object.__setattr__(self, value_name, value)
    return value


# The members and getsets of CPython's type parameter objects; any other
# name goes to the instance __dict__.
_PARAM_MEMBERS = {
    'TypeVar': {'__name__', '__covariant__', '__contravariant__', '__infer_variance__'},
    'ParamSpec': {'__name__', '__bound__', '__covariant__', '__contravariant__', '__infer_variance__'},
    'TypeVarTuple': {'__name__', '__bound__', '__covariant__', '__contravariant__', '__infer_variance__'}}
_PARAM_GETSETS = {
    'TypeVar': {'__bound__', '__constraints__', '__default__', 'evaluate_bound', 'evaluate_constraints',
                'evaluate_default'},
    'ParamSpec': {'__default__', 'evaluate_default', 'args', 'kwargs'},
    'TypeVarTuple': {'__default__', 'evaluate_default'}}


def _param_check(self, name):
    kind = type(self).__name__
    if name in _PARAM_MEMBERS[kind]:
        raise AttributeError('readonly attribute')
    if name in _PARAM_GETSETS[kind]:
        raise AttributeError(f"attribute '{name}' of 'typing.{kind}' objects is not writable")


def _param_setattr(self, name, value):
    _param_check(self, name)
    object.__setattr__(self, name, value)


def _param_delattr(self, name):
    _param_check(self, name)
    object.__delattr__(self, name)


def _args_readonly(self, name):
    # ParamSpecArgs and ParamSpecKwargs have the member __origin__ and no __dict__.
    kind = type(self).__name__
    if name == '__origin__':
        raise AttributeError('readonly attribute')
    if any(name in vars(cls) for cls in type(self).__mro__):
        raise AttributeError(f"'typing.{kind}' object attribute '{name}' is read-only")
    raise AttributeError(f"'typing.{kind}' object has no attribute '{name}'"
                         " and no __dict__ for setting new attributes")


def _variance_repr(self):
    if self._infer_variance:
        return self._name
    return ('+' if self._covariant else '-' if self._contravariant else '~') + self._name


def _has_default(self):
    if self._evaluate_default is not None:
        return True
    return self._default is not _UNSET and self._default is not NoDefault


def _default_get(self):
    return _lazy(self, '_default', '_evaluate_default', NoDefault)


def _evaluate_default_get(self):
    if self._evaluate_default is not None:
        return self._evaluate_default
    if self._default is not _UNSET:
        return _ConstEvaluator(self._default)
    return None


def _bound_get(self):
    return _lazy(self, '_bound', '_evaluate_bound', None)


def _evaluate_bound_get(self):
    if self._evaluate_bound is not None:
        return self._evaluate_bound
    if self._bound is not _UNSET and self._bound is not None:
        return _ConstEvaluator(self._bound)
    return None


def _no_subclass(kind):
    def __mro_entries__(self, bases):
        raise TypeError(f"Cannot subclass an instance of {kind}")
    return __mro_entries__


class TypeVar:
    """Type variable."""
    __module__ = 'typing'
    __init_subclass__ = _final('typing.TypeVar')

    def __init__(self, name, *constraints, bound=None, covariant=False, contravariant=False,
                 infer_variance=False, default=NoDefault):
        _param_init(self, name, None, covariant, contravariant, infer_variance, default)
        if constraints and bound is not None:
            raise TypeError('Constraints cannot be combined with bound=...')
        if len(constraints) == 1:
            raise TypeError('A single constraint is not allowed')
        if bound is not None:
            object.__setattr__(self, '_bound', _type_check(bound, 'Bound must be a type.'))
        msg = 'TypeVar(name, constraint, ...): constraints must be types.'
        object.__setattr__(self, '_constraints', tuple(_type_check(t, msg) for t in constraints))

    __setattr__ = _param_setattr
    __delattr__ = _param_delattr
    __repr__ = _variance_repr
    __mro_entries__ = _no_subclass('TypeVar')
    has_default = _has_default
    __covariant__ = property(lambda self: self._covariant)
    __contravariant__ = property(lambda self: self._contravariant)
    __infer_variance__ = property(lambda self: self._infer_variance)
    __bound__ = property(_bound_get)
    evaluate_bound = property(_evaluate_bound_get)
    __default__ = property(_default_get)
    evaluate_default = property(_evaluate_default_get)

    @property
    def __constraints__(self):
        return _lazy(self, '_constraints', '_evaluate_constraints', ())

    @property
    def evaluate_constraints(self):
        if self._evaluate_constraints is not None:
            return self._evaluate_constraints
        if self._constraints is not _UNSET and self._constraints:
            return _ConstEvaluator(self._constraints)
        return None

    def __or__(self, right):
        return Union[self, right]

    def __ror__(self, left):
        return Union[left, self]

    def __typing_subst__(self, arg):
        arg = _type_check(arg, 'Parameters to generic types must be types.')
        if ((isinstance(arg, _GenericAlias) and arg.__origin__ is Unpack) or
                (isinstance(arg, GenericAlias) and arg.__unpacked__)):
            raise TypeError(f"{arg} is not valid as type argument")
        return arg

    def __typing_prepare_subst__(self, alias, args):
        params = alias.__parameters__
        i = params.index(self)
        if i < len(args):
            return args
        if i == len(args) and self.has_default():
            return (*args, self.__default__)
        raise TypeError(f"Too few arguments for {alias}; actual {len(args)}, expected at least {i + 1}")

    def __reduce__(self):
        return self._name


class TypeVarTuple:
    """Type variable tuple."""
    __module__ = 'typing'
    __init_subclass__ = _final('typing.TypeVarTuple')

    def __init__(self, name, *, bound=None, covariant=False, contravariant=False,
                 infer_variance=False, default=NoDefault):
        _param_init(self, name, bound, covariant, contravariant, infer_variance, default)

    __setattr__ = _param_setattr
    __delattr__ = _param_delattr
    __repr__ = _variance_repr
    __mro_entries__ = _no_subclass('TypeVarTuple')
    has_default = _has_default
    __covariant__ = property(lambda self: self._covariant)
    __contravariant__ = property(lambda self: self._contravariant)
    __infer_variance__ = property(lambda self: self._infer_variance)
    __bound__ = property(_bound_get)
    __default__ = property(_default_get)
    evaluate_default = property(_evaluate_default_get)

    def __iter__(self):
        yield Unpack[self]

    def __typing_subst__(self, arg):
        raise TypeError("Substitution of bare TypeVarTuple is not supported")

    def __typing_prepare_subst__(self, alias, args):
        params = alias.__parameters__
        typevartuple_index = params.index(self)
        for param in params[typevartuple_index + 1:]:
            if isinstance(param, TypeVarTuple):
                raise TypeError(f"More than one TypeVarTuple parameter in {alias}")
        alen = len(args)
        plen = len(params)
        left = typevartuple_index
        right = plen - typevartuple_index - 1
        var_tuple_index = None
        fillarg = None
        for k, arg in enumerate(args):
            if not isinstance(arg, type):
                subargs = getattr(arg, '__typing_unpacked_tuple_args__', None)
                if subargs and len(subargs) == 2 and subargs[-1] is ...:
                    if var_tuple_index is not None:
                        raise TypeError("More than one unpacked arbitrary-length tuple argument")
                    var_tuple_index = k
                    fillarg = subargs[0]
        if var_tuple_index is not None:
            left = min(left, var_tuple_index)
            right = min(right, alen - var_tuple_index - 1)
        elif left + right > alen:
            raise TypeError(f"Too few arguments for {alias}; actual {alen}, expected at least {plen - 1}")
        if left == alen - right and self.has_default():
            replacement = tuple(_unpack_args(self.__default__))
        else:
            replacement = args[left: alen - right]
        return (*args[:left], *([fillarg] * (typevartuple_index - left)), replacement,
                *([fillarg] * (plen - right - left - typevartuple_index - 1)), *args[alen - right:])

    def __reduce__(self):
        return self._name


class ParamSpecArgs:
    """The args for a ParamSpec object."""
    __module__ = 'typing'
    __init_subclass__ = _final('typing.ParamSpecArgs')

    def __init__(self, origin):
        object.__setattr__(self, '__origin__', origin)

    def __setattr__(self, name, value):
        _args_readonly(self, name)

    def __delattr__(self, name):
        _args_readonly(self, name)

    def __repr__(self):
        return f"{self.__origin__.__name__}.args"

    def __eq__(self, other):
        if not isinstance(other, ParamSpecArgs):
            return NotImplemented
        return self.__origin__ == other.__origin__

    def __hash__(self):
        return hash((ParamSpecArgs, self.__origin__))

    __mro_entries__ = _no_subclass('ParamSpecArgs')


class ParamSpecKwargs:
    """The kwargs for a ParamSpec object."""
    __module__ = 'typing'
    __init_subclass__ = _final('typing.ParamSpecKwargs')

    def __init__(self, origin):
        object.__setattr__(self, '__origin__', origin)

    def __setattr__(self, name, value):
        _args_readonly(self, name)

    def __delattr__(self, name):
        _args_readonly(self, name)

    def __repr__(self):
        return f"{self.__origin__.__name__}.kwargs"

    def __eq__(self, other):
        if not isinstance(other, ParamSpecKwargs):
            return NotImplemented
        return self.__origin__ == other.__origin__

    def __hash__(self):
        return hash((ParamSpecKwargs, self.__origin__))

    __mro_entries__ = _no_subclass('ParamSpecKwargs')


class ParamSpec:
    """Parameter specification variable."""
    __module__ = 'typing'
    __init_subclass__ = _final('typing.ParamSpec')

    def __init__(self, name, *, bound=None, covariant=False, contravariant=False,
                 infer_variance=False, default=NoDefault):
        _param_init(self, name, None, covariant, contravariant, infer_variance, default)
        if bound is not None:
            object.__setattr__(self, '_bound', _type_check(bound, 'Bound must be a type.'))

    __setattr__ = _param_setattr
    __delattr__ = _param_delattr
    __repr__ = _variance_repr
    __mro_entries__ = _no_subclass('ParamSpec')
    has_default = _has_default
    __covariant__ = property(lambda self: self._covariant)
    __contravariant__ = property(lambda self: self._contravariant)
    __infer_variance__ = property(lambda self: self._infer_variance)
    __bound__ = property(_bound_get)
    __default__ = property(_default_get)
    evaluate_default = property(_evaluate_default_get)
    args = property(lambda self: ParamSpecArgs(self))
    kwargs = property(lambda self: ParamSpecKwargs(self))

    def __or__(self, right):
        return Union[self, right]

    def __ror__(self, left):
        return Union[left, self]

    def __typing_subst__(self, arg):
        if isinstance(arg, (list, tuple)):
            arg = tuple(_type_check(a, 'Parameters to generic types must be types.') for a in arg)
        elif not _is_param_expr(arg):
            raise TypeError(f"Expected a list of types, an ellipsis, ParamSpec, or Concatenate. Got {arg}")
        return arg

    def __typing_prepare_subst__(self, alias, args):
        params = alias.__parameters__
        i = params.index(self)
        if i == len(args) and self.has_default():
            args = (*args, self.__default__)
        if i >= len(args):
            raise TypeError(f"Too few arguments for {alias}")
        if len(params) == 1 and not _is_param_expr(args[0]):
            assert i == 0
            args = (args,)
        elif isinstance(args[i], list):
            args = (*args[:i], tuple(args[i]), *args[i + 1:])
        return args

    def __reduce__(self):
        return self._name


# typing's generic aliases: Generic[T], C[int], Unpack[Ts].

class _SpecialForm:
    __module__ = 'typing'

    def __init__(self, name):
        object.__setattr__(self, '_name', name)

    def __repr__(self):
        return 'typing.' + self._name

    def __getitem__(self, parameter):
        return _UnpackGenericAlias(self, (parameter,))

    def __call__(self, *args, **kwargs):
        raise TypeError(f"Cannot instantiate {self!r}")

    def __mro_entries__(self, bases):
        raise TypeError(f"Cannot subclass {self!r}")


Unpack = _SpecialForm('Unpack')


def _is_dunder(attr):
    return attr.startswith('__') and attr.endswith('__')


class _GenericAlias:
    __module__ = 'typing'

    def __init__(self, origin, args, *, inst=True, name=None):
        self._inst = inst
        self._name = name
        self.__origin__ = origin
        if not isinstance(args, tuple):
            args = (args,)
        self.__args__ = tuple(... if a is _TypingEllipsis else a for a in args)
        self.__parameters__ = _collect_type_parameters(args, enforce_default_ordering=False)
        if not name:
            self.__module__ = origin.__module__

    def __getattr__(self, attr):
        if attr in {'__origin__', '__args__'}:
            raise AttributeError(attr)
        if '__origin__' in self.__dict__ and not _is_dunder(attr):
            return getattr(self.__origin__, attr)
        raise AttributeError(attr)

    def __call__(self, *args, **kwargs):
        if not self._inst:
            raise TypeError(f"Type {self._name} cannot be instantiated; use {self.__origin__.__name__}() instead")
        result = self.__origin__(*args, **kwargs)
        try:
            result.__orig_class__ = self
        except Exception:
            pass
        return result

    def __mro_entries__(self, bases):
        if isinstance(self.__origin__, _SpecialForm):
            raise TypeError(f"Cannot subclass {self!r}")
        if self.__origin__ is Generic:
            i = bases.index(self)
            for b in bases[i + 1:]:
                if isinstance(b, _GenericAlias) and b is not self:
                    return ()
        return (self.__origin__,)

    def __instancecheck__(self, obj):
        raise TypeError("Subscripted generics cannot be used with class and instance checks")

    def __subclasscheck__(self, cls):
        raise TypeError("Subscripted generics cannot be used with class and instance checks")

    def __eq__(self, other):
        if not isinstance(other, _GenericAlias):
            return NotImplemented
        return self.__origin__ == other.__origin__ and self.__args__ == other.__args__

    def __hash__(self):
        return hash((self.__origin__, self.__args__))

    def __or__(self, right):
        return Union[self, right]

    def __ror__(self, left):
        return Union[left, self]

    def __getitem__(self, args):
        if self.__origin__ is Generic:
            raise TypeError(f"Cannot subscript already-subscripted {self}")
        if not self.__parameters__:
            raise TypeError(f"{self} is not a generic class")
        if not isinstance(args, tuple):
            args = (args,)
        args = tuple(_unpack_args(*(_type_convert(p) for p in args)))
        new_args = self._determine_new_args(args)
        return self.copy_with(new_args)

    def _determine_new_args(self, args):
        params = self.__parameters__
        for param in params:
            prepare = getattr(param, '__typing_prepare_subst__', None)
            if prepare is not None:
                args = prepare(self, args)
        alen = len(args)
        plen = len(params)
        if alen != plen:
            raise TypeError(f"Too {'many' if alen > plen else 'few'} arguments for {self};"
                            f" actual {alen}, expected {plen}")
        new_arg_by_param = dict(zip(params, args))
        return tuple(self._make_substitution(self.__args__, new_arg_by_param))

    def _make_substitution(self, args, new_arg_by_param):
        new_args = []
        for old_arg in args:
            if isinstance(old_arg, type):
                new_args.append(old_arg)
                continue
            substfunc = getattr(old_arg, '__typing_subst__', None)
            if substfunc:
                new_arg = substfunc(new_arg_by_param[old_arg])
            else:
                subparams = getattr(old_arg, '__parameters__', ())
                if not subparams:
                    new_arg = old_arg
                else:
                    subargs = []
                    for x in subparams:
                        if isinstance(x, TypeVarTuple):
                            subargs.extend(new_arg_by_param[x])
                        else:
                            subargs.append(new_arg_by_param[x])
                    new_arg = old_arg[tuple(subargs)]
            if _is_unpacked_typevartuple(old_arg):
                new_args.extend(new_arg)
            elif isinstance(old_arg, tuple):
                new_args.append(tuple(self._make_substitution(old_arg, new_arg_by_param)))
            else:
                new_args.append(new_arg)
        return new_args

    def copy_with(self, args):
        return self.__class__(self.__origin__, args, name=self._name, inst=self._inst)

    def __repr__(self):
        if self._name:
            name = 'typing.' + self._name
        else:
            name = _type_repr(self.__origin__)
        if self.__args__:
            args = ', '.join([_type_repr(a) for a in self.__args__])
        else:
            args = '()'
        return f'{name}[{args}]'

    def __iter__(self):
        yield Unpack[self]


class _TypingEllipsis:
    """Internal placeholder for ... (ellipsis)."""


class _UnpackGenericAlias(_GenericAlias):
    def __repr__(self):
        return f'typing.Unpack[{_type_repr(self.__args__[0])}]'

    def __getitem__(self, args):
        if self.__typing_is_unpacked_typevartuple__:
            return args
        return super().__getitem__(args)

    @property
    def __typing_unpacked_tuple_args__(self):
        arg, = self.__args__
        if isinstance(arg, (_GenericAlias, GenericAlias)):
            if arg.__origin__ is not tuple:
                raise TypeError("Unpack[...] must be used with a tuple type")
            return arg.__args__
        return None

    @property
    def __typing_is_unpacked_typevartuple__(self):
        return isinstance(self.__args__[0], TypeVarTuple)


def _check_generic_specialization(cls, arguments):
    expected_len = len(cls.__parameters__)
    if not expected_len:
        raise TypeError(f"{cls} is not a generic class")
    actual_len = len(arguments)
    if actual_len != expected_len:
        if actual_len < expected_len:
            if cls.__parameters__[actual_len].has_default():
                return
            expected_len -= sum(p.has_default() for p in cls.__parameters__)
            expect_val = f"at least {expected_len}"
        else:
            expect_val = expected_len
        raise TypeError(f"Too {'many' if actual_len > expected_len else 'few'} arguments"
                        f" for {cls}; actual {actual_len}, expected {expect_val}")


class Generic:
    """Abstract base class for generic types."""
    __module__ = 'typing'

    def __class_getitem__(cls, params):
        if not isinstance(params, tuple):
            params = (params,)
        params = tuple(_type_convert(p) for p in params)
        if cls is Generic:
            if not params:
                raise TypeError(f"Parameter list to {cls.__qualname__}[...] cannot be empty")
            if not all(_is_typevar_like(p) for p in params):
                raise TypeError(f"Parameters to {cls.__name__}[...] must all be type variables "
                                "or parameter specification variables.")
            if len(set(params)) != len(params):
                raise TypeError(f"Parameters to {cls.__name__}[...] must all be unique")
        else:
            for param in cls.__parameters__:
                prepare = getattr(param, '__typing_prepare_subst__', None)
                if prepare is not None:
                    params = prepare(cls, params)
            _check_generic_specialization(cls, params)
            new_args = []
            for param, new_arg in zip(cls.__parameters__, params):
                if isinstance(param, TypeVarTuple):
                    new_args.extend(new_arg)
                else:
                    new_args.append(new_arg)
            params = tuple(new_args)
        return _GenericAlias(cls, params)

    def __init_subclass__(cls, *args, **kwargs):
        super(Generic, cls).__init_subclass__(*args, **kwargs)
        tvars = []
        if '__orig_bases__' in cls.__dict__:
            error = Generic in cls.__orig_bases__
        else:
            error = Generic in cls.__bases__ and cls.__name__ != 'Protocol'
        if error:
            raise TypeError("Cannot inherit from plain Generic")
        if '__orig_bases__' in cls.__dict__:
            tvars = _collect_type_parameters(cls.__orig_bases__)
            gvars = None
            for base in cls.__orig_bases__:
                if isinstance(base, _GenericAlias) and base.__origin__ is Generic:
                    if gvars is not None:
                        raise TypeError("Cannot inherit from Generic[...] multiple times.")
                    gvars = base.__parameters__
            if gvars is not None:
                tvarset = set(tvars)
                gvarset = set(gvars)
                if not tvarset <= gvarset:
                    s_vars = ', '.join(str(t) for t in tvars if t not in gvarset)
                    s_args = ', '.join(str(g) for g in gvars)
                    raise TypeError(f"Some type variables ({s_vars}) are not listed in Generic[{s_args}]")
                tvars = gvars
        cls.__parameters__ = tuple(tvars)


# typing.TypeAliasType: the `type` statement (PEP 695).

def _alias_readonly(name):
    if name in ('__name__', '__qualname__'):
        raise AttributeError('readonly attribute')
    if name in {'__value__', '__type_params__', '__parameters__', 'evaluate_value'}:
        raise AttributeError(f"attribute '{name}' of 'typing.TypeAliasType' objects is not writable")
    raise AttributeError(f"'typing.TypeAliasType' object has no attribute '{name}' and no __dict__ for setting new attributes")


class TypeAliasType:
    """Type alias."""
    __module__ = 'typing'
    __init_subclass__ = _final('typing.TypeAliasType')

    def __init__(self, *arguments, **keywords):
        # Argument Clinic: typealias(name, value, *, type_params=(), qualname=None).
        if len(arguments) > 2:
            raise TypeError(f'typealias() takes exactly 2 positional arguments ({len(arguments)} given)')
        for key in keywords:
            if key not in ('name', 'value', 'type_params', 'qualname'):
                raise TypeError(f"typealias() got an unexpected keyword argument '{key}'")
        for position, key in enumerate(('name', 'value')):
            if key in keywords and position < len(arguments):
                raise TypeError(f"argument for typealias() given by name ('{key}') and position ({position + 1})")
        for position, key in enumerate(('name', 'value')):
            if position >= len(arguments) and key not in keywords:
                raise TypeError(f"typealias() missing required argument '{key}' (pos {position + 1})")
        name, value = arguments + tuple(keywords[key] for key in ('name', 'value')[len(arguments):])
        type_params = keywords.get('type_params', ())
        qualname = keywords.get('qualname')
        if not isinstance(name, str):
            raise TypeError(f"typealias() argument 'name' must be str, not {_type_name(name)}")
        if not isinstance(type_params, tuple):
            raise TypeError("type_params must be a tuple")
        default_seen = False
        for param in type_params:
            if not isinstance(param, (TypeVar, ParamSpec, TypeVarTuple)):
                raise TypeError(f"Expected a type param, got {param!r}")
            if param.has_default():
                default_seen = True
            elif default_seen:
                raise TypeError(f"non-default type parameter '{param!r}' follows default type parameter")
        if qualname is not None and not isinstance(qualname, str):
            raise TypeError('qualname must be a string')
        object.__setattr__(self, '_name', name)
        object.__setattr__(self, '__name__', name)
        object.__setattr__(self, '__qualname__', name if qualname is None else qualname)
        object.__setattr__(self, '_value', value)
        object.__setattr__(self, '_evaluate_value', None)
        object.__setattr__(self, '_type_params', type_params)
        object.__setattr__(self, '__module__', 'typing')
        object.__setattr__(self, '_defining_module', 'typing')

    def __setattr__(self, name, value):
        if name != '__module__':
            _alias_readonly(name)
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        # Without its own, an alias reports the module that defined it.
        if name != '__module__':
            _alias_readonly(name)
        object.__setattr__(self, name, self._defining_module)

    __type_params__ = property(lambda self: self._type_params)

    @property
    def __value__(self):
        return _lazy(self, '_value', '_evaluate_value', None)

    @property
    def evaluate_value(self):
        if self._evaluate_value is not None:
            return self._evaluate_value
        return _ConstEvaluator(self._value)

    @property
    def __parameters__(self):
        params = []
        for param in self._type_params:
            if isinstance(param, TypeVarTuple):
                params.extend(param)
            else:
                params.append(param)
        return tuple(params)

    def __repr__(self):
        return self._name

    def __getitem__(self, parameters):
        if not self._type_params:
            raise TypeError("Only generic type aliases are subscriptable")
        if not isinstance(parameters, tuple):
            parameters = (parameters,)
        return GenericAlias(self, parameters)

    def __or__(self, right):
        return Union[self, right]

    def __ror__(self, left):
        return Union[left, self]

    def __mro_entries__(self, bases):
        raise TypeError("Cannot subclass an instance of TypeAliasType")

    def __reduce__(self):
        return self._name


# Entry points used by the engine.

def _class_getitem(cls, item):
    return GenericAlias(cls, item)


def _type_param(kind, name, bound, constraints, default):
    # A PEP 695 type parameter; bound, constraints and default are lazy evaluators.
    cls = (TypeVar, TypeVarTuple, ParamSpec)[kind]
    param = object.__new__(cls)
    _param_init(param, name, _UNSET, False, False, True, _UNSET)
    if bound is None:
        object.__setattr__(param, '_bound', None)
    else:
        object.__setattr__(param, '_evaluate_bound', bound)
    if constraints is not None:
        object.__setattr__(param, '_constraints', _UNSET)
        object.__setattr__(param, '_evaluate_constraints', constraints)
    if default is None:
        object.__setattr__(param, '_default', _UNSET)
    else:
        object.__setattr__(param, '_evaluate_default', default)
    return param


def _type_alias(name, evaluate, type_params, module):
    alias = object.__new__(TypeAliasType)
    object.__setattr__(alias, '_name', name)
    object.__setattr__(alias, '__name__', name)
    object.__setattr__(alias, '__qualname__', evaluate.__qualname__)
    object.__setattr__(alias, '_value', _UNSET)
    object.__setattr__(alias, '_evaluate_value', evaluate)
    object.__setattr__(alias, '_type_params', type_params)
    object.__setattr__(alias, '__module__', module)
    object.__setattr__(alias, '_defining_module', module)
    return alias


def _generic_base(type_params):
    params = []
    for param in type_params:
        if isinstance(param, TypeVarTuple):
            params.extend(param)
        else:
            params.append(param)
    return Generic[tuple(params)]


# object.__reduce__, __reduce_ex__ and __getstate__, after Objects/typeobject.c.
# copyreg is imported when first needed, as CPython does.

def _plain_layout(cls):
    # Python classes whose instances hold no builtin value beyond object's.
    for base in cls.__mro__:
        if base is object:
            return True
        if base.__module__ == 'builtins':
            return False
    return True


def _slotnames(cls):
    # _PyType_GetSlotNames: the cached __slotnames__, else copyreg._slotnames,
    # whose result (cached on the class when possible) is computed here.
    names = cls.__dict__.get('__slotnames__')
    if names is not None:
        if not isinstance(names, list):
            raise TypeError(f'{cls.__name__}.__slotnames__ should be a list or None, not {type(names).__name__}')
        return names
    names = []
    if hasattr(cls, '__slots__'):
        for c in cls.__mro__:
            if '__slots__' in c.__dict__:
                slots = c.__dict__['__slots__']
                if isinstance(slots, str):
                    slots = (slots,)
                for name in slots:
                    if name in ('__dict__', '__weakref__'):
                        continue
                    elif name.startswith('__') and not name.endswith('__'):
                        stripped = c.__name__.lstrip('_')
                        names.append('_%s%s' % (stripped, name) if stripped else name)
                    else:
                        names.append(name)
    try:
        cls.__slotnames__ = names
    except:
        pass
    return names


def _object_getstate_default(obj, required):
    cls = type(obj)
    if required and not _plain_layout(cls):
        raise TypeError(f"cannot pickle {cls.__name__!r} object")
    try:
        state = object.__getattribute__(obj, '__dict__')
    except AttributeError:
        state = None
    state = dict(state) if state else None
    slotnames = _slotnames(cls)
    if slotnames:
        slots = {}
        size = len(slotnames)
        i = 0
        while i < len(slotnames):
            name = slotnames[i]
            try:
                slots[name] = getattr(obj, name)
            except AttributeError:
                pass
            # The list lives on the class, so the lookups may change it.
            if len(slotnames) != size:
                raise RuntimeError('__slotsname__ changed size during iteration')
            i += 1
        if slots:
            state = (state, slots)
    return state


def _object_getstate(obj, required):
    getstate = getattr(obj, '__getstate__')
    if getattr(type(obj), '__getstate__', None) is object.__getstate__:
        return _object_getstate_default(obj, required)
    return getstate()


def _object_newargs(obj):
    cls = type(obj)
    getnewargs_ex = getattr(cls, '__getnewargs_ex__', None)
    if getnewargs_ex is not None:
        result = getnewargs_ex(obj)
        if not isinstance(result, tuple):
            raise TypeError(f"__getnewargs_ex__ should return a tuple, not '{type(result).__name__}'")
        if len(result) != 2:
            raise ValueError(f"__getnewargs_ex__ should return a tuple of length 2, not {len(result)}")
        args, kwargs = result
        if not isinstance(args, tuple):
            raise TypeError("first item of the tuple returned by __getnewargs_ex__ must be "
                            f"a tuple, not '{type(args).__name__}'")
        if not isinstance(kwargs, dict):
            raise TypeError("second item of the tuple returned by __getnewargs_ex__ must be "
                            f"a dict, not '{type(kwargs).__name__}'")
        return args, kwargs
    getnewargs = getattr(cls, '__getnewargs__', None)
    if getnewargs is not None:
        args = getnewargs(obj)
        if not isinstance(args, tuple):
            raise TypeError(f"__getnewargs__ should return a tuple, not '{type(args).__name__}'")
        return args, None
    return None, None


# PLS-315 20.1.4: the reconstruction functions that __reduce_ex__ results
# name. CPython's library publishes them in copyreg, their home module name.
def __newobj__(cls, *args):
    return cls.__new__(cls, *args)


def __newobj_ex__(cls, args, kwargs):
    return cls.__new__(cls, *args, **kwargs)


def _reconstructor(cls, base, state):
    if base is object:
        obj = object.__new__(cls)
    else:
        obj = base.__new__(cls, state)
        if base.__init__ != object.__init__:
            base.__init__(obj, state)
    return obj


for _function in (__newobj__, __newobj_ex__, _reconstructor):
    _function.__module__ = 'copyreg'
del _function


def _object_reduce_old(obj, protocol, base):
    # Protocols 0 and 1; base is the first class of the Standard in the MRO.
    cls = type(obj)
    if base is object:
        state = None
    else:
        if base is cls:
            raise TypeError(f"cannot pickle {cls.__name__!r} object")
        state = base(obj)
    args = (cls, base, state)
    try:
        getstate = obj.__getstate__
    except AttributeError:
        if getattr(obj, "__slots__", None):
            raise TypeError(f"cannot pickle {cls.__name__!r} object: "
                            f"a class that defines __slots__ without "
                            f"defining __getstate__ cannot be pickled "
                            f"with protocol {protocol}") from None
        try:
            state = obj.__dict__
        except AttributeError:
            state = None
    else:
        if type(obj).__getstate__ is object.__getstate__ and getattr(obj, "__slots__", None):
            raise TypeError("a class that defines __slots__ without "
                            "defining __getstate__ cannot be pickled")
        state = getstate()
    if state:
        return _reconstructor, args, state
    return _reconstructor, args


def _object_reduce_newobj(obj):
    cls = type(obj)
    if getattr(cls, '__new__', None) is None:
        raise TypeError(f"cannot pickle {cls.__name__!r} object")
    args, kwargs = _object_newargs(obj)
    hasargs = args is not None
    if not kwargs:
        newobj = __newobj__
        newargs = (cls,) + (args or ())
    else:
        newobj = __newobj_ex__
        newargs = (cls, args, kwargs)
    state = _object_getstate(obj, not (hasargs or isinstance(obj, (list, dict))))
    listitems = iter(obj) if isinstance(obj, list) else None
    dictitems = iter(obj.items()) if isinstance(obj, dict) else None
    return newobj, newargs, state, listitems, dictitems


def _object_common_reduce(obj, protocol, base):
    if protocol >= 2:
        return _object_reduce_newobj(obj)
    return _object_reduce_old(obj, protocol, base)


def _object_reduce_ex(obj, protocol, base):
    if getattr(type(obj), '__reduce__', None) is not object.__reduce__:
        return obj.__reduce__()
    return _object_common_reduce(obj, protocol, base)


# File objects for the open() builtin, following CPython's _io classes over
# the engine's mount-checked descriptor primitives. Buffered objects pass
# straight through to the raw file; text files decode utf-8, latin-1, or
# ascii incrementally and translate newlines.

class UnsupportedOperation(OSError, ValueError):
    __module__ = 'io'


def _check_open(f):
    if f.closed:
        raise ValueError("I/O operation on closed file.")


def _readline_bytes(f, size):
    line = bytearray()
    while size < 0 or len(line) < size:
        b = f.read(1)
        if not b:
            break
        line += b
        if b == b'\n':
            break
    return bytes(line)


class _IOBase:
    __module__ = '_io'

    def __enter__(self):
        _check_open(self)
        return self

    def __exit__(self, *exc):
        self.close()

    def __iter__(self):
        _check_open(self)
        return self

    def __next__(self):
        line = self.readline()
        if not line:
            raise StopIteration
        return line

    def readlines(self, hint=-1):
        lines, total = [], 0
        for line in self:
            lines.append(line)
            total += len(line)
            if 0 < hint <= total:
                break
        return lines

    def writelines(self, lines):
        _check_open(self)
        for line in lines:
            self.write(line)

    def flush(self):
        _check_open(self)

    def isatty(self):
        _check_open(self)
        return False

    def _unsupported(self, name):
        raise UnsupportedOperation(name)

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class FileIO(_IOBase):
    __module__ = '_io'

    def __init__(self, file, mode='r', closefd=True, opener=None):
        from _spy import _file_open
        if opener is not None:
            raise NotImplementedError("open() does not support opener")
        self._fd = -1
        if isinstance(file, float):
            raise TypeError("integer argument expected, got float")
        if not isinstance(mode, str):
            raise TypeError(f"FileIO() argument 'mode' must be str, not {type(mode).__name__}")
        kinds = [k for k in 'rwax' if k in mode]
        if len(kinds) != 1 or any(ch not in 'rwaxb+' for ch in mode) or any(mode.count(ch) > 1 for ch in mode):
            raise ValueError("Must have exactly one of create/read/write/append mode and at most one plus")
        kind, plus = kinds[0], '+' in mode
        if isinstance(file, int):
            raise OSError(9, "Bad file descriptor")
        self._fd = _file_open(file, kind + ('+' if plus else ''))
        if kind == 'a':
            from _spy import _file_seek
            _file_seek(self._fd, 0, 2)
        self.name = file
        self.closefd = closefd
        self._readable = kind == 'r' or plus
        self._writable = kind != 'r' or plus
        self.mode = {'r': 'rb', 'w': 'wb', 'a': 'ab', 'x': 'xb'}[kind] if not plus else \
            {'r': 'rb+', 'w': 'rb+', 'a': 'ab+', 'x': 'xb+'}[kind]

    @property
    def closed(self):
        return self._fd < 0

    def __repr__(self):
        if self.closed:
            return '<_io.FileIO [closed]>'
        return f'<_io.FileIO name={self.name!r} mode={self.mode!r} closefd={self.closefd!r}>'

    def fileno(self):
        _check_open(self)
        return self._fd

    def readable(self):
        _check_open(self)
        return self._readable

    def writable(self):
        _check_open(self)
        return self._writable

    def seekable(self):
        _check_open(self)
        return True

    def read(self, size=-1):
        from _spy import _file_read
        _check_open(self)
        if not self._readable:
            raise UnsupportedOperation('File not open for reading')
        return _file_read(self._fd, -1 if size is None else size)

    def readall(self):
        return self.read()

    def readinto(self, buffer):
        data = self.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)

    def readline(self, size=-1):
        _check_open(self)
        return _readline_bytes(self, -1 if size is None else size)

    def write(self, data):
        from _spy import _file_write
        _check_open(self)
        if not self._writable:
            raise UnsupportedOperation('File not open for writing')
        return _file_write(self._fd, bytes(data) if isinstance(data, memoryview) else data)

    def seek(self, pos, whence=0):
        from _spy import _file_seek
        _check_open(self)
        return _file_seek(self._fd, pos, whence)

    def tell(self):
        return self.seek(0, 1)

    def truncate(self, size=None):
        from _spy import _file_truncate
        _check_open(self)
        if not self._writable:
            raise UnsupportedOperation('File not open for writing')
        return _file_truncate(self._fd, self.tell() if size is None else size)

    def close(self):
        from _spy import _file_close
        if self._fd >= 0:
            fd, self._fd = self._fd, -1
            if self.closefd:
                _file_close(fd)


class _Buffered(_IOBase):
    __module__ = '_io'

    def __init__(self, raw, buffer_size=8192):
        self.raw = raw

    name = property(lambda self: self.raw.name)
    mode = property(lambda self: self.raw.mode)
    closed = property(lambda self: self.raw.closed)

    def __repr__(self):
        return f'<_io.{type(self).__name__} name={self.name!r}>'

    def fileno(self):
        return self.raw.fileno()

    def readable(self):
        return self.raw.readable()

    def writable(self):
        return self.raw.writable()

    def seekable(self):
        return self.raw.seekable()

    def read(self, size=-1):
        _check_open(self)
        if size is None or size < 0:
            return self.raw.read()
        chunks = []
        while size > 0:
            chunk = self.raw.read(size)
            if not chunk:
                break
            chunks.append(chunk)
            size -= len(chunk)
        return b''.join(chunks)

    def read1(self, size=-1):
        return self.read(size)

    def peek(self, size=0):
        pos = self.tell()
        data = self.read(max(size, 1))
        self.seek(pos)
        return data

    def readinto(self, buffer):
        data = self.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)

    def readline(self, size=-1):
        _check_open(self)
        return _readline_bytes(self, -1 if size is None else size)

    def write(self, data):
        _check_open(self)
        return self.raw.write(data)

    def seek(self, pos, whence=0):
        return self.raw.seek(pos, whence)

    def tell(self):
        return self.raw.tell()

    def truncate(self, size=None):
        return self.raw.truncate(size)

    def detach(self):
        raw, self.raw = self.raw, None
        return raw

    def close(self):
        if self.raw is not None and not self.raw.closed:
            self.raw.close()


class BufferedReader(_Buffered):
    pass


class BufferedWriter(_Buffered):
    pass


class BufferedRandom(_Buffered):
    pass


def _encoding_name(encoding):
    key = encoding.lower().replace('_', '-')
    if key in ('utf-8', 'utf8', 'u8', 'utf'):
        return 'utf-8'
    if key in ('latin-1', 'latin1', 'iso-8859-1', 'iso8859-1', 'l1', 'latin'):
        return 'latin-1'
    if key in ('ascii', 'us-ascii', '646'):
        return 'ascii'
    raise LookupError(f"unknown encoding: {encoding}")


def _utf8_cut(data):
    # The longest prefix of data that does not end inside a UTF-8 sequence.
    end = len(data)
    for back in range(1, min(4, end) + 1):
        byte = data[end - back]
        if byte & 0xC0 != 0x80:
            need = 1 if byte < 0x80 else 2 if byte >> 5 == 6 else 3 if byte >> 4 == 14 else 4 if byte >> 3 == 30 else 1
            return end if need <= back else end - back
    return end


class TextIOWrapper(_IOBase):
    __module__ = '_io'

    def __init__(self, buffer, encoding=None, errors=None, newline=None, line_buffering=False, write_through=False):
        if newline not in (None, '', '\n', '\r', '\r\n'):
            raise ValueError(f"illegal newline value: {newline}")
        if encoding is None:
            encoding = 'utf-8'
        if not isinstance(encoding, str):
            raise TypeError(f"TextIOWrapper() argument 'encoding' must be str or None, not {type(encoding).__name__}")
        self._codec = _encoding_name(encoding)
        self.buffer = buffer
        self.encoding = encoding
        self.errors = 'strict' if errors is None else errors
        self._newline = newline
        self.line_buffering = line_buffering
        self.write_through = write_through
        self._raw = ''        # decoded, untranslated text not yet returned
        self._bytes = b''     # undecoded tail of the last chunk
        self._eof = False
        self._seen = 0        # newline kinds seen: 1 '\r', 2 '\n', 4 '\r\n'

    name = property(lambda self: self.buffer.name)
    closed = property(lambda self: self.buffer.closed)

    @property
    def newlines(self):
        kinds = [n for bit, n in ((1, '\r'), (2, '\n'), (4, '\r\n')) if self._seen & bit]
        return None if not kinds else kinds[0] if len(kinds) == 1 else tuple(kinds)

    def __repr__(self):
        text = '<_io.TextIOWrapper'
        try:
            text += f' name={self.name!r}'
        except AttributeError:
            pass
        mode = getattr(self, 'mode', None)
        if mode is not None:
            text += f' mode={mode!r}'
        return text + f' encoding={self.encoding!r}>'

    def fileno(self):
        return self.buffer.fileno()

    def readable(self):
        return self.buffer.readable()

    def writable(self):
        return self.buffer.writable()

    def seekable(self):
        return self.buffer.seekable()

    def detach(self):
        buffer, self.buffer = self.buffer, None
        return buffer

    def _fill(self):
        # Decode one more chunk into _raw; False at end of file.
        if self._eof:
            return False
        chunk = self.buffer.read(8192)
        if not chunk:
            self._eof = True
            if self._bytes:
                self._raw += self._bytes.decode(self._codec, self.errors)
                self._bytes = b''
            return False
        data = self._bytes + chunk
        cut = _utf8_cut(data) if self._codec == 'utf-8' else len(data)
        self._raw += data[:cut].decode(self._codec, self.errors)
        self._bytes = data[cut:]
        return True

    def _note(self, text):
        crlf = text.count('\r\n')
        if crlf:
            self._seen |= 4
        if text.count('\r') > crlf:
            self._seen |= 1
        if text.count('\n') > crlf:
            self._seen |= 2

    def _take(self, count):
        # Remove count raw characters from _raw and return them translated.
        text, self._raw = self._raw[:count], self._raw[count:]
        if self._newline is None:
            self._note(text)
            text = text.replace('\r\n', '\n').replace('\r', '\n')
        return text

    def read(self, size=-1):
        _check_open(self)
        if not self.readable():
            raise UnsupportedOperation('not readable')
        if size is None or size < 0:
            while self._fill():
                pass
            return self._take(len(self._raw))
        # A trailing '\r' may begin '\r\n', so universal mode looks one further.
        while len(self._raw) < size + 1 and self._fill():
            pass
        count, produced = 0, 0
        while produced < size and count < len(self._raw):
            if self._newline is None and self._raw[count] == '\r' and self._raw[count + 1:count + 2] == '\n':
                count += 1
            count += 1
            produced += 1
        return self._take(count)

    def _line_end(self):
        # The raw length of the first complete line in _raw, or -1.
        raw, newline = self._raw, self._newline
        if newline is None or newline == '':
            for i, ch in enumerate(raw):
                if ch == '\n':
                    return i + 1
                if ch == '\r':
                    if i + 1 < len(raw):
                        return i + 2 if raw[i + 1] == '\n' else i + 1
                    return i + 1 if self._eof else -1
            return -1
        at = raw.find(newline)
        return -1 if at < 0 else at + len(newline)

    def readline(self, size=-1):
        _check_open(self)
        if not self.readable():
            raise UnsupportedOperation('not readable')
        if size is None:
            size = -1
        while True:
            end = self._line_end()
            if end >= 0 or not self._fill():
                break
        if end < 0:
            end = len(self._raw)
        if size >= 0 and end > size:
            end = size
        return self._take(end)

    def __next__(self):
        line = self.readline()
        if not line:
            raise StopIteration
        return line

    def write(self, text):
        _check_open(self)
        if not isinstance(text, str):
            raise TypeError(f"write() argument must be str, not {type(text).__name__}")
        if not self.writable():
            raise UnsupportedOperation('not writable')
        # As CPython, read-ahead is dropped and writing continues where it left the file.
        self._raw, self._bytes, self._eof = '', b'', False
        length = len(text)
        if self._newline not in (None, '', '\n'):
            text = text.replace('\n', self._newline)
        self.buffer.write(text.encode(self._codec, self.errors))
        if self.line_buffering and ('\n' in text or '\r' in text):
            self.flush()
        return length

    def flush(self):
        self.buffer.flush()

    def tell(self):
        _check_open(self)
        return self.buffer.tell() - len(self._bytes) - len(self._raw.encode(self._codec, self.errors))

    def seek(self, cookie, whence=0):
        _check_open(self)
        if whence == 1:
            if cookie != 0:
                raise UnsupportedOperation("can't do nonzero cur-relative seeks")
            return self.tell()
        if whence == 2:
            if cookie != 0:
                raise UnsupportedOperation("can't do nonzero end-relative seeks")
            position = self.buffer.seek(0, 2)
        elif whence == 0:
            if cookie < 0:
                raise ValueError(f"negative seek position {cookie}")
            position = self.buffer.seek(cookie)
        else:
            raise ValueError(f"invalid whence ({whence}, should be 0, 1 or 2)")
        self._raw, self._bytes, self._eof = '', b'', False
        return position

    def truncate(self, size=None):
        self.flush()
        return self.buffer.truncate(self.tell() if size is None else size)

    def close(self):
        if self.buffer is not None and not self.closed:
            self.buffer.close()


def open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
    if hasattr(file, '__fspath__') and not isinstance(file, (str, bytes)):
        file = file.__fspath__()
    if not isinstance(file, (str, bytes, int)) or isinstance(file, bool):
        raise TypeError(f"expected str, bytes or os.PathLike object, not {type(file).__name__}")
    if not isinstance(mode, str):
        raise TypeError(f"open() argument 'mode' must be str, not {type(mode).__name__}")
    if any(ch not in 'rwaxbt+' for ch in mode) or len(set(mode)) != len(mode):
        raise ValueError(f"invalid mode: {mode!r}")
    binary, text = 'b' in mode, 't' in mode
    if sum(ch in mode for ch in 'rwax') != 1:
        raise ValueError("must have exactly one of create/read/write/append mode")
    if binary and text:
        raise ValueError("can't have text and binary mode at once")
    if binary and encoding is not None:
        raise ValueError("binary mode doesn't take an encoding argument")
    if binary and errors is not None:
        raise ValueError("binary mode doesn't take an errors argument")
    if binary and newline is not None:
        raise ValueError("binary mode doesn't take a newline argument")
    if binary and buffering == 1:
        buffering = -1
    if not binary and buffering == 0:
        raise ValueError("can't have unbuffered text I/O")
    raw = FileIO(file, ''.join(ch for ch in mode if ch in 'rwax+'), closefd, opener=opener)
    try:
        if buffering == 0:
            return raw
        if '+' in mode:
            buffer = BufferedRandom(raw)
        elif 'r' in mode:
            buffer = BufferedReader(raw)
        else:
            buffer = BufferedWriter(raw)
        if binary:
            return buffer
        wrapper = TextIOWrapper(buffer, encoding, errors, newline, line_buffering=buffering == 1)
        wrapper.mode = mode
        return wrapper
    except BaseException:
        raw.close()
        raise

