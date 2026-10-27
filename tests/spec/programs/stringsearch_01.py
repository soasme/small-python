# spec: PLS-315 23.1
# description: Programs on string search methods, each with the output CPython 3.15 gives.
from harness import *

check_program('''print('aaa'.count('a'))
print(b'aaa'.count(b'a'))
print('aaa'.count('b'))
print(b'aaa'.count(b'b'))
print('aaa'.count('a'))
print(b'aaa'.count(b'a'))
print('aaa'.count('b'))
print(b'aaa'.count(b'b'))
print('aaa'.count('a'))
print(b'aaa'.count(b'a'))
print('aaa'.count('b'))
print(b'aaa'.count(b'b'))
print('aaa'.count('b'))
print(b'aaa'.count(b'b'))
print('aaa'.count('a', 1))
print(b'aaa'.count(b'a', 1))
print('aaa'.count('a', 10))
print(b'aaa'.count(b'a', 10))
print('aaa'.count('a', -1))
print(b'aaa'.count(b'a', -1))
print('aaa'.count('a', -10))
print(b'aaa'.count(b'a', -10))
print('aaa'.count('a', 0, 1))
print(b'aaa'.count(b'a', 0, 1))
print('aaa'.count('a', 0, 10))
print(b'aaa'.count(b'a', 0, 10))
print('aaa'.count('a', 0, -1))
print(b'aaa'.count(b'a', 0, -1))
print('aaa'.count('a', 0, -10))
print(b'aaa'.count(b'a', 0, -10))
print('aaa'.count('', 1))
print(b'aaa'.count(b'', 1))
print('aaa'.count('', 3))
print(b'aaa'.count(b'', 3))
print('aaa'.count('', 10))
print(b'aaa'.count(b'', 10))
print('aaa'.count('', -1))
print(b'aaa'.count(b'', -1))
print('aaa'.count('', -10))
print(b'aaa'.count(b'', -10))
print(''.count(''))
print(b''.count(b''))
print(''.count('', 1, 1))
print(b''.count(b'', 1, 1))
print(''.count('xx'))
print(b''.count(b'xx'))
print(''.count('xx', 1, 1))
print(b''.count(b'xx', 1, 1))
print(b'hello'.count(42))
print('abcdefghiabc'.find('abc'))
print(b'abcdefghiabc'.find(b'abc'))
print('abcdefghiabc'.find('abc', 1))
print(b'abcdefghiabc'.find(b'abc', 1))
print('abcdefghiabc'.find('def', 4))
print(b'abcdefghiabc'.find(b'def', 4))
print('abc'.find('', 0))
print(b'abc'.find(b'', 0))
print('abc'.find('', 3))
print(b'abc'.find(b'', 3))
print('abc'.find('', 4))
print(b'abc'.find(b'', 4))
print('rrarrrrrrrrra'.find('a'))
print(b'rrarrrrrrrrra'.find(b'a'))
print('rrarrrrrrrrra'.find('a', 4))
print(b'rrarrrrrrrrra'.find(b'a', 4))
print('rrarrrrrrrrra'.find('a', 4, 6))
print(b'rrarrrrrrrrra'.find(b'a', 4, 6))
print('rrarrrrrrrrra'.find('a', 4, None))
print(b'rrarrrrrrrrra'.find(b'a', 4, None))
print('rrarrrrrrrrra'.find('a', None, 6))
print(b'rrarrrrrrrrra'.find(b'a', None, 6))
print(''.find(''))
print(b''.find(b''))
print(''.find('', 1, 1))
print(b''.find(b'', 1, 1))
print(''.find('xx'))
print(b''.find(b'xx'))
print(''.find('xx', 1, 1))
print(b''.find(b'xx', 1, 1))
print(b'hello'.find(42))
''',
              '''3
3
0
0
3
3
0
0
3
3
0
0
0
0
2
2
0
0
1
1
3
3
1
1
3
3
2
2
0
0
3
3
1
1
0
0
2
2
4
4
1
1
0
0
0
0
0
0
0
0
0
9
9
-1
-1
0
0
3
3
-1
-1
2
2
12
12
-1
-1
12
12
2
2
0
0
-1
-1
-1
-1
-1
-1
-1
''')

check_program('''print('abcdefghiabc'.rfind('abc'))
print(b'abcdefghiabc'.rfind(b'abc'))
print('abcdefghiabc'.rfind(''))
print(b'abcdefghiabc'.rfind(b''))
print('abcdefghiabc'.rfind('abcd'))
print(b'abcdefghiabc'.rfind(b'abcd'))
print('abcdefghiabc'.rfind('abcz'))
print(b'abcdefghiabc'.rfind(b'abcz'))
print('abc'.rfind('', 0))
print(b'abc'.rfind(b'', 0))
print('abc'.rfind('', 3))
print(b'abc'.rfind(b'', 3))
print('abc'.rfind('', 4))
print(b'abc'.rfind(b'', 4))
print('rrarrrrrrrrra'.rfind('a'))
print(b'rrarrrrrrrrra'.rfind(b'a'))
print('rrarrrrrrrrra'.rfind('a', 4))
print(b'rrarrrrrrrrra'.rfind(b'a', 4))
print('rrarrrrrrrrra'.rfind('a', 4, 6))
print(b'rrarrrrrrrrra'.rfind(b'a', 4, 6))
print('rrarrrrrrrrra'.rfind('a', 4, None))
print(b'rrarrrrrrrrra'.rfind(b'a', 4, None))
print('rrarrrrrrrrra'.rfind('a', None, 6))
print(b'rrarrrrrrrrra'.rfind(b'a', None, 6))
print('<......м...'.rfind('<'))
print(b'hello'.rfind(42))
print('abcdefghiabc'.index(''))
print(b'abcdefghiabc'.index(b''))
print('abcdefghiabc'.index('def'))
print(b'abcdefghiabc'.index(b'def'))
print('abcdefghiabc'.index('abc'))
print(b'abcdefghiabc'.index(b'abc'))
print('abcdefghiabc'.index('abc', 1))
print(b'abcdefghiabc'.index(b'abc', 1))
print('rrarrrrrrrrra'.index('a'))
print(b'rrarrrrrrrrra'.index(b'a'))
print('rrarrrrrrrrra'.index('a', 4))
print(b'rrarrrrrrrrra'.index(b'a', 4))
print('rrarrrrrrrrra'.index('a', 4, None))
print(b'rrarrrrrrrrra'.index(b'a', 4, None))
print('rrarrrrrrrrra'.index('a', None, 6))
print(b'rrarrrrrrrrra'.index(b'a', None, 6))
print('abcdefghiabc'.rindex(''))
print(b'abcdefghiabc'.rindex(b''))
print('abcdefghiabc'.rindex('def'))
print(b'abcdefghiabc'.rindex(b'def'))
print('abcdefghiabc'.rindex('abc'))
print(b'abcdefghiabc'.rindex(b'abc'))
print('abcdefghiabc'.rindex('abc', 0, -1))
print(b'abcdefghiabc'.rindex(b'abc', 0, -1))
print('rrarrrrrrrrra'.rindex('a'))
print(b'rrarrrrrrrrra'.rindex(b'a'))
print('rrarrrrrrrrra'.rindex('a', 4))
print(b'rrarrrrrrrrra'.rindex(b'a', 4))
print('rrarrrrrrrrra'.rindex('a', 4, None))
print(b'rrarrrrrrrrra'.rindex(b'a', 4, None))
print('rrarrrrrrrrra'.rindex('a', None, 6))
print(b'rrarrrrrrrrra'.rindex(b'a', None, 6))
print('hello'.startswith('he'))
print(b'hello'.startswith(b'he'))
print('hello'.startswith('hello'))
print(b'hello'.startswith(b'hello'))
print('hello'.startswith('hello world'))
print(b'hello'.startswith(b'hello world'))
print('hello'.startswith(''))
print(b'hello'.startswith(b''))
print('hello'.startswith('ello'))
print(b'hello'.startswith(b'ello'))
print('hello'.startswith('ello', 1))
print(b'hello'.startswith(b'ello', 1))
print('hello'.startswith('o', 4))
print(b'hello'.startswith(b'o', 4))
print('hello'.startswith('o', 5))
print(b'hello'.startswith(b'o', 5))
print('hello'.startswith('', 5))
print(b'hello'.startswith(b'', 5))
print('hello'.startswith('lo', 6))
print(b'hello'.startswith(b'lo', 6))
print('helloworld'.startswith('lowo', 3))
print(b'helloworld'.startswith(b'lowo', 3))
''',
              '''9
9
12
12
0
0
-1
-1
3
3
3
3
-1
-1
12
12
12
12
-1
-1
12
12
2
2
0
-1
0
0
3
3
0
0
9
9
2
2
12
12
12
12
2
2
12
12
3
3
9
9
0
0
12
12
12
12
12
12
2
2
True
True
True
True
False
False
True
True
False
False
True
True
True
True
False
False
True
True
False
False
True
True
''')

check_program('''print('helloworld'.startswith('lowo', 3, 7))
print('helloworld'.startswith('lowo', 3, 6))
print(''.startswith('', 0, 1))
print(''.startswith('', 0, 0))
print(''.startswith('', 1, 0))
print('hello'.startswith('he', 0, -1))
print('hello'.startswith('he', -53, -1))
print('hello'.startswith('hello', 0, -1))
print('hello'.startswith('hello world', -1, -10))
print('hello'.startswith('ello', -5))
print('hello'.startswith('ello', -4))
print('hello'.startswith('o', -2))
print('hello'.startswith('o', -1))
print('hello'.startswith('', -3, -3))
print('hello'.startswith('lo', -9))
print('hello'.startswith(('he', 'ha')))
print('hello'.startswith(('lo', 'llo')))
print('hello'.startswith(('hellox', 'hello')))
print('hello'.startswith(()))
print('helloworld'.startswith(('hellowo', 'rld', 'lowo'), 3))
print('helloworld'.startswith(('hellowo', 'ello', 'rld'), 3))
print('hello'.startswith(('lo', 'he'), 0, -1))
print('hello'.startswith(('he', 'hel'), 0, 1))
print('hello'.startswith(('he', 'hel'), 0, 2))
print('hello'.endswith('lo'))
print('hello'.endswith('he'))
print('hello'.endswith(''))
print('hello'.endswith('hello world'))
print('helloworld'.endswith('worl'))
print('helloworld'.endswith('worl', 3, 9))
print('helloworld'.endswith('world', 3, 12))
print('helloworld'.endswith('lowo', 1, 7))
print('helloworld'.endswith('lowo', 2, 7))
print('helloworld'.endswith('lowo', 3, 7))
print('helloworld'.endswith('lowo', 4, 7))
print('helloworld'.endswith('lowo', 3, 8))
print('ab'.endswith('ab', 0, 1))
print('ab'.endswith('ab', 0, 0))
print(''.endswith('', 0, 1))
print(''.endswith('', 0, 0))
''',
              '''True
False
True
True
False
True
True
False
False
False
True
False
True
True
False
True
False
True
False
True
False
True
False
True
True
False
True
False
False
True
True
True
True
True
False
False
False
False
True
True
''')

check_program('''print(''.endswith('', 1, 0))
print(b''.endswith(b'', 1, 0))
print('hello'.endswith('lo', -2))
print(b'hello'.endswith(b'lo', -2))
print('hello'.endswith('he', -2))
print(b'hello'.endswith(b'he', -2))
print('hello'.endswith('', -3, -3))
print(b'hello'.endswith(b'', -3, -3))
print('hello'.endswith('hello world', -10, -2))
print(b'hello'.endswith(b'hello world', -10, -2))
print('helloworld'.endswith('worl', -6))
print(b'helloworld'.endswith(b'worl', -6))
print('helloworld'.endswith('worl', -5, -1))
print(b'helloworld'.endswith(b'worl', -5, -1))
print('helloworld'.endswith('worl', -5, 9))
print(b'helloworld'.endswith(b'worl', -5, 9))
print('helloworld'.endswith('world', -7, 12))
print(b'helloworld'.endswith(b'world', -7, 12))
print('helloworld'.endswith('lowo', -99, -3))
print(b'helloworld'.endswith(b'lowo', -99, -3))
print('helloworld'.endswith('lowo', -8, -3))
print(b'helloworld'.endswith(b'lowo', -8, -3))
print('helloworld'.endswith('lowo', -7, -3))
print(b'helloworld'.endswith(b'lowo', -7, -3))
print('helloworld'.endswith('lowo', 3, -4))
print(b'helloworld'.endswith(b'lowo', 3, -4))
print('helloworld'.endswith('lowo', -8, -2))
print(b'helloworld'.endswith(b'lowo', -8, -2))
print('hello'.endswith(('he', 'ha')))
print(b'hello'.endswith((b'he', b'ha')))
print('hello'.endswith(('lo', 'llo')))
print(b'hello'.endswith((b'lo', b'llo')))
print('hello'.endswith(('hellox', 'hello')))
print(b'hello'.endswith((b'hellox', b'hello')))
print('hello'.endswith(()))
print(b'hello'.endswith(()))
print('helloworld'.endswith(('hellowo', 'rld', 'lowo'), 3))
print(b'helloworld'.endswith((b'hellowo', b'rld', b'lowo'), 3))
print('helloworld'.endswith(('hellowo', 'ello', 'rld'), 3, -1))
print(b'helloworld'.endswith((b'hellowo', b'ello', b'rld'), 3, -1))
print('hello'.endswith(('hell', 'ell'), 0, -1))
print(b'hello'.endswith((b'hell', b'ell'), 0, -1))
print('hello'.endswith(('he', 'hel'), 0, 1))
print(b'hello'.endswith((b'he', b'hel'), 0, 1))
print('hello'.endswith(('he', 'hell'), 0, 4))
print(b'hello'.endswith((b'he', b'hell'), 0, 4))
''',
              '''False
False
True
True
False
False
True
True
False
False
False
False
True
True
True
True
True
True
True
True
True
True
True
True
False
False
False
False
False
False
True
True
True
True
False
False
True
True
False
False
True
True
False
False
True
True
''')

check_program("try: print(b'\\xe4\\xb8\\xadcc\\xe4\\xb8\\xada\\x00bb\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9b\\xed\\xa0\\x80\\x00\\x00c\\xe4\\xb8\\xadac\\xc3\\xa9acbabb'.startswith(b'\\xc3\\xa9acbabb', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadcc\\xe4\\xb8\\xada\\x00bb\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9b\\xed\\xa0\\x80\\x00\\x00c\\xe4\\xb8\\xadac\\xc3\\xa9acbabb'.rindex(b'\\xc3\\xa9acbabb', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中ac\\ud800\\x00ba\\x00\\x00é\\x00é\\x00éa\\x00acbb中\\x00'.rfind('b\\x00c\\x00b', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xc3\\xa9c\\xed\\xa0\\x80\\xc3\\xa9ba\\x00\\xed\\xa0\\x80b\\xe4\\xb8\\xad\\x00a\\xe4\\xb8\\xad'.endswith(b'\\xe4\\xb8\\xadc\\xed\\xa0\\x80', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xc3\\xa9c\\xed\\xa0\\x80\\xc3\\xa9ba\\x00\\xed\\xa0\\x80b\\xe4\\xb8\\xad\\x00a\\xe4\\xb8\\xad'.count(b'\\xe4\\xb8\\xadc\\xed\\xa0\\x80', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800\\x00\\ud800c\\x00bé中'.index('中', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9cc\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\xc3\\xa9a\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9cbbac\\xe4\\xb8\\xad'.find(b'\\xed\\xa0\\x80a\\x00c'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cébc中aa\\ud800\\x00'.startswith('中\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cébc中aa\\ud800\\x00'.rindex('中\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xc3\\xa9acb\\xc3\\xa9b\\x00c\\xc3\\xa9a\\xe4\\xb8\\xadcab\\xe4\\xb8\\xadb\\xc3\\xa9a\\xc3\\xa9'.rfind(b'cb\\xc3\\xa9b\\x00c\\xc3\\xa9a\\xe4\\xb8\\xadcab\\xe4\\xb8\\xadb\\xc3\\xa9a\\xc3\\xa9'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aca\\x00ba中a中abéb中ébca\\ud800ab'.endswith('中a\\ud800\\ud800é\\ud800', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aca\\x00ba中a中abéb中ébca\\ud800ab'.count('中a\\ud800\\ud800é\\ud800', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9c\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xc3\\xa9b\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9bb'.index(b'\\xed\\xa0\\x80aa\\x00\\xed\\xa0\\x80'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aé\\ud800\\ud800\\x00\\ud800\\ud800c中éab\\ud800\\x00é\\x00a\\ud800b\\x00\\x00a\\x00\\ud800éb'.find('\\ud800\\x00é\\x00a\\ud800b\\x00\\x00a\\x00\\ud800éb', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b''.startswith(b'bb\\xc3\\xa9\\xc3\\xa9a\\xed\\xa0\\x80b', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b''.rindex(b'bb\\xc3\\xa9\\xc3\\xa9a\\xed\\xa0\\x80b', -100, 100))\nexcept Exception as error: print(type(error).__name__)\n",
              '''False
31
-1
False
0
ValueError
-1
False
ValueError
4
False
0
ValueError
12
False
ValueError
''')

check_program("try: print('中\\x00中\\ud800a中ca\\ud800a中\\x00中cb\\ud800é\\ud800c中\\x00'.rfind('中中a中中', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ac\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xed\\xa0\\x80\\x00\\xc3\\xa9\\x00aab\\xed\\xa0\\x80b\\xc3\\xa9ab\\x00c\\xc3\\xa9b\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80'.find(b'b\\xc3\\xa9ab\\x00c\\xc3\\xa9b\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c\\x00\\x00中bc中'.endswith('中bccca', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9c\\xed\\xa0\\x80c\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadbbb\\xed\\xa0\\x80\\xed\\xa0\\x80b\\xed\\xa0\\x80bc\\x00a\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80b\\x00\\x00\\xc3\\xa9c\\xed\\xa0\\x80caa\\x00\\xed\\xa0\\x80c\\xc3\\xa9b'.startswith(b'c', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9c\\xed\\xa0\\x80c\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadbbb\\xed\\xa0\\x80\\xed\\xa0\\x80b\\xed\\xa0\\x80bc\\x00a\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80b\\x00\\x00\\xc3\\xa9c\\xed\\xa0\\x80caa\\x00\\xed\\xa0\\x80c\\xc3\\xa9b'.count(b'c', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bcécb'.rindex('cb', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\x00ca\\x00'.index(b'bbb'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800éé\\x00cé\\x00c\\ud800中é中ac\\ud800a'.rfind('\\ud800a', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xc3\\xa9\\xc3\\xa9\\x00\\xc3\\xa9\\xc3\\xa9b\\xed\\xa0\\x80\\xc3\\xa9ca\\xed\\xa0\\x80\\x00\\x00\\xed\\xa0\\x80a\\x00b\\xed\\xa0\\x80\\x00ac\\xed\\xa0\\x80'.find(b'b\\xed\\xa0\\x80\\x00ac\\xed\\xa0\\x80', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a\\ud800\\ud800acb\\x00b\\ud800\\x00éb\\x00\\x00\\x00é\\ud800a中é中\\x00\\x00\\x00éb中'.endswith('accb中'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80c\\x00acc\\xed\\xa0\\x80ac\\xc3\\xa9\\xed\\xa0\\x80\\x00\\xc3\\xa9cc\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadcbc\\xc3\\xa9'.startswith(b'\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00c', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80c\\x00acc\\xed\\xa0\\x80ac\\xc3\\xa9\\xed\\xa0\\x80\\x00\\xc3\\xa9cc\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadcbc\\xc3\\xa9'.count(b'\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00c', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ééc\\x00a\\x00bcbb中aa\\ud800中\\ud800\\ud800中\\x00\\ud800a\\x00aa'.rindex('a\\x00bcbb中aa\\ud800中\\ud800\\ud800中\\x00\\ud800a\\x00aa', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xe4\\xb8\\xad\\x00c\\xe4\\xb8\\xad\\x00ba\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9cabbca\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xed\\xa0\\x80c'.index(b'b\\xe4\\xb8\\xada\\xe4\\xb8\\xad\\xed\\xa0\\x80', 10000))\nexcept Exception as error: print(type(error).__name__)\n",
              '''-1
27
False
False
6
3
ValueError
-1
28
False
False
0
ValueError
ValueError
''')

check_program("try: print(b'\\xc3\\xa9\\xe4\\xb8\\xad\\x00c\\xe4\\xb8\\xad\\x00ba\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9cabbca\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xed\\xa0\\x80c'.count(b'b\\xe4\\xb8\\xada\\xe4\\xb8\\xad\\xed\\xa0\\x80', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aébéb中\\x00b中aacé\\x00\\x00\\ud800\\x00\\ud800cé\\ud800\\ud800éaaaa\\x00'.index('a', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9b\\xed\\xa0\\x80cc\\x00cb\\xc3\\xa9'.find(b'cb\\xc3\\xa9'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('béé中é\\x00\\x00é\\ud800\\ud800é\\ud800中b\\x00c\\x00\\ud800\\ud800éb\\x00\\ud800ébb\\x00\\ud800ca\\ud800'.startswith('éc\\ud800', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('béé中é\\x00\\x00é\\ud800\\ud800é\\ud800中b\\x00c\\x00\\ud800\\ud800éb\\x00\\ud800ébb\\x00\\ud800ca\\ud800'.rindex('éc\\ud800', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xc3\\xa9\\x00\\xc3\\xa9\\xed\\xa0\\x80ba\\xc3\\xa9\\xc3\\xa9a\\xed\\xa0\\x80b\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9b\\xed\\xa0\\x80\\xc3\\xa9'.rfind(b'', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cé\\ud800\\x00béc\\x00中中\\ud800\\x00ébc'.endswith('c\\x00中中\\ud800\\x00ébc', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cé\\ud800\\x00béc\\x00中中\\ud800\\x00ébc'.count('c\\x00中中\\ud800\\x00ébc', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\x00\\xe4\\xb8\\xadbbc\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xadc'.index(b'c\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\x00aa\\x00a\\x00cbc'.find('', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80cb\\xc3\\xa9ab\\x00c\\xc3\\xa9\\xed\\xa0\\x80\\x00a'.startswith(b'', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80cb\\xc3\\xa9ab\\x00c\\xc3\\xa9\\xed\\xa0\\x80\\x00a'.rindex(b'', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00\\ud800中é\\x00éééc\\ud800éaacéc\\ud800c中\\ud800é中a\\ud800b\\ud800b中中\\x00b\\ud800\\x00\\x00é'.rfind('', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadcc\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\xed\\xa0\\x80'.endswith(b'', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadcc\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\xed\\xa0\\x80'.count(b'', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00中\\ud800中baccabacaéé'.index('中baccabacaéé', 0))\nexcept Exception as error: print(type(error).__name__)\n",
              '''0
0
14
False
ValueError
32
True
1
ValueError
-1
True
17
35
True
1
3
''')

check_program("try: print(b'\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80\\x00\\x00\\x00\\xc3\\xa9a\\xe4\\xb8\\xadc\\xed\\xa0\\x80b\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80a\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xadb\\xed\\xa0\\x80c'.find(b'b\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80a', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00c\\ud800é\\ud800abb\\ud800\\ud800bc\\ud800\\ud800aé\\x00ac\\ud800'.endswith('\\x00ébé', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xc3\\xa9a\\xc3\\xa9c\\xed\\xa0\\x80b\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9b\\xed\\xa0\\x80ac\\xc3\\xa9ab\\xed\\xa0\\x80b\\x00c\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80a\\xc3\\xa9\\xed\\xa0\\x80ac\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xc3\\xa9\\xed\\xa0\\x80b\\x00b\\x00\\xc3\\xa9'.startswith(b'c\\xc3\\xa9\\xed\\xa0\\x80b\\x00b\\x00\\xc3\\xa9', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xc3\\xa9a\\xc3\\xa9c\\xed\\xa0\\x80b\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9b\\xed\\xa0\\x80ac\\xc3\\xa9ab\\xed\\xa0\\x80b\\x00c\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80a\\xc3\\xa9\\xed\\xa0\\x80ac\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xc3\\xa9\\xed\\xa0\\x80b\\x00b\\x00\\xc3\\xa9'.count(b'c\\xc3\\xa9\\xed\\xa0\\x80b\\x00b\\x00\\xc3\\xa9', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ac中\\ud800b'.rindex('', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'bb\\x00\\xc3\\xa9\\xc3\\xa9'.index(b'\\xed\\xa0\\x80c\\x00baca'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\ud800中aab中é中éécé中中\\x00bbbcb中c\\x00b中bb\\ud800中'.rfind('b中é中éécé中中\\x00bbbcb中c\\x00b中bb\\ud800中', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9abbb\\xc3\\xa9\\xc3\\xa9c'.find(b'\\xed\\xa0\\x80a'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ccb\\ud800\\ud800éa\\x00é\\ud800bb\\x00ab\\ud800\\ud800cé\\ud800\\ud800\\x00\\x00cba中cb\\ud800'.endswith('\\x00中\\ud800aéa', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xc3\\xa9b\\xe4\\xb8\\xadaab\\x00aaa\\xed\\xa0\\x80c\\xed\\xa0\\x80bcc\\xed\\xa0\\x80ac\\xed\\xa0\\x80\\xed\\xa0\\x80'.startswith(b'\\xed\\xa0\\x80'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xc3\\xa9b\\xe4\\xb8\\xadaab\\x00aaa\\xed\\xa0\\x80c\\xed\\xa0\\x80bcc\\xed\\xa0\\x80ac\\xed\\xa0\\x80\\xed\\xa0\\x80'.count(b'\\xed\\xa0\\x80'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中中\\ud800\\ud800\\ud800cc\\x00ccaé\\x00中\\x00bc\\ud800bb中中'.rindex('\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadcbb\\x00\\xc3\\xa9\\xed\\xa0\\x80b\\x00\\x00b\\xed\\xa0\\x80\\xed\\xa0\\x80c\\xc3\\xa9a\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80c\\xed\\xa0\\x80\\x00\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xad'.index(b'\\xe4\\xb8\\xad\\xc3\\xa9a', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ac中\\ud800中b中acéaé中é中b\\ud800\\ud800é\\ud800中éc中\\x00b\\ud800中bé\\x00céac'.rfind('中\\ud800中b中acéaé中é中b\\ud800\\ud800é\\ud800中éc中\\x00b\\ud800中bé\\x00céac', None))\nexcept Exception as error: print(type(error).__name__)\n",
              '''-1
False
False
1
5
ValueError
-1
-1
False
True
6
ValueError
ValueError
2
''')

check_program("try: print('ac中\\ud800中b中acéaé中é中b\\ud800\\ud800é\\ud800中éc中\\x00b\\ud800中bé\\x00céac'.rindex('中\\ud800中b中acéaé中é中b\\ud800\\ud800é\\ud800中éc中\\x00b\\ud800中bé\\x00céac', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9acac\\xed\\xa0\\x80b\\xe4\\xb8\\xadc\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xadcb\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80\\xc3\\xa9ab\\xed\\xa0\\x80\\x00\\x00\\xe4\\xb8\\xadbba'.index(b'\\xc3\\xa9\\xed\\xa0\\x80b', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('éa\\ud800a中c\\x00é中b\\x00é\\ud800c中\\ud800é\\ud800中c'.rfind('中éa', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadcb\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xadb\\xc3\\xa9\\x00\\x00\\x00'.find(b'\\xe4\\xb8\\xadcb\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xadb\\xc3\\xa9\\x00\\x00\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b\\x00abca\\ud800c中b\\ud800中éab中a中\\ud800éé'.endswith('中\\ud800中\\x00c', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00abb\\xe4\\xb8\\xadcab\\xe4\\xb8\\xada\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xadaaaba\\xed\\xa0\\x80a\\xc3\\xa9a\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80ccaccb\\xe4\\xb8\\xad\\x00bca'.startswith(b'acbaa'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00abb\\xe4\\xb8\\xadcab\\xe4\\xb8\\xada\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xadaaaba\\xed\\xa0\\x80a\\xc3\\xa9a\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80ccaccb\\xe4\\xb8\\xad\\x00bca'.count(b'acbaa'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(''.rindex('', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00ca\\xe4\\xb8\\xadba\\x00b\\x00b\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xe4\\xb8\\xada'.index(b'\\xed\\xa0\\x80c\\xe4\\xb8\\xad', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cbccé中c中a\\x00\\ud800中é\\x00中\\ud800bc'.rfind('a中'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00c\\xe4\\xb8\\xad\\xc3\\xa9c\\xc3\\xa9c\\xed\\xa0\\x80'.find(b'\\xe4\\xb8\\xad\\x00c\\xe4\\xb8\\xad\\xc3\\xa9c\\xc3\\xa9c\\xed\\xa0\\x80', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00ba中bca\\ud800éb\\x00cacé中ab中\\x00é\\x00cbbb\\x00\\x00中a\\x00'.endswith('', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'cb\\xe4\\xb8\\xadc\\x00\\x00b\\x00\\xc3\\xa9b\\x00\\x00\\xed\\xa0\\x80'.startswith(b'\\xed\\xa0\\x80\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'cb\\xe4\\xb8\\xadc\\x00\\x00b\\x00\\xc3\\xa9b\\x00\\x00\\xed\\xa0\\x80'.count(b'\\xed\\xa0\\x80\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\n",
              '''2
ValueError
-1
0
False
False
0
0
ValueError
-1
7
False
False
0
''')

check_program("try: print('c中\\ud800ca\\x00aac\\ud800'.endswith('\\ud800ca\\x00aac\\ud800', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c中\\ud800ca\\x00aac\\ud800'.count('\\ud800ca\\x00aac\\ud800', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xed\\xa0\\x80cbbbb\\xc3\\xa9\\xc3\\xa9\\x00\\xe4\\xb8\\xad'.index(b'', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c\\x00b中cc\\ud800\\x00\\x00é中aa\\x00éb\\ud800bécéé中a中é\\x00b中é\\ud800é'.find('ébéb中c', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\x00b\\xe4\\xb8\\xadbccca\\xe4\\xb8\\xadaabc\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80bcac\\xc3\\xa9\\x00'.startswith(b'\\xed\\xa0\\x80\\xed\\xa0\\x80bcac\\xc3\\xa9\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\x00b\\xe4\\xb8\\xadbccca\\xe4\\xb8\\xadaabc\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80bcac\\xc3\\xa9\\x00'.rindex(b'\\xed\\xa0\\x80\\xed\\xa0\\x80bcac\\xc3\\xa9\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c中\\ud800cababb\\x00\\ud800b\\x00é\\ud800中a\\ud800\\x00b\\ud800\\x00a中écbé\\ud800é'.rfind('caab'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xc3\\xa9\\x00\\xc3\\xa9ab\\x00cac\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80bb\\xed\\xa0\\x80\\x00aa\\xed\\xa0\\x80ccab\\xc3\\xa9bba'.endswith(b'\\xed\\xa0\\x80bc\\xed\\xa0\\x80b', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xc3\\xa9\\x00\\xc3\\xa9ab\\x00cac\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80bb\\xed\\xa0\\x80\\x00aa\\xed\\xa0\\x80ccab\\xc3\\xa9bba'.count(b'\\xed\\xa0\\x80bc\\xed\\xa0\\x80b', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a中\\x00éb\\ud800\\ud800\\ud800中é\\ud800\\x00cc中'.index('\\ud800\\ud800\\ud800中é\\ud800\\x00cc中', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00bca\\xc3\\xa9aa\\xe4\\xb8\\xadacbbb\\xe4\\xb8\\xadc\\xe4\\xb8\\xad\\xe4\\xb8\\xad'.find(b'\\xe4\\xb8\\xadc', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中中éaé\\ud800中\\ud800\\x00bab\\x00\\ud800中b\\x00éb\\ud800中ab中'.startswith('c\\ud800\\x00\\ud800\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中中éaé\\ud800中\\ud800\\x00bab\\x00\\ud800中b\\x00éb\\ud800中ab中'.rindex('c\\ud800\\x00\\ud800\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\x00\\xe4\\xb8\\xad\\xc3\\xa9c\\xed\\xa0\\x80bb\\x00\\xe4\\xb8\\xada\\xe4\\xb8\\xadbb\\xed\\xa0\\x80\\xed\\xa0\\x80ab\\x00\\x00\\xc3\\xa9a'.rfind(b'\\xc3\\xa9a', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c\\ud800a'.endswith('c\\x00é', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c\\ud800a'.count('c\\x00é', None))\nexcept Exception as error: print(type(error).__name__)\n",
              '''True
1
14
-1
False
30
-1
False
0
5
16
False
ValueError
33
False
0
''')

check_program("try: print(b'\\x00\\xc3\\xa9'.index(b'', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c\\x00\\x00中中\\x00bcc\\x00abéa\\x00中'.rfind('béa\\x00中', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9c\\xc3\\xa9bb\\xc3\\xa9'.find(b'c\\xc3\\xa9cc\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中ac\\ud800é'.endswith(''))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\x00cabcb\\x00\\x00\\x00\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\xc3\\xa9cc\\xe4\\xb8\\xad\\xc3\\xa9caa\\xc3\\xa9\\xe4\\xb8\\xad\\x00a\\xed\\xa0\\x80'.startswith(b'\\x00\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\xc3\\xa9cc\\xe4\\xb8\\xad\\xc3\\xa9caa\\xc3\\xa9\\xe4\\xb8\\xad\\x00a\\xed\\xa0\\x80', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\x00cabcb\\x00\\x00\\x00\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\xc3\\xa9cc\\xe4\\xb8\\xad\\xc3\\xa9caa\\xc3\\xa9\\xe4\\xb8\\xad\\x00a\\xed\\xa0\\x80'.count(b'\\x00\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\xc3\\xa9cc\\xe4\\xb8\\xad\\xc3\\xa9caa\\xc3\\xa9\\xe4\\xb8\\xad\\x00a\\xed\\xa0\\x80', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ac\\ud800ccabc'.rindex('\\ud800ab\\x00\\ud800', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00a\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xed\\xa0\\x80a\\xed\\xa0\\x80\\xed\\xa0\\x80aa\\x00a\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xad'.index(b'b', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cb中é\\ud800中\\x00c\\x00c\\ud800\\x00b\\x00'.rfind('c\\x00c\\ud800\\x00b\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadb'.find(b'\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xad\\x00\\x00a', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c中cb\\ud800cc\\ud800中中'.endswith('c\\ud800\\x00é中', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00b\\xc3\\xa9cc\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9b\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xe4\\xb8\\xad\\x00a\\x00\\x00\\xc3\\xa9baa\\x00\\x00\\xe4\\xb8\\xadac\\xe4\\xb8\\xadacccc\\xed\\xa0\\x80a\\x00\\xe4\\xb8\\xadac'.startswith(b'\\xc3\\xa9cc\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9b\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xe4\\xb8\\xad\\x00a\\x00\\x00\\xc3\\xa9baa\\x00\\x00\\xe4\\xb8\\xadac\\xe4\\xb8\\xadacccc\\xed\\xa0\\x80a\\x00\\xe4\\xb8\\xadac'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00b\\xc3\\xa9cc\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9b\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xe4\\xb8\\xad\\x00a\\x00\\x00\\xc3\\xa9baa\\x00\\x00\\xe4\\xb8\\xadac\\xe4\\xb8\\xadacccc\\xed\\xa0\\x80a\\x00\\xe4\\xb8\\xadac'.count(b'\\xc3\\xa9cc\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9b\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xe4\\xb8\\xad\\x00a\\x00\\x00\\xc3\\xa9baa\\x00\\x00\\xe4\\xb8\\xadac\\xe4\\xb8\\xadacccc\\xed\\xa0\\x80a\\x00\\xe4\\xb8\\xadac'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a\\x00\\ud800\\ud800中b中\\x00ac中中c\\x00\\ud800éabacb中c中cbcb\\ud800c'.rindex('', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\n",
              '''1
-1
-1
True
False
1
ValueError
ValueError
-1
-1
False
False
1
30
''')

check_program("try: print(b'b\\xe4\\xb8\\xadbc\\x00\\xed\\xa0\\x80c\\xc3\\xa9cac\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9a\\xe4\\xb8\\xad'.startswith(b'\\x00aaa\\xe4\\xb8\\xad', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xe4\\xb8\\xadbc\\x00\\xed\\xa0\\x80c\\xc3\\xa9cac\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9a\\xe4\\xb8\\xad'.count(b'\\x00aaa\\xe4\\xb8\\xad', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800b\\ud800a中中\\x00ca\\ud800\\x00cé\\x00a'.rindex('\\x00ca\\ud800\\x00cé\\x00a', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadc\\x00\\xed\\xa0\\x80a\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xadbc\\x00a\\x00aac\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80c\\x00\\x00\\x00'.index(b'\\xc3\\xa9b', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800bb\\ud800a\\ud800中\\ud800c中abcc中中\\x00b\\x00中é中b\\x00a\\x00aéb\\x00中\\x00cbb'.rfind('中b中éé\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80b\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9a\\xe4\\xb8\\xadb\\xc3\\xa9c\\xed\\xa0\\x80c\\xc3\\xa9'.find(b'\\xe4\\xb8\\xadb\\xc3\\xa9c\\xed\\xa0\\x80c\\xc3\\xa9', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00accc中'.endswith('c中\\ud800中bb', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xed\\xa0\\x80b\\x00\\xed\\xa0\\x80b\\xe4\\xb8\\xad\\xc3\\xa9\\x00\\xe4\\xb8\\xad\\xc3\\xa9cc\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00ba\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80\\x00a\\xe4\\xb8\\xada\\x00ab'.startswith(b'\\xed\\xa0\\x80\\x00', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xed\\xa0\\x80b\\x00\\xed\\xa0\\x80b\\xe4\\xb8\\xad\\xc3\\xa9\\x00\\xe4\\xb8\\xad\\xc3\\xa9cc\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00ba\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80\\x00a\\xe4\\xb8\\xada\\x00ab'.count(b'\\xed\\xa0\\x80\\x00', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a中a中b\\x00écé中cé\\x00bbc\\ud800\\ud800é中\\x00bcb'.rindex('中cé\\x00bbc\\ud800\\ud800é中\\x00bcb', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xed\\xa0\\x80baa\\x00ab\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\xc3\\xa9\\xe4\\xb8\\xadc\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00b\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xc3\\xa9aaa'.index(b'b\\xc3\\xa9\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ébé'.rfind('ba\\x00cbb', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xc3\\xa9\\xc3\\xa9aa\\xed\\xa0\\x80\\x00\\x00\\xc3\\xa9cccb\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80a\\xc3\\xa9c\\xed\\xa0\\x80c\\x00b\\x00cbaa\\xed\\xa0\\x80c\\xe4\\xb8\\xadb\\x00\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00\\x00c'.find(b'c\\xe4\\xb8\\xadb\\x00\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00\\x00c', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800é\\x00\\x00bé中中éé中a\\x00bc\\x00aaébébca中é\\x00aééca\\x00b'.endswith('\\ud800c\\ud800bc中\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\n",
              '''False
0
6
ValueError
-1
12
False
False
0
9
ValueError
-1
45
False
''')

check_program("try: print('\\ud800é\\x00\\x00bé中中éé中a\\x00bc\\x00aaébébca中é\\x00aééca\\x00b'.rfind('\\ud800c\\ud800bc中\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'aa\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xadb\\x00\\x00\\x00b\\xc3\\xa9c'.endswith(b'\\xc3\\xa9\\xc3\\xa9a', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'aa\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xadb\\x00\\x00\\x00b\\xc3\\xa9c'.count(b'\\xc3\\xa9\\xc3\\xa9a', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00\\x00b\\ud800b\\x00c中béé\\ud800a'.index('c中béé\\ud800a', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00b\\xc3\\xa9a\\xc3\\xa9\\xed\\xa0\\x80a\\xe4\\xb8\\xadab\\xed\\xa0\\x80'.find(b'c', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('écba\\ud800bb\\ud800aa\\ud800é\\x00b\\x00a中é\\x00c\\ud800\\x00\\ud800é\\x00'.startswith('\\x00\\x00é中bb', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('écba\\ud800bb\\ud800aa\\ud800é\\x00b\\x00a中é\\x00c\\ud800\\x00\\ud800é\\x00'.rindex('\\x00\\x00é中bb', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80\\x00'.rfind(b'\\x00\\xed\\xa0\\x80\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800'.endswith('é中accb', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800'.count('é中accb', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadbb\\xc3\\xa9\\xc3\\xa9baca\\xe4\\xb8\\xadc\\xc3\\xa9\\x00b\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00cb\\xe4\\xb8\\xada\\x00b\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xc3\\xa9'.index(b'', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c中abc\\x00\\x00a'.find('a', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80b\\xc3\\xa9ca\\x00a\\x00\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\xe4\\xb8\\xadac\\x00b\\xe4\\xb8\\xadcb\\xe4\\xb8\\xadbabb\\xc3\\xa9\\xc3\\xa9\\x00\\x00\\xed\\xa0\\x80ba\\x00\\xe4\\xb8\\xad'.startswith(b'\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80b\\xc3\\xa9ca\\x00a\\x00\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\xe4\\xb8\\xadac\\x00b\\xe4\\xb8\\xadcb\\xe4\\xb8\\xadbabb\\xc3\\xa9\\xc3\\xa9\\x00\\x00\\xed\\xa0\\x80ba\\x00\\xe4\\xb8\\xad'.rindex(b'\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('abc中b中éa中c中c\\ud800éaé\\ud800ac\\ud800b\\ud800c\\ud800a'.rfind('\\ud800中c\\x00b', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00c\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00ba\\xc3\\xa9\\x00\\x00c\\xed\\xa0\\x80bbaa\\x00cacba\\xc3\\xa9c\\x00a\\x00\\xc3\\xa9\\xe4\\xb8\\xada\\x00\\xed\\xa0\\x80c\\xe4\\xb8\\xad'.endswith(b'c\\x00a\\x00\\xc3\\xa9\\xe4\\xb8\\xada\\x00\\xed\\xa0\\x80c\\xe4\\xb8\\xad', None))\nexcept Exception as error: print(type(error).__name__)\n",
              '''-1
False
0
6
-1
False
ValueError
3
False
0
45
2
False
ValueError
-1
True
''')

check_program("try: print(b'b\\x00c\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00ba\\xc3\\xa9\\x00\\x00c\\xed\\xa0\\x80bbaa\\x00cacba\\xc3\\xa9c\\x00a\\x00\\xc3\\xa9\\xe4\\xb8\\xada\\x00\\xed\\xa0\\x80c\\xe4\\xb8\\xad'.count(b'c\\x00a\\x00\\xc3\\xa9\\xe4\\xb8\\xada\\x00\\xed\\xa0\\x80c\\xe4\\xb8\\xad', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\x00é\\x00a\\x00\\x00\\ud800éa\\ud800caécbé\\ud800cééba'.index('ab', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadcb\\x00\\x00\\xe4\\xb8\\xad\\x00bba\\x00bc\\xc3\\xa9'.find(b'\\xe4\\xb8\\xadc\\xe4\\xb8\\xada', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aaba\\ud800\\x00中\\x00bc\\x00\\ud800éa\\x00\\x00aéa'.startswith('bc\\x00\\ud800éa\\x00\\x00aéa'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aaba\\ud800\\x00中\\x00bc\\x00\\ud800éa\\x00\\x00aéa'.rindex('bc\\x00\\ud800éa\\x00\\x00aéa'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xed\\xa0\\x80ca\\xc3\\xa9baa\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xed\\xa0\\x80bbb\\x00c\\xed\\xa0\\x80\\x00\\x00c\\xc3\\xa9bba\\xed\\xa0\\x80\\x00a\\xc3\\xa9b\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80'.rfind(b'\\x00\\xed\\xa0\\x80\\x00c\\xc3\\xa9c', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aa\\ud800é\\x00baé\\x00c中中é\\x00acé\\x00\\x00é'.endswith('ca', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aa\\ud800é\\x00baé\\x00c中中é\\x00acé\\x00\\x00é'.count('ca', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00c\\x00cc\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9\\x00'.index(b'cc\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9\\x00', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中é中\\x00a中'.find('中中b\\ud800b\\ud800b', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a'.startswith(b'\\xc3\\xa9b\\xed\\xa0\\x80\\x00\\xc3\\xa9', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a'.rindex(b'\\xc3\\xa9b\\xed\\xa0\\x80\\x00\\xc3\\xa9', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('béab\\ud800\\ud800中\\x00c\\x00中b'.rfind('中b', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xed\\xa0\\x80c\\xe4\\xb8\\xada\\x00\\xe4\\xb8\\xadc\\x00\\x00ba\\xed\\xa0\\x80ba\\xed\\xa0\\x80aaa\\xc3\\xa9\\xc3\\xa9c\\xe4\\xb8\\xadaa\\xe4\\xb8\\xad\\x00a\\xc3\\xa9\\xe4\\xb8\\xad\\x00'.endswith(b'\\xc3\\xa9\\xed\\xa0\\x80c\\x00c', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xed\\xa0\\x80c\\xe4\\xb8\\xada\\x00\\xe4\\xb8\\xadc\\x00\\x00ba\\xed\\xa0\\x80ba\\xed\\xa0\\x80aaa\\xc3\\xa9\\xc3\\xa9c\\xe4\\xb8\\xadaa\\xe4\\xb8\\xad\\x00a\\xc3\\xa9\\xe4\\xb8\\xad\\x00'.count(b'\\xc3\\xa9\\xed\\xa0\\x80c\\x00c', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bé\\ud800é中\\x00\\ud800\\ud800a\\ud800\\ud800\\x00bé中b中\\ud800\\ud800c\\ud800中\\ud800'.index(''))\nexcept Exception as error: print(type(error).__name__)\n",
              '''1
ValueError
-1
False
8
-1
False
0
ValueError
-1
False
ValueError
-1
False
0
0
''')

check_program("try: print(b'\\xc3\\xa9\\xe4\\xb8\\xadbc\\xe4\\xb8\\xadcc\\x00\\xed\\xa0\\x80'.find(b'bc\\xe4\\xb8\\xadcc\\x00\\xed\\xa0\\x80', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('abb中é\\x00\\x00céé\\x00c中中中bac中'.endswith('a\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80cab\\xed\\xa0\\x80b\\xed\\xa0\\x80bcc\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80'.startswith(b'b', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80cab\\xed\\xa0\\x80b\\xed\\xa0\\x80bcc\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80'.count(b'b', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('éa\\x00中ca\\x00aé中c中acbab中aéaé\\x00é\\x00'.rindex('\\x00é\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xadbc\\xc3\\xa9\\x00ca\\xed\\xa0\\x80b\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80b'.index(b'\\xc3\\xa9\\xe4\\xb8\\xad', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800éc\\x00中中bccbbb中acbéé\\ud800bcb中b\\ud800'.rfind('c', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xc3\\xa9\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\x00\\xed\\xa0\\x80aa\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\x00caac\\xe4\\xb8\\xad\\xc3\\xa9\\x00'.find(b'\\x00caac\\xe4\\xb8\\xad\\xc3\\xa9\\x00', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('éa\\ud800中\\x00\\ud800\\ud800中'.endswith('', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80cb\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00b\\xc3\\xa9\\xed\\xa0\\x80\\x00\\x00aaa\\xc3\\xa9c\\xc3\\xa9bc\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xadb\\xc3\\xa9c\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xc3\\xa9a\\xed\\xa0\\x80\\xc3\\xa9ca\\x00\\x00'.startswith(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80cb\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00b\\xc3\\xa9\\xed\\xa0\\x80\\x00\\x00aaa\\xc3\\xa9c\\xc3\\xa9bc\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xadb\\xc3\\xa9c\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xc3\\xa9a\\xed\\xa0\\x80\\xc3\\xa9ca\\x00\\x00'.count(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c'.rindex('', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xc3\\xa9a\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xadc\\xe4\\xb8\\xadcbbaa\\xe4\\xb8\\xadac\\x00\\x00ab\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80a\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80b\\xe4\\xb8\\xadbbc\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80\\x00c'.index(b'\\xed\\xa0\\x80\\xc3\\xa9b\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80a', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bcé\\ud800c\\ud800c中ba\\ud800ba中b\\ud800bb\\x00中\\ud800中b'.rfind('é', -3, -1))\nexcept Exception as error: print(type(error).__name__)\n",
              '''5
False
False
0
ValueError
ValueError
-1
38
True
False
0
0
ValueError
-1
''')

check_program("try: print('bcé\\ud800c\\ud800c中ba\\ud800ba中b\\ud800bb\\x00中\\ud800中b'.rindex('é', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00b\\xc3\\xa9b\\xed\\xa0\\x80a\\xe4\\xb8\\xadcc\\xe4\\xb8\\xadc\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\xe4\\xb8\\xad\\xed\\xa0\\x80ca\\x00bccbccaa\\xc3\\xa9\\x00\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80'.index(b'\\xe4\\xb8\\xadc\\xe4\\xb8\\xad\\xed\\xa0\\x80ca\\x00bccbccaa\\xc3\\xa9\\x00\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('caccé\\ud800a中ébb\\ud800\\x00éccab\\x00'.rfind('\\ud800\\ud800中bac', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xe4\\xb8\\xadb\\xc3\\xa9acbac\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80ba'.find(b'\\xe4\\xb8\\xada\\xe4\\xb8\\xad', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00中c\\ud800bc\\ud800a中中écbc\\x00'.endswith('\\x00', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xe4\\xb8\\xad\\xc3\\xa9bc\\x00caa\\xed\\xa0\\x80a\\xc3\\xa9\\x00abc\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9c\\xc3\\xa9b\\xc3\\xa9'.startswith(b'\\x00\\x00', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xe4\\xb8\\xad\\xc3\\xa9bc\\x00caa\\xed\\xa0\\x80a\\xc3\\xa9\\x00abc\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9c\\xc3\\xa9b\\xc3\\xa9'.count(b'\\x00\\x00', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é中cbcb\\x00c\\x00béb中\\x00a中c\\ud800aa中中'.rindex('b\\ud800', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'bc\\xe4\\xb8\\xada\\x00aa\\xed\\xa0\\x80cc\\x00\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xe4\\xb8\\xadababa'.index(b'', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('acb\\x00\\ud800c\\ud800b\\ud800中\\ud800écb中\\x00\\ud800bc\\ud800b\\x00'.rfind('', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9bcc'.find(b'\\xe4\\xb8\\xad\\x00baaa', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é中\\x00cabc\\ud800\\ud800\\ud800cb\\ud800\\ud800cabb\\ud800\\ud800cca中é中\\x00cb'.endswith('é中\\x00cabc\\ud800\\ud800\\ud800cb\\ud800\\ud800cabb\\ud800\\ud800cca中é中\\x00cb', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\x00b\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xada\\x00\\xc3\\xa9ac\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xadbb\\xe4\\xb8\\xad\\xed\\xa0\\x80c\\x00baab\\x00cb\\xe4\\xb8\\xad\\xc3\\xa9c\\xc3\\xa9'.startswith(b'\\xc3\\xa9b\\xc3\\xa9', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\x00b\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xada\\x00\\xc3\\xa9ac\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xadbb\\xe4\\xb8\\xad\\xed\\xa0\\x80c\\x00baab\\x00cb\\xe4\\xb8\\xad\\xc3\\xa9c\\xc3\\xa9'.count(b'\\xc3\\xa9b\\xc3\\xa9', 0))\nexcept Exception as error: print(type(error).__name__)\n",
              '''ValueError
27
-1
-1
False
False
0
ValueError
1
-1
-1
False
False
0
''')

check_program("try: print('aé\\x00acé\\x00é\\x00\\ud800bbc\\ud800\\ud800baa\\ud800b\\ud800c\\ud800ééabaaba'.endswith('\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xadb\\x00ccbbbbcbbb\\xc3\\xa9\\xe4\\xb8\\xadb\\xed\\xa0\\x80cca\\xe4\\xb8\\xada\\xe4\\xb8\\xad\\xc3\\xa9a'.startswith(b'cbbbbcbbb\\xc3\\xa9\\xe4\\xb8\\xadb\\xed\\xa0\\x80cca\\xe4\\xb8\\xada\\xe4\\xb8\\xad\\xc3\\xa9a'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xadb\\x00ccbbbbcbbb\\xc3\\xa9\\xe4\\xb8\\xadb\\xed\\xa0\\x80cca\\xe4\\xb8\\xada\\xe4\\xb8\\xad\\xc3\\xa9a'.count(b'cbbbbcbbb\\xc3\\xa9\\xe4\\xb8\\xadb\\xed\\xa0\\x80cca\\xe4\\xb8\\xada\\xe4\\xb8\\xad\\xc3\\xa9a'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aéb\\ud800c中ébcbbb\\x00\\x00cé中c中\\x00\\ud800'.rindex('\\ud800éb\\ud800', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9'.index(b'', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00c\\ud800\\ud800ca中b\\x00c\\ud800c\\x00\\x00éc\\ud800ab\\x00'.rfind('\\ud800\\ud800ca中b\\x00c\\ud800c\\x00\\x00éc\\ud800ab\\x00', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\x00cbc\\xc3\\xa9a\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xe4\\xb8\\xadc\\xc3\\xa9\\xc3\\xa9ab\\xe4\\xb8\\xada\\xed\\xa0\\x80cb\\xed\\xa0\\x80\\xe4\\xb8\\xadaaab\\xe4\\xb8\\xad\\x00'.find(b'a\\xc3\\xa9\\xed\\xa0\\x80a\\xc3\\xa9\\xc3\\xa9', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('éa中\\ud800c中cbac中a中baéc\\x00'.endswith('aéacéc', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xc3\\xa9b\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xadb\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9b\\xe4\\xb8\\xadc\\xe4\\xb8\\xadb\\xc3\\xa9b\\x00'.startswith(b'\\xc3\\xa9b\\xe4\\xb8\\xadc\\xe4\\xb8\\xadb\\xc3\\xa9b\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xc3\\xa9b\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xadb\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9b\\xe4\\xb8\\xadc\\xe4\\xb8\\xadb\\xc3\\xa9b\\x00'.count(b'\\xc3\\xa9b\\xe4\\xb8\\xadc\\xe4\\xb8\\xadb\\xc3\\xa9b\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é中\\ud800\\ud800é\\ud800c\\x00aéé\\ud800\\ud800cé\\x00ab'.rindex('abcéa', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9a\\xc3\\xa9\\x00a\\xe4\\xb8\\xad\\x00c\\xed\\xa0\\x80\\xc3\\xa9a\\xc3\\xa9bc\\xc3\\xa9c\\x00\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9cbb'.index(b'cb\\xed\\xa0\\x80', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00\\ud800\\ud800中\\x00éaé\\x00\\x00'.rfind('é\\x00\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xed\\xa0\\x80\\xc3\\xa9c\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\xe4\\xb8\\xadb\\xe4\\xb8\\xadccba\\xe4\\xb8\\xad\\x00\\x00cc\\xe4\\xb8\\xad\\xc3\\xa9\\x00\\xed\\xa0\\x80\\xc3\\xa9\\x00c'.find(b'a', -3, -1))\nexcept Exception as error: print(type(error).__name__)\n",
              '''False
False
1
ValueError
1
2
-1
False
False
1
ValueError
ValueError
7
-1
''')

check_program("try: print(b'c\\xed\\xa0\\x80\\xc3\\xa9c\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\xe4\\xb8\\xadb\\xe4\\xb8\\xadccba\\xe4\\xb8\\xad\\x00\\x00cc\\xe4\\xb8\\xad\\xc3\\xa9\\x00\\xed\\xa0\\x80\\xc3\\xa9\\x00c'.index(b'a', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(''.find(''))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xadbac\\xc3\\xa9c\\xc3\\xa9c\\x00b\\x00cba\\x00c\\x00caacba'.startswith(b'cba', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xadbac\\xc3\\xa9c\\xc3\\xa9c\\x00b\\x00cba\\x00c\\x00caacba'.rindex(b'cba', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('éb\\x00中\\ud800cé\\ud800é\\x00\\ud800\\ud800\\x00aécccaaca\\x00'.rfind('béé', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xed\\xa0\\x80\\xed\\xa0\\x80accac\\xc3\\xa9\\x00b\\xe4\\xb8\\xada\\xc3\\xa9b'.endswith(b'\\xc3\\xa9bba', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xed\\xa0\\x80\\xed\\xa0\\x80accac\\xc3\\xa9\\x00b\\xe4\\xb8\\xada\\xc3\\xa9b'.count(b'\\xc3\\xa9bba', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00a中\\x00a\\x00a\\ud800\\x00éé\\x00éé\\ud800中bca\\x00a'.index('éé\\ud800中bca\\x00a', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ccab\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xadab\\xc3\\xa9cb\\x00\\xed\\xa0\\x80'.find(b'', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bacba'.startswith('c\\x00béb', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bacba'.rindex('c\\x00béb', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xada\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xadc'.rfind(b'\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xadc', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a\\ud800\\ud800\\ud800b中\\x00c\\x00中\\ud800abééé中c中\\ud800c\\x00bébab\\ud800ac\\ud800c中\\ud800\\x00a'.endswith('\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a\\ud800\\ud800\\ud800b中\\x00c\\x00中\\ud800abééé中c中\\ud800c\\x00bébab\\ud800ac\\ud800c中\\ud800\\x00a'.count('\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xc3\\xa9b\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80c\\xc3\\xa9\\xe4\\xb8\\xada\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9a\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9a\\x00\\x00cbc\\x00\\x00bc\\xc3\\xa9\\xc3\\xa9ac\\xc3\\xa9'.index(b'\\x00\\xc3\\xa9a', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00\\ud800baé\\x00aéb\\x00bécéc\\x00ba\\ud800\\x00\\x00中中ba\\ud800'.find('éb\\x00bécéc\\x00ba\\ud800\\x00\\x00中中ba\\ud800', 0))\nexcept Exception as error: print(type(error).__name__)\n",
              '''ValueError
0
False
31
-1
False
0
12
0
False
ValueError
4
False
4
ValueError
7
''')

check_program("try: print(b'c\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\x00\\xc3\\xa9\\xe4\\xb8\\xada\\xed\\xa0\\x80\\xed\\xa0\\x80'.startswith(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\x00\\xc3\\xa9\\xe4\\xb8\\xada\\xed\\xa0\\x80\\xed\\xa0\\x80'.count(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\x00céab\\x00bébac\\x00aabécé中a\\x00\\ud800中中bé\\x00\\x00bc\\ud800éacé中'.rindex('bcéé', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'cb\\xc3\\xa9b\\x00\\xc3\\xa9a\\x00b\\x00\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xadacbac\\x00\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80c'.index(b'\\x00\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xadacbac\\x00\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80c'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cé\\x00bb\\x00b\\x00ca\\ud800\\x00b\\ud800b中中ba\\ud800écbabac\\ud800中\\ud800a中b\\x00é'.rfind('éb', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\x00\\x00b\\xe4\\xb8\\xadcb\\xc3\\xa9a'.find(b'\\xed\\xa0\\x80c\\x00\\xed\\xa0\\x80cc', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800'.endswith('\\ud800', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9cc\\xed\\xa0\\x80\\x00c\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9c\\xed\\xa0\\x80\\x00\\xc3\\xa9c\\x00ba\\x00c'.startswith(b'\\x00b\\xc3\\xa9ab', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9cc\\xed\\xa0\\x80\\x00c\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9c\\xed\\xa0\\x80\\x00\\xc3\\xa9c\\x00ba\\x00c'.count(b'\\x00b\\xc3\\xa9ab', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a\\ud800ba\\ud800中\\x00'.rindex('bbcc', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xe4\\xb8\\xadb\\xe4\\xb8\\xadba\\xed\\xa0\\x80\\xe4\\xb8\\xadccc\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\x00ac\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00bcc'.index(b'c\\xe4\\xb8\\xadb\\xe4\\xb8\\xadba\\xed\\xa0\\x80\\xe4\\xb8\\xadccc\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\x00ac\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00bcc', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b'.rfind('a', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00b\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\xc3\\xa9\\x00c\\xe4\\xb8\\xadb\\xe4\\xb8\\xad\\xc3\\xa9'.find(b'\\xe4\\xb8\\xad', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a中\\ud800b\\x00中中é\\x00ééa中é\\x00\\x00\\x00\\x00ba\\ud800éa中中aac'.endswith('a中中aac', 10000))\nexcept Exception as error: print(type(error).__name__)\n",
              '''False
0
ValueError
11
-1
-1
True
False
0
ValueError
ValueError
-1
7
False
''')

check_program("try: print('a中\\ud800b\\x00中中é\\x00ééa中é\\x00\\x00\\x00\\x00ba\\ud800éa中中aac'.rfind('a中中aac', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ca\\xc3\\xa9ac\\xed\\xa0\\x80a\\xed\\xa0\\x80c\\xe4\\xb8\\xadaba\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80acc\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xe4\\xb8\\xadaa\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9aa\\x00ba\\x00'.endswith(b'c\\xe4\\xb8\\xada\\xed\\xa0\\x80\\x00a\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ca\\xc3\\xa9ac\\xed\\xa0\\x80a\\xed\\xa0\\x80c\\xe4\\xb8\\xadaba\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80acc\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xe4\\xb8\\xadaa\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9aa\\x00ba\\x00'.count(b'c\\xe4\\xb8\\xada\\xed\\xa0\\x80\\x00a\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cé中中é\\ud800éb中\\ud800中\\ud800a中é中ébc中\\ud800aaéc\\x00中\\ud800\\x00'.index('\\x00c\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b''.find(b'', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('éé中\\ud800a\\x00ca中b\\x00é\\ud800\\ud800\\ud800\\x00c中b\\x00\\x00'.startswith('\\ud800é', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('éé中\\ud800a\\x00ca中b\\x00é\\ud800\\ud800\\ud800\\x00c中b\\x00\\x00'.rindex('\\ud800é', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9c\\xc3\\xa9a\\xc3\\xa9bb\\xe4\\xb8\\xadb\\xe4\\xb8\\xad\\xe4\\xb8\\xadb\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9b\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80'.rfind(b'', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\x00\\x00'.endswith('\\x00\\x00', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\x00\\x00'.count('\\x00\\x00', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xed\\xa0\\x80ca\\xed\\xa0\\x80c\\x00\\x00\\x00\\xed\\xa0\\x80\\x00b\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80\\x00a\\xc3\\xa9ba\\xe4\\xb8\\xad'.index(b'b\\x00\\x00\\x00', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('éa\\x00é\\ud800\\x00b中中c\\ud800bc中中éé\\ud800中a中\\ud800\\x00a\\x00\\ud800a中c中abb\\x00bé\\ud800'.find('\\ud800é\\x00é', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00bc\\x00\\xc3\\xa9'.startswith(b'\\x00bc\\x00\\xc3\\xa9', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00bc\\x00\\xc3\\xa9'.rindex(b'\\x00bc\\x00\\xc3\\xa9', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中\\ud800b中baa中c中c中b\\ud800\\x00\\x00aécaéaa中éabcé\\ud800c\\ud800béc\\x00é'.rfind('\\ud800é\\ud800\\x00ab中', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadccb\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9bccc\\xe4\\xb8\\xadb\\xe4\\xb8\\xadabc\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadab\\xed\\xa0\\x80b\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80c\\x00\\xc3\\xa9\\xed\\xa0\\x80a'.endswith(b'\\xed\\xa0\\x80', -3, -1))\nexcept Exception as error: print(type(error).__name__)\n",
              '''-1
False
0
ValueError
-1
False
ValueError
46
False
0
ValueError
-1
False
ValueError
-1
False
''')
