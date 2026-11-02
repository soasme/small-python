# test the invariant that
#   iff a==b then hash(a)==hash(b)
#
# Also test that hash implementations are inherited as expected

# spec: PLS-315 7.5.7, 16.4.3, 19.3.18, 22.1.9
# description: CPython's test_hash: equal numbers hash alike, __hash__ inheritance and None, builtin iterator hashes, and string hash distribution.
# Ported from CPython 3.15.2 Lib/test/test_hash.py (docs/licenses/python.txt);
# library imports are replaced by core equivalents, each change marked "(Ported)".
from harness import *
# (Ported) unittest is the harness's core equivalent. The hash randomization
# and datetime tests run subprocesses and library modules and are omitted,
# with IS_64BIT, which only they use.


class _HashableMeta(type):
    def __instancecheck__(cls, obj):
        for klass in type(obj).__mro__:
            if "__hash__" in klass.__dict__:
                return klass.__dict__["__hash__"] is not None
        return False


class Hashable(metaclass=_HashableMeta):
    """(Ported) collections.abc.Hashable: a class is hashable when the first
    __hash__ along its MRO is not None."""

def lcg(x, length=16):
    """Linear congruential generator"""
    if x == 0:
        return bytes(length)
    out = bytearray(length)
    for i in range(length):
        x = (214013 * x + 2531011) & 0x7fffffff
        out[i] = (x >> 16) & 0xff
    return bytes(out)

def pysiphash(uint64):
    """Convert SipHash24 output to Py_hash_t
    """
    assert 0 <= uint64 < (1 << 64)
    # simple unsigned to signed int64
    if uint64 > (1 << 63) - 1:
        int64 = uint64 - (1 << 64)
    else:
        int64 = uint64
    # mangle uint64 to uint32
    uint32 = (uint64 ^ uint64 >> 32) & 0xffffffff
    # simple unsigned to signed int32
    if uint32 > (1 << 31) - 1:
        int32 = uint32 - (1 << 32)
    else:
        int32 = uint32
    return int32, int64

def skip_unless_internalhash(test):
    """Skip decorator for tests that depend on SipHash24 or FNV"""
    ok = sys.hash_info.algorithm in {"fnv", "siphash13", "siphash24"}
    msg = "Requires SipHash13, SipHash24 or FNV"
    return test if ok else unittest.skip(msg)(test)


class HashEqualityTestCase(unittest.TestCase):

    def same_hash(self, *objlist):
        # Hash each object given and fail if
        # the hash values are not all the same.
        hashed = list(map(hash, objlist))
        for h in hashed[1:]:
            if h != hashed[0]:
                self.fail("hashed values differ: %r" % (objlist,))

    def test_numeric_literals(self):
        self.same_hash(1, 1, 1.0, 1.0+0.0j)
        self.same_hash(0, 0.0, 0.0+0.0j)
        self.same_hash(-1, -1.0, -1.0+0.0j)
        self.same_hash(-2, -2.0, -2.0+0.0j)

    def test_coerced_integers(self):
        self.same_hash(int(1), int(1), float(1), complex(1),
                       int('1'), float('1.0'))
        self.same_hash(int(-2**31), float(-2**31))
        self.same_hash(int(1-2**31), float(1-2**31))
        self.same_hash(int(2**31-1), float(2**31-1))
        # for 64-bit platforms
        self.same_hash(int(2**31), float(2**31))
        self.same_hash(int(-2**63), float(-2**63))
        self.same_hash(int(2**63), float(2**63))

    def test_coerced_floats(self):
        self.same_hash(int(1.23e300), float(1.23e300))
        self.same_hash(float(0.5), complex(0.5, 0.0))

    def test_unaligned_buffers(self):
        # The hash function for bytes-like objects shouldn't have
        # alignment-dependent results (example in issue #16427).
        b = b"123456789abcdefghijklmnopqrstuvwxyz" * 128
        for i in range(16):
            for j in range(16):
                aligned = b[i:128+j]
                unaligned = memoryview(b)[i:128+j]
                self.assertEqual(hash(aligned), hash(unaligned))


_default_hash = object.__hash__
class DefaultHash(object): pass

_FIXED_HASH_VALUE = 42
class FixedHash(object):
    def __hash__(self):
        return _FIXED_HASH_VALUE

class OnlyEquality(object):
    def __eq__(self, other):
        return self is other

class OnlyInequality(object):
    def __ne__(self, other):
        return self is not other

class InheritedHashWithEquality(FixedHash, OnlyEquality): pass
class InheritedHashWithInequality(FixedHash, OnlyInequality): pass

class NoHash(object):
    __hash__ = None

class HashInheritanceTestCase(unittest.TestCase):
    default_expected = [object(),
                        DefaultHash(),
                        OnlyInequality(),
                       ]
    fixed_expected = [FixedHash(),
                      InheritedHashWithEquality(),
                      InheritedHashWithInequality(),
                      ]
    error_expected = [NoHash(),
                      OnlyEquality(),
                      ]

    def test_default_hash(self):
        for obj in self.default_expected:
            self.assertEqual(hash(obj), _default_hash(obj))

    def test_fixed_hash(self):
        for obj in self.fixed_expected:
            self.assertEqual(hash(obj), _FIXED_HASH_VALUE)

    def test_error_hash(self):
        for obj in self.error_expected:
            self.assertRaises(TypeError, hash, obj)

    def test_hashable(self):
        objects = (self.default_expected +
                   self.fixed_expected)
        for obj in objects:
            self.assertIsInstance(obj, Hashable)

    def test_not_hashable(self):
        for obj in self.error_expected:
            self.assertNotIsInstance(obj, Hashable)


# Issue #4701: Check that some builtin types are correctly hashable
class DefaultIterSeq(object):
    seq = range(10)
    def __len__(self):
        return len(self.seq)
    def __getitem__(self, index):
        return self.seq[index]

class HashBuiltinsTestCase(unittest.TestCase):
    hashes_to_check = [enumerate(range(10)),
                       iter(DefaultIterSeq()),
                       iter(lambda: 0, 0),
                      ]

    def test_hashes(self):
        _default_hash = object.__hash__
        for obj in self.hashes_to_check:
            self.assertEqual(hash(obj), _default_hash(obj))

# (Ported) HashRandomizationTests and its subclasses omitted.


class HashDistributionTestCase(unittest.TestCase):

    def test_hash_distribution(self):
        # check for hash collision
        base = "abcdefghabcdefg"
        for i in range(1, len(base)):
            prefix = base[:i]
            with self.subTest(prefix=prefix):
                s15 = set()
                s255 = set()
                for c in range(256):
                    h = hash(prefix + chr(c))
                    s15.add(h & 0xf)
                    s255.add(h & 0xff)
                # SipHash24 distribution depends on key, usually > 60%
                self.assertGreater(len(s15), 8, prefix)
                self.assertGreater(len(s255), 128, prefix)

if __name__ == "__main__":
    unittest.main()
