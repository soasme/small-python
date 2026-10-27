# spec: PLS-315 23.1
# description: Programs on string search methods, each with the output CPython 3.15 gives.
from harness import *

check_program("try: print(b'a\\xed\\xa0\\x80b\\x00\\xc3\\xa9ac\\xed\\xa0\\x80\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\x00\\x00a\\xc3\\xa9ca\\xc3\\xa9bba\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9bb\\x00aa\\xc3\\xa9\\xed\\xa0\\x80'.startswith(b'\\x00b\\xe4\\xb8\\xad', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xed\\xa0\\x80b\\x00\\xc3\\xa9ac\\xed\\xa0\\x80\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\x00\\x00a\\xc3\\xa9ca\\xc3\\xa9bba\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9bb\\x00aa\\xc3\\xa9\\xed\\xa0\\x80'.rindex(b'\\x00b\\xe4\\xb8\\xad', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c\\x00a中中中caa中中\\x00a'.rfind('b中ac', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ca\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9bc\\xc3\\xa9\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9ab\\xed\\xa0\\x80b'.endswith(b'\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9ab\\xed\\xa0\\x80b', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ca\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9bc\\xc3\\xa9\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9ab\\xed\\xa0\\x80b'.count(b'\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9ab\\xed\\xa0\\x80b', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00c\\x00中\\ud800a中中\\x00\\ud800c中éaéc\\x00ccéca\\x00\\ud800\\ud800中baéébé'.index('cb'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xed\\xa0\\x80\\x00b\\xc3\\xa9a\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xadba\\x00\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\x00c\\xe4\\xb8\\xadabb\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xadb\\xe4\\xb8\\xadb'.find(b'\\x00', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00ébb\\x00中\\x00中baé\\ud800中ca\\x00é\\x00b'.startswith('a\\x00é\\x00b', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00ébb\\x00中\\x00中baé\\ud800中ca\\x00é\\x00b'.rindex('a\\x00é\\x00b', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00b\\x00cb\\x00\\xc3\\xa9\\xc3\\xa9c\\x00\\xe4\\xb8\\xadb\\xed\\xa0\\x80b\\xed\\xa0\\x80c\\xc3\\xa9ab'.rfind(b'\\x00b\\x00\\xed\\xa0\\x80'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800'.endswith('c\\ud800', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800'.count('c\\ud800', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\x00bb\\xc3\\xa9a\\xe4\\xb8\\xadb\\x00ba\\xc3\\xa9b\\xc3\\xa9ac\\xc3\\xa9'.index(b'b\\xc3\\xa9ac\\xc3\\xa9', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中\\x00中c中b中中\\x00\\ud800\\ud800c\\x00c中ca\\ud800中cb\\ud800中c'.find('aa中', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\x00bab\\xed\\xa0\\x80b\\xc3\\xa9ac\\x00c\\x00b'.startswith(b'b\\xe4\\xb8\\xad\\x00c\\x00\\xc3\\xa9'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\x00bab\\xed\\xa0\\x80b\\xc3\\xa9ac\\x00c\\x00b'.rindex(b'b\\xe4\\xb8\\xad\\x00c\\x00\\xc3\\xa9'))\nexcept Exception as error: print(type(error).__name__)\n",
              '''False
ValueError
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
18
-1
False
ValueError
''')

check_program("try: print('\\ud800béc\\x00cbbé\\ud800中中c\\x00abc'.rfind('中c\\x00abc', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00c\\x00\\xe4\\xb8\\xadb\\xc3\\xa9a\\xe4\\xb8\\xadaa\\xc3\\xa9a\\xe4\\xb8\\xadc\\xc3\\xa9a\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xada\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00c\\xed\\xa0\\x80b\\xe4\\xb8\\xada\\xe4\\xb8\\xadac'.find(b'\\x00a\\x00cca\\xe4\\xb8\\xad', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中éaaab\\ud800'.endswith('aéac\\ud800', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80aaa\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00ba'.startswith(b'\\xed\\xa0\\x80\\x00ba', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80aaa\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00ba'.count(b'\\xed\\xa0\\x80\\x00ba', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中中écc\\x00b中éébba\\x00中\\ud800\\ud800\\x00ééécabé\\ud800b\\x00a\\x00\\x00bbé'.rindex('中c\\x00\\x00\\x00c', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9bcc\\xe4\\xb8\\xadb\\xed\\xa0\\x80\\xc3\\xa9\\x00a\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xc3\\xa9\\x00a\\xed\\xa0\\x80\\x00a\\xed\\xa0\\x80c\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xc3\\xa9\\x00\\xc3\\xa9\\x00\\xed\\xa0\\x80ba\\xc3\\xa9b\\xc3\\xa9'.index(b'', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('éb中\\x00\\ud800c\\x00a\\x00a\\x00'.rfind('éb中\\x00\\ud800c\\x00a\\x00a\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xe4\\xb8\\xad'.find(b'\\xed\\xa0\\x80', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中a中é中abacbb中中\\x00a\\x00cbccééa中ccb\\ud800中\\x00中aaé\\ud800aaéb'.endswith('béa', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9'.startswith(b'\\xc3\\xa9', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9'.count(b'\\xc3\\xa9', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800a'.rindex('\\x00bcéc中', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9c\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9b\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00\\xc3\\xa9b\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xada\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xadb\\xc3\\xa9\\x00c\\x00cc\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9c'.index(b'ba\\xc3\\xa9\\x00\\x00\\xed\\xa0\\x80a', None))\nexcept Exception as error: print(type(error).__name__)\n",
              '''-1
-1
False
False
1
ValueError
65
0
-1
False
False
1
ValueError
ValueError
''')

check_program("try: print(b'\\xc3\\xa9\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9c\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9b\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00\\xc3\\xa9b\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xada\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xadb\\xc3\\xa9\\x00c\\x00cc\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9c'.count(b'ba\\xc3\\xa9\\x00\\x00\\xed\\xa0\\x80a', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('céb\\ud800cab\\x00\\x00b\\x00a中\\ud800c\\ud800b\\x00中éé\\ud800a中\\ud800\\x00éc\\x00中\\ud800\\ud800b'.rindex('中\\ud800c\\ud800b\\x00中éé\\ud800a中\\ud800\\x00éc\\x00中\\ud800\\ud800b', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'bc\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\xc3\\xa9cbc\\xed\\xa0\\x80\\xe4\\xb8\\xadbca\\xe4\\xb8\\xadb\\xed\\xa0\\x80\\xc3\\xa9a'.index(b'a\\xc3\\xa9c\\xc3\\xa9aac', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cc\\x00中cbéébc\\x00\\x00\\x00ééba中\\x00a\\x00\\x00cc\\ud800\\x00c\\ud800\\ud800b'.rfind('', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xe4\\xb8\\xadbabbc\\xed\\xa0\\x80\\xed\\xa0\\x80caccb\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00'.find(b'\\x00', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cbabccba中écé\\x00é中\\x00é中a\\ud800c中c\\ud800ééé\\x00cé\\ud800é\\x00\\x00'.endswith('éc', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\x00\\x00\\xc3\\xa9\\xe4\\xb8\\xadbc\\x00\\xe4\\xb8\\xadb\\xc3\\xa9\\xc3\\xa9b\\x00\\xc3\\xa9\\xe4\\xb8\\xadab\\xc3\\xa9b\\xc3\\xa9\\x00\\xc3\\xa9\\x00a\\x00\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9'.startswith(b'\\xc3\\xa9\\x00\\xc3\\xa9\\xe4\\xb8\\xadb', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\x00\\x00\\xc3\\xa9\\xe4\\xb8\\xadbc\\x00\\xe4\\xb8\\xadb\\xc3\\xa9\\xc3\\xa9b\\x00\\xc3\\xa9\\xe4\\xb8\\xadab\\xc3\\xa9b\\xc3\\xa9\\x00\\xc3\\xa9\\x00a\\x00\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9'.count(b'\\xc3\\xa9\\x00\\xc3\\xa9\\xe4\\xb8\\xadb', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('aa\\ud800中中a\\ud800baa\\ud800\\x00中中\\ud800é'.rindex('aa\\ud800中中a\\ud800baa\\ud800\\x00中中\\ud800é'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xed\\xa0\\x80aabc\\xc3\\xa9c\\xc3\\xa9c\\x00\\x00a\\xe4\\xb8\\xadc\\xed\\xa0\\x80c\\x00b\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\x00'.index(b'\\xc3\\xa9b\\x00a', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800\\x00\\x00ééccécc中é'.rfind('\\ud800c', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xc3\\xa9b\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\xc3\\xa9caa\\xed\\xa0\\x80a\\x00c\\x00acc\\xed\\xa0\\x80acca\\x00ab\\xed\\xa0\\x80\\xc3\\xa9ccc\\xe4\\xb8\\xadcc\\xe4\\xb8\\xadc\\xc3\\xa9c'.find(b'ca\\x00ab\\xed\\xa0\\x80\\xc3\\xa9ccc\\xe4\\xb8\\xadcc\\xe4\\xb8\\xadc\\xc3\\xa9c', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('éc中\\ud800éa\\ud800céa\\x00b中b\\x00ca\\x00b\\x00ac'.endswith('\\ud800'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ab\\xe4\\xb8\\xadaa'.startswith(b'\\xe4\\xb8\\xada'))\nexcept Exception as error: print(type(error).__name__)\n",
              '''0
ValueError
ValueError
30
33
False
False
0
0
ValueError
-1
-1
False
False
''')

check_program("try: print(b'ab\\xe4\\xb8\\xadaa'.find(b'\\xe4\\xb8\\xada'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cbcac\\ud800é中ba\\ud800\\ud800中\\x00中ccaa\\x00ba'.startswith('ccaa\\x00ba', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cbcac\\ud800é中ba\\ud800\\ud800中\\x00中ccaa\\x00ba'.rindex('ccaa\\x00ba', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xc3\\xa9c\\xc3\\xa9b\\xc3\\xa9c'.rfind(b'\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800中ab\\x00中\\x00a中\\x00b\\x00'.endswith('b\\ud800\\x00c中', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800中ab\\x00中\\x00a中\\x00b\\x00'.count('b\\ud800\\x00c中', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'bc'.index(b'', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bé\\x00中ac中cbca\\ud800\\ud800中bbb\\x00\\x00éé\\x00\\ud800b中ab\\ud800a\\ud800é'.find('中', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xc3\\xa9cbc\\xc3\\xa9aaa\\xe4\\xb8\\xadbb\\x00\\xed\\xa0\\x80a\\xe4\\xb8\\xadb\\x00b\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\xc3\\xa9b\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\x00caa\\xed\\xa0\\x80'.startswith(b'b\\x00\\xc3\\xa9\\xe4\\xb8\\xad'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xc3\\xa9cbc\\xc3\\xa9aaa\\xe4\\xb8\\xadbb\\x00\\xed\\xa0\\x80a\\xe4\\xb8\\xadb\\x00b\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\xc3\\xa9b\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\x00caa\\xed\\xa0\\x80'.rindex(b'b\\x00\\xc3\\xa9\\xe4\\xb8\\xad'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00c\\x00é\\x00\\ud800c中a\\ud800\\x00中中'.rfind('\\x00\\ud800c中a\\ud800\\x00中中', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xed\\xa0\\x80c\\xed\\xa0\\x80\\xe4\\xb8\\xada\\xc3\\xa9\\xc3\\xa9c\\xe4\\xb8\\xad\\x00\\x00\\x00\\xc3\\xa9\\xe4\\xb8\\xadba\\x00\\xe4\\xb8\\xadb\\xc3\\xa9b\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadbc'.endswith(b'\\xc3\\xa9bc\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xed\\xa0\\x80c\\xed\\xa0\\x80\\xe4\\xb8\\xada\\xc3\\xa9\\xc3\\xa9c\\xe4\\xb8\\xad\\x00\\x00\\x00\\xc3\\xa9\\xe4\\xb8\\xadba\\x00\\xe4\\xb8\\xadb\\xc3\\xa9b\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadbc'.count(b'\\xc3\\xa9bc\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800c中a中\\ud800é\\x00éé\\ud800b\\x00ééccca\\ud800éabé'.index('中', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadaac\\xed\\xa0\\x80b\\xe4\\xb8\\xad\\xc3\\xa9c\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00cc'.find(b'c', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bb\\ud800'.startswith('cb中\\ud800中c中', -3, -1))\nexcept Exception as error: print(type(error).__name__)\n",
              '''2
False
15
-1
False
0
0
3
False
ValueError
4
False
0
ValueError
5
False
''')

check_program("try: print('bb\\ud800'.rindex('cb中\\ud800中c中', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xed\\xa0\\x80b\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xad'.rfind(b'\\xc3\\xa9c\\xed\\xa0\\x80', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(''.endswith('', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(''.count('', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b''.index(b'\\x00\\xe4\\xb8\\xadcb\\x00', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('b\\x00éb中baa\\x00\\x00\\ud800a中aa\\ud800cb中\\x00中abcé\\x00c中\\x00a中'.find('bc中中c', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\xed\\xa0\\x80a\\x00c\\xe4\\xb8\\xadc\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00'.startswith(b'\\xed\\xa0\\x80\\xed\\xa0\\x80a\\x00c\\xe4\\xb8\\xadc\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\xed\\xa0\\x80a\\x00c\\xe4\\xb8\\xadc\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00'.rindex(b'\\xed\\xa0\\x80\\xed\\xa0\\x80a\\x00c\\xe4\\xb8\\xadc\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('béac中c中\\x00aaac\\x00éb\\x00\\x00cc\\x00中bc\\x00ca中中éééé\\x00é中中ac中'.rfind('bb\\x00\\ud800', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00\\x00\\x00aac\\xc3\\xa9c\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9c\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80acbbaac\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80'.endswith(b'\\xe4\\xb8\\xada\\xed\\xa0\\x80', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00\\x00\\x00aac\\xc3\\xa9c\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9c\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80acbbaac\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80'.count(b'\\xe4\\xb8\\xada\\xed\\xa0\\x80', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c\\ud800b中aé中'.index('b中aé中', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ca\\x00c\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\xe4\\xb8\\xadb\\xe4\\xb8\\xad'.find(b'\\xe4\\xb8\\xadc\\xe4\\xb8\\xadb\\xed\\xa0\\x80\\xed\\xa0\\x80', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800bc\\ud800中中bcc'.startswith('a\\ud800\\ud800c\\ud800', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800bc\\ud800中中bcc'.rindex('a\\ud800\\ud800c\\ud800', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\x00c\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xadcc\\xc3\\xa9cc\\xed\\xa0\\x80b\\x00cabac\\x00\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80c\\x00\\xc3\\xa9\\xc3\\xa9a\\xed\\xa0\\x80\\x00b\\x00a'.rfind(b'ac\\x00\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80c\\x00\\xc3\\xa9\\xc3\\xa9a\\xed\\xa0\\x80\\x00b\\x00a', 0))\nexcept Exception as error: print(type(error).__name__)\n",
              '''ValueError
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
ValueError
-1
False
ValueError
27
''')

check_program("try: print('ab中中bbbééc\\ud800c\\ud800éébéb\\ud800中b\\ud800\\x00é\\x00a\\x00c中bcc\\ud800\\ud800'.endswith('bc', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ab中中bbbééc\\ud800c\\ud800éébéb\\ud800中b\\ud800\\x00é\\x00a\\x00c中bcc\\ud800\\ud800'.count('bc', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ac\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\x00'.index(b'\\xe4\\xb8\\xadc\\x00c', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\ud800éb中b中ccécaca\\x00cacaabaé中c中a中\\x00\\x00cé\\ud800ba'.find('中c中a中\\x00\\x00cé\\ud800ba', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9acba\\xe4\\xb8\\xadc\\x00\\xed\\xa0\\x80ccb\\xed\\xa0\\x80bcbb\\xed\\xa0\\x80\\xed\\xa0\\x80'.startswith(b'\\xed\\xa0\\x80\\x00c', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9acba\\xe4\\xb8\\xadc\\x00\\xed\\xa0\\x80ccb\\xed\\xa0\\x80bcbb\\xed\\xa0\\x80\\xed\\xa0\\x80'.rindex(b'\\xed\\xa0\\x80\\x00c', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cb\\ud800b\\ud800béaéc中é'.rfind('ééé中é\\x00', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9'.endswith(b'', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9'.count(b'', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\ud800bc\\x00cé中中cc\\ud800'.index('bb', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00b\\xe4\\xb8\\xad\\x00c\\xc3\\xa9\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xada\\x00ca\\xe4\\xb8\\xadc\\xc3\\xa9\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xc3\\xa9\\xe4\\xb8\\xadc\\x00\\xc3\\xa9bac\\x00\\xc3\\xa9\\xe4\\xb8\\xadcbbb\\x00ba'.find(b'ccc\\xe4\\xb8\\xad'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ébb\\x00c\\x00a中aaaé\\ud800中\\ud800a中a中é\\x00\\ud800\\ud800é\\ud800é中cba\\x00中\\ud800b\\x00b'.startswith('\\x00b', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ébb\\x00c\\x00a中aaaé\\ud800中\\ud800a中a中é\\x00\\ud800\\ud800é\\ud800é中cba\\x00中\\ud800b\\x00b'.rindex('\\x00b', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b''.rfind(b'\\xed\\xa0\\x80a\\x00a\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bc中\\ud800中c\\x00中\\ud800中ébéa中bbccé'.endswith('c中é中\\x00中', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('bc中\\ud800中c\\x00中\\ud800中ébéa中bbccé'.count('c中é中\\x00中', -3, -1))\nexcept Exception as error: print(type(error).__name__)\n",
              '''False
0
ValueError
23
False
ValueError
-1
True
1
ValueError
-1
False
34
-1
False
0
''')

check_program("try: print(b'\\x00\\xc3\\xa9\\xed\\xa0\\x80c\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xadc\\xe4\\xb8\\xadba\\x00\\x00\\xc3\\xa9\\x00\\x00\\xed\\xa0\\x80b\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80ca\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00a\\xed\\xa0\\x80\\x00\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9a\\xc3\\xa9'.index(b'\\xc3\\xa9\\xed\\xa0\\x80c\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xadc\\xe4\\xb8\\xadba\\x00\\x00\\xc3\\xa9\\x00\\x00\\xed\\xa0\\x80b\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80ca\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00a\\xed\\xa0\\x80\\x00\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9a\\xc3\\xa9', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800a\\ud800éaa中\\x00c\\x00caé中éaéa中\\x00\\x00bc\\ud800é\\x00中ca'.find('', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b''.startswith(b'b\\x00b\\xe4\\xb8\\xad\\x00\\xc3\\xa9', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b''.rindex(b'b\\x00b\\xe4\\xb8\\xad\\x00\\xc3\\xa9', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cc'.rfind('c'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\x00acc\\xe4\\xb8\\xad\\xed\\xa0\\x80'.endswith(b'a\\xc3\\xa9\\xe4\\xb8\\xad\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\x00acc\\xe4\\xb8\\xad\\xed\\xa0\\x80'.count(b'a\\xc3\\xa9\\xe4\\xb8\\xad\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cbc\\x00a中cécbbbb中aaacc'.index('\\ud800a\\ud800\\ud800', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00'.find(b'\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800cé\\ud800\\ud800ééééébcéa\\x00éé'.startswith('b中\\ud800', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800cé\\ud800\\ud800ééééébcéa\\x00éé'.rindex('b中\\ud800', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\x00\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xc3\\xa9cbac\\xc3\\xa9cb\\xe4\\xb8\\xadbabbb\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9c\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80aa\\xc3\\xa9ac'.rfind(b'\\xe4\\xb8\\xada', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00中bacc中c\\x00éb中ébc\\ud800\\x00\\ud800a\\ud800aa\\x00bc'.endswith('c中c\\x00éb中ébc\\ud800\\x00\\ud800a\\ud800aa\\x00bc', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00中bacc中c\\x00éb中ébc\\ud800\\x00\\ud800a\\ud800aa\\x00bc'.count('c中c\\x00éb中ébc\\ud800\\x00\\ud800a\\ud800aa\\x00bc', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'bc\\xc3\\xa9\\x00c\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\x00bb\\xc3\\xa9b\\xe4\\xb8\\xadbb\\xc3\\xa9ba\\xed\\xa0\\x80b\\x00a\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80ca'.index(b'\\xed\\xa0\\x80b\\xed\\xa0\\x80\\xed\\xa0\\x80', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('acé\\ud800ab\\ud800b\\ud800中\\ud800'.find('éé', -3, -1))\nexcept Exception as error: print(type(error).__name__)\n",
              '''ValueError
0
False
ValueError
1
False
0
ValueError
-1
False
ValueError
-1
False
0
ValueError
-1
''')

check_program("try: print(b'\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00baa\\x00ba\\x00\\x00b\\xc3\\xa9c\\xc3\\xa9\\xc3\\xa9\\x00\\xed\\xa0\\x80'.startswith(b'a\\x00\\x00b\\xc3\\xa9c\\xc3\\xa9\\xc3\\xa9\\x00\\xed\\xa0\\x80', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00baa\\x00ba\\x00\\x00b\\xc3\\xa9c\\xc3\\xa9\\xc3\\xa9\\x00\\xed\\xa0\\x80'.rindex(b'a\\x00\\x00b\\xc3\\xa9c\\xc3\\xa9\\xc3\\xa9\\x00\\xed\\xa0\\x80', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中\\x00\\ud800ééaccba\\x00acb\\x00é中\\ud800é'.rfind('中中\\ud800cc', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xc3\\xa9b\\x00b\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9a\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9cc\\xc3\\xa9'.endswith(b'\\xc3\\xa9b'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xc3\\xa9b\\x00b\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xc3\\xa9a\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9cc\\xc3\\xa9'.count(b'\\xc3\\xa9b'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('écc\\x00b\\x00中\\ud800\\x00é'.index('b\\x00中\\ud800\\x00é', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80\\xc3\\xa9'.find(b'c\\xe4\\xb8\\xad\\xc3\\xa9\\x00', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c'.startswith('\\x00\\x00c\\x00', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c'.rindex('\\x00\\x00c\\x00', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'aa'.rfind(b'', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('écb中中\\x00aé\\ud800中a\\x00é中\\ud800bécbb\\x00b\\ud800\\ud800\\ud800c'.endswith('', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('écb中中\\x00aé\\ud800中a\\x00é中\\ud800bécbb\\x00b\\ud800\\ud800\\ud800c'.count('', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9cb\\xe4\\xb8\\xadaa'.index(b'', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00b\\x00ééc\\x00\\ud800é中abbabaéé\\ud800caa\\x00aa\\x00'.find('中abbabaéé\\ud800caa\\x00aa\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xed\\xa0\\x80\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\x00\\xc3\\xa9b\\xed\\xa0\\x80\\xc3\\xa9\\x00ab\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80b\\x00\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xadbbcbccc'.startswith(b'\\x00c\\xc3\\xa9', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xed\\xa0\\x80\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\x00\\xc3\\xa9b\\xed\\xa0\\x80\\xc3\\xa9\\x00ab\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80b\\x00\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00\\xe4\\xb8\\xadbbcbccc'.rindex(b'\\x00c\\xc3\\xa9', 1, 1))\nexcept Exception as error: print(type(error).__name__)\n",
              '''False
18
-1
False
1
4
-1
False
ValueError
2
True
3
6
9
False
ValueError
''')

check_program("try: print('中\\x00a中acé\\ud800aabb\\ud800\\x00\\ud800中cb\\ud800\\x00a中é\\x00\\x00a中中b\\x00\\ud800é中b\\ud800'.rfind('baac', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadb\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9'.endswith(b'\\xe4\\xb8\\xad\\xc3\\xa9', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xed\\xa0\\x80\\xe4\\xb8\\xadb\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9'.count(b'\\xe4\\xb8\\xad\\xc3\\xa9', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中\\ud800\\ud800中\\ud800c\\x00ca中cb\\ud800中中ca\\x00\\ud800c\\ud800\\ud800b\\x00\\x00a中中\\x00c'.index('中', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xe4\\xb8\\xadbba\\xe4\\xb8\\xad\\x00b\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\xe4\\xb8\\xadc\\x00'.find(b'\\xed\\xa0\\x80\\x00\\xc3\\xa9ca\\xe4\\xb8\\xad', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800中'.startswith('\\ud800中', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800中'.rindex('\\ud800中', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadbbb\\x00\\x00a\\x00\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80bcb\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xed\\xa0\\x80cc\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xad'.rfind(b'\\xed\\xa0\\x80bbcc', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c\\ud800cba中bbaaéb\\ud800b中b\\ud800\\ud800\\ud800'.endswith('céb\\x00中中\\ud800', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c\\ud800cba中bbaaéb\\ud800b中b\\ud800\\ud800\\ud800'.count('céb\\x00中中\\ud800', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\xc3\\xa9\\xc3\\xa9\\xed\\xa0\\x80abac\\xed\\xa0\\x80cb\\x00b\\x00ac\\xed\\xa0\\x80\\xed\\xa0\\x80b'.index(b'b', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800éé\\ud800\\ud800'.find('\\x00cé\\ud800', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xe4\\xb8\\xad\\xc3\\xa9b\\xc3\\xa9\\xe4\\xb8\\xada\\xc3\\xa9bbc\\xc3\\xa9\\x00c\\x00a\\x00cb\\x00\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9c\\xe4\\xb8\\xad\\x00b'.startswith(b'\\x00', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xe4\\xb8\\xad\\xc3\\xa9b\\xc3\\xa9\\xe4\\xb8\\xada\\xc3\\xa9bbc\\xc3\\xa9\\x00c\\x00a\\x00cb\\x00\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9c\\xe4\\xb8\\xad\\x00b'.rindex(b'\\x00', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中éb\\ud800béc\\x00'.rfind('béc\\x00', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xc3\\xa9\\x00ab\\xed\\xa0\\x80\\xc3\\xa9bb\\xc3\\xa9a\\x00\\x00\\xed\\xa0\\x80cca\\x00ab\\x00\\xed\\xa0\\x80b\\xc3\\xa9bccabb\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9a\\xe4\\xb8\\xad'.endswith(b'\\xc3\\xa9b\\x00\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\n",
              '''-1
False
0
0
-1
True
0
-1
False
0
ValueError
-1
False
45
4
False
''')

check_program("try: print(b'\\xc3\\xa9\\xc3\\xa9\\x00ab\\xed\\xa0\\x80\\xc3\\xa9bb\\xc3\\xa9a\\x00\\x00\\xed\\xa0\\x80cca\\x00ab\\x00\\xed\\xa0\\x80b\\xc3\\xa9bccabb\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9a\\xe4\\xb8\\xad'.count(b'\\xc3\\xa9b\\x00\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\ud800中b中\\x00中'.index('中\\x00', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xada\\xe4\\xb8\\xadaccc\\x00\\xc3\\xa9c'.find(b'a\\xe4\\xb8\\xadaccc\\x00\\xc3\\xa9c', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c'.startswith('éc中', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c'.rindex('éc中', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'a\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00\\xc3\\xa9ba\\xe4\\xb8\\xadc\\xc3\\xa9ca\\xe4\\xb8\\xadaab\\xc3\\xa9ccbc\\xe4\\xb8\\xadc'.rfind(b'', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ééb'.endswith('éb', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ééb'.count('éb', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9ac\\x00aa\\x00\\x00\\x00bb\\x00\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadbb'.index(b'a', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中\\ud800éa'.find('\\ud800é中cbé', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\x00\\x00\\xc3\\xa9a\\xc3\\xa9bb\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xc3\\xa9\\x00\\xe4\\xb8\\xad\\xc3\\xa9aaa\\xe4\\xb8\\xadbaac'.startswith(b'\\xc3\\xa9bb\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xc3\\xa9\\x00\\xe4\\xb8\\xad\\xc3\\xa9aaa\\xe4\\xb8\\xadbaac', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\x00\\x00\\xc3\\xa9a\\xc3\\xa9bb\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xc3\\xa9\\x00\\xe4\\xb8\\xad\\xc3\\xa9aaa\\xe4\\xb8\\xadbaac'.rindex(b'\\xc3\\xa9bb\\xe4\\xb8\\xad\\xed\\xa0\\x80a\\xc3\\xa9\\x00\\xe4\\xb8\\xad\\xc3\\xa9aaa\\xe4\\xb8\\xadbaac', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\ud800é\\x00c\\ud800\\x00中éc\\x00é\\x00\\ud800b中\\ud800\\ud800éaé中\\x00\\ud800cc\\ud800cb\\ud800a\\ud800\\ud800ba'.rfind('a', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00\\xed\\xa0\\x80b\\x00\\x00\\xc3\\xa9c\\xed\\xa0\\x80\\x00\\x00\\xed\\xa0\\x80b\\xc3\\xa9\\xe4\\xb8\\xad'.endswith(b'\\x00\\xed\\xa0\\x80c', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'b\\x00\\xed\\xa0\\x80b\\x00\\x00\\xc3\\xa9c\\xed\\xa0\\x80\\x00\\x00\\xed\\xa0\\x80b\\xc3\\xa9\\xe4\\xb8\\xad'.count(b'\\x00\\xed\\xa0\\x80c', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('éa\\x00aaaééb\\x00é\\x00a中b\\ud800b中b\\ud800\\ud800c\\ud800中'.index('b\\ud800\\ud800c\\ud800中', 10000))\nexcept Exception as error: print(type(error).__name__)\n",
              '''0
ValueError
3
False
ValueError
38
True
1
2
-1
False
6
34
False
0
ValueError
''')

check_program("try: print(b'c'.find(b'\\xed\\xa0\\x80\\xc3\\xa9a\\xc3\\xa9a\\xe4\\xb8\\xad\\x00', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中baaéa中中ébab\\x00b\\x00éééc'.endswith('\\x00\\ud800cé中', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ac\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80bba\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80ba\\xed\\xa0\\x80\\xc3\\xa9\\x00b\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00'.startswith(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ac\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80bba\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80ba\\xed\\xa0\\x80\\xc3\\xa9\\x00b\\xed\\xa0\\x80\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00'.count(b'\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中bééccé中中\\x00中éé中\\ud800é\\ud800c中a中a\\ud800éé\\x00a\\ud800b\\x00\\x00中\\x00中éacé中'.rindex('中a\\ud800\\x00aa', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadbaab\\x00a\\xe4\\xb8\\xad\\xc3\\xa9\\xc3\\xa9\\xc3\\xa9\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xadacbaaa\\xe4\\xb8\\xadbb\\x00bb\\xe4\\xb8\\xadcc'.index(b'', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中中\\ud800cc\\x00\\x00中é中écbéb中\\ud800\\x00é\\x00\\ud800ca'.rfind('\\x00\\ud800ca', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\xc3\\xa9a\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9c\\xe4\\xb8\\xadc\\x00\\xc3\\xa9\\xed\\xa0\\x80a\\xc3\\xa9cc\\xed\\xa0\\x80a\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00\\xed\\xa0\\x80ab\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80bc\\xed\\xa0\\x80\\xed\\xa0\\x80\\x00bb\\xed\\xa0\\x80'.find(b'\\xed\\xa0\\x80b\\x00\\xe4\\xb8\\xadb\\xe4\\xb8\\xad', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800é\\x00\\ud800c\\x00\\ud800c\\x00中c'.endswith('\\ud800中a\\x00\\ud800éb', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\x00\\xc3\\xa9\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80c\\x00\\xed\\xa0\\x80a'.startswith(b'\\xed\\xa0\\x80a', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\x00\\xc3\\xa9\\xed\\xa0\\x80c\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80c\\x00\\xed\\xa0\\x80a'.count(b'\\xed\\xa0\\x80a', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('cbé\\x00bcbccé\\ud800\\ud800c\\x00bcabac中béccc\\x00\\x00a\\ud800ébbc'.rindex('\\x00ac\\x00\\x00\\x00中', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b''.index(b'\\xe4\\xb8\\xad\\xed\\xa0\\x80'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ébbé\\ud800caa\\ud800\\x00cbééac中é\\ud800aa\\ud800bc\\x00b\\ud800\\ud800éb中ca\\x00ac\\ud800bb'.rfind('bbé\\ud800caa\\ud800\\x00cbééac中é\\ud800aa\\ud800bc\\x00b\\ud800\\ud800éb中ca\\x00ac\\ud800bb', 0))\nexcept Exception as error: print(type(error).__name__)\n",
              '''-1
False
False
0
ValueError
ValueError
-1
-1
False
False
0
ValueError
ValueError
1
''')

check_program("try: print('ébbé\\ud800caa\\ud800\\x00cbééac中é\\ud800aa\\ud800bc\\x00b\\ud800\\ud800éb中ca\\x00ac\\ud800bb'.rindex('bbé\\ud800caa\\ud800\\x00cbééac中é\\ud800aa\\ud800bc\\x00b\\ud800\\ud800éb中ca\\x00ac\\ud800bb', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\x00b\\xed\\xa0\\x80\\xc3\\xa9a\\xed\\xa0\\x80\\xc3\\xa9\\x00c'.rfind(b'c', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(''.endswith('ccé\\ud800\\ud800中', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(''.count('ccé\\ud800\\ud800中', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'ba\\x00b\\xed\\xa0\\x80b\\xed\\xa0\\x80\\x00ccca\\x00ab\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\xed\\xa0\\x80\\xed\\xa0\\x80acbabaa\\xe4\\xb8\\xada'.index(b'\\x00b\\xed\\xa0\\x80b\\xed\\xa0\\x80\\x00ccca\\x00ab\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\xed\\xa0\\x80\\xed\\xa0\\x80acbabaa\\xe4\\xb8\\xada'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800中é'.find('é中\\x00a中', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadb\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9bcacc\\xc3\\xa9\\x00\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xe4\\xb8\\xad'.startswith(b'\\x00\\xc3\\xa9\\x00ba\\xe4\\xb8\\xad', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadb\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9bcacc\\xc3\\xa9\\x00\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xadc\\xe4\\xb8\\xad'.rindex(b'\\x00\\xc3\\xa9\\x00ba\\xe4\\xb8\\xad', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800é\\x00cb中aa\\x00cb\\ud800abcba\\x00bcabb中b'.rfind('bcabb中b', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80babb\\xc3\\xa9c\\xe4\\xb8\\xad'.endswith(b'aa\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'c\\xe4\\xb8\\xad\\x00\\xed\\xa0\\x80\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80babb\\xc3\\xa9c\\xe4\\xb8\\xad'.count(b'aa\\x00', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('c中ca中bc\\ud800bbé\\x00中a中\\x00aéb\\ud800ca中\\ud800\\ud800\\ud800b\\x00é中中b\\x00中ccbéb'.index('ac中c'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'cbb\\x00b\\x00'.find(b'', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800c\\x00b\\ud800\\ud800b\\ud800aé中中\\ud800\\ud800\\x00中中\\x00bé\\ud800é\\ud800c中abaa\\x00b'.startswith('中', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800c\\x00b\\ud800\\ud800b\\ud800aé中中\\ud800\\ud800\\x00中中\\x00bé\\ud800é\\ud800c中abaa\\x00b'.rindex('中', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xad\\x00a\\x00a\\xc3\\xa9a\\xc3\\xa9b\\xc3\\xa9b\\xe4\\xb8\\xadc\\x00a\\xe4\\xb8\\xadcca\\xed\\xa0\\x80a\\xed\\xa0\\x80aa'.rfind(b'\\xe4\\xb8\\xad\\xed\\xa0\\x80b\\xe4\\xb8\\xad', -100, 100))\nexcept Exception as error: print(type(error).__name__)\n",
              '''1
16
False
0
2
-1
False
ValueError
-1
False
0
ValueError
0
False
ValueError
-1
''')

check_program("try: print('\\x00cc\\ud800中中éa中éb\\ud800中\\ud800bé\\x00éb中\\ud800中aa\\x00ca\\x00\\x00bcb\\ud800中\\ud800c\\x00é'.endswith('\\x00\\x00bcb\\ud800中\\ud800c\\x00é', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00cc\\ud800中中éa中éb\\ud800中\\ud800bé\\x00éb中\\ud800中aa\\x00ca\\x00\\x00bcb\\ud800中\\ud800c\\x00é'.count('\\x00\\x00bcb\\ud800中\\ud800c\\x00é', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9aa\\xe4\\xb8\\xada\\xc3\\xa9\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xed\\xa0\\x80ab'.index(b'\\x00\\xc3\\xa9a\\xe4\\xb8\\xadcb\\x00', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print('中a'.find('cbaaébb', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'bc\\xed\\xa0\\x80aa\\xed\\xa0\\x80\\xe4\\xb8\\xadab\\x00\\xed\\xa0\\x80a'.startswith(b'\\x00\\xed\\xa0\\x80a', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'bc\\xed\\xa0\\x80aa\\xed\\xa0\\x80\\xe4\\xb8\\xadab\\x00\\xed\\xa0\\x80a'.rindex(b'\\x00\\xed\\xa0\\x80a', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('acéé中cé中é\\x00bcécb\\ud800cébcébbéébb\\x00ééc中a'.rfind('\\ud800aé\\ud800\\x00', -10**100, 10**100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b''.endswith(b'\\x00c\\x00\\xe4\\xb8\\xad', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b''.count(b'\\x00c\\x00\\xe4\\xb8\\xad', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\x00abéc\\ud800\\x00bé\\x00aa\\x00ca\\ud800c\\ud800中c\\x00中\\ud800'.index('béc\\ud800\\x00bé\\x00aa\\x00ca\\ud800c\\ud800中c\\x00中\\ud800'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadbccc\\xe4\\xb8\\xad\\x00\\x00ab\\xc3\\xa9c\\xe4\\xb8\\xad\\xed\\xa0\\x80bb\\xed\\xa0\\x80ba\\x00'.find(b'', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a'.startswith('cb\\x00bé\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('a'.rindex('cb\\x00bé\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xad\\xe4\\xb8\\xadac\\x00aa\\xc3\\xa9\\x00\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xadc\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\x00aac\\x00\\xc3\\xa9'.rfind(b'\\xc3\\xa9\\x00\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xadc\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\x00aac\\x00\\xc3\\xa9', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800c\\ud800\\ud800écb'.endswith('bb中aaac', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800c\\ud800\\ud800écb'.count('bb中aaac', 0))\nexcept Exception as error: print(type(error).__name__)\n",
              '''False
0
ValueError
-1
False
15
-1
False
0
2
0
False
ValueError
15
False
0
''')

check_program("try: print(b'c\\xed\\xa0\\x80bb\\x00\\x00\\xe4\\xb8\\xadab\\xed\\xa0\\x80ac\\xe4\\xb8\\xad\\xe4\\xb8\\xadc\\x00c\\x00\\xed\\xa0\\x80ccbba\\x00c\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xc3\\xa9aa\\x00c\\xed\\xa0\\x80\\xc3\\xa9\\x00\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80'.index(b'a\\xc3\\xa9\\x00'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800\\x00中中\\x00acc\\ud800\\x00\\ud800ac\\x00béabc\\x00béb\\ud800'.rfind('ac\\x00béabc\\x00béb\\ud800', -3, -1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xed\\xa0\\x80a\\xc3\\xa9abbb\\xc3\\xa9b\\xed\\xa0\\x80\\x00caacb\\xe4\\xb8\\xada\\xc3\\xa9aaa\\xed\\xa0\\x80\\xc3\\xa9'.find(b'b\\xed\\xa0\\x80\\x00\\xe4\\xb8\\xadab', 0))\nexcept Exception as error: print(type(error).__name__)\ntry: print('ca\\ud800\\ud800ééab\\ud800中\\ud800\\ud800\\x00céb中中\\ud800bc\\ud800aaééa\\x00a'.endswith('é\\ud800', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\xed\\xa0\\x80\\xe4\\xb8\\xadba\\xed\\xa0\\x80b\\xed\\xa0\\x80'.startswith(b'b\\xed\\xa0\\x80', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xed\\xa0\\x80a\\xe4\\xb8\\xad\\xe4\\xb8\\xada\\xed\\xa0\\x80\\xe4\\xb8\\xadba\\xed\\xa0\\x80b\\xed\\xa0\\x80'.count(b'b\\xed\\xa0\\x80', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print(''.rindex('\\x00é\\ud800\\ud800acé', None))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\xe4\\xb8\\xadb\\xc3\\xa9b\\x00\\x00bbac\\xc3\\xa9\\xc3\\xa9\\x00aa\\xc3\\xa9\\x00\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9b\\x00'.index(b'', 10000))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é\\ud800baéacé\\x00\\x00中bb中'.rfind('baéacé\\x00\\x00中bb中'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00\\xe4\\xb8\\xadc\\xc3\\xa9\\xe4\\xb8\\xadc\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\xc3\\xa9\\xc3\\xa9\\x00ab\\xc3\\xa9\\x00\\xc3\\xa9\\xe4\\xb8\\xad\\xc3\\xa9\\xed\\xa0\\x80\\xe4\\xb8\\xad\\xe4\\xb8\\xadbc\\x00\\xed\\xa0\\x80b\\xe4\\xb8\\xad\\xed\\xa0\\x80\\xed\\xa0\\x80abb'.find(b'a\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\xed\\xa0\\x80\\x00c', -100, 100))\nexcept Exception as error: print(type(error).__name__)\ntry: print('é中\\x00éaé\\ud800abba\\x00\\x00中\\ud800\\x00\\ud800\\ud800é\\x00caé\\x00\\x00\\ud800cbé\\ud800\\ud800\\x00中'.endswith('', 1, 1))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00b\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00c\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80bc\\xe4\\xb8\\xadca\\xc3\\xa9a\\xc3\\xa9\\xed\\xa0\\x80ca\\xed\\xa0\\x80bcb\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xadcb\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\xc3\\xa9bb'.startswith(b'cb\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\xc3\\xa9bb'))\nexcept Exception as error: print(type(error).__name__)\ntry: print(b'\\x00b\\xe4\\xb8\\xad\\xe4\\xb8\\xad\\x00c\\xed\\xa0\\x80\\xed\\xa0\\x80\\xed\\xa0\\x80bc\\xe4\\xb8\\xadca\\xc3\\xa9a\\xc3\\xa9\\xed\\xa0\\x80ca\\xed\\xa0\\x80bcb\\xe4\\xb8\\xad\\x00\\xc3\\xa9\\xed\\xa0\\x80\\xc3\\xa9\\xe4\\xb8\\xadcb\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\xc3\\xa9bb'.count(b'cb\\xe4\\xb8\\xadc\\xed\\xa0\\x80\\xc3\\xa9bb'))\nexcept Exception as error: print(type(error).__name__)\ntry: print('\\ud800\\ud800c\\ud800\\x00\\x00\\x00bbc中b\\ud800éé\\x00\\x00中\\x00\\ud800caé中'.rindex('', None))\nexcept Exception as error: print(type(error).__name__)\n",
              '''ValueError
-1
-1
False
False
0
ValueError
ValueError
2
-1
True
False
1
24
''')

check_program('''
class Bound:
    def __index__(self): print('index'); return 1
print('hello'.startswith(('e', 42), Bound()))
print('hello'.endswith(('o', 42)))
for parts in [(42, 'h'), ('x', 42), ()]:
    try: print('hello'.startswith(parts))
    except TypeError: print('invalid tuple item')
print(b'abcabc'.find(97), b'abcabc'.rfind(97), b'abcabc'.count(97))
class Byte:
    def __index__(self): return 97
print(b'abcabc'.find(Byte()))
print(str.find('abc', 'b'), bytes.count(b'abca', 97))
for value in [-1, 256, 10**100, -10**100]:
    try: b'abc'.find(value)
    except ValueError: print('invalid byte')
text = 'a' * 10000 + 'b'
print(text.find('a' * 1000 + 'b'), text.rfind('a' * 1000 + 'b'))
''',
              '''index
True
True
invalid tuple item
invalid tuple item
False
0 3 2
0
1 2
invalid byte
invalid byte
invalid byte
invalid byte
9000 9000
''')
