# spec: PLS-315 23.1
# description: Programs on string search methods, each with the output CPython 3.15 gives.
from harness import *

check_program("try: print('ébbé中ca中中aaba\\ud800\\ud800'.rfind('bé中ca中中aaba\\ud800\\ud800', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9'.endswith(b'\\xc3\\xa9\\xed\\xa0\\x80c\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9'.count(b'\\xc3\\xa9\\xed\\xa0\\x80c\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cb中cbc\\ud800a\\x00ab\\ud800c\\x00\\ud800ccc\\ud800\\ud800中中'.index('b', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9bcc\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80b\\xed\\xa0\\x80\\x00\\x00b\\xed\\xa0\\x80acc'.find(b'acc', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bc中\\ud800céa\\ud800ébbbb'.startswith('cbb\\ud800', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bc中\\ud800céa\\ud800ébbbb'.rindex('cbb\\ud800', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\x00c\\x00\\x00\\xe4\\xb8\\xad'.rfind(b'\\xe4\\xb8\\xadab\\x00b', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a\\ud800\\x00c\\ud800b\\ud800\\x00c中bc中éa\\x00\\ud800\\ud800中\\x00é中中bééb\\ud800\\x00a中éa\\ud800\\x00éb\\x00'.endswith('b\\ud800\\x00a中éa\\ud800\\x00éb\\x00', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a\\ud800\\x00c\\ud800b\\ud800\\x00c中bc中éa\\x00\\ud800\\ud800中\\x00é中中bééb\\ud800\\x00a中éa\\ud800\\x00éb\\x00'.count('b\\ud800\\x00a中éa\\ud800\\x00éb\\x00', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'cb\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\x00'.index(b'\\xc3\\xa9\\x00\\xed\\xa0\\x80a', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('éé\\x00中\\ud800中é\\ud800ac中ébéa中'.find('中', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadb\\xe4\\xb8\\xadb\\xe4\\xb8\\xad\\xc3\\xa9\\x00\\xe4\\xb8\\xad\\x00bcbbbbcb\\xe4\\xb8\\xadc\\xed\\xa0\\x80b\\x00bbab\\x00b\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\x00'.startswith(b'\\xe4\\xb8\\xadc\\xed\\xa0\\x80b\\x00bbab\\x00b\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\x00', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadb\\xe4\\xb8\\xadb\\xe4\\xb8\\xad\\xc3\\xa9\\x00\\xe4\\xb8\\xad\\x00bcbbbbcb\\xe4\\xb8\\xadc\\xed\\xa0\\x80b\\x00bbab\\x00b\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\x00'.rindex(b'\\xe4\\xb8\\xadc\\xed\\xa0\\x80b\\x00bbab\\x00b\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\x00', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b\\x00bc'.rfind('c', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9cac\\xed\\xa0\\x80b\\x00\\xc3\\xa9\\x00\\x00b\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80ac\\xed\\xa0\\x80b\\xed\\xa0\\x80a'.endswith(b'', -100, 100))\nexcept Exception as error: print(type(error).__name__)\n",
              '''2
False
0
1
-1
False
ValueError
-1
False
0
ValueError
3
False
26
3
True
''')

check_program("try: print(b'\\xc3\\xa9cac\\xed\\xa0\\x80b\\x00\\xc3\\xa9\\x00\\x00b\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80ac\\xed\\xa0\\x80b\\xed\\xa0\\x80a'.count(b'', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c\\ud800b\\ud800中aaaa\\ud800a中\\x00\\x00abcc\\ud800ébcé'.index('ébcé', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xc3\\xa9\\x00\\x00bc\\xc3\\xa9\\xed\\xa0\\x80'.find(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('abbé\\x00'.startswith('中\\x00\\x00bé\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('abbé\\x00'.rindex('中\\x00\\x00bé\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadab\\x00\\xc3\\xa9\\xc3\\xa9b\\x00\\xed\\xa0\\x80b\\x00'.rfind(b'\\xe4\\xb8\\xadab\\x00\\xc3\\xa9\\xc3\\xa9b\\x00\\xed\\xa0\\x80b\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aaé中é\\ud800é\\ud800b\\x00\\x00ba\\x00bc中cb'.endswith('é中\\x00ccc', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aaé中é\\ud800é\\ud800b\\x00\\x00ba\\x00bc中cb'.count('é中\\x00ccc', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00b\\x00c\\x00\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9bb'.index(b'\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80b', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a\\x00中éé\\ud800\\x00aab\\x00\\ud800aaccbcécb\\ud800中\\ud800中c'.find('é\\ud800\\x00aab\\x00\\ud800aaccbcécb\\ud800中\\ud800中c', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\x00a\\xe4\\xb8\\xad\\xed\\xa0\\x80ba\\xc3\\xa9\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadbaa\\xe4\\xb8\\xadb\\xc3\\xa9a\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80ab\\xc3\\xa9'.startswith(b'a', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\x00a\\xe4\\xb8\\xad\\xed\\xa0\\x80ba\\xc3\\xa9\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadbaa\\xe4\\xb8\\xadb\\xc3\\xa9a\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80ab\\xc3\\xa9'.rindex(b'a', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c\\x00béacb中a\\ud800\\x00中aa中中c'.rfind('', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xc3\\xa9ba\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xed\\xa0\\x80acbb\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00b'.endswith(b'ba\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xed\\xa0\\x80acbb\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00b'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xc3\\xa9ba\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xed\\xa0\\x80acbb\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00b'.count(b'ba\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xed\\xa0\\x80acbb\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00b'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800c\\x00é\\x00cb\\ud800\\x00b\\ud800\\x00\\x00bc中ca'.index('ab\\x00\\ud800', None))\nexcept Exception as error: print(type(error).__name__)\n",
              '''34
19
-1
False
ValueError
0
False
0
ValueError
4
False
39
17
True
1
ValueError
''')

check_program("try: print(b'a\\x00a\\xed\\xa0\\x80a'.find(b'\\xed\\xa0\\x80\\xed\\xa0\\x80', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800b中\\ud800中a\\ud800b\\ud800\\x00中é\\ud800a\\x00\\ud800b\\x00bé\\ud800\\ud800b\\x00\\x00a\\x00abébéécbéa\\ud800中'.endswith('中', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9a\\x00c\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\x00bb\\x00\\xed\\xa0\\x80\\xc3\\xa9aca\\x00\\x00caca\\xed\\xa0\\x80\\xe4\\xb8\\xada\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80'.startswith(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9a\\x00c\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\x00bb\\x00\\xed\\xa0\\x80\\xc3\\xa9aca\\x00\\x00caca\\xed\\xa0\\x80\\xe4\\xb8\\xada\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80'.count(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中a\\ud800éé中a中\\ud800bé\\ud800中b\\x00éa\\x00中c中a中c\\ud800\\ud800中é中éé中aéb'.rindex('中bbba中é', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'aac\\xc3\\xa9\\x00\\xed\\xa0\\x80\\xc3\\xa9ac\\xc3\\xa9\\x00bc\\xc3\\xa9\\x00\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80c\\xc3\\xa9ccb\\x00\\xc3\\xa9a\\xe4\\xb8\\xad\\xe4\\xb8\\xadba'.index(b'ba', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c中écééb\\x00中éé'.rfind('b中b\\x00a中', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xed\\xa0\\x80b'.find(b'\\xe4\\xb8\\xad'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800中\\ud800c\\ud800c\\ud800c中écb中bc中c中中aéc\\ud800\\ud800中éb\\x00b\\x00aba'.endswith('中écb中bc中c中中aéc\\ud800\\ud800中éb\\x00b\\x00aba', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xed\\xa0\\x80\\x00c\\x00\\xc3\\xa9ca\\x00cabba\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xadcbcba\\xed\\xa0\\x80\\x00\\x00\\xed\\xa0\\x80\\x00'.startswith(b'\\x00\\xe4\\xb8\\xadb\\xe4\\xb8\\xad\\xc3\\xa9c\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xed\\xa0\\x80\\x00c\\x00\\xc3\\xa9ca\\x00cabba\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xadcbcba\\xed\\xa0\\x80\\x00\\x00\\xed\\xa0\\x80\\x00'.count(b'\\x00\\xe4\\xb8\\xadb\\xe4\\xb8\\xad\\xc3\\xa9c\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00éca中\\ud800b\\x00ba\\x00中b中\\x00a\\ud800\\x00ba\\ud800aabé\\ud800'.rindex('c\\x00é\\ud800ébb'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xadb\\xe4\\xb8\\xad\\x00\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00c\\x00bb\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xad'.index(b'\\xed\\xa0\\x80\\x00c\\x00bb\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xad', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c'.rfind('éa\\ud800中c', 1, 1))\nexcept Exception as error: print(type(error).__name__)\n",
              '''-1
True
False
0
ValueError
48
-1
0
False
False
0
ValueError
28
-1
''')

check_program("try: print('c'.rindex('éa\\ud800中c', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80b\\xed\\xa0\\x80\\x00bc\\x00\\xed\\xa0\\x80\\x00b\\xed\\xa0\\x80\\xc3\\xa9a\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9ba'.rfind(b'cc\\xe4\\xb8\\xadc\\x00bb'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中中a中中bcbba\\ud800中'.endswith('中', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中中a中中bcbba\\ud800中'.count('中', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xc3\\xa9b\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\x00\\x00b\\xe4\\xb8\\xadb\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00a\\x00\\x00c\\x00'.index(b'a', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800c\\x00b\\ud800bccbba\\ud800\\x00\\ud800\\x00c\\ud800b'.find('c\\x00b', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\x00\\xe4\\xb8\\xadca'.startswith(b'\\xe4\\xb8\\xadca', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\x00\\xe4\\xb8\\xadca'.rindex(b'\\xe4\\xb8\\xadca', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bc\\ud800\\x00é中bébc\\x00a\\ud800中\\ud800中\\x00bb'.rfind('bb\\ud800中é', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'aa\\xed\\xa0\\x80\\x00\\x00c\\xed\\xa0\\x80b\\x00aaab\\x00c\\xc3\\xa9c\\xe4\\xb8\\xadac'.endswith(b'\\x00cca\\xed\\xa0\\x80', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'aa\\xed\\xa0\\x80\\x00\\x00c\\xed\\xa0\\x80b\\x00aaab\\x00c\\xc3\\xa9c\\xe4\\xb8\\xadac'.count(b'\\x00cca\\xed\\xa0\\x80', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aacé中中'.index('acé中中'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xc3\\xa9\\xed\\xa0\\x80b\\xc3\\xa9\\xe4\\xb8\\xadc\\xc3\\xa9\\x00\\xc3\\xa9\\xe4\\xb8\\xad'.find(b'b\\xc3\\xa9', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é中c'.startswith('béc中b\\x00é', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é中c'.rindex('béc中b\\x00é', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\x00\\x00\\xc3\\xa9abb\\x00\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9ac\\xc3\\xa9\\xc3\\xa9bca\\xe4\\xb8\\xadbc\\x00\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80cb\\xe4\\xb8\\xad\\x00a\\xed\\xa0\\x80'.rfind(b'\\x00\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80cb\\xe4\\xb8\\xad\\x00a\\xed\\xa0\\x80', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\n",
              '''ValueError
-1
True
5
28
1
False
ValueError
-1
False
0
1
0
False
ValueError
31
''')

check_program("try: print('\\ud800\\ud800é\\ud800c\\ud800bbc\\x00éaaa\\x00\\x00é'.endswith(''))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800\\ud800é\\ud800c\\ud800bbc\\x00éaaa\\x00\\x00é'.count(''))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xc3\\xa9\\xe4\\xb8\\xad\\x00'.index(b'', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800\\x00'.find('\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'aaa\\x00\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xada\\xe4\\xb8\\xad\\x00\\x00ba\\xc3\\xa9c\\xe4\\xb8\\xad\\xed\\xa0\\x80bc\\x00c'.startswith(b'b\\xe4\\xb8\\xad\\x00\\x00\\xe4\\xb8\\xad', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'aaa\\x00\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xada\\xe4\\xb8\\xad\\x00\\x00ba\\xc3\\xa9c\\xe4\\xb8\\xad\\xed\\xa0\\x80bc\\x00c'.rindex(b'b\\xe4\\xb8\\xad\\x00\\x00\\xe4\\xb8\\xad', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ba中\\ud800c\\ud800'.rfind('\\ud800éa中', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00a\\x00a\\x00\\xc3\\xa9\\xed\\xa0\\x80a\\xed\\xa0\\x80\\xc3\\xa9b\\xed\\xa0\\x80c\\xc3\\xa9\\xc3\\xa9ba\\xed\\xa0\\x80\\x00b\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80c\\xe4\\xb8\\xadc\\xe4\\xb8\\xadb'.endswith(b'', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00a\\x00a\\x00\\xc3\\xa9\\xed\\xa0\\x80a\\xed\\xa0\\x80\\xc3\\xa9b\\xed\\xa0\\x80c\\xc3\\xa9\\xc3\\xa9ba\\xed\\xa0\\x80\\x00b\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80c\\xe4\\xb8\\xadc\\xe4\\xb8\\xadb'.count(b'', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aba中b\\ud800bc\\x00é'.index('\\x00c\\x00\\ud800', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'abac\\xed\\xa0\\x80acb\\xed\\xa0\\x80b\\x00\\xe4\\xb8\\xad\\x00a\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00cb\\xc3\\xa9\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xad'.find(b'abc\\x00\\x00\\xed\\xa0\\x80', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bcéc中中é\\x00\\ud800中中\\x00bééaab\\x00éaa'.startswith('é\\x00\\ud800中中\\x00bééaab\\x00éaa'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bcéc中中é\\x00\\ud800中中\\x00bééaab\\x00éaa'.rindex('é\\x00\\ud800中中\\x00bééaab\\x00éaa'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'cb\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9b'.rfind(b'cb'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00é\\x00b\\ud800\\x00b\\ud800bccéb\\ud800'.endswith('\\x00é', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00é\\x00b\\ud800\\x00b\\ud800bccéb\\ud800'.count('\\x00é', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\n",
              '''True
18
0
1
False
ValueError
-1
True
54
ValueError
-1
False
6
0
False
1
''')

check_program("try: print(b'\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xc3\\xa9a\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\x00\\x00c\\x00\\xe4\\xb8\\xada\\x00\\x00\\xe4\\xb8\\xad\\x00abc\\xed\\xa0\\x80c\\x00b'.index(b'bc\\xed\\xa0\\x80c\\x00b', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00bb中ac中\\x00\\x00céé\\x00aa\\x00éb\\x00aé\\ud800中é中\\ud800aac'.find('中c中b\\ud800b中', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xed\\xa0\\x80c\\xc3\\xa9b\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\x00b\\xc3\\xa9ccab\\xe4\\xb8\\xad\\x00a\\x00\\x00\\xc3\\xa9b'.startswith(b'c\\xc3\\xa9\\xc3\\xa9\\x00cc', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xed\\xa0\\x80c\\xc3\\xa9b\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\x00b\\xc3\\xa9ccab\\xe4\\xb8\\xad\\x00a\\x00\\x00\\xc3\\xa9b'.rindex(b'c\\xc3\\xa9\\xc3\\xa9\\x00cc', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a\\ud800\\x00中中\\x00bc中c中c\\x00'.rfind('\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'bcca\\x00c\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadcca\\x00\\xc3\\xa9cbb\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xc3\\xa9cb\\xed\\xa0\\x80\\x00ab\\xe4\\xb8\\xad\\xe4\\xb8\\xadb'.endswith(b'', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'bcca\\x00c\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadcca\\x00\\xc3\\xa9cbb\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xc3\\xa9cb\\xed\\xa0\\x80\\x00ab\\xe4\\xb8\\xad\\xe4\\xb8\\xadb'.count(b'', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c\\ud800a\\x00a\\ud800céé\\x00aéc\\x00\\ud800béc\\x00\\ud800éé'.index('b\\x00\\ud800ac', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xed\\xa0\\x80a\\xe4\\xb8\\xadc\\xe4\\xb8\\xadb\\xed\\xa0\\x80bbc\\x00c\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9ba'.find(b'ba', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中acababé中éé\\ud800\\ud800\\ud800\\x00c\\ud800cé中c中中中中\\ud800中é'.startswith('', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中acababé中éé\\ud800\\ud800\\ud800\\x00c\\ud800cé中c中中中中\\ud800中é'.rindex('', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\x00c\\xc3\\xa9a\\x00\\xc3\\xa9b'.rfind(b'\\xed\\xa0\\x80a\\xc3\\xa9\\xe4\\xb8\\xad', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00a中é\\ud800\\ud800中\\x00\\ud800a\\ud800中'.endswith('\\ud800中', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00a中é\\ud800\\ud800中\\x00\\ud800a\\ud800中'.count('\\ud800中', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00\\xed\\xa0\\x80cc\\xed\\xa0\\x80b\\xe4\\xb8\\xadcbb\\xe4\\xb8\\xadcc\\xed\\xa0\\x80\\xc3\\xa9\\x00a\\xe4\\xb8\\xadbbb\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad'.index(b'a\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c中é中\\ud800中é\\x00c中éb\\ud800b\\ud800\\ud800\\x00a\\x00中é中\\x00中a中cébaa'.find('a\\x00cacé中', -100, 100))\nexcept Exception as error: print(type(error).__name__)\n",
              '''ValueError
-1
False
ValueError
12
True
47
ValueError
27
True
28
-1
True
2
ValueError
-1
''')

check_program("try: print(b'cb\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\x00a\\xe4\\xb8\\xad\\xc3\\xa9a\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80c\\xc3\\xa9c\\x00\\xc3\\xa9c\\xc3\\xa9a\\xe4\\xb8\\xad\\xc3\\xa9b\\x00\\xc3\\xa9ba\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xc3\\xa9\\xed\\xa0\\x80'.startswith(b'c\\xc3\\xa9\\xed\\xa0\\x80', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'cb\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\x00a\\xe4\\xb8\\xad\\xc3\\xa9a\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80c\\xc3\\xa9c\\x00\\xc3\\xa9c\\xc3\\xa9a\\xe4\\xb8\\xad\\xc3\\xa9b\\x00\\xc3\\xa9ba\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xc3\\xa9\\xed\\xa0\\x80'.count(b'c\\xc3\\xa9\\xed\\xa0\\x80', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00\\x00\\x00éacbéé\\ud800éc\\x00\\x00a\\x00c'.rindex('éab', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9cbc'.index(b'\\xed\\xa0\\x80\\xc3\\xa9bb\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aabb\\ud800中é中ab'.rfind('中ab'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xc3\\xa9caa\\xc3\\xa9ca\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xada\\xe4\\xb8\\xad\\x00c\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xadaaaaa\\xe4\\xb8\\xad\\xc3\\xa9a\\xed\\xa0\\x80b\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad'.find(b'a\\xed\\xa0\\x80\\xed\\xa0\\x80b\\xc3\\xa9\\xed\\xa0\\x80', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ébb中acb中\\ud800ébaa中aéééc\\ud800b\\ud800'.endswith('é\\ud800bc', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9b\\xc3\\xa9\\x00\\x00aa\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80ab\\x00bb\\xc3\\xa9ba\\xed\\xa0\\x80c\\xed\\xa0\\x80aa'.startswith(b'\\xc3\\xa9\\xc3\\xa9b\\xc3\\xa9\\x00\\x00aa\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80ab\\x00bb\\xc3\\xa9ba\\xed\\xa0\\x80c\\xed\\xa0\\x80aa', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9b\\xc3\\xa9\\x00\\x00aa\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80ab\\x00bb\\xc3\\xa9ba\\xed\\xa0\\x80c\\xed\\xa0\\x80aa'.count(b'\\xc3\\xa9\\xc3\\xa9b\\xc3\\xa9\\x00\\x00aa\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80ab\\x00bb\\xc3\\xa9ba\\xed\\xa0\\x80c\\xed\\xa0\\x80aa', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cbc\\x00aa\\x00bcbbb'.rindex('é\\x00\\x00', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ab\\xed\\xa0\\x80cac\\x00\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xadba\\xe4\\xb8\\xadc\\xed\\xa0\\x80abcb\\xc3\\xa9c'.index(b'\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9c\\xc3\\xa9ca', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b\\ud800aa中céabaa\\ud800a中'.rfind('', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\x00\\xc3\\xa9\\xe4\\xb8\\xadccba\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\xc3\\xa9'.find(b'b', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00é\\ud800a'.endswith('\\ud800b', -100, 100))\nexcept Exception as error: print(type(error).__name__)\n",
              '''False
0
ValueError
ValueError
7
-1
False
False
0
ValueError
ValueError
1
-1
False
''')

check_program("try: print('\\x00é\\ud800a'.rfind('\\ud800b', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xc3\\xa9cc\\xe4\\xb8\\xada'.find(b'c\\xe4\\xb8\\xada'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('écaaabba\\ud800\\x00'.endswith('\\x00é\\ud800caéa', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\xc3\\xa9b\\x00\\xc3\\xa9\\xe4\\xb8\\xadc\\x00cb\\x00\\xe4\\xb8\\xad\\x00ac\\xe4\\xb8\\xad\\xed\\xa0\\x80c\\xe4\\xb8\\xadaccb\\xe4\\xb8\\xadcc\\xe4\\xb8\\xadb\\xed\\xa0\\x80'.startswith(b'b\\xe4\\xb8\\xadc\\xed\\xa0\\x80', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\xc3\\xa9b\\x00\\xc3\\xa9\\xe4\\xb8\\xadc\\x00cb\\x00\\xe4\\xb8\\xad\\x00ac\\xe4\\xb8\\xad\\xed\\xa0\\x80c\\xe4\\xb8\\xadaccb\\xe4\\xb8\\xadcc\\xe4\\xb8\\xadb\\xed\\xa0\\x80'.count(b'b\\xe4\\xb8\\xadc\\xed\\xa0\\x80', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800aa\\ud800aacc\\ud800é\\ud800\\x00cééa中cb\\ud800abé中'.rindex('', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xc3\\xa9'.index(b'c', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aa中a\\ud800éébéc'.rfind('\\x00\\x00', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xed\\xa0\\x80acc\\xed\\xa0\\x80\\xe4\\xb8\\xadb\\xc3\\xa9a\\xe4\\xb8\\xad\\xed\\xa0\\x80cca\\x00\\xc3\\xa9\\xed\\xa0\\x80\\x00'.find(b'\\xe4\\xb8\\xad\\xed\\xa0\\x80cca\\x00\\xc3\\xa9\\xed\\xa0\\x80\\x00', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00bé中\\x00\\x00\\x00b\\ud800é\\x00cé\\x00baa中中bcb中éb'.endswith('\\x00cé\\ud800a', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadabacb\\xe4\\xb8\\xad\\xe4\\xb8\\xadcc\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9a\\xed\\xa0\\x80c\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\xed\\xa0\\x80aca\\xe4\\xb8\\xadbabcc\\xed\\xa0\\x80'.startswith(b'\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xe4\\xb8\\xad', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadabacb\\xe4\\xb8\\xad\\xe4\\xb8\\xadcc\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9a\\xed\\xa0\\x80c\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\xed\\xa0\\x80aca\\xe4\\xb8\\xadbabcc\\xed\\xa0\\x80'.count(b'\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xe4\\xb8\\xad', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('acébc\\x00c\\x00céaébb中\\x00中中é中acé\\x00c\\ud800中\\ud800中c\\ud800\\ud800é'.rindex('\\x00中中é中acé\\x00c\\ud800中\\ud800中c\\ud800\\ud800é'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xc3\\xa9\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\xe4\\xb8\\xadaab\\x00c\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00b\\xe4\\xb8\\xada\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\x00\\xe4\\xb8\\xadcaab\\x00bc\\xed\\xa0\\x80\\xed\\xa0\\x80'.index(b'\\xe4\\xb8\\xad\\xc3\\xa9\\x00\\xc3\\xa9\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\n",
              '''-1
4
False
False
0
ValueError
0
-1
19
False
False
0
15
ValueError
''')

check_program("try: print(b'\\xe4\\xb8\\xad\\xc3\\xa9\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\xe4\\xb8\\xadaab\\x00c\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00b\\xe4\\xb8\\xada\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\x00\\xe4\\xb8\\xadcaab\\x00bc\\xed\\xa0\\x80\\xed\\xa0\\x80'.count(b'\\xe4\\xb8\\xad\\xc3\\xa9\\x00\\xc3\\xa9\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bcéa中écc\\x00b\\x00b\\ud800\\x00'.index('\\x00', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'bacb\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\xc3\\xa9ca\\xed\\xa0\\x80\\x00babb\\xc3\\xa9b\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadcaca\\x00'.find(b'\\x00babb\\xc3\\xa9b\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadcaca\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800中c\\ud800éa中c\\x00éa\\ud800\\ud800中\\ud800é\\ud800'.startswith('\\x00bb\\x00cc', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800中c\\ud800éa中c\\x00éa\\ud800\\ud800中\\ud800é\\ud800'.rindex('\\x00bb\\x00cc', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xed\\xa0\\x80\\x00c\\xc3\\xa9c\\x00\\xe4\\xb8\\xadc\\xc3\\xa9babbaa\\xc3\\xa9\\xe4\\xb8\\xadcca\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\xc3\\xa9\\xc3\\xa9b\\x00cb'.rfind(b'\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cb\\ud800c\\x00\\ud800中ca\\ud800c\\ud800\\x00bb\\x00中cébé中'.endswith('c\\ud800\\x00bb\\x00中cébé中', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cb\\ud800c\\x00\\ud800中ca\\ud800c\\ud800\\x00bb\\x00中cébé中'.count('c\\ud800\\x00bb\\x00中cébé中', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'cb\\xed\\xa0\\x80\\x00bb\\xed\\xa0\\x80\\xe4\\xb8\\xadb\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9\\x00'.index(b'bb\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中bacé\\ud800é中\\ud800éa中c\\ud800中'.find('a\\x00', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9cb\\xe4\\xb8\\xad\\x00\\x00\\xc3\\xa9\\xed\\xa0\\x80a\\x00\\xe4\\xb8\\xad'.startswith(b'\\xe4\\xb8\\xad\\x00\\x00\\xc3\\xa9\\xed\\xa0\\x80a\\x00\\xe4\\xb8\\xad'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9cb\\xe4\\xb8\\xad\\x00\\x00\\xc3\\xa9\\xed\\xa0\\x80a\\x00\\xe4\\xb8\\xad'.rindex(b'\\xe4\\xb8\\xad\\x00\\x00\\xc3\\xa9\\xed\\xa0\\x80a\\x00\\xe4\\xb8\\xad'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中'.rfind('é\\ud800'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadcc\\xed\\xa0\\x80\\xed\\xa0\\x80bbc\\xe4\\xb8\\xadc'.endswith(b'', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadcc\\xed\\xa0\\x80\\xed\\xa0\\x80bbc\\xe4\\xb8\\xadc'.count(b'', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b中'.index('', 1, 1))\nexcept Exception as error: print(type(error).__name__)\n",
              '''0
8
21
False
ValueError
-1
False
0
ValueError
-1
False
10
-1
True
24
1
''')

check_program("try: print(b'\\x00\\xe4\\xb8\\xadbca\\x00\\xed\\xa0\\x80\\xc3\\xa9c\\x00\\xe4\\xb8\\xadc\\xc3\\xa9ab\\xc3\\xa9c\\x00\\xe4\\xb8\\xadb\\xe4\\xb8\\xadc\\x00\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xadc\\xc3\\xa9b'.find(b'', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cc中é中\\x00\\ud800b\\ud800é\\ud800a中bbbbb\\ud800bb\\ud800bb'.endswith('c中', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xed\\xa0\\x80\\xed\\xa0\\x80c\\xed\\xa0\\x80c\\x00\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80\\x00\\xc3\\xa9\\x00\\xc3\\xa9c\\x00\\x00'.startswith(b'', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xed\\xa0\\x80\\xed\\xa0\\x80c\\xed\\xa0\\x80c\\x00\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80\\x00\\xc3\\xa9\\x00\\xc3\\xa9c\\x00\\x00'.count(b'', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b\\ud800aa中'.rindex('', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00abb\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80c\\xe4\\xb8\\xadb\\xe4\\xb8\\xadcc\\x00\\x00b\\xed\\xa0\\x80\\xe4\\xb8\\xadb\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9\\x00b\\xe4\\xb8\\xad\\xc3\\xa9b\\xed\\xa0\\x80\\xed\\xa0\\x80'.index(b'\\xe4\\xb8\\xadc\\xed\\xa0\\x80', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é中ccc中c\\x00c中\\ud800c中中a\\x00aa中bcéa中\\ud800bbéa\\x00'.rfind('éa\\x00', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00\\xe4\\xb8\\xadca\\xe4\\xb8\\xada\\xc3\\xa9bcc\\xe4\\xb8\\xada\\x00\\x00\\x00bb\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xadba\\x00\\xe4\\xb8\\xadb\\x00\\xc3\\xa9\\xed\\xa0\\x80'.find(b'b', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800\\x00\\x00a'.endswith('\\x00中éé中中', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadb\\xe4\\xb8\\xadac\\xc3\\xa9\\xe4\\xb8\\xadc\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xadbabb\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xadbc\\xe4\\xb8\\xadbb\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00c\\x00'.startswith(b'\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xadbabb\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xadbc\\xe4\\xb8\\xadbb\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00c\\x00', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadb\\xe4\\xb8\\xadac\\xc3\\xa9\\xe4\\xb8\\xadc\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xadbabb\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xadbc\\xe4\\xb8\\xadbb\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00c\\x00'.count(b'\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xadbabb\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xadbc\\xe4\\xb8\\xadbb\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00c\\x00', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('éaacac\\x00aé中\\x00ébab\\x00cé中\\ud800\\x00\\x00éc中中\\x00\\x00\\ud800aé\\x00\\x00'.rindex('', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xad'.index(b'b\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b\\ud800éccéa\\x00\\x00écb中中cc中b\\ud800éaca\\x00\\x00中éb中éb\\ud800ab中a'.rfind('éb\\ud800ab中a', 1, 1))\nexcept Exception as error: print(type(error).__name__)\n",
              '''0
False
True
3
5
ValueError
27
-1
False
False
1
33
ValueError
-1
''')

check_program("try: print('b\\ud800éccéa\\x00\\x00écb中中cc中b\\ud800éaca\\x00\\x00中éb中éb\\ud800ab中a'.rindex('éb\\ud800ab中a', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9b\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80bb\\xc3\\xa9c\\xc3\\xa9c'.rfind(b'c\\xe4\\xb8\\xadcb\\xe4\\xb8\\xad\\xed\\xa0\\x80', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\ud800中中\\x00\\x00中中\\x00éba\\ud800a中c\\ud800\\x00a'.endswith('a\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\ud800中中\\x00\\x00中中\\x00éba\\ud800a中c\\ud800\\x00a'.count('a\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00a\\xc3\\xa9b\\xc3\\xa9ab\\xc3\\xa9'.index(b'\\x00a\\xc3\\xa9b\\xc3\\xa9ab\\xc3\\xa9', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('éb\\x00中中céa\\ud800aa\\x00a\\x00aé'.find('é中ca\\x00a', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xe4\\xb8\\xadb\\x00\\xed\\xa0\\x80cbc\\x00b\\xed\\xa0\\x80ac'.startswith(b'b\\xe4\\xb8\\xadbc\\xc3\\xa9a', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xe4\\xb8\\xadb\\x00\\xed\\xa0\\x80cbc\\x00b\\xed\\xa0\\x80ac'.rindex(b'b\\xe4\\xb8\\xadbc\\xc3\\xa9a', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(''.rfind('', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xe4\\xb8\\xadb\\xe4\\xb8\\xada\\xc3\\xa9c\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80bc\\xe4\\xb8\\xad\\xed\\xa0\\x80ab\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9baa\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\xed\\xa0\\x80a\\xe4\\xb8\\xadac\\xed\\xa0\\x80b'.endswith(b'c\\x00', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xe4\\xb8\\xadb\\xe4\\xb8\\xada\\xc3\\xa9c\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80bc\\xe4\\xb8\\xad\\xed\\xa0\\x80ab\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9baa\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\xed\\xa0\\x80a\\xe4\\xb8\\xadac\\xed\\xa0\\x80b'.count(b'c\\x00', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('caé\\ud800中\\ud800c\\x00éba中b\\ud800中cccb'.index('', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00b'.find(b'', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00\\x00é\\ud800ba中中中c中ééé\\ud800cacé\\ud800a中éc\\x00caac中c中aé中'.startswith('ccba', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00\\x00é\\ud800ba中中中c中ééé\\ud800cacé\\ud800a中éc\\x00caac中c中aé中'.rindex('ccba', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80b\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9bb\\x00\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xc3\\xa9aa\\xe4\\xb8\\xad\\xc3\\xa9c\\xed\\xa0\\x80\\xed\\xa0\\x80'.rfind(b'c\\x00', None))\nexcept Exception as error: print(type(error).__name__)\n",
              '''ValueError
-1
False
0
ValueError
-1
False
ValueError
0
False
0
0
0
False
ValueError
-1
''')

check_program("try: print('é\\x00'.endswith('', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\x00'.count('', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80b\\xe4\\xb8\\xadaccbb\\x00\\xe4\\xb8\\xada\\x00\\xe4\\xb8\\xadc'.index(b'c\\x00\\x00bc\\xc3\\xa9\\xe4\\xb8\\xad', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a\\x00中c\\ud800'.find('\\x00\\ud800aé\\ud800', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00c\\xc3\\xa9abb\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80cac\\xc3\\xa9\\xc3\\xa9ca\\xe4\\xb8\\xadaac\\xc3\\xa9c\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xadcbb\\xc3\\xa9'.startswith(b'\\xc3\\xa9ca\\xe4\\xb8\\xadaac\\xc3\\xa9c\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xadcbb\\xc3\\xa9', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00c\\xc3\\xa9abb\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80cac\\xc3\\xa9\\xc3\\xa9ca\\xe4\\xb8\\xadaac\\xc3\\xa9c\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xadcbb\\xc3\\xa9'.rindex(b'\\xc3\\xa9ca\\xe4\\xb8\\xadaac\\xc3\\xa9c\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xadcbb\\xc3\\xa9', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00c'.rfind('éc', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xc3\\xa9\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xadbc'.endswith(b'\\x00', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xc3\\xa9\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xadbc'.count(b'\\x00', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b\\x00'.index('b\\x00', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ccb\\x00a\\x00\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00a\\xc3\\xa9caabb'.find(b'\\xc3\\xa9\\xe4\\xb8\\xad\\x00cab'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cb中\\x00éé中éb\\x00a\\ud800\\ud800中abcabc中é\\x00中é中\\x00中b中a'.startswith('b\\x00中\\ud800c中', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cb中\\x00éé中éb\\x00a\\ud800\\ud800中abcabc中é\\x00中é中\\x00中b中a'.rindex('b\\x00中\\ud800c中', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00cb\\xed\\xa0\\x80bc\\x00\\xe4\\xb8\\xad\\xc3\\xa9b\\x00'.rfind(b'b\\xed\\xa0\\x80bc\\x00\\xe4\\xb8\\xad\\xc3\\xa9b\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800中é中ébébaé\\ud800c\\x00'.endswith('\\ud800cb', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800中é中ébébaé\\ud800c\\x00'.count('\\ud800cb', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\n",
              '''True
3
ValueError
-1
False
ValueError
-1
False
1
0
-1
False
ValueError
2
False
0
''')

check_program("try: print(b'a\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80'.index(b'aa\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\x00c中babééabbé\\x00b\\ud800中acb中中\\x00aa\\ud800a中éé中c\\ud800cb\\x00'.find('abbé\\x00b\\ud800中acb中中\\x00aa\\ud800a中éé中c\\ud800cb\\x00', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00\\xc3\\xa9a\\xc3\\xa9c\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80c\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xad\\x00a\\xed\\xa0\\x80\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9a\\x00\\xe4\\xb8\\xad\\x00a\\xc3\\xa9\\xed\\xa0\\x80b\\xc3\\xa9'.startswith(b'', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00\\xc3\\xa9a\\xc3\\xa9c\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80c\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xad\\x00a\\xed\\xa0\\x80\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9a\\x00\\xe4\\xb8\\xad\\x00a\\xc3\\xa9\\xed\\xa0\\x80b\\xc3\\xa9'.rindex(b'', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中中\\x00abb\\ud800aébb\\x00bcc'.rfind('\\x00c\\x00\\x00中a\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xc3\\xa9b\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80a\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xadac\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9c\\xe4\\xb8\\xadbb\\x00\\x00'.endswith(b'ac\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9c\\xe4\\xb8\\xadbb\\x00\\x00', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xc3\\xa9b\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80a\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xadac\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9c\\xe4\\xb8\\xadbb\\x00\\x00'.count(b'ac\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9c\\xe4\\xb8\\xadbb\\x00\\x00', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ccc\\x00c\\ud800cb\\ud800bca\\ud800\\ud800'.index('\\ud800中\\ud800'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'bcc\\xe4\\xb8\\xad\\x00b'.find(b'\\xed\\xa0\\x80', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800中\\x00\\x00'.startswith('\\ud800中\\x00\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800中\\x00\\x00'.rindex('\\ud800中\\x00\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xc3\\xa9ab\\xed\\xa0\\x80\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xadab\\xe4\\xb8\\xadc\\xc3\\xa9\\xed\\xa0\\x80a'.rfind(b'a\\x00b\\xc3\\xa9', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中\\x00中éc\\x00\\ud800éb\\x00\\ud800\\ud800中'.endswith('\\x00b\\ud800b', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中\\x00中éc\\x00\\ud800éb\\x00\\ud800\\ud800中'.count('\\x00b\\ud800b', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xed\\xa0\\x80b\\xc3\\xa9'.index(b'\\xed\\xa0\\x80b\\xc3\\xa9', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中中\\x00caacbé\\x00bcé\\ud800中\\x00中ba\\x00'.find('中bc\\ud800a', 1, 1))\nexcept Exception as error: print(type(error).__name__)\n",
              '''ValueError
9
True
58
-1
False
0
ValueError
-1
True
0
-1
False
0
2
-1
''')

check_program("try: print(b'\\xed\\xa0\\x80bb\\xed\\xa0\\x80a\\xc3\\xa9ccb\\xc3\\xa9cc\\xed\\xa0\\x80\\xc3\\xa9a\\xed\\xa0\\x80\\xc3\\xa9\\x00'.startswith(b'\\xe4\\xb8\\xad', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80bb\\xed\\xa0\\x80a\\xc3\\xa9ccb\\xc3\\xa9cc\\xed\\xa0\\x80\\xc3\\xa9a\\xed\\xa0\\x80\\xc3\\xa9\\x00'.rindex(b'\\xe4\\xb8\\xad', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cb中é\\x00baccb\\x00b\\ud800中\\x00\\x00c中b\\ud800céa中'.rfind('\\x00b\\ud800中\\x00\\x00c中b\\ud800céa中', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\x00'.endswith(b'a\\xc3\\xa9c', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\x00'.count(b'a\\xc3\\xa9c', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800b\\x00b\\ud800é\\ud800éa\\x00é\\x00\\x00aéb中\\ud800中\\x00\\ud800中\\x00cba中\\ud800bé中\\ud800c中\\x00a'.index('cc中cc', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xe4\\xb8\\xadcc\\xc3\\xa9c\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80b\\xed\\xa0\\x80\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\x00'.find(b'b\\xed\\xa0\\x80\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\x00', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aca\\ud800\\ud800b中c中中abacé'.startswith('a中中b', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aca\\ud800\\ud800b中c中中abacé'.rindex('a中中b', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\x00\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xed\\xa0\\x80c\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9\\x00\\xe4\\xb8\\xadc\\x00\\xe4\\xb8\\xadc\\x00c\\xc3\\xa9'.rfind(b'\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aa\\x00中ba\\x00\\x00\\x00é中c\\ud800é\\ud800aabbacébaéaaa'.endswith('é\\ud800aabbacébaéaaa', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aa\\x00中ba\\x00\\x00\\x00é中c\\ud800é\\ud800aabbacébaéaaa'.count('é\\ud800aabbacébaéaaa', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadc'.index(b'\\x00\\x00c\\xed\\xa0\\x80', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00céabb\\ud800bééé\\ud800é中'.find('b\\x00b中', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xadaaca\\xed\\xa0\\x80b\\x00\\xed\\xa0\\x80a'.startswith(b'\\xe4\\xb8\\xad\\xe4\\xb8\\xadaaca\\xed\\xa0\\x80b\\x00\\xed\\xa0\\x80a', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xadaaca\\xed\\xa0\\x80b\\x00\\xed\\xa0\\x80a'.rindex(b'\\xe4\\xb8\\xad\\xe4\\xb8\\xadaaca\\xed\\xa0\\x80b\\x00\\xed\\xa0\\x80a', None))\nexcept Exception as error: print(type(error).__name__)\n",
              '''False
ValueError
10
False
0
ValueError
16
False
ValueError
-1
False
0
ValueError
-1
False
3
''')

check_program("try: print('中中éacé'.rfind('ccb'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ab\\xe4\\xb8\\xadaa\\xe4\\xb8\\xad\\xed\\xa0\\x80ba\\xe4\\xb8\\xada\\xe4\\xb8\\xada\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80a\\x00\\xc3\\xa9ba\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\x00\\xed\\xa0\\x80cc\\xc3\\xa9cba\\xc3\\xa9\\xed\\xa0\\x80abc'.endswith(b'b\\xed\\xa0\\x80a\\xe4\\xb8\\xad'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ab\\xe4\\xb8\\xadaa\\xe4\\xb8\\xad\\xed\\xa0\\x80ba\\xe4\\xb8\\xada\\xe4\\xb8\\xada\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80a\\x00\\xc3\\xa9ba\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\x00\\xed\\xa0\\x80cc\\xc3\\xa9cba\\xc3\\xa9\\xed\\xa0\\x80abc'.count(b'b\\xed\\xa0\\x80a\\xe4\\xb8\\xad'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中caca中中a\\x00\\x00é中aa中b中é\\x00aa\\x00c\\ud800\\ud800bc中中中bb中acéb'.index('aca中中a\\x00\\x00é中aa中b中é\\x00aa\\x00c\\ud800\\ud800bc中中中bb中acéb', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ab\\xed\\xa0\\x80b\\x00'.find(b'\\xc3\\xa9\\xc3\\xa9', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aab中bcécaccb中中é\\ud800cbbé'.startswith('', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aab中bcécaccb中中é\\ud800cbbé'.rindex('', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'cca\\xed\\xa0\\x80\\x00bb\\xe4\\xb8\\xadb\\x00\\x00b\\xe4\\xb8\\xadb\\xed\\xa0\\x80\\xe4\\xb8\\xadb\\xc3\\xa9bc\\xe4\\xb8\\xada\\xc3\\xa9\\x00\\x00'.rfind(b'a\\xc3\\xa9\\x00\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b\\x00éé\\ud800a\\x00ccé\\x00bcéa\\x00a\\ud800\\x00\\ud800\\x00b\\ud800\\x00中acé\\ud800b\\ud800中中a中\\ud800'.endswith('', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b\\x00éé\\ud800a\\x00ccé\\x00bcéa\\x00a\\ud800\\x00\\ud800\\x00b\\ud800\\x00中acé\\ud800b\\ud800中中a中\\ud800'.count('', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00\\xc3\\xa9c\\xed\\xa0\\x80a\\x00a\\xc3\\xa9a\\xc3\\xa9bc\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00bc'.index(b'bc\\xe4\\xb8\\xad', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中\\ud800ca\\x00\\ud800\\x00中é'.find('中\\ud800ca\\x00\\ud800\\x00中é', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadc\\x00\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80'.startswith(b'', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadc\\x00\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80'.rindex(b'', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\ud800\\x00bé\\ud800\\ud800bbc中c\\x00bcaéa\\x00中bba\\ud800中bécéc\\ud800a中\\x00'.rfind('\\x00caé\\x00', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\x00\\xc3\\xa9'.endswith(b'', -3, -1))\nexcept Exception as error: print(type(error).__name__)\n",
              '''-1
False
0
2
-1
True
19
34
False
0
ValueError
-1
False
ValueError
-1
True
''')

check_program("try: print(b'c\\x00\\xc3\\xa9'.count(b'', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cé\\ud800a\\x00é\\x00bca\\x00\\x00\\ud800\\x00bb\\ud800abcéca\\x00cé\\ud800\\ud800ba'.index('', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00ab'.find(b'\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('éaécéac\\ud800a中ab中c\\ud800\\x00'.startswith('céac\\ud800a中ab中c\\ud800\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('éaécéac\\ud800a中ab中c\\ud800\\x00'.rindex('céac\\ud800a中ab中c\\ud800\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9'.rfind(b'\\x00\\xed\\xa0\\x80\\x00b\\xed\\xa0\\x80c\\xc3\\xa9', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800ccc\\x00caabb\\x00c\\ud800\\ud800\\x00aa\\ud800bba\\x00c\\x00\\x00\\ud800cé\\x00'.endswith('中\\ud800', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800ccc\\x00caabb\\x00c\\ud800\\ud800\\x00aa\\ud800bba\\x00c\\x00\\x00\\ud800cé\\x00'.count('中\\ud800', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xed\\xa0\\x80c\\x00c\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xe4\\xb8\\xadbba\\xed\\xa0\\x80ca\\xed\\xa0\\x80bb\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\x00\\xe4\\xb8\\xada\\xc3\\xa9\\xe4\\xb8\\xadba\\x00b\\xed\\xa0\\x80\\x00b'.index(b'b\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\x00\\xe4\\xb8\\xada\\xc3\\xa9\\xe4\\xb8\\xadba\\x00b\\xed\\xa0\\x80\\x00b', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cé\\x00é'.find('é'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xc3\\xa9b\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\x00c\\x00baaaa'.startswith(b'\\xed\\xa0\\x80'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xc3\\xa9b\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\x00c\\x00baaaa'.rindex(b'\\xed\\xa0\\x80'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00ccéa\\ud800ca\\x00cé'.rfind('céa\\ud800ca\\x00cé', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'cabcc\\xe4\\xb8\\xadb\\xc3\\xa9\\xe4\\xb8\\xad\\x00\\xc3\\xa9ca\\xc3\\xa9\\xe4\\xb8\\xad'.endswith(b'\\x00a\\x00', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'cabcc\\xe4\\xb8\\xadb\\xc3\\xa9\\xe4\\xb8\\xad\\x00\\xc3\\xa9ca\\xc3\\xa9\\xe4\\xb8\\xad'.count(b'\\x00a\\x00', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中aéaabc\\x00ca\\ud800b中b中a\\x00a\\x00ca\\ud800'.index('aé中', 10000))\nexcept Exception as error: print(type(error).__name__)\n",
              '''3
0
0
False
3
-1
False
0
31
1
False
5
-1
False
0
ValueError
''')

check_program("try: print(b'c\\x00a\\xc3\\xa9\\xed\\xa0\\x80b\\x00\\x00\\xed\\xa0\\x80'.find(b'a\\xc3\\xa9\\xed\\xa0\\x80b\\x00\\x00\\xed\\xa0\\x80', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b'.endswith('cc\\x00a', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\x00\\xed\\xa0\\x80ca\\xc3\\xa9c\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\xc3\\xa9c\\x00a\\xed\\xa0\\x80\\xed\\xa0\\x80a'.startswith(b'', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\x00\\xed\\xa0\\x80ca\\xc3\\xa9c\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\xc3\\xa9c\\x00a\\xed\\xa0\\x80\\xed\\xa0\\x80a'.count(b'', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中中acbbé\\ud800céc\\x00\\ud800中\\x00céé\\ud800a\\x00\\x00b\\ud800b中ba\\ud800bc\\x00b\\x00é\\x00中éb'.rindex('bé\\ud800céc\\x00\\ud800中\\x00céé\\ud800a\\x00\\x00b\\ud800b中ba\\ud800bc\\x00b\\x00é\\x00中éb', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xe4\\xb8\\xad\\xc3\\xa9a\\xc3\\xa9\\xe4\\xb8\\xadb\\xc3\\xa9\\xe4\\xb8\\xadccbcbb\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\xe4\\xb8\\xad'.index(b'b\\xc3\\xa9b\\xe4\\xb8\\xadb', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ba\\ud800ba中\\x00b中ab中abcbbbéaaa中中bcb\\ud800中\\ud800é'.rfind('\\x00ac', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\x00c\\x00\\xc3\\xa9c\\x00\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xadbb\\xed\\xa0\\x80\\xed\\xa0\\x80a\\x00\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xed\\xa0\\x80a\\xc3\\xa9\\x00\\xe4\\xb8\\xadcc\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80bcaac\\xc3\\xa9c\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xad'.find(b'\\xed\\xa0\\x80a\\x00\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xed\\xa0\\x80a\\xc3\\xa9\\x00\\xe4\\xb8\\xadcc\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80bcaac\\xc3\\xa9c\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xad'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bcaaabbbaccéé中\\ud800\\ud800中caab\\x00a\\ud800中\\ud800a'.endswith('', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9b\\xc3\\xa9b\\xed\\xa0\\x80b\\xc3\\xa9c\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80cc'.startswith(b'\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9b\\xc3\\xa9b\\xed\\xa0\\x80b\\xc3\\xa9c\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80cc'.count(b'\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c\\ud800\\x00a中\\x00b\\x00b中cc中\\x00b\\x00\\x00bé\\ud800中\\ud800\\ud800中\\x00aaabaéc\\ud800\\ud800中é\\x00'.rindex('cc中\\x00b\\x00\\x00bé\\ud800中\\ud800\\ud800中\\x00aaabaéc\\ud800\\ud800中é\\x00', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ac\\x00c\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9b\\xed\\xa0\\x80cbb\\xed\\xa0\\x80ba\\xed\\xa0\\x80\\xc3\\xa9b\\xe4\\xb8\\xadccaa\\x00\\xc3\\xa9\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80'.index(b'\\xe4\\xb8\\xad\\x00a'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('acé\\x00céa\\x00a'.rfind('\\ud800\\ud800', 10000))\nexcept Exception as error: print(type(error).__name__)\n",
              '''-1
False
True
30
5
ValueError
-1
21
True
False
0
ValueError
ValueError
-1
''')

check_program("try: print('acé\\x00céa\\x00a'.rindex('\\ud800\\ud800', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ca\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00\\x00\\xed\\xa0\\x80ba\\xc3\\xa9\\x00c\\xed\\xa0\\x80a\\xc3\\xa9baca\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xadba\\xc3\\xa9\\xe4\\xb8\\xada\\xe4\\xb8\\xadcaaa\\xe4\\xb8\\xad\\xc3\\xa9'.index(b'\\xe4\\xb8\\xadba\\xc3\\xa9\\xe4\\xb8\\xada\\xe4\\xb8\\xadcaaa\\xe4\\xb8\\xad\\xc3\\xa9'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中\\x00\\ud800ca\\x00b中acéa\\ud800中中éaccab\\ud800cé\\ud800a\\x00a中c\\x00\\ud800中b\\x00ca'.rfind('', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xe4\\xb8\\xada\\xc3\\xa9c\\xed\\xa0\\x80c\\x00b\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xadb\\x00b\\xe4\\xb8\\xadaa\\xed\\xa0\\x80\\xed\\xa0\\x80aaac\\xe4\\xb8\\xadb'.find(b'\\xc3\\xa9\\xe4\\xb8\\xadc', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00bccé中\\x00\\x00cé中acc中béaaéb'.endswith('cé中\\x00\\x00cé中acc中béaaéb', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80abbbbab\\xe4\\xb8\\xadcb\\xe4\\xb8\\xadb\\x00\\x00\\xc3\\xa9\\xed\\xa0\\x80acbabc\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\x00c\\xc3\\xa9\\xe4\\xb8\\xada'.startswith(b'\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00c\\xe4\\xb8\\xad\\xe4\\xb8\\xada', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80abbbbab\\xe4\\xb8\\xadcb\\xe4\\xb8\\xadb\\x00\\x00\\xc3\\xa9\\xed\\xa0\\x80acbabc\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\x00c\\xc3\\xa9\\xe4\\xb8\\xada'.count(b'\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00c\\xe4\\xb8\\xad\\xe4\\xb8\\xada', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aa中a'.rindex('中bcé中a\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadccca\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80abb\\xc3\\xa9\\xed\\xa0\\x80ca\\xe4\\xb8\\xada\\xc3\\xa9b\\xc3\\xa9'.index(b'cca\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80abb\\xc3\\xa9\\xed\\xa0\\x80ca\\xe4\\xb8\\xada\\xc3\\xa9b\\xc3\\xa9', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00a\\x00\\ud800\\x00a\\ud800\\ud800b中中\\x00\\ud800'.rfind('écc\\ud800中ac', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80cb\\xed\\xa0\\x80\\x00\\x00a\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80a\\xc3\\xa9\\x00\\x00a\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xed\\xa0\\x80\\xc3\\xa9bcbca'.find(b'cc\\xe4\\xb8\\xadc', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00\\x00中éa\\x00\\x00\\ud800c\\x00b\\x00\\ud800\\ud800中c\\ud800中ccaé\\x00ébcé中\\ud800a'.endswith('\\ud800中ccaé\\x00ébcé中\\ud800a', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ccab'.startswith(b'\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\x00c', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ccab'.count(b'\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\x00c', 10000))\nexcept Exception as error: print(type(error).__name__)\n",
              '''ValueError
34
1
-1
True
False
0
ValueError
ValueError
-1
-1
True
False
0
''')

check_program("try: print('\\x00中c中ééébé\\x00bbbb'.endswith('\\x00aaa'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00ac\\x00b\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9c\\x00\\xed\\xa0\\x80ac\\x00\\xe4\\xb8\\xad\\xc3\\xa9b\\xe4\\xb8\\xadaa\\xc3\\xa9\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xad\\xc3\\xa9\\x00\\x00baa\\xe4\\xb8\\xad\\x00\\x00\\xed\\xa0\\x80a'.endswith(b'c\\x00b\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9c\\x00\\xed\\xa0\\x80ac\\x00\\xe4\\xb8\\xad\\xc3\\xa9b\\xe4\\xb8\\xadaa\\xc3\\xa9\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xad\\xc3\\xa9\\x00\\x00baa\\xe4\\xb8\\xad\\x00\\x00\\xed\\xa0\\x80a', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cé\\x00\\ud800\\x00é\\ud800\\ud800éa\\ud800\\x00aé\\ud800éa中cc中\\x00éac中\\x00béé'.endswith('中\\x00\\x00éb\\ud800é', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xad\\xc3\\xa9\\x00bcb\\xe4\\xb8\\xad\\xc3\\xa9aa\\xc3\\xa9a\\x00\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80b'.endswith(b'\\xed\\xa0\\x80\\xed\\xa0\\x80b\\xc3\\xa9', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00\\x00\\x00中cé'.endswith('é', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80ccb\\xed\\xa0\\x80a\\x00b\\xe4\\xb8\\xada\\xc3\\xa9a\\xed\\xa0\\x80\\x00a\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xadb\\xc3\\xa9\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9b\\xe4\\xb8\\xadba\\x00\\x00\\x00cca\\xed\\xa0\\x80'.endswith(b'\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b\\ud800cbc\\ud800\\ud800ccé\\ud800\\ud800aa\\x00\\x00\\x00\\ud800cb中cc'.endswith('éé', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ca\\xe4\\xb8\\xad\\x00c\\xc3\\xa9\\xe4\\xb8\\xadc\\xc3\\xa9c\\xc3\\xa9a\\xc3\\xa9cc\\x00\\x00a\\x00c\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9acacb\\xed\\xa0\\x80\\x00\\x00b'.endswith(b'c\\xc3\\xa9\\xe4\\xb8\\xadc\\xc3\\xa9c\\xc3\\xa9a\\xc3\\xa9cc\\x00\\x00a\\x00c\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9acacb\\xed\\xa0\\x80\\x00\\x00b', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800\\x00中\\ud800\\x00\\ud800中accbcbc中baébbb\\ud800ccb\\x00abéa\\x00aa\\ud800ba\\x00'.endswith('c\\ud800ac', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'bbbcb\\x00\\x00\\x00\\x00ab\\xed\\xa0\\x80a\\xed\\xa0\\x80\\xc3\\xa9cc\\xe4\\xb8\\xad\\xed\\xa0\\x80bc\\xe4\\xb8\\xadc\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80baaab\\xe4\\xb8\\xad\\xe4\\xb8\\xad'.endswith(b'acca\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800\\x00\\ud800\\ud800aééc\\x00é\\ud800éé\\x00\\ud800\\ud800\\x00中ba中baab\\ud800中中a'.endswith('aééc\\x00é\\ud800éé\\x00\\ud800\\ud800\\x00中ba中baab\\ud800中中a'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xe4\\xb8\\xadc\\xed\\xa0\\x80bca\\xe4\\xb8\\xadcb\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9ac\\xc3\\xa9\\xe4\\xb8\\xada\\xc3\\xa9\\x00ac\\xc3\\xa9\\xc3\\xa9ca\\xc3\\xa9ba\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80\\x00aca'.endswith(b'\\xed\\xa0\\x80c\\xed\\xa0\\x80\\xed\\xa0\\x80c', -3, -1))\nexcept Exception as error: print(type(error).__name__)\n",
              '''False
False
False
False
False
False
False
True
False
False
True
False
''')

check_program("try: print(b'\\xc3\\xa9\\xe4\\xb8\\xadc\\xed\\xa0\\x80bca\\xe4\\xb8\\xadcb\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9ac\\xc3\\xa9\\xe4\\xb8\\xada\\xc3\\xa9\\x00ac\\xc3\\xa9\\xc3\\xa9ca\\xc3\\xa9ba\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80\\x00aca'.index(b'\\xed\\xa0\\x80c\\xed\\xa0\\x80\\xed\\xa0\\x80c', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cééacéb\\x00éé\\ud800a'.find('b\\x00\\ud800é\\ud800', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80b\\xc3\\xa9c\\xc3\\xa9b\\xed\\xa0\\x80'.startswith(b'b\\xc3\\xa9c\\xc3\\xa9b\\xed\\xa0\\x80'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80b\\xc3\\xa9c\\xc3\\xa9b\\xed\\xa0\\x80'.rindex(b'b\\xc3\\xa9c\\xc3\\xa9b\\xed\\xa0\\x80'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中bé'.rfind('é', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00b\\x00b\\x00\\xe4\\xb8\\xadb\\xed\\xa0\\x80b\\x00cca\\xed\\xa0\\x80\\xed\\xa0\\x80ab\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xada'.endswith(b'c\\xed\\xa0\\x80aa', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00b\\x00b\\x00\\xe4\\xb8\\xadb\\xed\\xa0\\x80b\\x00cca\\xed\\xa0\\x80\\xed\\xa0\\x80ab\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xada'.count(b'c\\xed\\xa0\\x80aa', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ca\\x00a\\ud800中b中中\\x00'.index('\\ud800中b中中\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'cba\\xe4\\xb8\\xada\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80bb\\xc3\\xa9\\xc3\\xa9aa\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\x00a\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80ccc\\xc3\\xa9a\\x00\\x00cc\\xed\\xa0\\x80\\x00'.find(b'\\xe4\\xb8\\xadac\\xe4\\xb8\\xadb', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bcéc\\x00é\\ud800b中abc\\ud800aa中\\x00c\\x00b中c中éc\\x00中'.startswith('\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bcéc\\x00é\\ud800b中abc\\ud800aa中\\x00c\\x00b中c中éc\\x00中'.rindex('\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80b\\xe4\\xb8\\xad\\xed\\xa0\\x80cb\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80b\\xe4\\xb8\\xad\\x00ab\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80cabb\\xc3\\xa9\\x00\\xc3\\xa9\\xc3\\xa9\\x00b\\xe4\\xb8\\xadb'.rfind(b'\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80b\\xe4\\xb8\\xad\\x00ab\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80cabb\\xc3\\xa9\\x00\\xc3\\xa9\\xc3\\xa9\\x00b\\xe4\\xb8\\xadb'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b\\x00cc'.endswith('c', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b\\x00cc'.count('c', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xed\\xa0\\x80c\\x00b\\xed\\xa0\\x80b\\xe4\\xb8\\xada\\x00'.index(b'bbab\\xc3\\xa9', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800c'.find('', 10000))\nexcept Exception as error: print(type(error).__name__)\n",
              '''ValueError
-1
False
3
2
False
0
4
-1
False
25
12
True
1
ValueError
-1
''')
