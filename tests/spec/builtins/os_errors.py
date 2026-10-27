# spec: PLS-315 21.5, 21.3.4, B.3.3
# description: OSError arguments, the errno subclass table, and errors raised by HostOpen.
from harness import *

e = OSError(2, "No such file", "name")
assert_type(e, FileNotFoundError)
assert_eq((e.errno, e.strerror, e.filename, e.filename2), (2, "No such file", "name", None))
assert_eq(e.args, (2, "No such file"))
assert_eq(str(e), "[Errno 2] No such file: 'name'")
e = OSError(1, "perm", "a", None, "b")
assert_type(e, PermissionError)
assert_eq(str(e), "[Errno 1] perm: 'a' -> 'b'")
assert_eq(str(OSError(13, "denied")), "[Errno 13] denied")
for number, cls in ((1, PermissionError), (2, FileNotFoundError), (3, ProcessLookupError), (4, InterruptedError),
                    (10, ChildProcessError), (13, PermissionError), (17, FileExistsError), (20, NotADirectoryError),
                    (21, IsADirectoryError), (32, BrokenPipeError)):
    assert_type(OSError(number, "x"), cls)
assert_type(OSError(99999, "x"), OSError)
assert_type(OSError("2", "x"), OSError)
# One argument or more than five: no attributes, args kept.
e = OSError("just a message")
assert_eq((e.errno, e.strerror, e.filename, e.filename2), (None, None, None, None))
assert_eq(e.args, ("just a message",))
assert_eq(str(e), "just a message")
assert_eq(OSError(1, 2, 3, 4, 5, 6).args, (1, 2, 3, 4, 5, 6))
# A subclass call never changes the class.
class MyError(OSError): pass
assert_type(MyError(2, "x"), MyError)
assert_type(FileExistsError(2, "x"), FileExistsError)
b = BlockingIOError(11, "again", 5)
assert_eq(b.characters_written, 5)
e = assert_raises(AttributeError, getattr, BlockingIOError(11, "again"), "characters_written")
assert_eq(str(e), "characters_written")
assert_is(EnvironmentError, OSError)
assert_is(IOError, OSError)

# HostOpen reports missing files with FileNotFoundError; without HostOpen, open raises OSError.
e = assert_raises(OSError, open, "spec-no-such-file.txt")
if e.errno is not None:
    assert_type(e, FileNotFoundError)
    assert_eq(e.filename, "spec-no-such-file.txt")
