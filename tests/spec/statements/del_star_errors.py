# spec: PLS-315 14.7
# description: a del statement whose top-level starred item does not parse
# is reported at the items before it, their first invalid part, or else is
# invalid syntax at the star; a starred item that parses cannot be deleted.
from harness import *

for source, message, at, end in [("del *lambda: 0", "invalid syntax", 5, 6), ("del *yield", "invalid syntax", 5, 6), ("del *", "invalid syntax", 5, 6),
                                 ("del a, *lambda: 0", "invalid syntax", 8, 9), ("del *not a", "invalid syntax", 5, 6),
                                 ("del f(), *lambda: 0", "cannot delete function call", 5, 8), ("del a, (b, f()), *not c", "cannot delete function call", 12, 15),
                                 ("del [a, *b], *lambda: 0", "cannot delete starred", 9, 11), ("del *a", "cannot delete starred", 5, 7),
                                 ("del a, *b", "cannot delete starred", 8, 10), ("del *await a", "cannot delete starred", 5, 13),
                                 ("del (*lambda: 0)", "cannot use starred expression here", 6, 16)]:
    caught = assert_syntax_error(source)
    assert_eq((caught.msg, caught.offset, caught.end_offset), (message, at, end), source)
