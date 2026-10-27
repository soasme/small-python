# spec: PLS-315 15.3
# description: Programs on loops, each with the output CPython 3.15 gives.
from harness import *

check_program("for text in ['', 'a', '\\n', 'a\\nb\\r\\nc\\r', '\\v\\f\\x1c\\x1d\\x1e',\n             'é\\x85🙂\\u2028尾\\u2029']:\n    print(text.splitlines(), text.splitlines(True), text.splitlines(keepends=True))\n",
              "[] [] []\n['a'] ['a'] ['a']\n[''] ['\\n'] ['\\n']\n['a', 'b', 'c'] ['a\\n', 'b\\r\\n', 'c\\r'] ['a\\n', 'b\\r\\n', 'c\\r']\n['', '', '', '', ''] ['\\x0b', '\\x0c', '\\x1c', '\\x1d', '\\x1e'] ['\\x0b', '\\x0c', '\\x1c', '\\x1d', '\\x1e']\n['é', '🙂', '尾'] ['é\\x85', '🙂\\u2028', '尾\\u2029'] ['é\\x85', '🙂\\u2028', '尾\\u2029']\n")

check_program('''x = 0
while x < 5:
    x += 1
    if x == 2:
        continue
    print(x)
else:
    print('done')
''',
              '''1
3
4
5
done
''')

check_program('''for x in range(5):
    if x == 3:
        break
    print(x)
else:
    print('bad')
for x in []:
    print('bad')
else:
    print('empty')
''',
              '''0
1
2
empty
''')

check_program('''for x in range(3):
    for y in range(3):
        if y == 1:
            break
        print(x, y)
''',
              '''0 0
1 0
2 0
''')
