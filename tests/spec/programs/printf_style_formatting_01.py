# spec: PLS-315 23.6
# description: Programs on printf-style formatting, each with the output CPython 3.15 gives.
from harness import *

check_program('''print(', '.join(str(i) for i in range(4))); print('a%d:%s:%r:%%' % (3, 'x', 'y'))
''',
              '''0, 1, 2, 3
a3:x:'y':%
''')

check_program(''''%d' % ()
''',
              '''TypeError: not enough arguments for format string (got 0)
''')

check_program('''print((7469) | (14))
print((-79345) >= (-22))
print((-93456) - (27))
print((-74455) > (22))
print((-7163) ^ (-29))
print((-88995) != (-25))
print((-24640) * (-21))
print((-9327) < (-8))
print((11178) ^ (21))
print((96967) ^ (7))
print((11862) // (25))
print((-7094) & (-18))
print((-29132) <= (25))
print((42233) & (28))
print((89137) <= (23))
print((-90856) != (-24))
print((26935) // (28))
print((-18067) == (-4))
print((-41356) % (-15))
print((-6904) < (2))
print((-48724) + (9))
print((59043) < (12))
print((34659) | (2))
print((32603) // (-5))
print((89014) & (-4))
print((-45391) & (-23))
print((-25953) != (3))
print((-48324) & (-1))
print((-12385) % (29))
print((-54473) - (2))
print((-87543) // (-14))
print((-96047) < (22))
print((-88065) - (-4))
print((-72901) != (-25))
print((-69652) > (24))
print((-37626) > (-13))
print((-94824) * (-30))
print((57290) - (25))
print((5407) != (-14))
print((-52933) != (-2))
print((51248) == (-20))
print((-80460) + (4))
print((40000) != (-11))
print((-84043) + (-5))
print((14266) % (-8))
print((63206) % (20))
print((17545) > (-21))
print((-35998) == (27))
print((-29585) ^ (1))
print((-82157) + (30))
print((-594) - (-14))
print((-29724) // (24))
print((-98614) > (-28))
print((-86393) > (31))
print((-32762) >= (28))
print((96896) <= (18))
print((64144) > (20))
print((39725) & (7))
print((-89242) % (20))
print((36393) > (-22))
print((-52267) != (-11))
print((63761) ^ (25))
print((-69922) < (14))
print((-1365) >= (15))
print((78095) <= (-10))
print((-62303) != (-4))
print((-16958) | (9))
print((16318) > (29))
print((55709) // (10))
print((65904) * (-22))
print((-68617) > (30))
print((-83176) ^ (24))
print((-18126) + (3))
print((15305) % (-11))
print((-33702) & (13))
print((-46335) // (-24))
print((60050) <= (9))
print((-67900) == (-4))
print((-56440) <= (-21))
print((42349) & (-6))
print((71278) ^ (-12))
print((51497) % (30))
print((-97907) ^ (13))
print((-67389) % (-2))
print((-82624) + (-13))
print((-96388) - (23))
print((8936) < (22))
print((59815) > (-10))
print((95555) != (9))
print((72162) % (-27))
print((6881) & (24))
print((95820) < (22))
print((14499) <= (-1))
print((-42957) <= (25))
print((-9924) | (-14))
print((-78286) <= (6))
print((28796) // (22))
print((-75603) - (-27))
print((36748) > (-3))
print((-75465) != (12))
''',
              '''7471
False
-93483
False
7142
True
517440
True
11199
96960
474
-7094
True
24
False
True
961
False
-1
True
-48715
False
34659
-6521
89012
-45407
True
-48324
27
-54475
6253
True
-88061
True
False
False
2844720
57265
True
True
False
-80456
True
-84048
-6
6
True
False
-29586
-82127
-580
-1239
False
False
False
False
True
5
18
True
True
63752
True
False
False
True
-16949
True
5570
-1449888
False
-83200
-18123
-7
8
1930
False
False
True
42344
-71270
17
-97920
-1
-82637
-96411
False
True
True
-9
0
False
False
True
-2
True
1308
-75576
True
True
''')
