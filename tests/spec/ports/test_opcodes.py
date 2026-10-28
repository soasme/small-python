# spec: PLS-315 15.4, 14.8, 16.6, 14.4, 13.14, 23.6
# description: Try statements in loops, annotations namespaces, raising class exceptions, comparing functions, and % on str subclasses.
# Ported from CPython 3.15.0 Lib/test/test_opcodes.py (docs/licenses/python.txt);
# library imports are replaced by core equivalents, each change marked "(Ported)".
from harness import *
# Python test set -- part 2, opcodes

# (Ported) test.support.swap_item, and the annotated module's source text.
class support:
    class swap_item:
        def __init__(self, obj, item, new_val):
            self.obj, self.item, self.new_val = obj, item, new_val
        def __enter__(self):
            self.real_val = self.obj.get(self.item, None)
            self.had = self.item in self.obj
            self.obj[self.item] = self.new_val
        def __exit__(self, *exc):
            if self.had:
                self.obj[self.item] = self.real_val
            else:
                self.obj.pop(self.item, None)
ANN_MODULE = """
\"\"\"
The module for testing variable annotations.
Empty lines above are for good reason (testing for correct line numbers)
\"\"\"

from typing import Optional

__annotations__[1] = 2

class C:

    x = 5; y: Optional['C'] = None
"""

class OpcodeTest(unittest.TestCase):

    def test_try_inside_for_loop(self):
        n = 0
        for i in range(10):
            n = n+i
            try: 1/0
            except NameError: pass
            except ZeroDivisionError: pass
            except TypeError: pass
            try: pass
            except: pass
            try: pass
            finally: pass
            n = n+i
        if n != 90:
            self.fail('try inside for')

    def test_setup_annotations_line(self):
        # check that SETUP_ANNOTATIONS does not create spurious line numbers
        co = compile(ANN_MODULE, "ann_module.py", 'exec')  # (Ported) source text, not a file
        self.assertEqual(co.co_firstlineno, 1)

    def test_default_annotations_exist(self):
        class C: pass
        self.assertEqual(C.__annotations__, {})

    def test_use_existing_annotations(self):
        ns = {'__annotations__': {1: 2}}
        exec('x: int', ns)
        self.assertEqual(ns['__annotations__'], {1: 2})

    def test_do_not_recreate_annotations(self):
        # Don't rely on the existence of the '__annotations__' global.
        with support.swap_item(globals(), '__annotations__', {}):
            globals().pop('__annotations__', None)
            class C:
                try:
                    del __annotations__
                except NameError:
                    pass
                x: int
            self.assertEqual(C.__annotations__, {"x": int})

    def test_raise_class_exceptions(self):

        class AClass(Exception): pass
        class BClass(AClass): pass
        class CClass(Exception): pass
        class DClass(AClass):
            def __init__(self, ignore):
                pass

        try: raise AClass()
        except: pass

        try: raise AClass()
        except AClass: pass

        try: raise BClass()
        except AClass: pass

        try: raise BClass()
        except CClass: self.fail()
        except: pass

        a = AClass()
        b = BClass()

        try:
            raise b
        except AClass as v:
            self.assertEqual(v, b)
        else:
            self.fail("no exception")

        # not enough arguments
        ##try:  raise BClass, a
        ##except TypeError: pass
        ##else: self.fail("no exception")

        try:  raise DClass(a)
        except DClass as v:
            self.assertIsInstance(v, DClass)
        else:
            self.fail("no exception")

    def test_compare_function_objects(self):

        f = eval('lambda: None')
        g = eval('lambda: None')
        self.assertNotEqual(f, g)

        f = eval('lambda a: a')
        g = eval('lambda a: a')
        self.assertNotEqual(f, g)

        f = eval('lambda a=1: a')
        g = eval('lambda a=1: a')
        self.assertNotEqual(f, g)

        f = eval('lambda: 0')
        g = eval('lambda: 1')
        self.assertNotEqual(f, g)

        f = eval('lambda: None')
        g = eval('lambda a: None')
        self.assertNotEqual(f, g)

        f = eval('lambda a: None')
        g = eval('lambda b: None')
        self.assertNotEqual(f, g)

        f = eval('lambda a: None')
        g = eval('lambda a=None: None')
        self.assertNotEqual(f, g)

        f = eval('lambda a=0: None')
        g = eval('lambda a=1: None')
        self.assertNotEqual(f, g)

    def test_modulo_of_string_subclasses(self):
        class MyString(str):
            def __mod__(self, value):
                return 42
        self.assertEqual(MyString() % 3, 42)


if __name__ == '__main__':
    unittest.main()
