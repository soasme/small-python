# spec: PLS-315 16.7, 20.1.4, 27.1, 29.2, 29.5, 29.6, 29.9.1, 29.9.2, 29.9.3, 29.9.4
# description: CPython's test_genericalias: subscripting builtin classes, alias attributes, parameters and substitution, repr, equality, reduction, unpacking and iteration.
# Ported from CPython 3.15.2 Lib/test/test_genericalias.py (docs/licenses/python.txt);
# library imports are replaced by core equivalents, each change marked "(Ported)".
"""Tests for C-implemented GenericAlias."""

from harness import *
# (Ported) unittest and pickle are the harness's core equivalents; copy.copy
# and copy.deepcopy reduce their argument as the copy module does for a
# generic alias, and weakref.ref is the host's weak reference. The types,
# typing and string.templatelib classes are reached through the syntax that
# creates their instances. The library classes of the original generic_types
# list (array, collections, collections.abc, concurrent.futures, contextlib,
# contextvars, csv, dataclasses, functools, graphlib, logging, mailbox,
# ctypes, difflib, filecmp, fileinput, itertools, http.cookies,
# multiprocessing, os, re, tempfile, urllib.parse, unittest.case, queue,
# weakref, tkinter) are not imported, nor typing's List, Dict, Callable,
# Mapping and Unpack.

GenericAlias = type(list[int])  # (Ported) types.GenericAlias
MappingProxyType = type(type.__dict__)  # (Ported) types.MappingProxyType
def _generator():
    yield
async def _coroutine():
    pass
async def _async_generator():
    yield
GeneratorType = type(_generator())  # (Ported) types.GeneratorType
_coroutine_object = _coroutine()
CoroutineType = type(_coroutine_object)  # (Ported) types.CoroutineType
_coroutine_object.close()
del _coroutine_object
AsyncGeneratorType = type(_async_generator())  # (Ported) types.AsyncGeneratorType
Template = type(t"")  # (Ported) string.templatelib.Template
Interpolation = type(t"{0}".interpolations[0])  # (Ported) string.templatelib.Interpolation
Union = type(int | str)  # (Ported) typing.Union is types.UnionType
def _params[T](): pass
TypeVar = type(_params.__type_params__[0])  # (Ported) typing.TypeVar
ref = host.weak_reference  # (Ported) weakref.ref


class copy:
    # (Ported) copy.copy and copy.deepcopy of a generic alias: GenericAlias
    # never reads __copy__ or __deepcopy__ from its origin, so both copy
    # through the reduction protocol.
    copy = staticmethod(lambda obj: pickle.loads(pickle.dumps(obj, 4)))
    deepcopy = staticmethod(lambda obj: pickle.loads(pickle.dumps(obj, 4)))


T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

_UNPACKED_TUPLES = [
    # Unpacked tuple using `*`
    (*tuple[int],)[0],
    (*tuple[T],)[0],
    (*tuple[int, str],)[0],
    (*tuple[int, ...],)[0],
    (*tuple[T, ...],)[0],
    tuple[*tuple[int, ...]],
    tuple[*tuple[T, ...]],
    tuple[str, *tuple[int, ...]],
    tuple[*tuple[int, ...], str],
    tuple[float, *tuple[int, ...], str],
    tuple[*tuple[*tuple[int, ...]]],
    # (Ported) The entries using typing.Unpack, alone and mixed with `*`,
    # are removed: Unpack is a library class.
]


class BaseTest(unittest.TestCase):
    """Test basics."""
    # (Ported) Only the core classes are kept; the library classes listed in
    # the header are removed.
    generic_types = [type, tuple, list, dict, frozendict,
                     set, frozenset, enumerate, memoryview,
                     slice,
                     MappingProxyType, AsyncGeneratorType,
                     GeneratorType, CoroutineType,
                     staticmethod,
                     classmethod,
                     Template,
                     Interpolation,
                    ]

    def test_subscriptable(self):
        for t in self.generic_types:
            if t is None:
                continue
            tname = t.__name__
            with self.subTest(f"Testing {tname}"):
                alias = t[int]
                self.assertIs(alias.__origin__, t)
                self.assertEqual(alias.__args__, (int,))
                self.assertEqual(alias.__parameters__, ())

    def test_unsubscriptable(self):
        # (Ported) collections.abc.Sized and Hashable are removed.
        for t in int, str, float:
            tname = t.__name__
            with self.subTest(f"Testing {tname}"):
                with self.assertRaisesRegex(TypeError, tname):
                    t[int]

    def test_instantiate(self):
        # (Ported) defaultdict and deque are removed, with the defaultdict branch.
        for t in tuple, list, dict, set, frozenset:
            tname = t.__name__
            with self.subTest(f"Testing {tname}"):
                alias = t[int]
                self.assertEqual(alias(), t())
                if t is dict:
                    self.assertEqual(alias(iter([('a', 1), ('b', 2)])), dict(a=1, b=2))
                    self.assertEqual(alias(a=1, b=2), dict(a=1, b=2))
                else:
                    self.assertEqual(alias(iter((1, 2, 3))), t((1, 2, 3)))

    def test_unbound_methods(self):
        t = list[int]
        a = t()
        t.append(a, 'foo')
        self.assertEqual(a, ['foo'])
        x = t.__getitem__(a, 0)
        self.assertEqual(x, 'foo')
        self.assertEqual(t.__len__(a), 1)

    def test_subclassing(self):
        class C(list[int]):
            pass
        self.assertEqual(C.__bases__, (list,))
        self.assertEqual(C.__class__, type)

    def test_class_methods(self):
        t = dict[int, None]
        self.assertEqual(dict.fromkeys(range(2)), {0: None, 1: None})  # This works
        self.assertEqual(t.fromkeys(range(2)), {0: None, 1: None})  # Should be equivalent

    def test_no_chaining(self):
        t = list[int]
        with self.assertRaises(TypeError):
            t[int]

    def test_generic_subclass(self):
        class MyList(list):
            pass
        t = MyList[int]
        self.assertIs(t.__origin__, MyList)
        self.assertEqual(t.__args__, (int,))
        self.assertEqual(t.__parameters__, ())

    def test_repr(self):
        class MyList(list):
            pass
        class MyGeneric:
            __class_getitem__ = classmethod(GenericAlias)

        self.assertEqual(repr(list[str]), 'list[str]')
        self.assertEqual(repr(list[()]), 'list[()]')
        self.assertEqual(repr(tuple[int, ...]), 'tuple[int, ...]')
        x1 = tuple[*tuple[int]]
        self.assertEqual(repr(x1), 'tuple[*tuple[int]]')
        x2 = tuple[*tuple[int, str]]
        self.assertEqual(repr(x2), 'tuple[*tuple[int, str]]')
        x3 = tuple[*tuple[int, ...]]
        self.assertEqual(repr(x3), 'tuple[*tuple[int, ...]]')
        self.assertEndsWith(repr(MyList[int]), '.BaseTest.test_repr.<locals>.MyList[int]')
        self.assertEqual(repr(list[str]()), '[]')  # instances should keep their normal repr

        # gh-105488
        self.assertEndsWith(repr(MyGeneric[int]), 'MyGeneric[int]')
        self.assertEndsWith(repr(MyGeneric[[]]), 'MyGeneric[[]]')
        self.assertEndsWith(repr(MyGeneric[[int, str]]), 'MyGeneric[[int, str]]')

    def test_evil_repr1(self):
        # gh-143635
        class Zap:
            def __init__(self, container):
                self.container = container
            def __getattr__(self, name):
                if name == "__origin__":
                    self.container.clear()
                    return None
                if name == "__args__":
                    return ()
                raise AttributeError

        params = []
        params.append(Zap(params))
        alias = GenericAlias(list, (params,))
        repr_str = repr(alias)
        self.assertTrue(repr_str.startswith("list[["), repr_str)

    def test_evil_repr2(self):
        class Zap:
            def __init__(self, container):
                self.container = container
            def __getattr__(self, name):
                if name == "__qualname__":
                    self.container.clear()
                    return "abcd"
                if name == "__module__":
                    return None
                raise AttributeError

        params = []
        params.append(Zap(params))
        alias = GenericAlias(list, (params,))
        repr_str = repr(alias)
        self.assertTrue(repr_str.startswith("list[["), repr_str)

    def test_evil_repr3(self):
        # gh-143823
        lst = []
        class X:
            def __repr__(self):
                lst.clear()
                return "x"

        lst += [X(), 1]
        ga = GenericAlias(int, lst)
        with self.assertRaises(IndexError):
            repr(ga)

    def test_exposed_type(self):
        # (Ported) types.GenericAlias is the type of a subscripted class.
        a = GenericAlias(list, int)
        self.assertEqual(str(a), 'list[int]')
        self.assertIs(a.__origin__, list)
        self.assertEqual(a.__args__, (int,))
        self.assertEqual(a.__parameters__, ())

    def test_parameters(self):
        # (Ported) The L3, L4a, L4b and L5 cases, which nest typing's List,
        # Dict and Callable aliases, are removed.
        D0 = dict[str, int]
        self.assertEqual(D0.__args__, (str, int))
        self.assertEqual(D0.__parameters__, ())
        D1a = dict[str, V]
        self.assertEqual(D1a.__args__, (str, V))
        self.assertEqual(D1a.__parameters__, (V,))
        D1b = dict[K, int]
        self.assertEqual(D1b.__args__, (K, int))
        self.assertEqual(D1b.__parameters__, (K,))
        D2a = dict[K, V]
        self.assertEqual(D2a.__args__, (K, V))
        self.assertEqual(D2a.__parameters__, (K, V))
        D2b = dict[T, T]
        self.assertEqual(D2b.__args__, (T, T))
        self.assertEqual(D2b.__parameters__, (T,))

        L0 = list[str]
        self.assertEqual(L0.__args__, (str,))
        self.assertEqual(L0.__parameters__, ())
        L1 = list[T]
        self.assertEqual(L1.__args__, (T,))
        self.assertEqual(L1.__parameters__, (T,))
        L2 = list[list[T]]
        self.assertEqual(L2.__args__, (list[T],))
        self.assertEqual(L2.__parameters__, (T,))

        T1 = tuple[*tuple[int]]
        self.assertEqual(
            T1.__args__,
            (*tuple[int],),
        )
        self.assertEqual(T1.__parameters__, ())

        T2 = tuple[*tuple[T]]
        self.assertEqual(
            T2.__args__,
            (*tuple[T],),
        )
        self.assertEqual(T2.__parameters__, (T,))

        T4 = tuple[*tuple[int, str]]
        self.assertEqual(
            T4.__args__,
            (*tuple[int, str],),
        )
        self.assertEqual(T4.__parameters__, ())

    def test_parameter_chaining(self):
        # (Ported) The cases nesting typing's List, Dict and Callable aliases
        # are removed; typing.Union is the core union type.
        self.assertEqual(list[T][int], list[int])
        self.assertEqual(dict[str, T][int], dict[str, int])
        self.assertEqual(dict[T, int][str], dict[str, int])
        self.assertEqual(dict[K, V][str, int], dict[str, int])
        self.assertEqual(dict[T, T][int], dict[int, int])

        self.assertEqual(list[list[T]][int], list[list[int]])
        self.assertEqual(list[dict[T, int]][str], list[dict[str, int]])
        self.assertEqual(list[dict[str, T]][int], list[dict[str, int]])
        self.assertEqual(list[dict[K, V]][str, int], list[dict[str, int]])
        self.assertEqual(dict[T, list[int]][str], dict[str, list[int]])

        self.assertEqual(list[Union[K, V]][str, int], list[Union[str, int]])

        with self.assertRaises(TypeError):
            list[int][int]
        with self.assertRaises(TypeError):
            dict[T, int][str, int]
        with self.assertRaises(TypeError):
            dict[str, T][str, int]
        with self.assertRaises(TypeError):
            dict[T, T][str, int]

    def test_equality(self):
        self.assertEqual(list[int], list[int])
        self.assertEqual(dict[str, int], dict[str, int])
        self.assertEqual((*tuple[int],)[0], (*tuple[int],)[0])
        self.assertEqual(tuple[*tuple[int]], tuple[*tuple[int]])
        self.assertNotEqual(dict[str, int], dict[str, str])
        self.assertNotEqual(list, list[int])
        self.assertNotEqual(list[int], list)
        self.assertNotEqual(list[int], tuple[int])
        self.assertNotEqual((*tuple[int],)[0], tuple[int])

    def test_isinstance(self):
        self.assertTrue(isinstance([], list))
        with self.assertRaises(TypeError):
            isinstance([], list[str])

    def test_issubclass(self):
        class L(list): ...
        self.assertIsSubclass(L, list)
        with self.assertRaises(TypeError):
            issubclass(L, list[str])

    def test_type_generic(self):
        t = type[int]
        Test = t('Test', (), {})
        self.assertTrue(isinstance(Test, type))
        test = Test()
        self.assertEqual(t(test), Test)
        self.assertEqual(t(0), int)

    def test_type_subclass_generic(self):
        class MyType(type):
            pass
        with self.assertRaisesRegex(TypeError, 'MyType'):
            MyType[int]

    def test_pickle(self):
        aliases = [GenericAlias(list, T)] + _UNPACKED_TUPLES
        for alias in aliases:
            for proto in range(pickle.HIGHEST_PROTOCOL + 1):
                with self.subTest(alias=alias, proto=proto):
                    s = pickle.dumps(alias, proto)
                    loaded = pickle.loads(s)
                    self.assertEqual(loaded.__origin__, alias.__origin__)
                    self.assertEqual(loaded.__args__, alias.__args__)
                    self.assertEqual(loaded.__parameters__, alias.__parameters__)
                    self.assertEqual(type(loaded), type(alias))

    def test_copy(self):
        class X(list):
            def __copy__(self):
                return self
            def __deepcopy__(self, memo):
                return self

        # (Ported) The aliases of collections.deque are removed.
        aliases = [
            GenericAlias(list, T),
            GenericAlias(X, T),
            X[T],
            list[T],
        ] + _UNPACKED_TUPLES
        for alias in aliases:
            with self.subTest(alias=alias):
                copied = copy.copy(alias)
                self.assertEqual(copied.__origin__, alias.__origin__)
                self.assertEqual(copied.__args__, alias.__args__)
                self.assertEqual(copied.__parameters__, alias.__parameters__)
                copied = copy.deepcopy(alias)
                self.assertEqual(copied.__origin__, alias.__origin__)
                self.assertEqual(copied.__args__, alias.__args__)
                self.assertEqual(copied.__parameters__, alias.__parameters__)

    def test_unpack(self):
        alias = tuple[str, ...]
        self.assertIs(alias.__unpacked__, False)
        unpacked = (*alias,)[0]
        self.assertIs(unpacked.__unpacked__, True)

    def test_union(self):
        a = Union[list[int], list[str]]
        self.assertEqual(a.__args__, (list[int], list[str]))
        self.assertEqual(a.__parameters__, ())

    def test_union_generic(self):
        a = Union[list[T], tuple[T, ...]]
        self.assertEqual(a.__args__, (list[T], tuple[T, ...]))
        self.assertEqual(a.__parameters__, (T,))

    def test_dir(self):
        ga = list[int]
        dir_of_gen_alias = set(dir(ga))
        self.assertTrue(dir_of_gen_alias.issuperset(dir(list)))
        for generic_alias_property in (
            "__origin__", "__args__", "__parameters__",
            "__unpacked__",
        ):
            with self.subTest(generic_alias_property=generic_alias_property):
                self.assertIn(generic_alias_property, dir_of_gen_alias)
        for blocked in (
            "__bases__",
            "__copy__",
            "__deepcopy__",
        ):
            with self.subTest(blocked=blocked):
                self.assertNotIn(blocked, dir_of_gen_alias)

        for entry in dir_of_gen_alias:
            with self.subTest(entry=entry):
                getattr(ga, entry)  # must not raise `AttributeError`

    def test_weakref(self):
        for t in self.generic_types:
            if t is None:
                continue
            tname = t.__name__
            with self.subTest(f"Testing {tname}"):
                alias = t[int]
                self.assertEqual(ref(alias)(), alias)

    def test_no_kwargs(self):
        # bpo-42576
        with self.assertRaises(TypeError):
            GenericAlias(bad=float)

    def test_subclassing_types_genericalias(self):
        class SubClass(GenericAlias): ...
        alias = SubClass(list, int)
        class Bad(GenericAlias):
            def __new__(cls, *args, **kwargs):
                super().__new__(cls, *args, **kwargs)

        self.assertEqual(alias, list[int])
        with self.assertRaises(TypeError):
            Bad(list, int, bad=int)

    def test_iter_creates_starred_tuple(self):
        t = tuple[int, str]
        iter_t = iter(t)
        x = next(iter_t)
        self.assertEqual(repr(x), '*tuple[int, str]')

    def test_calling_next_twice_raises_stopiteration(self):
        t = tuple[int, str]
        iter_t = iter(t)
        next(iter_t)
        with self.assertRaises(StopIteration):
            next(iter_t)

    def test_del_iter(self):
        t = tuple[int, str]
        iter_x = iter(t)
        del iter_x

    def test_paramspec_specialization(self):
        # gh-124445
        # (Ported) The alias values are never evaluated, so typing.Callable
        # is not needed.
        T = TypeVar("T")
        U = TypeVar("U")
        type X[**P] = Callable[P, int]

        generic = X[[T]]
        self.assertEqual(generic.__args__, ([T],))
        self.assertEqual(generic.__parameters__, (T,))
        specialized = generic[str]
        self.assertEqual(specialized.__args__, ([str],))
        self.assertEqual(specialized.__parameters__, ())

        generic = X[(T,)]
        self.assertEqual(generic.__args__, (T,))
        self.assertEqual(generic.__parameters__, (T,))
        specialized = generic[str]
        self.assertEqual(specialized.__args__, (str,))
        self.assertEqual(specialized.__parameters__, ())

        generic = X[[T, U]]
        self.assertEqual(generic.__args__, ([T, U],))
        self.assertEqual(generic.__parameters__, (T, U))
        specialized = generic[str, int]
        self.assertEqual(specialized.__args__, ([str, int],))
        self.assertEqual(specialized.__parameters__, ())

        generic = X[(T, U)]
        self.assertEqual(generic.__args__, (T, U))
        self.assertEqual(generic.__parameters__, (T, U))
        specialized = generic[str, int]
        self.assertEqual(specialized.__args__, (str, int))
        self.assertEqual(specialized.__parameters__, ())

    def test_nested_paramspec_specialization(self):
        # gh-124445
        type X[**P, T] = Callable[P, T]

        x_list = X[[int, str], float]
        self.assertEqual(x_list.__args__, ([int, str], float))
        self.assertEqual(x_list.__parameters__, ())

        x_tuple = X[(int, str), float]
        self.assertEqual(x_tuple.__args__, ((int, str), float))
        self.assertEqual(x_tuple.__parameters__, ())

        U = TypeVar("U")
        V = TypeVar("V")

        multiple_params_list = X[[int, U], V]
        self.assertEqual(multiple_params_list.__args__, ([int, U], V))
        self.assertEqual(multiple_params_list.__parameters__, (U, V))
        multiple_params_list_specialized = multiple_params_list[str, float]
        self.assertEqual(multiple_params_list_specialized.__args__, ([int, str], float))
        self.assertEqual(multiple_params_list_specialized.__parameters__, ())

        multiple_params_tuple = X[(int, U), V]
        self.assertEqual(multiple_params_tuple.__args__, ((int, U), V))
        self.assertEqual(multiple_params_tuple.__parameters__, (U, V))
        multiple_params_tuple_specialized = multiple_params_tuple[str, float]
        self.assertEqual(multiple_params_tuple_specialized.__args__, ((int, str), float))
        self.assertEqual(multiple_params_tuple_specialized.__parameters__, ())

        deeply_nested = X[[U, [V], int], V]
        self.assertEqual(deeply_nested.__args__, ([U, [V], int], V))
        self.assertEqual(deeply_nested.__parameters__, (U, V))
        deeply_nested_specialized = deeply_nested[str, float]
        self.assertEqual(deeply_nested_specialized.__args__, ([str, [float], int], float))
        self.assertEqual(deeply_nested_specialized.__parameters__, ())

    def test_gh150146(self):
        # It used to crash:
        # (Ported) The starred typing.Mapping[..., ...] alias is replaced by
        # the starred core alias dict[..., ...], also not a valid argument.
        for container in [memoryview, list, tuple]:
            with self.subTest(container=container):
                x = container[TypeVar("")]
                with self.assertRaises(TypeError):
                    x[*dict[..., ...]]


class TypeIterationTests(unittest.TestCase):
    _UNITERABLE_TYPES = (list, tuple)

    def test_cannot_iterate(self):
        for test_type in self._UNITERABLE_TYPES:
            with self.subTest(type=test_type):
                expected_error_regex = "object is not iterable"
                with self.assertRaisesRegex(TypeError, expected_error_regex):
                    iter(test_type)
                with self.assertRaisesRegex(TypeError, expected_error_regex):
                    list(test_type)
                with self.assertRaisesRegex(TypeError, expected_error_regex):
                    for _ in test_type:
                        pass

    # (Ported) test_is_not_instance_of_iterable is removed: it tests
    # isinstance against collections.abc.Iterable.


if __name__ == "__main__":
    unittest.main()
