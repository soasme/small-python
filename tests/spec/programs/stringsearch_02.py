# spec: PLS-315 23.1
# description: Programs on string search methods, each with the output CPython 3.15 gives.
from harness import *

check_program("try: print(b'\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadccb\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9bccc\\xe4\\xb8\\xadb\\xe4\\xb8\\xadabc\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadab\\xed\\xa0\\x80b\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80c\\x00\\xc3\\xa9\\xed\\xa0\\x80a'.count(b'\\xed\\xa0\\x80', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800\\ud800\\x00\\ud800bcé\\x00ééb\\ud800é中\\x00\\ud800中\\ud800bbé\\x00\\ud800éaba\\x00é\\ud800\\ud800'.rindex('cé\\x00ééb\\ud800é中\\x00\\ud800中\\ud800bbé\\x00\\ud800éaba\\x00é\\ud800\\ud800', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xc3\\xa9a\\xe4\\xb8\\xad\\x00\\x00cabb\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xad'.index(b'\\x00a\\xc3\\xa9', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\x00中\\ud800aa\\x00'.rfind('', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9cc\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9\\x00ba\\xed\\xa0\\x80\\x00'.find(b'\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9\\x00ba\\xed\\xa0\\x80\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800éa\\x00中a\\x00b中\\x00ac\\x00\\x00aa\\ud800a\\x00c\\ud800\\ud800中b\\x00'.endswith('bc中acé\\ud800'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadb\\xc3\\xa9\\xed\\xa0\\x80a\\x00\\xc3\\xa9\\xc3\\xa9\\x00c\\xed\\xa0\\x80\\xed\\xa0\\x80ca\\x00\\x00a\\xed\\xa0\\x80\\x00bc\\xed\\xa0\\x80\\xed\\xa0\\x80b\\xe4\\xb8\\xad\\x00'.startswith(b'\\xe4\\xb8\\xadcb\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xad', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadb\\xc3\\xa9\\xed\\xa0\\x80a\\x00\\xc3\\xa9\\xc3\\xa9\\x00c\\xed\\xa0\\x80\\xed\\xa0\\x80ca\\x00\\x00a\\xed\\xa0\\x80\\x00bc\\xed\\xa0\\x80\\xed\\xa0\\x80b\\xe4\\xb8\\xad\\x00'.count(b'\\xe4\\xb8\\xadcb\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xad', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中c中éc\\ud800éb中\\ud800\\x00\\ud800c'.rindex('\\ud800\\x00\\ud800c', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80cac\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xadaa\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xadacc\\xc3\\xa9a\\xc3\\xa9\\xed\\xa0\\x80ca\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xadac'.index(b'\\x00acbb\\xed\\xa0\\x80'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\ud800é\\x00中\\x00c\\ud800cc\\ud800\\x00bé\\x00\\ud800aca'.rfind('c\\ud800', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'aaa\\xe4\\xb8\\xad\\x00\\x00c\\xe4\\xb8\\xad\\x00\\x00bc\\x00cca\\xc3\\xa9b'.find(b'c\\xe4\\xb8\\xad\\x00\\x00bc\\x00cca\\xc3\\xa9b', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\ud800a\\x00\\ud800écca\\ud800\\x00é中\\ud800céb\\ud800é'.endswith('écb'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'acca\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80bb\\x00\\x00\\xe4\\xb8\\xadc\\x00\\x00\\xed\\xa0\\x80\\x00\\xc3\\xa9\\xc3\\xa9c\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xad\\x00a'.startswith(b'abc\\xc3\\xa9bc\\xc3\\xa9', None))\nexcept Exception as error: print(type(error).__name__)\n",
              '''0
5
ValueError
7
4
False
False
0
9
ValueError
-1
8
False
False
''')

check_program("try: print(b'acca\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80bb\\x00\\x00\\xe4\\xb8\\xadc\\x00\\x00\\xed\\xa0\\x80\\x00\\xc3\\xa9\\xc3\\xa9c\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xad\\x00a'.find(b'abc\\xc3\\xa9bc\\xc3\\xa9', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a'.find(''))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ba\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadaacc\\xc3\\xa9\\xc3\\xa9bcc\\xc3\\xa9b\\xc3\\xa9a\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80'.find(b'\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xad', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\x00中c\\x00中ébac中b\\x00cacé\\ud800c'.find('cbééb', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80b\\xc3\\xa9c\\xed\\xa0\\x80\\xed\\xa0\\x80cb\\xed\\xa0\\x80\\xc3\\xa9c\\xc3\\xa9b\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xad\\x00cbacc\\xed\\xa0\\x80a'.find(b'a', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a\\x00\\x00bc\\x00c\\ud800中\\x00中c\\x00\\x00c中ééé中\\x00\\ud800aabé\\x00\\ud800a\\x00ébb中中'.find('\\x00ca\\ud800\\ud800\\x00中'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xc3\\xa9\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9baacb\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9\\x00abb\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xadb\\xe4\\xb8\\xad\\x00\\x00b\\xc3\\xa9b\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xad'.find(b'a\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xad'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中\\ud800ébbbé\\x00\\x00aab\\x00b\\x00\\ud800céab\\x00cb\\ud800bb'.find('aab\\x00b\\x00\\ud800céab\\x00cb\\ud800bb', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xe4\\xb8\\xad\\x00\\x00c\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80bb\\xed\\xa0\\x80\\xc3\\xa9aa\\x00\\x00c\\xe4\\xb8\\xadcbb\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\xe4\\xb8\\xad\\x00a\\x00\\xc3\\xa9a'.find(b'\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中a\\x00é\\x00é\\ud800\\x00中ééb\\x00c中\\ud800\\ud800\\ud800\\ud800a中\\ud800b\\x00b\\x00\\ud800c\\x00ééc'.find('éccb', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xed\\xa0\\x80b\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xed\\xa0\\x80\\x00aa\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9b\\x00\\x00\\x00b\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xadcc\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\xc3\\xa9'.find(b'\\x00\\x00\\x00b\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xadcc\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\xc3\\xa9', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b\\x00中b\\ud800cabbbcc\\x00ac\\ud800é'.find('', -3, -1))\nexcept Exception as error: print(type(error).__name__)\n",
              '''-1
0
-1
-1
34
-1
-1
9
-1
-1
30
14
''')

check_program("try: print('b\\x00中b\\ud800cabbbcc\\x00ac\\ud800é'.rindex('', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80aaa\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9c\\x00\\x00\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80\\x00a\\x00\\xed\\xa0\\x80\\xc3\\xa9cab\\xc3\\xa9\\xe4\\xb8\\xadb\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\x00bb\\xc3\\xa9\\xed\\xa0\\x80cc'.index(b'aa\\xe4\\xb8\\xad\\xed\\xa0\\x80', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800\\ud800a中c\\x00中\\ud800中\\ud800c\\ud800ac\\x00中\\x00\\ud800cac\\x00éc中中bacéb\\ud800'.rfind('a中c\\x00中\\ud800中\\ud800c\\ud800ac\\x00中\\x00\\ud800cac\\x00éc中中bacéb\\ud800', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00\\xc3\\xa9\\xed\\xa0\\x80a\\xe4\\xb8\\xadbc\\xed\\xa0\\x80\\xc3\\xa9a\\xe4\\xb8\\xadc\\xc3\\xa9c\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9c\\xc3\\xa9b\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80b\\xe4\\xb8\\xad'.find(b'\\xc3\\xa9', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('abaéa\\ud800中\\ud800a中\\ud800é'.endswith('\\ud800', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ca\\xed\\xa0\\x80ba\\xc3\\xa9b\\xe4\\xb8\\xad\\xed\\xa0\\x80cb\\xed\\xa0\\x80ac\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9\\x00\\x00c\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\x00\\x00\\xc3\\xa9ccc\\x00aac\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xed\\xa0\\x80'.startswith(b'\\x00\\xc3\\xa9\\x00\\x00\\xc3\\xa9ccc\\x00aac\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xed\\xa0\\x80', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ca\\xed\\xa0\\x80ba\\xc3\\xa9b\\xe4\\xb8\\xad\\xed\\xa0\\x80cb\\xed\\xa0\\x80ac\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9\\x00\\x00c\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\x00\\x00\\xc3\\xa9ccc\\x00aac\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xed\\xa0\\x80'.count(b'\\x00\\xc3\\xa9\\x00\\x00\\xc3\\xa9ccc\\x00aac\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xed\\xa0\\x80', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cabécc\\ud800\\x00é\\x00c\\ud800\\x00\\x00b中c\\ud800\\ud800\\ud800aab\\x00éé中ac\\x00caa'.rindex('é\\x00b'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80bac\\xed\\xa0\\x80c\\x00\\xe4\\xb8\\xadb\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9a\\x00\\xed\\xa0\\x80\\x00'.index(b'', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800éé\\ud800bac\\ud800é中\\x00éabac\\x00\\ud800bbb\\x00é\\x00\\ud800中b中acb\\x00中中ébb\\x00中'.rfind('bb\\x00é\\x00\\ud800中b中acb\\x00中中ébb\\x00中', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80c\\x00\\xc3\\xa9b\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80'.find(b'cc\\x00', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800\\ud800a\\ud800cab中'.endswith('é中b中b', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80c\\xe4\\xb8\\xadb\\xe4\\xb8\\xadc\\xc3\\xa9'.startswith(b'c\\xc3\\xa9', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80c\\xe4\\xb8\\xadb\\xe4\\xb8\\xadc\\xc3\\xa9'.count(b'c\\xc3\\xa9', 1, 1))\nexcept Exception as error: print(type(error).__name__)\n",
              '''16
ValueError
-1
7
False
False
0
ValueError
0
19
-1
False
False
0
''')

check_program("try: print('\\x00bécbaé\\ud800\\x00c中c'.endswith('éé'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00bécbaé\\ud800\\x00c中c'.count('éé'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80b\\x00\\x00b\\xed\\xa0\\x80a\\xc3\\xa9\\x00b\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9'.index(b'', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800c\\x00\\x00b\\x00céa\\ud800\\ud800中c\\ud800ca'.find('ca', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ac\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xadcb\\xe4\\xb8\\xad'.startswith(b'', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ac\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xadcb\\xe4\\xb8\\xad'.rindex(b'', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\ud800中acbbébb\\ud800\\x00éé\\x00\\ud800é\\ud800aé\\x00\\x00ba'.rfind('\\x00a', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xc3\\xa9\\xc3\\xa9\\x00'.endswith(b'\\xc3\\xa9\\xc3\\xa9\\x00', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xc3\\xa9\\xc3\\xa9\\x00'.count(b'\\xc3\\xa9\\xc3\\xa9\\x00', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ababé\\ud800b\\ud800aéa中éabéb\\x00béb中é'.index('a\\x00\\x00ca', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadc\\xed\\xa0\\x80c\\xe4\\xb8\\xadb\\x00\\xc3\\xa9a\\xed\\xa0\\x80\\xc3\\xa9b\\xed\\xa0\\x80a\\x00'.find(b'\\xe4\\xb8\\xad\\x00\\x00\\xe4\\xb8\\xad\\xc3\\xa9b\\xc3\\xa9', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800\\x00cb\\ud800éca\\x00aé\\x00\\ud800\\x00\\ud800abc\\ud800bbb\\x00a\\ud800aa\\ud800é'.startswith('\\ud800éca\\x00aé\\x00\\ud800\\x00\\ud800abc\\ud800bbb\\x00a\\ud800aa\\ud800é', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800\\x00cb\\ud800éca\\x00aé\\x00\\ud800\\x00\\ud800abc\\ud800bbb\\x00a\\ud800aa\\ud800é'.rindex('\\ud800éca\\x00aé\\x00\\ud800\\x00\\ud800abc\\ud800bbb\\x00a\\ud800aa\\ud800é', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xadcbc\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80\\xc3\\xa9ba'.rfind(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c中c\\x00中aé中aé中\\x00中中\\ud800c\\x00中b\\ud800aca\\x00\\x00\\x00\\ud800bb\\ud800'.endswith('é\\ud800c\\x00bé\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c中c\\x00中aé中aé中\\x00中中\\ud800c\\x00中b\\ud800aca\\x00\\x00\\x00\\ud800bb\\ud800'.count('é\\ud800c\\x00bé\\x00'))\nexcept Exception as error: print(type(error).__name__)\n",
              '''False
0
0
14
True
14
-1
True
1
ValueError
-1
False
4
16
False
0
''')

check_program("try: print(b'\\xe4\\xb8\\xadb\\x00bb\\x00\\x00\\xed\\xa0\\x80c\\x00a\\xc3\\xa9abba\\xc3\\xa9\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xadc\\xe4\\xb8\\xad\\xed\\xa0\\x80c\\xed\\xa0\\x80\\xe4\\xb8\\xada\\x00c\\xe4\\xb8\\xadc'.index(b'\\xed\\xa0\\x80c\\xed\\xa0\\x80\\xe4\\xb8\\xada\\x00c\\xe4\\xb8\\xadc', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é'.find('', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80ac\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xadb\\xc3\\xa9c\\xe4\\xb8\\xad\\x00a\\xed\\xa0\\x80a\\xed\\xa0\\x80c\\x00\\x00\\xc3\\xa9c\\xed\\xa0\\x80\\xc3\\xa9a'.startswith(b'\\xc3\\xa9\\x00\\x00a\\x00\\xe4\\xb8\\xad', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80ac\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xadb\\xc3\\xa9c\\xe4\\xb8\\xad\\x00a\\xed\\xa0\\x80a\\xed\\xa0\\x80c\\x00\\x00\\xc3\\xa9c\\xed\\xa0\\x80\\xc3\\xa9a'.rindex(b'\\xc3\\xa9\\x00\\x00a\\x00\\xe4\\xb8\\xad', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c中\\x00\\ud800c中c\\ud800\\ud800中中aaa\\x00中éé中abéé'.rfind('aa\\x00中éé中abéé', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xc3\\xa9ccc\\xe4\\xb8\\xadacc\\xe4\\xb8\\xad\\x00\\x00bac\\x00\\x00\\x00\\x00\\xed\\xa0\\x80a\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\xed\\xa0\\x80'.endswith(b'ab', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xc3\\xa9ccc\\xe4\\xb8\\xadacc\\xe4\\xb8\\xad\\x00\\x00bac\\x00\\x00\\x00\\x00\\xed\\xa0\\x80a\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\xed\\xa0\\x80'.count(b'ab', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00c\\x00baaabbé中c\\x00c\\x00\\ud800\\x00é'.index('\\x00c', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b''.find(b''))\nexcept Exception as error: print(type(error).__name__)\ntry: print('babéab\\ud800béc\\x00a中éc中cc\\x00\\x00cac\\x00a中é中中é\\ud800b'.startswith('b\\x00aaa\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('babéab\\ud800béc\\x00a中éc中cc\\x00\\x00cac\\x00a中é中中é\\ud800b'.rindex('b\\x00aaa\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\x00\\xe4\\xb8\\xada\\xe4\\xb8\\xadb\\xc3\\xa9\\xe4\\xb8\\xadb\\xed\\xa0\\x80c\\xed\\xa0\\x80\\xc3\\xa9\\x00ac\\x00\\xc3\\xa9cbb'.rfind(b'ab', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bé\\ud800c中中c\\ud800中中\\ud800\\x00\\x00bbcc\\x00中aé'.endswith('中中c\\ud800中中\\ud800\\x00\\x00bbcc\\x00中aé', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bé\\ud800c中中c\\ud800中中\\ud800\\x00\\x00bbcc\\x00中aé'.count('中中c\\ud800中中\\ud800\\x00\\x00bbcc\\x00中aé', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80cbba\\xc3\\xa9a\\xe4\\xb8\\xad\\x00\\xc3\\xa9acb\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xada'.index(b'cc\\xe4\\xb8\\xad'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00\\ud800a\\x00cb\\x00é\\ud800\\x00\\x00b\\ud800\\x00\\x00'.find('écb\\ud800ac', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\n",
              '''ValueError
0
False
ValueError
-1
False
0
0
0
False
ValueError
-1
False
0
ValueError
-1
''')

check_program("try: print(b'a\\x00\\xe4\\xb8\\xad'.startswith(b'a\\x00\\xe4\\xb8\\xad', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\x00\\xe4\\xb8\\xad'.count(b'a\\x00\\xe4\\xb8\\xad', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cbac中bcéa\\ud800bcb\\ud800\\ud800中\\x00bbc\\ud800中éa\\x00acccécé中\\x00b'.rindex('\\x00éa'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xc3\\xa9\\xc3\\xa9ba\\xe4\\xb8\\xadc\\x00ac\\xed\\xa0\\x80c\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xadb\\x00b\\x00\\xed\\xa0\\x80c\\xe4\\xb8\\xada\\x00a\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00abc\\xe4\\xb8\\xadc\\xe4\\xb8\\xadcac\\x00a'.index(b'bc\\x00ca\\x00b', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800béc\\ud800中céc\\x00\\x00中b中b\\x00bcaa\\x00cb\\ud800a中\\x00c\\ud800éé\\ud800aa中\\ud800ééé'.rfind('中\\x00c\\ud800éé\\ud800aa中\\ud800ééé', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\x00ccb\\xe4\\xb8\\xad\\x00ba\\xe4\\xb8\\xad\\xe4\\xb8\\xadb\\x00\\xc3\\xa9\\x00\\xe4\\xb8\\xadc\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80b\\xc3\\xa9b\\xed\\xa0\\x80caa\\x00ac\\xe4\\xb8\\xadb\\xc3\\xa9\\xed\\xa0\\x80b\\x00\\xe4\\xb8\\xad\\x00'.find(b'c\\x00', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中中中éé'.endswith('', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80ab\\x00b\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xada\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9bb\\xed\\xa0\\x80a\\x00\\xc3\\xa9\\x00'.startswith(b'\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xada\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9bb\\xed\\xa0\\x80a\\x00\\xc3\\xa9\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80ab\\x00b\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xada\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9bb\\xed\\xa0\\x80a\\x00\\xc3\\xa9\\x00'.count(b'\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xada\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9bb\\xed\\xa0\\x80a\\x00\\xc3\\xa9\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(''.rindex('中', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xe4\\xb8\\xadb\\x00\\xed\\xa0\\x80bcca\\xe4\\xb8\\xadc\\x00\\xe4\\xb8\\xadc'.index(b'', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bb\\x00ca中aca\\ud800é\\ud800ccc\\x00'.rfind('', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xc3\\xa9\\x00b\\x00a\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9aac'.find(b'a', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('éaababb\\x00aaa'.endswith('bcbaba', 0))\nexcept Exception as error: print(type(error).__name__)\n",
              '''True
1
ValueError
ValueError
25
-1
True
False
1
ValueError
0
16
-1
False
''')

check_program("try: print('éaababb\\x00aaa'.rfind('bcbaba', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80b\\xed\\xa0\\x80\\x00\\xc3\\xa9\\x00\\x00a\\xc3\\xa9\\xed\\xa0\\x80'.endswith(b'b\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80b\\xed\\xa0\\x80\\x00\\xc3\\xa9\\x00\\x00a\\xc3\\xa9\\xed\\xa0\\x80', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80b\\xed\\xa0\\x80\\x00\\xc3\\xa9\\x00\\x00a\\xc3\\xa9\\xed\\xa0\\x80'.count(b'b\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80b\\xed\\xa0\\x80\\x00\\xc3\\xa9\\x00\\x00a\\xc3\\xa9\\xed\\xa0\\x80', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b\\ud800'.index('', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\x00b\\xed\\xa0\\x80bc\\xed\\xa0\\x80b\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80a\\xe4\\xb8\\xadb\\xed\\xa0\\x80b\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9a\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xc3\\xa9\\xc3\\xa9a'.find(b'\\xe4\\xb8\\xadca\\xc3\\xa9a\\xc3\\xa9\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ca\\ud800bab中cbcéaé中\\ud800éc中é中ac\\ud800\\x00cc中éc\\x00b'.startswith('cc中éc\\x00b', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ca\\ud800bab中cbcéaé中\\ud800éc中é中ac\\ud800\\x00cc中éc\\x00b'.rindex('cc中éc\\x00b', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9aa\\xed\\xa0\\x80\\xed\\xa0\\x80bbc\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xc3\\xa9\\xed\\xa0\\x80a\\xc3\\xa9c\\x00b\\x00b\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00\\xc3\\xa9'.rfind(b'c\\xc3\\xa9ca', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中中c中cb\\ud800中中é\\ud800c中a\\ud800中b中ccbé\\x00\\ud800'.endswith('c中中中c\\ud800é', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中中c中cb\\ud800中中é\\ud800c中a\\ud800中b中ccbé\\x00\\ud800'.count('c中中中c\\ud800é', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00a\\x00\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9bca\\xed\\xa0\\x80bb'.index(b'\\xe4\\xb8\\xad\\x00a\\x00\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9bca\\xed\\xa0\\x80bb', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800abébcb中cé中a\\x00a\\ud800aé'.find('aé中', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xc3\\xa9aa'.startswith(b'c\\xe4\\xb8\\xadb\\xe4\\xb8\\xadaa\\xed\\xa0\\x80', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xc3\\xa9aa'.rindex(b'c\\xe4\\xb8\\xadb\\xe4\\xb8\\xadaa\\xed\\xa0\\x80', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c\\ud800accc\\x00'.rfind('cc\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00a\\x00\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9c\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9a'.endswith(b'\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xed\\xa0\\x80', -3, -1))\nexcept Exception as error: print(type(error).__name__)\n",
              '''-1
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
-1
False
ValueError
4
False
''')

check_program("try: print(b'\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00a\\x00\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9c\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9a'.count(b'\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xed\\xa0\\x80', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b中b中\\x00ccab\\ud800中\\x00éé\\ud800c\\x00\\x00\\x00\\x00aa\\ud800c\\x00b\\x00bébc中bc\\ud800中\\ud800\\ud800b'.rindex('中中c', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ca\\x00\\x00\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xc3\\xa9\\x00b\\xc3\\xa9\\xe4\\xb8\\xadbb\\xc3\\xa9c\\xe4\\xb8\\xad\\xe4\\xb8\\xadb\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xadcc\\xed\\xa0\\x80b\\xed\\xa0\\x80'.index(b'\\xe4\\xb8\\xadcc\\xed\\xa0\\x80b\\xed\\xa0\\x80'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aaaé\\ud800bc\\x00é\\ud800中\\ud800'.rfind('ééé', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'bacb\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80'.find(b'\\xc3\\xa9c\\xe4\\xb8\\xad', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\ud800ééébc\\x00\\ud800\\ud800a\\x00é\\ud800ca'.endswith('ééébc\\x00\\ud800\\ud800a\\x00é\\ud800ca'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00b\\x00cb\\x00b\\xc3\\xa9\\xe4\\xb8\\xadcb\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80\\x00c\\xc3\\xa9\\x00\\xed\\xa0\\x80a\\xe4\\xb8\\xadb'.startswith(b'\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xadba', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00b\\x00cb\\x00b\\xc3\\xa9\\xe4\\xb8\\xadcb\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80\\x00c\\xc3\\xa9\\x00\\xed\\xa0\\x80a\\xe4\\xb8\\xadb'.count(b'\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xadba', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cba\\ud800c'.rindex('bbb', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'accba\\xe4\\xb8\\xad\\xc3\\xa9caabb\\xed\\xa0\\x80a\\x00\\x00ba\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\x00\\x00acbb\\xed\\xa0\\x80cc\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9ac'.index(b'acbb\\xed\\xa0\\x80cc\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9ac', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\x00bé\\ud800aaa中cébabb\\ud800\\ud800\\ud800中'.rfind('\\x00a中a\\x00', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xed\\xa0\\x80\\x00\\x00\\xed\\xa0\\x80a\\xe4\\xb8\\xadbc\\x00\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\x00cab'.find(b'c\\xc3\\xa9', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中\\x00\\x00b\\x00a\\ud800b'.endswith('b\\x00a\\ud800b', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\x00\\xc3\\xa9cab\\xe4\\xb8\\xadcb\\xc3\\xa9\\xc3\\xa9cc\\x00\\x00\\xe4\\xb8\\xadc\\xe4\\xb8\\xada\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad'.startswith(b'\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9', None))\nexcept Exception as error: print(type(error).__name__)\n",
              '''0
ValueError
47
-1
-1
True
False
0
ValueError
39
-1
-1
False
False
''')

check_program("try: print(b'\\xed\\xa0\\x80\\x00\\xc3\\xa9cab\\xe4\\xb8\\xadcb\\xc3\\xa9\\xc3\\xa9cc\\x00\\x00\\xe4\\xb8\\xadc\\xe4\\xb8\\xada\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad'.find(b'\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中cb\\x00éa\\x00中\\ud800éa\\x00c中cc\\ud800ccéca'.startswith('\\ud800c\\ud800中', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中cb\\x00éa\\x00中\\ud800éa\\x00c中cc\\ud800ccéca'.rindex('\\ud800c\\ud800中', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xc3\\xa9c\\xed\\xa0\\x80cb\\xed\\xa0\\x80\\xc3\\xa9bb\\xe4\\xb8\\xadc\\xed\\xa0\\x80b\\xc3\\xa9\\xed\\xa0\\x80c\\x00b\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80cac\\xe4\\xb8\\xadaac\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00aca'.rfind(b'c\\xed\\xa0\\x80b\\xc3\\xa9\\xed\\xa0\\x80c\\x00b\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80cac\\xe4\\xb8\\xadaac\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00aca', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c'.endswith('éb中中\\ud800\\x00é', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c'.count('éb中中\\ud800\\x00é', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b''.index(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中b中'.find(''))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\xed\\xa0\\x80a\\xc3\\xa9\\xe4\\xb8\\xadcaca\\xc3\\xa9\\xc3\\xa9b\\x00\\x00\\xc3\\xa9aa\\xed\\xa0\\x80'.startswith(b'', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\xed\\xa0\\x80a\\xc3\\xa9\\xe4\\xb8\\xadcaca\\xc3\\xa9\\xc3\\xa9b\\x00\\x00\\xc3\\xa9aa\\xed\\xa0\\x80'.rindex(b'', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00\\ud800中中\\x00éé\\ud800\\x00b\\x00'.rfind('\\ud800\\ud800c\\x00é'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xc3\\xa9b\\xc3\\xa9cc\\xed\\xa0\\x80b\\x00\\xed\\xa0\\x80ac'.endswith(b'\\xc3\\xa9b\\xc3\\xa9cc\\xed\\xa0\\x80b\\x00\\xed\\xa0\\x80ac', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xc3\\xa9b\\xc3\\xa9cc\\xed\\xa0\\x80b\\x00\\xed\\xa0\\x80ac'.count(b'\\xc3\\xa9b\\xc3\\xa9cc\\xed\\xa0\\x80b\\x00\\xed\\xa0\\x80ac', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00\\ud800\\x00cc\\ud800\\x00'.index('ccba\\x00', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ba\\xed\\xa0\\x80a'.find(b'\\xed\\xa0\\x80c\\xe4\\xb8\\xad', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c\\ud800é\\ud800caéb\\ud800a\\ud800\\ud800aé\\ud800'.startswith('é\\ud800caéb\\ud800a\\ud800\\ud800aé\\ud800', None))\nexcept Exception as error: print(type(error).__name__)\n",
              '''-1
False
ValueError
26
False
0
ValueError
0
True
38
-1
True
1
ValueError
-1
False
''')

check_program("try: print('c\\ud800é\\ud800caéb\\ud800a\\ud800\\ud800aé\\ud800'.rindex('é\\ud800caéb\\ud800a\\ud800\\ud800aé\\ud800', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'bc\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80ac\\x00b\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9a\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\xed\\xa0\\x80c\\xed\\xa0\\x80ac\\xc3\\xa9b\\xed\\xa0\\x80a\\xc3\\xa9\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xadca'.index(b'a\\xe4\\xb8\\xad\\xe4\\xb8\\xadc', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('éacéb\\x00b\\ud800\\ud800\\ud800\\ud800éa中éacé中\\ud800cbécb中ac\\ud800a\\x00中\\ud800中c\\x00'.rfind('é\\x00中中', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xada\\x00\\xc3\\xa9bc\\xc3\\xa9\\xed\\xa0\\x80cb\\xe4\\xb8\\xada\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xada\\x00a\\x00cb\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80c\\xc3\\xa9\\xed\\xa0\\x80cccc\\xed\\xa0\\x80a'.find(b'\\xed\\xa0\\x80c\\xc3\\xa9\\xed\\xa0\\x80cccc\\xed\\xa0\\x80a', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中中中bc中bb\\x00\\x00中aéc中éa\\x00é'.endswith('\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80bc'.startswith(b'\\xe4\\xb8\\xad', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80bc'.count(b'\\xe4\\xb8\\xad', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a\\ud800é\\x00\\x00cacécé中c'.rindex('é\\x00\\x00cacécé中c'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ca\\x00ca\\xed\\xa0\\x80bb\\xed\\xa0\\x80b\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80'.index(b'c\\xe4\\xb8\\xad\\xed\\xa0\\x80'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00\\ud800中中c中acbé\\x00中b\\ud800é\\ud800abc'.rfind('éb', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadaab\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xadb\\xc3\\xa9a\\xed\\xa0\\x80aaa\\xc3\\xa9\\xc3\\xa9a\\x00bcb\\xe4\\xb8\\xadbcb\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadcc\\xed\\xa0\\x80bb\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9'.find(b'cb\\xe4\\xb8\\xadbcb\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadcc\\xed\\xa0\\x80bb\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(''.endswith('中é', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xed\\xa0\\x80bbb\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80cc\\x00\\xc3\\xa9\\xe4\\xb8\\xadab\\xed\\xa0\\x80c\\xe4\\xb8\\xadb\\xc3\\xa9\\xc3\\xa9aa\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xad'.startswith(b'b\\x00c\\x00\\xed\\xa0\\x80\\xc3\\xa9', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xed\\xa0\\x80bbb\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80cc\\x00\\xc3\\xa9\\xe4\\xb8\\xadab\\xed\\xa0\\x80c\\xe4\\xb8\\xadb\\xc3\\xa9\\xc3\\xa9aa\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xad'.count(b'b\\x00c\\x00\\xed\\xa0\\x80\\xc3\\xa9', 10000))\nexcept Exception as error: print(type(error).__name__)\n",
              '''2
ValueError
-1
-1
False
False
0
2
ValueError
-1
30
False
False
0
''')

check_program("try: print('\\ud800a\\x00caaéab\\x00中b'.endswith('中b', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00b\\xe4\\xb8\\xadc\\xe4\\xb8\\xadbc\\xed\\xa0\\x80\\xc3\\xa9\\x00a\\xed\\xa0\\x80bb\\xe4\\xb8\\xadbbb\\xed\\xa0\\x80c\\xed\\xa0\\x80ca\\x00\\xe4\\xb8\\xada\\xe4\\xb8\\xadab\\xc3\\xa9\\xc3\\xa9\\x00\\xc3\\xa9\\xe4\\xb8\\xada\\xc3\\xa9\\xed\\xa0\\x80'.startswith(b'\\xed\\xa0\\x80', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00b\\xe4\\xb8\\xadc\\xe4\\xb8\\xadbc\\xed\\xa0\\x80\\xc3\\xa9\\x00a\\xed\\xa0\\x80bb\\xe4\\xb8\\xadbbb\\xed\\xa0\\x80c\\xed\\xa0\\x80ca\\x00\\xe4\\xb8\\xada\\xe4\\xb8\\xadab\\xc3\\xa9\\xc3\\xa9\\x00\\xc3\\xa9\\xe4\\xb8\\xada\\xc3\\xa9\\xed\\xa0\\x80'.count(b'\\xed\\xa0\\x80', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800c中a'.rindex('中ccb\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80a\\xed\\xa0\\x80b\\x00aa\\x00\\x00\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00c'.index(b'c', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bé中\\ud800中中中\\x00'.rfind('cé中\\x00é', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadaa\\x00c\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xadcc\\xe4\\xb8\\xadcca\\xe4\\xb8\\xadcaba\\x00a\\x00cbab'.find(b'', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('éé\\x00\\ud800a\\x00éb中\\x00aéabab中é中a中\\x00\\ud800\\ud800c\\x00'.endswith('é\\x00\\ud800a\\x00éb中\\x00aéabab中é中a中\\x00\\ud800\\ud800c\\x00', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xed\\xa0\\x80\\xe4\\xb8\\xadb\\xc3\\xa9\\xc3\\xa9ccca\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xada\\xc3\\xa9\\xc3\\xa9\\x00\\xed\\xa0\\x80'.startswith(b'\\xe4\\xb8\\xad\\xc3\\xa9c\\xed\\xa0\\x80c', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xed\\xa0\\x80\\xe4\\xb8\\xadb\\xc3\\xa9\\xc3\\xa9ccca\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xada\\xc3\\xa9\\xc3\\xa9\\x00\\xed\\xa0\\x80'.count(b'\\xe4\\xb8\\xad\\xc3\\xa9c\\xed\\xa0\\x80c', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800中c\\x00\\ud800中b\\ud800aé中bé\\x00caéba\\x00c\\x00aécé\\x00\\x00ccbéb\\ud800'.rindex('\\ud800b'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9ba\\xed\\xa0\\x80\\xe4\\xb8\\xadaa\\xe4\\xb8\\xad\\xc3\\xa9ac\\x00b\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80bbcca\\xc3\\xa9\\x00\\x00\\xc3\\xa9b\\xe4\\xb8\\xadbb\\xe4\\xb8\\xad\\xe4\\xb8\\xadcaa\\x00\\xe4\\xb8\\xad\\x00b'.index(b'a\\x00\\xe4\\xb8\\xad\\x00b'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\ud800\\x00\\x00\\x00中cééac中éé\\ud800\\x00a中aa'.rfind('', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'caaa\\x00\\x00\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80bccc\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9'.find(b'\\xed\\xa0\\x80', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\n",
              '''True
False
5
ValueError
21
-1
-1
False
False
0
ValueError
53
20
13
''')

check_program("try: print(b'caaa\\x00\\x00\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80bccc\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9'.index(b'\\xed\\xa0\\x80', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800b\\ud800\\x00中\\x00éa'.find('', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ca\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xadcac\\xc3\\xa9b\\xc3\\xa9\\xed\\xa0\\x80c\\xed\\xa0\\x80\\xc3\\xa9a\\xed\\xa0\\x80ca'.startswith(b'b\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ca\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xadcac\\xc3\\xa9b\\xc3\\xa9\\xed\\xa0\\x80c\\xed\\xa0\\x80\\xc3\\xa9a\\xed\\xa0\\x80ca'.rindex(b'b\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aca中éac\\ud800\\x00é'.rfind('éa', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'abb\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80a\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\x00aaa'.endswith(b'\\xed\\xa0\\x80a\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\x00aaa', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'abb\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80a\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\x00aaa'.count(b'\\xed\\xa0\\x80a\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\x00aaa', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a'.index('中\\x00aa\\x00\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\x00bb\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\x00\\xc3\\xa9\\xc3\\xa9b\\xc3\\xa9\\xed\\xa0\\x80ac\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad\\x00\\x00\\xed\\xa0\\x80a\\xed\\xa0\\x80\\x00c\\xc3\\xa9cb\\xc3\\xa9b\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80c\\xe4\\xb8\\xad'.find(b'\\xe4\\xb8\\xad', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bbé中\\x00中b\\ud800c\\ud800c中é\\ud800中中中\\x00bé\\ud800bcac\\x00cébéébé'.startswith('\\ud800中中中\\x00bé\\ud800bcac\\x00cébéébé', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bbé中\\x00中b\\ud800c\\ud800c中é\\ud800中中中\\x00bé\\ud800bcac\\x00cébéébé'.rindex('\\ud800中中中\\x00bé\\ud800bcac\\x00cébéébé', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xc3\\xa9bcc\\xed\\xa0\\x80cbc\\xe4\\xb8\\xad\\x00\\xc3\\xa9a\\xed\\xa0\\x80\\xc3\\xa9b'.rfind(b'\\xc3\\xa9a', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b\\ud800éaé\\x00'.endswith('é\\ud800\\x00ba'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b\\ud800éaé\\x00'.count('é\\ud800\\x00ba'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80babab\\xc3\\xa9aba'.index(b'a'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a中中cc\\x00ébbbé\\ud800é\\x00\\x00éé\\ud800écaca\\x00acb中\\x00céaéé中cb\\x00'.find('\\ud800ac'))\nexcept Exception as error: print(type(error).__name__)\n",
              '''13
0
False
ValueError
4
False
0
ValueError
5
False
ValueError
16
False
0
0
-1
''')

check_program("try: print(b'c\\xc3\\xa9b\\x00\\xed\\xa0\\x80'.startswith(b'c\\x00\\x00\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xad', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xc3\\xa9b\\x00\\xed\\xa0\\x80'.rindex(b'c\\x00\\x00\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xad', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aé\\x00b\\ud800c\\ud800écaéc\\ud800a中bb中éab\\x00é'.rfind('aé\\x00b\\ud800c\\ud800écaéc\\ud800a中bb中éab\\x00é', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xed\\xa0\\x80accaabcc\\xed\\xa0\\x80\\x00baa\\xed\\xa0\\x80ccb\\xe4\\xb8\\xad'.endswith(b'acab'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xed\\xa0\\x80accaabcc\\xed\\xa0\\x80\\x00baa\\xed\\xa0\\x80ccb\\xe4\\xb8\\xad'.count(b'acab'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中ca\\x00a\\x00c\\ud800c中\\x00\\ud800\\x00中中\\ud800中éacc中b中'.index('\\ud800éc\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00cbb\\x00'.find(b'', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800aab'.startswith('b中中cbb', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800aab'.rindex('b中中cbb', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xc3\\xa9b\\x00abacc\\xe4\\xb8\\xad\\x00'.rfind(b'ca', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a\\x00\\ud800中acébb中中中é中é中中\\x00中中b中'.endswith('中b中', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a\\x00\\ud800中acébb中中中é中é中中\\x00中中b中'.count('中b中', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'aa\\xe4\\xb8\\xad'.index(b'\\xed\\xa0\\x80\\xed\\xa0\\x80b\\xed\\xa0\\x80b\\xed\\xa0\\x80a', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a中\\x00中béé中c'.find('中b\\x00aa中é', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00ca\\x00\\xed\\xa0\\x80ba\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xada\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80a\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00bc\\x00\\xed\\xa0\\x80b'.startswith(b'\\xe4\\xb8\\xada\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80a\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00bc\\x00\\xed\\xa0\\x80b', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00ca\\x00\\xed\\xa0\\x80ba\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xada\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80a\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00bc\\x00\\xed\\xa0\\x80b'.rindex(b'\\xe4\\xb8\\xada\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80a\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00bc\\x00\\xed\\xa0\\x80b', None))\nexcept Exception as error: print(type(error).__name__)\n",
              '''False
ValueError
0
False
0
ValueError
-1
False
ValueError
-1
True
1
ValueError
-1
False
23
''')

check_program("try: print('a中aaab中\\ud800'.rfind('中', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xad'.endswith(b'aa\\xe4\\xb8\\xadbc\\xed\\xa0\\x80\\xc3\\xa9', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xad'.count(b'aa\\xe4\\xb8\\xadbc\\xed\\xa0\\x80\\xc3\\xa9', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中é中中\\x00ééa'.index('', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80bb\\xe4\\xb8\\xad\\xed\\xa0\\x80c\\x00\\x00ccb\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xadc\\xe4\\xb8\\xadba\\xc3\\xa9'.find(b'\\xe4\\xb8\\xadbcb\\xc3\\xa9', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bcéabé'.startswith('\\ud800ccb\\ud800', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bcéabé'.rindex('\\ud800ccb\\ud800', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xe4\\xb8\\xad\\xed\\xa0\\x80cca\\xed\\xa0\\x80\\xc3\\xa9bb'.rfind(b'\\xed\\xa0\\x80cca\\xed\\xa0\\x80\\xc3\\xa9bb', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bc\\x00é\\ud800中écc中中中c\\x00中'.endswith('', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bc\\x00é\\ud800中écc中中中c\\x00中'.count('', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xc3\\xa9\\x00b\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\x00b\\xed\\xa0\\x80b\\x00c\\xe4\\xb8\\xad\\x00\\xc3\\xa9cc\\xc3\\xa9cc\\xed\\xa0\\x80\\x00ba'.index(b'c\\x00\\xed\\xa0\\x80', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b中\\x00c'.find('\\x00c', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xc3\\xa9'.startswith(b'\\x00\\xe4\\xb8\\xadcab\\xed\\xa0\\x80', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xc3\\xa9'.rindex(b'\\x00\\xe4\\xb8\\xadcab\\xed\\xa0\\x80', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b\\x00中éaéé中\\x00b\\ud800a中中'.rfind('中b中a'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\x00caaa\\xe4\\xb8\\xadb\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9a\\x00ba\\xe4\\xb8\\xad\\x00'.endswith(b'\\x00\\x00caaa\\xe4\\xb8\\xadb\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9a\\x00ba\\xe4\\xb8\\xad\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\n",
              '''6
False
0
1
-1
False
ValueError
-1
True
16
ValueError
-1
False
ValueError
-1
True
''')

check_program("try: print(b'\\x00\\x00caaa\\xe4\\xb8\\xadb\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9a\\x00ba\\xe4\\xb8\\xad\\x00'.count(b'\\x00\\x00caaa\\xe4\\xb8\\xadb\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9a\\x00ba\\xe4\\xb8\\xad\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中中bb\\ud800a中baa\\ud800\\ud800中b\\ud800é中c\\ud800b'.index('中\\x00b中éé', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ba\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9a\\xed\\xa0\\x80\\x00'.find(b'', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c\\x00中b中aééba\\x00中中ébé\\ud800éc\\x00\\ud800cbé中aébb'.startswith('bé中aébb', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c\\x00中b中aééba\\x00中中ébé\\ud800éc\\x00\\ud800cbé中aébb'.rindex('bé中aébb', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'cbb\\xed\\xa0\\x80aa\\x00a\\xe4\\xb8\\xad\\x00b\\xc3\\xa9bba\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\xc3\\xa9a\\x00\\xed\\xa0\\x80ca\\xed\\xa0\\x80\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\x00'.rfind(b'b\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xada', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bc\\ud800\\x00\\ud800bé中a\\ud800b\\ud800\\ud800cé中cb\\x00a\\x00ac中\\x00c\\ud800a\\ud800\\ud800é\\ud800\\x00a'.endswith('\\x00\\x00\\ud800cé中b', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bc\\ud800\\x00\\ud800bé中a\\ud800b\\ud800\\ud800cé中cb\\x00a\\x00ac中\\x00c\\ud800a\\ud800\\ud800é\\ud800\\x00a'.count('\\x00\\x00\\ud800cé中b', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80aa\\xe4\\xb8\\xadb\\xed\\xa0\\x80\\xed\\xa0\\x80ac\\x00\\xe4\\xb8\\xad\\x00\\x00bbc\\x00cc\\x00'.index(b'\\x00', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中\\x00cé中bé中\\ud800\\ud800aécb\\x00中ééécc\\x00\\x00中aa\\ud800\\x00abaa\\x00\\x00c\\x00éb'.find('é\\x00c\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\x00\\xe4\\xb8\\xadc\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\xc3\\xa9b\\xe4\\xb8\\xadca\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xc3\\xa9\\x00b\\x00\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9ab\\xc3\\xa9\\xe4\\xb8\\xadc'.startswith(b'c\\xed\\xa0\\x80ab\\xe4\\xb8\\xad\\x00', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\x00\\xe4\\xb8\\xadc\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\xc3\\xa9b\\xe4\\xb8\\xadca\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xc3\\xa9\\x00b\\x00\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9ab\\xc3\\xa9\\xe4\\xb8\\xadc'.rindex(b'c\\xed\\xa0\\x80ab\\xe4\\xb8\\xad\\x00', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aca中a'.rfind('中a', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\x00'.endswith(b'b\\x00b', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\x00'.count(b'b\\x00b', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800\\ud800éca\\x00中é'.index('a\\x00', 10000))\nexcept Exception as error: print(type(error).__name__)\n",
              '''1
ValueError
0
False
ValueError
-1
False
0
17
-1
False
ValueError
3
False
0
ValueError
''')

check_program("try: print(b''.find(b'', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800\\x00中b\\x00c'.startswith('\\ud800\\ud800\\ud800a\\ud800cc', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800\\x00中b\\x00c'.rindex('\\ud800\\ud800\\ud800a\\ud800cc', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ccbbb\\xe4\\xb8\\xadbb\\xc3\\xa9c\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\xc3\\xa9a\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9a'.rfind(b'', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é中\\x00\\ud800中\\ud800\\ud800ébé\\ud800aéa\\ud800\\x00c\\x00\\x00\\ud800cécé中c中\\x00'.endswith('\\ud800中\\ud800\\ud800ébé\\ud800aéa\\ud800\\x00c\\x00\\x00\\ud800cécé中c中\\x00', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é中\\x00\\ud800中\\ud800\\ud800ébé\\ud800aéa\\ud800\\x00c\\x00\\x00\\ud800cécé中c中\\x00'.count('\\ud800中\\ud800\\ud800ébé\\ud800aéa\\ud800\\x00c\\x00\\x00\\ud800cécé中c中\\x00', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00b\\x00\\xe4\\xb8\\xadc\\x00c\\xed\\xa0\\x80a\\xc3\\xa9ba\\x00\\x00c'.index(b'acca', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800cc\\x00\\x00c中中中中\\ud800\\ud800ba中\\ud800éc\\x00\\ud800éac'.find('a\\x00\\ud800中b'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadcbb\\xe4\\xb8\\xad\\x00b\\x00\\x00c\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9c\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\x00cabb\\xc3\\xa9\\xed\\xa0\\x80b\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80aba\\xc3\\xa9\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9c'.startswith(b'', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadcbb\\xe4\\xb8\\xad\\x00b\\x00\\x00c\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9c\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\x00cabb\\xc3\\xa9\\xed\\xa0\\x80b\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80aba\\xc3\\xa9\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9c'.rindex(b'', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ccacéaac\\ud800\\ud800b中aéccé中c\\ud800\\ud800bé中c'.rfind('é中b中c', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xe4\\xb8\\xad\\xc3\\xa9cbbccaa\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80c\\xc3\\xa9b\\xed\\xa0\\x80a\\x00bcbc\\xc3\\xa9\\xe4\\xb8\\xadbc\\x00'.endswith(b'bc\\xed\\xa0\\x80a\\x00', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xe4\\xb8\\xad\\xc3\\xa9cbbccaa\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80c\\xc3\\xa9b\\xed\\xa0\\x80a\\x00bcbc\\xc3\\xa9\\xe4\\xb8\\xadbc\\x00'.count(b'bc\\xed\\xa0\\x80a\\x00', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中bcaé'.index('中bcaé', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'bbbcca\\xc3\\xa9ba\\xc3\\xa9'.find(b'', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cb\\ud800é中中\\x00a'.startswith('\\x00c\\x00\\x00中中c'))\nexcept Exception as error: print(type(error).__name__)\n",
              '''0
False
ValueError
33
False
0
ValueError
-1
True
67
-1
False
0
0
-1
False
''')

check_program("try: print('cb\\ud800é中中\\x00a'.rindex('\\x00c\\x00\\x00中中c'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9c\\xe4\\xb8\\xad\\x00\\x00a\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80cb\\x00\\xe4\\xb8\\xad\\x00'.rfind(b'\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80cb\\x00\\xe4\\xb8\\xad\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(''.endswith('中\\x00é', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(''.count('中\\x00é', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xc3\\xa9ca\\xc3\\xa9\\xed\\xa0\\x80abcca\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9'.index(b'\\x00\\xed\\xa0\\x80c\\xed\\xa0\\x80a', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800é中c\\x00\\x00cb中\\ud800\\x00cébé中bc\\x00cb中\\x00é中a\\x00c\\ud800c\\x00aé\\x00b中b'.find('\\x00b中b', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xed\\xa0\\x80\\xed\\xa0\\x80cc\\xc3\\xa9c\\xc3\\xa9bbcaa\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00c\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad\\x00\\x00a\\xed\\xa0\\x80ac'.startswith(b'c', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xed\\xa0\\x80\\xed\\xa0\\x80cc\\xc3\\xa9c\\xc3\\xa9bbcaa\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00c\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad\\x00\\x00a\\xed\\xa0\\x80ac'.rindex(b'c', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ccc'.rfind('\\x00\\x00\\ud800中', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\xed\\xa0\\x80ac\\x00\\xc3\\xa9\\xc3\\xa9'.endswith(b'\\xc3\\xa9', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\xed\\xa0\\x80ac\\x00\\xc3\\xa9\\xc3\\xa9'.count(b'\\xc3\\xa9', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c\\x00\\x00éc中中\\ud800cc\\x00中cé'.index('b中中\\ud800', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00b\\xc3\\xa9\\xe4\\xb8\\xad\\x00b\\x00\\xed\\xa0\\x80'.find(b'', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a\\x00\\x00cc\\ud800écc中b\\ud800ébaé中a\\x00'.startswith('é中a\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a\\x00\\x00cc\\ud800écc中b\\ud800ébaé中a\\x00'.rindex('é中a\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'bb\\x00\\xe4\\xb8\\xad\\x00\\x00\\xed\\xa0\\x80\\xc3\\xa9aaa\\xc3\\xa9cc\\x00\\xe4\\xb8\\xadc\\x00\\xc3\\xa9bc\\xc3\\xa9\\xe4\\xb8\\xadccc\\xed\\xa0\\x80c\\xed\\xa0\\x80ac\\xc3\\xa9c\\xe4\\xb8\\xadc'.rfind(b'\\xed\\xa0\\x80c\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad'))\nexcept Exception as error: print(type(error).__name__)\n",
              '''ValueError
9
False
0
ValueError
-1
False
44
-1
False
0
ValueError
11
False
15
-1
''')

check_program("try: print('cbé\\x00\\ud800中écb\\ud800a中ba\\ud800中\\ud800\\ud800'.endswith('', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cbé\\x00\\ud800中écb\\ud800a中ba\\ud800中\\ud800\\ud800'.count('', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ac\\xc3\\xa9ba\\xed\\xa0\\x80a\\xe4\\xb8\\xad'.index(b'\\xe4\\xb8\\xad', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b中abaa\\ud800\\x00'.find('c\\ud800', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xc3\\xa9baab\\x00\\xe4\\xb8\\xad\\x00bac\\x00c\\xc3\\xa9\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xadc'.startswith(b'c', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xc3\\xa9baab\\x00\\xe4\\xb8\\xad\\x00bac\\x00c\\xc3\\xa9\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xadc'.rindex(b'c', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800ba\\ud800b\\ud800a\\x00bb\\ud800\\ud800aacé\\x00a中中c中caac\\ud800\\ud800é中ca中'.rfind('中c中caac\\ud800\\ud800é中ca中', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80abb\\xed\\xa0\\x80\\x00\\x00ca\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00aac\\xc3\\xa9\\xed\\xa0\\x80ba'.endswith(b'', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80abb\\xed\\xa0\\x80\\x00\\x00ca\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00aac\\xc3\\xa9\\xed\\xa0\\x80ba'.count(b'', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00acbc'.index('中bé中中\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xe4\\xb8\\xada\\x00\\xe4\\xb8\\xad\\xc3\\xa9cc\\x00cc\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9\\x00ba\\x00\\x00\\xed\\xa0\\x80ca'.find(b'\\xc3\\xa9\\xe4\\xb8\\xada\\x00\\xe4\\xb8\\xad\\xc3\\xa9cc\\x00cc\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9\\x00ba\\x00\\x00\\xed\\xa0\\x80ca', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cc中\\ud800\\ud800ca\\x00中aé\\ud800bé中bab中éb\\x00'.startswith('acé', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cc中\\ud800\\ud800ca\\x00中aé\\ud800bé中bab中éb\\x00'.rindex('acé', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\x00\\xc3\\xa9c\\xe4\\xb8\\xadb\\x00ccb'.rfind(b'cc', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中é中aba\\x00bb\\x00a中\\ud800中caa\\ud800é中\\ud800aca'.endswith('中\\ud800aca', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中é中aba\\x00bb\\x00a中\\ud800中caa\\ud800é中\\ud800aca'.count('中\\ud800aca', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\n",
              '''True
19
ValueError
-1
False
39
19
True
33
ValueError
0
False
ValueError
19
True
1
''')

check_program("try: print(b'a\\xed\\xa0\\x80cbcbc\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\xc3\\xa9'.index(b'\\x00c\\xed\\xa0\\x80b\\x00cc', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a\\ud800babb\\x00b\\ud800\\ud800b\\ud800cc\\ud800\\ud800\\ud800aéa\\ud800a中\\x00cé\\ud800c\\ud800\\x00aaé\\ud800ééc\\ud800中'.rfind('中\\ud800a\\ud800a', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\xed\\xa0\\x80c\\xed\\xa0\\x80\\x00abccab\\xed\\xa0\\x80'.find(b''))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aa\\x00aaaaé\\ud800c\\ud800\\x00cb\\x00cb中\\ud800b\\x00中中中中中中é\\ud800a\\ud800\\ud800ba\\x00\\ud800\\x00a'.endswith('', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9b\\xc3\\xa9\\xe4\\xb8\\xad\\x00ca\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadaa\\xc3\\xa9ac\\xe4\\xb8\\xad\\xe4\\xb8\\xad'.startswith(b'\\x00\\xed\\xa0\\x80\\xc3\\xa9c\\x00b', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9b\\xc3\\xa9\\xe4\\xb8\\xad\\x00ca\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadaa\\xc3\\xa9ac\\xe4\\xb8\\xad\\xe4\\xb8\\xad'.count(b'\\x00\\xed\\xa0\\x80\\xc3\\xa9c\\x00b', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é中cb\\ud800c中\\ud800béc\\ud800'.rindex('中\\ud800béc\\ud800', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadcc\\x00b\\x00babc\\xed\\xa0\\x80\\xc3\\xa9ca\\x00c\\x00\\xc3\\xa9ab\\x00c\\x00\\xe4\\xb8\\xad\\x00ba\\x00\\xc3\\xa9\\xe4\\xb8\\xadb\\x00\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9a\\x00'.index(b'aa', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00中\\x00é\\x00b\\ud800中c中\\x00ac中\\ud800'.rfind('\\x00中', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9c\\xc3\\xa9c\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xc3\\xa9a\\x00c'.find(b'c\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xc3\\xa9a\\x00c'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00\\ud800bcc中\\x00中éa\\x00c'.endswith('\\ud800\\ud800é\\ud800b', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80b'.startswith(b'a\\xed\\xa0\\x80b', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80b'.count(b'a\\xed\\xa0\\x80b', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00é\\x00\\x00ab\\x00中\\x00aaé\\x00\\ud800a中éé\\ud800é\\ud800\\x00é\\ud800\\ud800\\ud800a\\x00\\x00a'.rindex('\\x00\\ud800a中éé\\ud800é\\ud800\\x00é\\ud800\\ud800\\ud800a\\x00\\x00a'))\nexcept Exception as error: print(type(error).__name__)\n",
              '''ValueError
-1
0
True
False
0
ValueError
ValueError
-1
12
False
False
0
12
''')

check_program("try: print(b'\\xc3\\xa9\\xed\\xa0\\x80c'.startswith(b'\\x00\\xe4\\xb8\\xada\\xe4\\xb8\\xad\\xc3\\xa9', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xed\\xa0\\x80c'.count(b'\\x00\\xe4\\xb8\\xada\\xe4\\xb8\\xad\\xc3\\xa9', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00\\x00中a'.rindex('\\x00éa', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadb\\xe4\\xb8\\xada\\xc3\\xa9b\\xed\\xa0\\x80b\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80bc\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xadcbc\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00'.index(b'\\xc3\\xa9\\xe4\\xb8\\xadcbc\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中acéab\\ud800ac\\ud800'.rfind('\\ud800a\\ud800', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ca\\xc3\\xa9\\x00\\xc3\\xa9\\xed\\xa0\\x80aa\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9c\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9c\\xe4\\xb8\\xadc\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80'.find(b'acaa', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é中a\\x00中\\ud800c\\ud800\\ud800\\ud800\\ud800\\x00bé\\x00ébéa\\x00ccé\\x00\\x00\\ud800中éb\\ud800b'.endswith('béa\\x00ccé\\x00\\x00\\ud800中éb\\ud800b', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ca\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\x00\\x00\\xc3\\xa9abbcb\\x00a\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9b\\xc3\\xa9a\\x00bb\\xed\\xa0\\x80b\\xe4\\xb8\\xada\\xed\\xa0\\x80'.startswith(b'\\xe4\\xb8\\xad', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ca\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\x00\\x00\\xc3\\xa9abbcb\\x00a\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9b\\xc3\\xa9a\\x00bb\\xed\\xa0\\x80b\\xe4\\xb8\\xada\\xed\\xa0\\x80'.count(b'\\xe4\\xb8\\xad', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bcb\\ud800c\\x00'.rindex('b', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xc3\\xa9b\\x00\\xe4\\xb8\\xadc\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80acc\\x00a\\xed\\xa0\\x80cbb\\x00\\xed\\xa0\\x80\\x00\\xc3\\xa9b\\xed\\xa0\\x80b\\xed\\xa0\\x80\\xc3\\xa9a'.index(b'b\\xed\\xa0\\x80b\\xed\\xa0\\x80\\xc3\\xa9a', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00b\\x00ba中a\\x00bc\\x00ca\\ud800c中中a中caéc中\\ud800éébc\\x00\\ud800a\\x00'.rfind('\\ud800baba'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9aa\\xc3\\xa9cb\\xed\\xa0\\x80'.find(b'\\xe4\\xb8\\xad\\xc3\\xa9', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ébbé中ca中中aaba\\ud800\\ud800'.endswith('bé中ca中中aaba\\ud800\\ud800', 0))\nexcept Exception as error: print(type(error).__name__)\n",
              '''False
0
ValueError
32
-1
-1
False
False
0
2
ValueError
-1
-1
True
''')
