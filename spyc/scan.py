"""The imports a module's source names (docs/build.md 3.3, 3.4), and
--minify (6.2), read from the engine's own tokens.

_spy.tokenize gives the tokens the engine lexes, so spyc reads what the
program runs. Statements are found from the tokens alone: a logical line
ends at a NEWLINE token, a block is INDENT ... DEDENT, and a compound
statement's header ends at its first colon outside brackets that no lambda
claims. A token's level is the bracket depth after it.
"""

import _spy

GUARDS = ("ImportError", "ModuleNotFoundError", "Exception", "BaseException")
COMPOUND = ("if", "elif", "else", "while", "for", "try", "except", "finally", "with", "def", "class")


class Token:
    __slots__ = ("kind", "text", "line", "level")

    def __init__(self, kind, text, line, level):
        self.kind, self.text, self.line, self.level = kind, text, line, level


def tokenize(source, path):
    """The decoded source as bytes, its tokens, and their byte spans;
    SyntaxError if it does not lex."""
    text, raw = _spy.tokenize(source, path)
    tokens = [Token(kind, text[start:end].decode("utf-8"), line, level) for kind, start, end, line, level in raw]
    return text, tokens, [(start, end) for _, start, end, _, _ in raw]


def prefix(token):
    return token.text[:token.text.index(token.text[-1])].lower()


def literal(tokens):
    """The value of a str literal, its adjacent parts joined, or None."""
    if not tokens or any(t.kind != "STRING" or set(prefix(t)) & set("bft") for t in tokens):
        return None
    return eval(" ".join(t.text for t in tokens))


def split(tokens, level):
    """TOKENS split at the commas at depth LEVEL; a trailing comma ends no
    further part."""
    parts, part = [], []
    for t in tokens:
        if t.kind == "OP" and t.text == "," and t.level == level:
            parts.append(part)
            part = []
        else:
            part.append(t)
    if part:
        parts.append(part)
    return parts


def wrapped(tokens, level, open="(", close=")"):
    """Whether one pair of brackets encloses TOKENS, at depth LEVEL."""
    return len(tokens) >= 2 and tokens[0].text == open and tokens[-1].text == close and \
        tokens[-1].level == level and all(t.level > level for t in tokens[:-1])


def unwrap(tokens, level):
    while wrapped(tokens, level):
        tokens, level = tokens[1:-1], level + 1
    return tokens, level


def display(tokens, level):
    """The items of the list or tuple display that TOKENS are, or None."""
    if wrapped(tokens, level, "[", "]"):
        return split(tokens[1:-1], level + 1)
    tokens, level = unwrap(tokens, level)
    commas = any(t.kind == "OP" and t.text == "," and t.level == level for t in tokens)
    return split(tokens, level) if commas or not tokens else None


def keyword(arg):
    return len(arg) > 1 and arg[0].kind == "NAME" and arg[1].kind == "OP" and arg[1].text == "="


def identifier(text):
    """A name spyc accepts: ASCII letters, digits and _, or any non-ASCII
    character, and no leading digit."""
    return bool(text) and not "0" <= text[0] <= "9" and \
        all(ch == "_" or ("a" <= ch.lower() <= "z") or "0" <= ch <= "9" or ord(ch) >= 128 for ch in text)


def dotted(name):
    return all(identifier(part) for part in name.split("."))


class Scanner:
    """The walk of one module. REQUEST(name, required, kind, line) for each
    import, WARN(line, text) for a computed one, and RESOLVE(dots, name,
    required, line) for the absolute name of a relative import, or None."""

    def __init__(self, tokens, request, warn, resolve):
        self.tokens, self.request, self.warn, self.resolve = tokens, request, warn, resolve
        self.stars = []

    # A block's statements: ("simple", start, end, None) for a simple
    # statement, ("compound", start, colon, body) for a clause, its body a
    # list of statements, each a span of self.tokens.
    def block(self, i):
        tokens, statements = self.tokens, []
        while tokens[i].kind not in ("DEDENT", "ENDMARKER"):
            end = i
            while tokens[end].kind != "NEWLINE":
                end += 1
            colon = self.header(i, end)
            if colon is None:
                statements += self.simple(i, end)
                i = end + 1
            elif colon + 1 == end and tokens[end + 1].kind == "INDENT":
                body, after = self.block(end + 2)
                statements.append(("compound", i, colon, body))
                i = after + 1
            else:
                statements.append(("compound", i, colon, self.simple(colon + 1, end)))
                i = end + 1
        return statements, i

    def header(self, i, end):
        """The colon ending a compound statement's header, or None."""
        tokens = self.tokens
        first = tokens[i + 1] if tokens[i].text == "async" and tokens[i].kind == "NAME" else tokens[i]
        if first.kind != "NAME":
            return None
        if first.text not in COMPOUND:
            # match and case are soft keywords: a subject must follow.
            after = tokens[i + 1]
            if first.text not in ("match", "case") or after.kind == "NEWLINE" or (after.kind == "OP" and after.text not in "([{-~*"):
                return None
        lambdas = []
        for j in range(i, end):
            t = tokens[j]
            if t.kind == "NAME" and t.text == "lambda":
                lambdas.append(t.level)
            elif t.kind == "OP" and t.text == ":":
                if lambdas and lambdas[-1] == t.level:
                    lambdas.pop()
                elif t.level == 0:
                    return j
        return None

    def simple(self, i, end):
        statements = []
        for j in range(i, end + 1):
            if j == end or (self.tokens[j].kind == "OP" and self.tokens[j].text == ";"):
                if j > i:
                    statements.append(("simple", i, j, None))
                i = j + 1
        return statements

    def walk(self, statements, guarded):
        tokens, k = self.tokens, 0
        while k < len(statements):
            kind, start, end, body = statements[k]
            k += 1
            if kind == "simple":
                self.statement(tokens[start:end], guarded)
                continue
            if tokens[start].text != "try":
                self.calls(tokens[start:end], guarded)
                self.walk(body, guarded)
                continue
            clauses = []
            while k < len(statements) and statements[k][0] == "compound" and tokens[statements[k][1]].text in ("except", "else", "finally"):
                clauses.append(statements[k])
                k += 1
            catches = any(self.catches(tokens[s + 1:e]) for _, s, e, _ in clauses if tokens[s].text == "except")
            self.walk(body, guarded or catches)
            for _, s, e, b in clauses:
                self.calls(tokens[s:e], guarded)
                self.walk(b, guarded)

    def catches(self, header):
        """Whether an except clause catches a failed import: bare, or naming
        one of GUARDS alone or in a tuple."""
        if header and header[0].text == "*":
            header = header[1:]
        if len(header) >= 2 and header[-2].text == "as" and header[-2].level == 0:
            header = header[:-2]
        if not header:
            return True
        header, level = unwrap(header, 0)
        for part in split(header, level):
            part, _ = unwrap(part, level)
            if len(part) == 1 and part[0].kind == "NAME" and part[0].text in GUARDS:
                return True
        return False

    def statement(self, line, guarded):
        lazy = len(line) > 1 and line[0].text == "lazy" and line[1].text in ("import", "from") and line[1].kind == "NAME"
        if lazy:
            line = line[1:]
        if line[0].kind == "NAME" and line[0].text == "import":
            for part in split(line[1:], 0):
                name = "".join(t.text for t in (part[:-2] if len(part) > 2 and part[-2].text == "as" else part))
                self.request(name, not guarded, "lazy-import" if lazy else "import-statement", line[0].line)
        elif line[0].kind == "NAME" and line[0].text == "from":
            self.from_import(line, guarded, lazy)
        else:
            self.calls(line, guarded)

    def from_import(self, line, guarded, lazy):
        at = next(i for i, t in enumerate(line) if t.kind == "NAME" and t.text == "import")
        lead = 1
        while lead < at and set(line[lead].text) == {"."}:
            lead += 1
        dots = sum(len(t.text) for t in line[1:lead])
        module = "".join(t.text for t in line[lead:at])
        if not dots and module == "__future__":
            return
        base = self.resolve(dots, module, not guarded, line[0].line)
        if base is None:
            return
        self.request(base, not guarded, "lazy-import" if lazy else "from-statement", line[0].line)
        names = line[at + 1:]
        if names[0].text == "*":
            self.stars.append(base)
            return
        names, level = unwrap(names, 0)
        for part in split(names, level):
            self.request(base + "." + part[0].text, False, "maybe", line[0].line)

    def calls(self, line, guarded):
        """Each __import__("a.b", ..., fromlist) with literal names, as the
        import statement."""
        for i, t in enumerate(line):
            if t.kind == "STRING" and "{" in t.text and set(prefix(t)) & set("ft"):
                self.fields(t, guarded)
            if t.kind != "NAME" or t.text != "__import__" or i + 1 == len(line) or line[i + 1].text != "(" or \
                    (i and line[i - 1].text in (".", "def", "class")):
                continue
            end = i + 2
            while line[end].level > t.level:
                end += 1
            args = split(line[i + 2:end], t.level + 1)
            fromlist = next((a[2:] for a in args if keyword(a) and a[0].text == "fromlist"), None)
            if len(args) > 3 and not keyword(args[3]):
                fromlist = args[3]
            name = literal(args[0]) if args and not keyword(args[0]) else None
            if name is None or not dotted(name):
                self.warn(t.line, "__import__ of a computed name cannot be bundled; name its modules with -D")
                continue
            self.request(name, not guarded, "dynamic-import", t.line)
            for item in (display(fromlist, t.level + 1) if fromlist and fromlist[0].text in "([" else None) or []:
                value = literal(item)
                if value is not None and identifier(value):
                    self.request(name + "." + value, False, "maybe", t.line)

    def fields(self, token, guarded):
        """The __import__ calls in the fields of an f-string or t-string."""
        text, depth, start = token.text, 0, 0
        for i, ch in enumerate(text):
            if ch == "{":
                depth += 1
                start = i + 1 if depth == 1 else start
            elif ch == "}" and depth:
                depth -= 1
                if not depth:
                    try:
                        _, tokens, _ = tokenize(text[start:i].encode("utf-8"), "<string>")
                    except SyntaxError:
                        continue
                    for t in tokens:
                        t.line += token.line - 1
                    self.calls(tokens, guarded)


def scan(source, path, request, warn, resolve):
    """Walk SOURCE: its literal __all__ and the modules it imports * from."""
    _, tokens, _ = tokenize(source, path)
    scanner = Scanner(tokens, request, warn, resolve)
    statements, _ = scanner.block(0)
    scanner.walk(statements, False)
    names = []
    for kind, start, end, _ in statements:
        line = tokens[start:end]
        if kind == "simple" and len(line) > 2 and line[0].text == "__all__" and line[1].text == "=" and \
                sum(t.text == "=" and t.level == 0 for t in line) == 1:
            for item in display(line[2:], 0) or []:
                value = literal(item)
                if value is not None:
                    names.append(value)
    return names, scanner.stars


# --minify: the tokens again, each on its line, with one space per
# indentation level and between two tokens only where they would otherwise
# lex as one. Comments go, except a #! line and those that name @license or
# @preserve. The result is UTF-8, so it needs no coding declaration. None if
# it does not lex to the same tokens.
PAIRS = (b"==", b"!=", b"<>", b"<=", b">=", b"**", b"//", b"<<", b">>", b"+=", b"-=", b"*=", b"/=",
         b"%=", b"@=", b"&=", b"|=", b"^=", b":=", b"->", b"..")


def word(byte):
    return chr(byte).isalnum() and byte < 128 or byte == 95 or byte >= 128


def merges(a, b, x, y):
    number = a.kind == "NUMBER"
    if (word(x) or number) and (word(y) or (number and y == 46)):
        return True
    return (a.kind == "STRING" and b.kind == "STRING") or bytes((x, y)) in PAIRS


class Minified:
    def __init__(self, text):
        self.text, self.out, self.line, self.fresh, self.level, self.started = text, [], 1, True, 0, False

    def down_to(self, line):
        """A new line between statements or inside brackets, else a
        backslash continuation."""
        while self.line < line:
            self.out.append(b"\n" if self.fresh or self.level else b"\\\n")
            self.line += 1
            self.started = False

    def comments(self, start, end, line):
        text, i = self.text, start
        while i < end:
            if text[i] == 10:
                line += 1
            elif text[i] == 35:
                stop = text.find(b"\n", i)
                stop = len(text) if stop < 0 else stop
                comment = text[i:stop]
                if (i == 0 and comment[1:2] == b"!") or b"@license" in comment or b"@preserve" in comment:
                    self.down_to(line)
                    self.out.append((b" " if self.started else b"") + comment)
                    self.started = True
                i = stop - 1
            i += 1


def minify(source, path):
    text, tokens, spans = tokenize(source, path)
    m, gap, gap_line, depth, last = Minified(text), 0, 1, 0, None
    for t, (start, end) in zip(tokens, spans):
        m.comments(gap, len(text) if t.kind == "ENDMARKER" else start, gap_line)
        if t.kind == "ENDMARKER":
            m.down_to(t.line)
            break
        if t.kind in ("INDENT", "DEDENT"):
            depth += 1 if t.kind == "INDENT" else -1
            continue
        if t.kind == "NEWLINE":
            m.fresh, gap, gap_line = True, start, t.line
            continue
        m.down_to(t.line)
        if not m.started and m.fresh:
            m.out.append(b" " * depth)
        elif m.started and merges(last, t, text[last_end - 1], text[start]):
            m.out.append(b" ")
        m.out.append(text[start:end])
        m.line += text.count(b"\n", start, end)
        m.fresh, m.started, m.level, last, last_end = False, True, t.level, t, end
        gap, gap_line = end, m.line
    small = b"".join(m.out)
    try:
        _, again, _ = tokenize(small, path)
    except SyntaxError:
        return None
    same = len(again) == len(tokens) and all(
        a.kind == b.kind and a.line == b.line and (a.kind == "NEWLINE" or a.text == b.text) for a, b in zip(tokens, again))
    return small if same else None
