# spec: PLS-315 19.3, 20.2
# description: __instancecheck__ and __subclasscheck__ on metaclasses.
# Ported from CPython 3.15.0 Lib/test/test_typechecks.py (docs/licenses/python.txt);
# library imports are replaced by core equivalents, each change marked "(Ported)".
from harness import *
"""Unit tests for __instancecheck__ and __subclasscheck__."""



class ABC(type):

    def __instancecheck__(cls, inst):
        """Implement isinstance(inst, cls)."""
        return any(cls.__subclasscheck__(c)
                   for c in {type(inst), inst.__class__})

    def __subclasscheck__(cls, sub):
        """Implement issubclass(sub, cls)."""
        candidates = cls.__dict__.get("__subclass__", set()) | {cls}
        return any(c in candidates for c in sub.mro())


class Integer(metaclass=ABC):
    __subclass__ = {int}


class SubInt(Integer):
    pass


class TypeChecksTest(unittest.TestCase):

    def testIsSubclassInternal(self):
        self.assertEqual(Integer.__subclasscheck__(int), True)
        self.assertEqual(Integer.__subclasscheck__(float), False)

    def testIsSubclassBuiltin(self):
        self.assertEqual(issubclass(int, Integer), True)
        self.assertEqual(issubclass(int, (Integer,)), True)
        self.assertEqual(issubclass(float, Integer), False)
        self.assertEqual(issubclass(float, (Integer,)), False)

    def testIsInstanceBuiltin(self):
        self.assertEqual(isinstance(42, Integer), True)
        self.assertEqual(isinstance(42, (Integer,)), True)
        self.assertEqual(isinstance(3.14, Integer), False)
        self.assertEqual(isinstance(3.14, (Integer,)), False)

    def testIsInstanceActual(self):
        self.assertEqual(isinstance(Integer(), Integer), True)
        self.assertEqual(isinstance(Integer(), (Integer,)), True)

    def testIsSubclassActual(self):
        self.assertEqual(issubclass(Integer, Integer), True)
        self.assertEqual(issubclass(Integer, (Integer,)), True)

    def testSubclassBehavior(self):
        self.assertEqual(issubclass(SubInt, Integer), True)
        self.assertEqual(issubclass(SubInt, (Integer,)), True)
        self.assertEqual(issubclass(SubInt, SubInt), True)
        self.assertEqual(issubclass(SubInt, (SubInt,)), True)
        self.assertEqual(issubclass(Integer, SubInt), False)
        self.assertEqual(issubclass(Integer, (SubInt,)), False)
        self.assertEqual(issubclass(int, SubInt), False)
        self.assertEqual(issubclass(int, (SubInt,)), False)
        self.assertEqual(isinstance(SubInt(), Integer), True)
        self.assertEqual(isinstance(SubInt(), (Integer,)), True)
        self.assertEqual(isinstance(SubInt(), SubInt), True)
        self.assertEqual(isinstance(SubInt(), (SubInt,)), True)
        self.assertEqual(isinstance(42, SubInt), False)
        self.assertEqual(isinstance(42, (SubInt,)), False)


if __name__ == "__main__":
    unittest.main()
