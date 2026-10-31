/* The metering probe (docs/metering.md 5): adversarial programs, one or more
 * for every family of native operation, most repeating it forever. Under a
 * budget of 1,000,000 steps each must be stopped by the budget, neither
 * completed nor interrupted by the watchdog, which an unmetered operation
 * would reach. */
#include "../spy.h"

#include <stdio.h>
#include <time.h>

static const char *const programs[] = {
    "s = 'a' * 10**7; t = 'a' * 10**7\nwhile True: s == t",
    "s = 'a' * 10**7; t = 'a' * 10**7\nwhile True: s < t",
    "s = 'a' * 10**7\nwhile True: 'b' in s",
    "s = 'a' * 10**7\nwhile True: s.find('b')",
    "s = 'a' * 10**7\nwhile True: s.rfind('b')",
    "s = 'a' * 10**7\nwhile True: s.count('a')",
    "s = 'a' * 10**7\nwhile True: s.replace('b', 'c')",
    "s = 'a' * 10**7\nwhile True: s.strip('b')",
    "s = 'a' * 10**7\nwhile True: s.isalpha()",
    "s = 'a' * 10**7\nwhile True: s.split('b')",
    "s = 'a' * 10**7\nwhile True: s.startswith('a' * 10**6)",
    "s = 'a' * 10**7\nwhile True: s.partition('b')",
    "s = 'a' * 10**7\nwhile True: 'a' * 999 + 'b' in s",
    "s = 'a' * 10**7\nwhile True: s.splitlines()",
    "s = 'a' * 10**7\nwhile True: s.lower()",
    "s = 'a' * 10**7\nwhile True: s.casefold() == s",
    "s = 'a' * 10**7\nwhile True: hash(s[:])",
    "s = 'a' * 10**7\nwhile True: s.encode()",
    "s = 'a' * 10**7\nwhile True: s.isascii()",
    "s = 'a' * 10**7\nwhile True: s.isidentifier()",
    "s = '1' * 10**7\nwhile True: s.isdigit()",
    "s = '1' * 10**6\nwhile True: float(s)",
    "s = 'ab' * 10**6\nwhile True: s.translate({97: 98})",
    "s = 'ä' * 5 * 10**6\nwhile True: s[4 * 10**6]",
    "s = 'ä' * 5 * 10**6\nwhile True: len(s)",
    "s = 'ä' * 10**6\nwhile True: s.find('b')",
    "s = 'ä' * 10**6\nwhile True: s.split('b')",
    "s = 'ä' * 10**6\nwhile True: s.encode()",
    "s = 'ä' * 10**6\nwhile True: s[::-1]",
    "b = b'a' * 10**7; c = b'a' * 10**7\nwhile True: b == c",
    "b = b'a' * 10**7\nwhile True: b'b' in b",
    "b = b'a' * 10**7\nwhile True: b.count(b'a')",
    "b = b'1' * 10**7\nwhile True: b.isdigit()",
    "b = bytes(10**7)\nwhile True: bytes(b)",
    "b = bytes(10**7)\nwhile True: b.hex()",
    "b = bytearray(10**7)\nwhile True: b.find(b'x')",
    "b = bytearray(10**7)\nwhile True: b.insert(0, 1); del b[0]",
    "m = memoryview(b'a' * 10**7); n = memoryview(b'a' * 10**7)\nwhile True: m == n",
    "m = memoryview(bytearray(10**7))\nwhile True: m.tolist()",
    "l = [0] * 10**6; m = [0] * 10**6\nwhile True: l == m",
    "l = [0] * 10**6; m = [0] * 10**6\nwhile True: l < m",
    "l = [0] * 10**6; m = [1] * 10**6\nwhile True: l[:] = m",
    "l = [0] * 10**6\nwhile True: 1 in l",
    "l = [0] * 10**6\nwhile True: l.count(1)",
    "l = [0] * 10**6\nwhile True: l.reverse()",
    "l = [0] * 10**6\nwhile True: l.copy()",
    "l = [0] * 10**6\nwhile True: max(l)",
    "l = [0] * 10**6\nwhile True: sum(l)",
    "l = [0] * 10**6\nwhile True: any(l)",
    "l = [0] * 10**6\nwhile True: str(l)",
    "l = [0] * 10**6\nwhile True: sorted(l)",
    "l = [0] * 10**6\nwhile True: set(l)",
    "l = [0] * 10**6\nwhile True: dict.fromkeys(l)",
    "l = [0] * 10**6\nwhile True: l.insert(0, 1); l.pop(0)",
    "l = [0] * 10**6\nwhile True: del l[0]; l.append(0)",
    "l = [[0]] * 10**6\nwhile True: l == l[:]",
    "l = list(range(10**6))\nwhile True: l.index(10**6 - 1)",
    "l = list(range(10**6))\nwhile True: l.sort()",
    "l = ['a'] * 10**6\nwhile True: ''.join(l)",
    "l = [b'a'] * 10**6\nwhile True: b''.join(l)",
    "t = (0,) * 10**6\nwhile True: hash(t)",
    "t = (0,) * 10**6; u = (0,) * 10**6\nwhile True: t == u",
    "t = (0,) * 10**6\nwhile True: t.count(0)",
    "t = (0,) * 10**6\nwhile True: t.index(0, 10**6 - 1)",
    "t = (int,) * 10**6\nwhile True: isinstance('', t)",
    "t = (int,) * 10**6\nwhile True: issubclass(str, t)",
    "t = ('x',) * 10**6\nwhile True: 'abc'.startswith(t)",
    "d = dict.fromkeys(range(10**5)); e = dict.fromkeys(range(10**5))\nwhile True: d == e",
    "d = dict.fromkeys(range(10**5)); e = dict.fromkeys(range(10**5))\nwhile True: d.keys() <= e.keys()",
    "d = dict.fromkeys(range(10**5))\nwhile True: list(d)",
    "a = set(range(10**5)); b = set(range(10**5))\nwhile True: a <= b",
    "a = set(range(10**5)); b = set(range(10**5, 2 * 10**5))\nwhile True: a.isdisjoint(b)",
    "a = frozenset(range(10**5))\nwhile True: hash(frozenset(a))",
    "x = 7 ** 300000\nwhile True: x * x",
    "x = 7 ** 300000; y = 3 ** 100000\nwhile True: x // y",
    "x = 7 ** 300000\nwhile True: x % 7",
    "x = 7 ** 300000\nwhile True: hex(x)",
    "x = 7 ** 300000; y = 7 ** 300000\nwhile True: x == y",
    "x = 7 ** 300000\nwhile True: x < x + 1",
    "x = 7 ** 300000\nwhile True: x == 1.5",
    "x = 7 ** 300000\nwhile True: hash(x)",
    "x = 7 ** 300000\nwhile True: x.bit_count()",
    "x = 7 ** 300000\nwhile True: x.bit_length()",
    "x = 2 ** 10**6\nwhile True: x >> 1",
    "x = 10 ** 4000\nwhile True: str(x)",
    "h = 'f' * 10**6\nwhile True: int(h, 16)",
    "pow(3, 10**100000, 10**1000 + 7)",
    "x = 7 ** 3000000",
    "s = 'a' * 10**8",
    "l = [0] * 10**8",
    "f = 1e300\nwhile True: '%.1000f' % f",
    "while True: format(5e-324, '.1100f')",
    "while True: format(1.5, '.10000f')",
    "while True: format(1, ',').zfill(10**6)",
    "exec('x = 1\\n' * 10**6)",
    "compile('x = 1\\n' * 10**6, '', 'exec')",
    "while True: eval('1 + 1')",
    "code = compile('x = 1\\n' * 10**5, '', 'exec')\nwhile True: exec(code)",
    "code = compile('class C:\\n' + '    x = 1\\n' * 10**5, '', 'exec')\nwhile True: exec(code)",
    "exec('def f():\\n' + '    x = 1\\n' * 10**5)\nwhile True: f()",
    "exec('def g():\\n' + '    x = 1\\n' * 10**5 + '    yield\\n')\nwhile True: next(g())",
    "f = eval('lambda: (' + '1, ' * 10**5 + '1)')\nwhile True: f()",
};

static double now(void) {
    struct timespec t;
    timespec_get(&t, TIME_UTC);
    return t.tv_sec + t.tv_nsec / 1e9;
}
/* Ten seconds a program: far above the slowest, so that only an unmetered
 * operation reaches it, also under sanitizers. */
static int watchdog(void *data) { return now() > *(double *)data + 10; }

int main(void) {
    double slowest = 0;
    size_t worst = 0, failed = 0, n = sizeof(programs) / sizeof(*programs);
    for (size_t i = 0; i < n; i++) {
        SPYContext *c = spy_context_new();
        double start = now();
        spy_set_step_limit(c, 1000000);
        spy_set_interrupt(c, watchdog, &start);
        int status = spy_exec(c, programs[i], "probe.py");
        double took = now() - start;
        if (status == 0 || spy_stopped(c) != SPY_STOP_STEPS) {
            fprintf(stderr, "metering: %s after %.3fs (%s: %s):\n%s\n", status ? "not stopped by steps" : "completed", took,
                    status ? spy_error_type(c) : "", status ? spy_error_message(c) : "", programs[i]);
            failed++;
        }
        if (took > slowest) { slowest = took; worst = i; }
        spy_context_free(c);
    }
    if (failed) return 1;
    printf("Metering: %zu programs stopped by 1,000,000 steps, the slowest in %.3fs:\n%s\n", n, slowest, programs[worst]);
    return 0;
}
