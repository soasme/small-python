"""Values crossing between CPython and the engine."""
import math
import unittest

from small_python import Object, Runtime


class RoundTripTest(unittest.TestCase):
    def setUp(self):
        self.rt = Runtime()

    def tearDown(self):
        self.rt.close()

    def round_trip(self, value):
        self.rt["x"] = value
        return self.rt.eval("x")

    def test_plain_values_keep_type_and_value(self):
        for value in [None, True, False, 0, 1, -7, 2**63 - 1, -(2**63), 2**63, 2**100, -(2**70),
                      0.0, 1.5, -2.25, 1e308, 2+3j, -1j, "", "héllo\U0001f600", "a\x00b",
                      b"", b"\x00\xff", bytearray(b"ab"), [], [1, [2, [3]]], (), (1, "a"), (1,),
                      {}, {"k": [1]}, {1: "a", (2, 3): None}, set(), {1, 2}, frozenset({3, (4, 5)})]:
            with self.subTest(value=value):
                got = self.round_trip(value)
                self.assertEqual(got, value)
                self.assertIs(type(got), type(value))

    def test_huge_integers(self):
        for value in [10**5000, -(10**5000) - 1, 2**100000 + 12345]:
            with self.subTest(bits=value.bit_length()):
                self.assertEqual(self.round_trip(value), value)
        self.assertEqual(self.rt.eval("(10**5000).bit_length()"), (10**5000).bit_length())
        self.assertEqual(self.rt.eval("-(2**20000)"), -(2**20000))

    def test_engine_sees_the_value(self):
        self.rt["n"] = 2**80
        self.assertEqual(self.rt.eval("n // 2**79"), 2)
        self.rt["s"] = "héllo"
        self.assertEqual(self.rt.eval("len(s), s.upper()"), (5, "HÉLLO"))
        self.rt["b"] = bytearray(b"ab")
        self.assertEqual(self.rt.eval("type(b).__name__"), "bytearray")
        self.rt["fs"] = frozenset({1})
        self.assertEqual(self.rt.eval("type(fs).__name__"), "frozenset")

    def test_special_floats(self):
        nan, inf, negzero = self.rt.eval("float('nan'), float('inf'), -0.0")
        self.assertTrue(math.isnan(nan))
        self.assertEqual(inf, math.inf)
        self.assertEqual(math.copysign(1, negzero), -1)
        self.assertTrue(math.isnan(self.round_trip(math.nan)))

    def test_lone_surrogates(self):
        self.assertEqual(self.round_trip("a\ud800b"), "a\ud800b")
        self.assertEqual(self.rt.eval("len(x)"), 3)
        self.assertEqual(self.rt.eval("'\\udc80'"), "\udc80")

    def test_dict_order_is_kept(self):
        value = {"z": 1, "a": 2, "m": 3}
        self.assertEqual(list(self.round_trip(value)), ["z", "a", "m"])

    def test_values_are_copied(self):
        items = [1, 2]
        self.rt["items"] = items
        items.append(3)
        self.assertEqual(self.rt["items"], [1, 2])
        got = self.rt["items"]
        got.append(4)
        self.assertEqual(self.rt.eval("items"), [1, 2])

    def test_subclasses_of_python_types_convert_to_the_base_type(self):
        class Name(str):
            pass

        class Count(int):
            pass

        got = self.round_trip({"name": Name("a"), "count": Count(3), "flag": True})
        self.assertEqual(got, {"name": "a", "count": 3, "flag": True})
        self.assertIs(type(got["name"]), str)
        self.assertIs(type(got["count"]), int)

    def test_engine_subclasses_stay_engine_objects(self):
        self.rt.exec("class L(list): pass\nclass S(str): pass\nclass I(int): pass")
        for source in ["L([1])", "S('x')", "I(3)"]:
            with self.subTest(source=source):
                self.assertIsInstance(self.rt.eval(source), Object)
        self.assertEqual(list(self.rt.eval("L([1, 2])")), [1, 2])

    def test_containers_of_engine_objects(self):
        self.rt.exec("class P: pass\na = P()\nb = P()")
        values = self.rt.eval("[a, b, a]")
        self.assertIsInstance(values[0], Object)
        self.assertEqual(values[0], values[2])
        self.assertNotEqual(values[0], values[1])
        self.assertEqual(len(self.rt.eval("{a: 1, b: 2}")), 2)
        self.assertEqual(len(self.rt.eval("{a, b, a}")), 2)

    def test_unconvertible_python_values(self):
        for value in [object(), [1, object()], {"k": object()}, {object(): 1}, range(3), ...]:
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    self.rt["bad"] = value
        with self.assertRaises(KeyError):
            self.rt["bad"]

    def test_nesting_limit(self):
        deep = []
        for _ in range(500):
            deep = [deep]
        with self.assertRaises(RecursionError):
            self.rt["deep"] = deep
        with self.assertRaises(RecursionError):
            self.rt.eval("d = []\nfor _ in range(500):\n    d = [d]\nd")
        with self.assertRaises(RecursionError):
            self.rt.eval("a = []\na.append(a)\na")
        self.assertEqual(len(self.round_trip([[[[1]]]])), 1)


if __name__ == "__main__":
    unittest.main()
