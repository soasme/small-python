# spec: PLS-315 19.3, 22.3
# description: Programs on round() and float formatting, each with the output CPython 3.15 gives.
from harness import *

check_program('''try:
    value = round(28.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(29.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(29.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(29.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(29.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(30.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(30.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(30.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(30.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(30.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(31.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(31.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(31.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(31.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(32.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(32.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(32.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(32.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(32.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(33.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float 28.5
float 29.0
float 0.0
int 30
float 29.5
int 30
float 0.0
float 0.0
float 30.5
float 30.5
float 31.0
float 0.0
int 32
float 31.5
int 32
float 0.0
float 0.0
float 32.5
float 32.5
float 33.0
''')

check_program('''try:
    value = round(33.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(33.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(33.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(34.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(34.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(34.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(34.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(34.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(35.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(35.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(35.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(35.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(36.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(36.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(36.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(36.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(36.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(37.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(37.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(37.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float 0.0
int 34
float 33.5
int 34
float 0.0
float 0.0
float 34.5
float 34.5
float 35.0
float 0.0
int 36
float 35.5
int 36
float 0.0
float 0.0
float 36.5
float 36.5
float 37.0
float 0.0
int 38
''')

check_program('''try:
    value = round(37.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(38.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(38.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(38.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(38.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(38.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(39.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(39.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(39.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(39.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(40.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(40.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(40.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(40.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(40.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(41.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(41.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(41.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(41.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(42.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float 37.5
int 38
float 0.0
float 0.0
float 38.5
float 38.5
float 39.0
float 0.0
int 40
float 39.5
int 40
float 0.0
float 0.0
float 40.5
float 40.5
float 41.0
float 0.0
int 42
float 41.5
int 42
''')

check_program('''try:
    value = round(42.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(42.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(42.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(42.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(43.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(43.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(43.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(43.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(44.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(44.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(44.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(44.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(44.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(45.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(45.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(45.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(45.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(46.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(46.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(46.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float 0.0
float 0.0
float 42.5
float 42.5
float 43.0
float 0.0
int 44
float 43.5
int 44
float 0.0
float 0.0
float 44.5
float 44.5
float 45.0
float 0.0
int 46
float 45.5
int 46
float 0.0
float 0.0
''')

check_program('''try:
    value = round(46.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(46.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(47.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(47.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(47.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(47.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(48.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(48.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(48.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(48.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(48.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(49.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(49.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(49.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(49.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(50.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(50.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(50.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(50.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(50.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float 46.5
float 46.5
float 47.0
float 0.0
int 48
float 47.5
int 48
float 0.0
float 0.0
float 48.5
float 48.5
float 49.0
float 0.0
int 50
float 49.5
int 50
float 0.0
float 0.0
float 50.5
float 50.5
''')

check_program('''try:
    value = round(-1.7197055736461095e-72, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1541549072082890892289116473811510225767821304830486255754741446705600189341170776352918042975442903600379216800466315943666798157406350481211219090491756998272897093837118017597831099871710563821017943407721968190611537558070790300273142807217967613341526)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1541549072082890892289116473811510225767821304830486255754741446705600189341170776352918042975442903600379216800466315943666798157406350481211219090491756998272897093837118017597831099871710563821017943407721968190611537558070790300273142807217967613341526, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-2.300222424964324e-169, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-14449778927974691121572940885994859486539696008272935815417295590153870519215291726821124729206953926239505017104376061272794358507538216462657559841193447302492402263037186702104480754361278402835860578154888793982815490183774974065762488939, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-4.51545142271739e-106, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-4.51545142271739e-106, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(3043779423838, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-4.712454344245196e-305, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-20757943495814935026034382033037869145703832893833389622814920716133082501039542243905822919635715924584069874093945789577241367403765588712070036276711644716271590944810138329843233618031675617939539967197151336305624584878478304120470602948875884036787905675344163188233490604227681985746663004593101513556650009101828203451630136099259679975878678314726591489236623866907677930083561913994045930907368714407118475534581311014048603621253139863746906904016819087822355454240567717191508568889218765988447115, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-1.3523006571430974e+210)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-1.3523006571430974e+210, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float -0.0
int 1541549072082890892289116473811510225767821304830486255754741446705600189341170776352918042975442903600379216800466315943666798157406350481211219090491756998272897093837118017597831099871710563821017943407721968190611537558070790300273142807217967613341526
int 1541549072082890892289116473811510225767821304830486255754741446705600189341170776352918042975442903600379216800466315943666798157406350481211219090491756998272897093837118017597831099871710563821017943407721968190611537558070790300273142807217967613341526
float -2.300222424964324e-169
int -14449778927974691121572940885994859486539696008272935815417295590153870519215291726821124729206953926239505017104376061272794358507538216462657559841193447302492402263037186702104480754361278402835860578154888793982815490183774974065762488939
int 0
float -0.0
int 0
float -0.0
int -20757943495814935026034382033037869145703832893833389622814920716133082501039542243905822919635715924584069874093945789577241367403765588712070036276711644716271590944810138329843233618031675617939539967197151336305624584878478304120470602948875884036787905675344163188233490604227681985746663004593101513556650009101828203451630136099259679975878678314726591489236623866907677930083561913994045930907368714407118475534581311014048603621253139863746906904016819087822355454240567717191508568889218765988447115
int -1352300657143097423579989274128623261223517391346105927460888556945219730619379570558385995279420698984092197336671151678071908341239956418280326241631052786581219911028185120532714407008430039486914211138764800
float -1.3523006571430974e+210
''')

check_program('''try:
    value = round(-125837240312742496876837364819754165398280045715689466409955166527816268839684231716984025090059363576772615416606053206093590274446634536848410827062946207900181978502883698308792036351389783964145, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(8.501315527848138e+43, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-94997344925589202964179221211670629702051801089266736496435565824287844170936231239513060424436055505285735470758208864850895128981924037543537927285022119636718214479667910424217699105287562205, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.0183750473985374e+62, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-22555268752805531088328741190354507995460941578670551129499796825559573019292866350154737566597907318167372585379303258353468993644685389330822371673774635820202694202474117586561831972110394056709292834806027781911399811734711839575967820870, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(3.665283034165523e-69, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-637161235323555881099815517071063581319665772053097889372669625767281408245460126787551391346532325198523098089515236399627970783844363382290002408114953726127089917089570286651325596802636189991020334586070256018712825715668479433295590591893180679474208691181864107910354709681390499722861279526727935356654039333576631851623473020769988153183034393419307184924326001093920859965703738691512439184211360176872642700324764269219624794118056274502773195891366485984871853696725926984186208137694686295449913471855785999868161080943776170622862920587432231273698325026525300285, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.4303961229980947e+104, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''int -125837240312742496876837364819754165398280045715689466409955166527816268839684231716984025090059363576772615416606053206093590274446634536848410827062946207900181978502883698308792036351389783964145
float 8.501315527848138e+43
int -94997344925589202964179221211670629702051801089266736496435565824287844170936231239513060424436055505285735470758208864850895128981924037543537927285022119636718214479667910424217699105287562205
float 1.0183750473985374e+62
int -22555268752805531088328741190354507995460941578670551129499796825559573019292866350154737566597907318167372585379303258353468993644685389330822371673774635820202694202474117586561831972110394056709292834806027781911399811734711839575967820870
float 0.0
int -637161235323555881099815517071063581319665772053097889372669625767281408245460126787551391346532325198523098089515236399627970783844363382290002408114953726127089917089570286651325596802636189991020334586070256018712825715668479433295590591893180679474208691181864107910354709681390499722861279526727935356654039333576631851623473020769988153183034393419307184924326001093920859965703738691512439184211360176872642700324764269219624794118056274502773195891366485984871853696725926984186208137694686295449913471855785999868161080943776170622862920587432231273698325026525300285
float 0.0
''')

check_program('''try:
    value = round(4.775742496624525e+294)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(4.775742496624525e+294, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-985913965209711176307340764257922890715470040389267168054117468065726598745348317950434855845354188714589909968, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.570513590438112e-153, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(74309884783115105976995801135626747051362632634833786420653850525074532252328660739057272523206109598018249870659015542903197528498234832756799830539124364131351146684313179653202277596417280560272409299060713807428530217172242402030109347069226549281036137271953984554322568669183278221011989916874447029410293893292790956054089038064408426795702836434019434890072533107053960636472111188312450832234876833309842604918537483767601082489226533089536399044754722814383469385141066876761460207611470783114334141068736010895953807423276495, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-1.8753686421761867e+152, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-267671043289575, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-1.4414610131164441e+256, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(24272458515796519264624357393542290816858681722341424536094247206522483485199911941682635797590808104610052414119101320401924901584988264189965715311937233526462257698558292586600762864665826803000815135676597540469519226371605818811718627417337208569814659953014399964497870548555366558728710155808959922510317590534005015414223913083337231417206647215557401815582784860455863964565982775049078829614085771292517668567459638869111675166835712996626127175027650539008810028999372503345548232138122015676725628295720221528883731406898886448172317, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(2.8679290742676086e+293)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''int 4775742496624525128618491644341294599118346220043536864783442950287177957024616985179036110563595464378001822554538422570712730057000832501451773852384673735111173559019219958718714392100982287902509468226817196611389734435970897289405285909007388665846245524143597929801683901416203784330149888
float 0.0
int -985913965209711176307340764257922890715470040389267168054117468065726598745348317950434855845354188714589909968
float 0.0
int 74309884783115105976995801135626747051362632634833786420653850525074532252328660739057272523206109598018249870659015542903197528498234832756799830539124364131351146684313179653202277596417280560272409299060713807428530217172242402030109347069226549281036137271953984554322568669183278221011989916874447029410293893292790956054089038064408426795702836434019434890072533107053960636472111188312450832234876833309842604918537483767601082489226533089536399044754722814383469385141066876761460207611470783114334141068736010895953807423276495
float -1.8753686421761867e+152
int -267671043289575
float -1.4414610131164441e+256
int 24272458515796519264624357393542290816858681722341424536094247206522483485199911941682635797590808104610052414119101320401924901584988264189965715311937233526462257698558292586600762864665826803000815135676597540469519226371605818811718627417337208569814659953014399964497870548555366558728710155808959922510317590534005015414223913083337231417206647215557401815582784860455863964565982775049078829614085771292517668567459638869111675166835712996626127175027650539008810028999372503345548232138122015676725628295720221528883731406898886448172317
int 286792907426760863605307477008164849724760427588796762340039351247004649011526443449320713974582346415648193475073802330008732064721756511844686128854714305696254081606540613880171043033296332275077921775124218710345876439012366912521911718809605962629791968837452087426279601952566479907979264
''')

check_program('''try:
    value = round(2.8679290742676086e+293, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(234103878703623040340172132094944622711574871521967836476161957394321867367005631406030748572308835691113831732288538358586209461875106150989887870674037360740552979960465904392211983350489408900132803115243320876609445105269300728033980456107607464985501944414002480054646, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.4791832056017271e-33, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(32258403515647524867180751868729002496397719386922680684554999233258395410191253110296903031487989210312680631117117862336391427062291372231683097285724864184625607953089525048857058482685353280161001960, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-1.4168928204738218e-239, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-26956884613812615069595717052358607698530339415168899308134335665835309296825513143646331675243932104460138032071056964628677467928883511110851891065600062612622336936645879807785955308825124254913808459629951854827793667750740541564674577012368993843260621172697, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(3.1597418080222165e+171, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-44154716008086430203671524225096858312223190333135085012913307900080704438814685545363499725921836754067564334579002549227296738111550691035624311811549402046867000031073628345240183932591672776783268291793062731550603415572423437104529651143418358161870903402747227951311682265409723868119423035928001491309613421649237414046447, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.0978149829725418e-291)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.0978149829725418e-291, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float 0.0
int 234103878703623040340172132094944622711574871521967836476161957394321867367005631406030748572308835691113831732288538358586209461875106150989887870674037360740552979960465904392211983350489408900132803115243320876609445105269300728033980456107607464985501944414002480054646
float 0.0
int 32258403515647524867180751868729002496397719386922680684554999233258395410191253110296903031487989210312680631117117862336391427062291372231683097285724864184625607953089525048857058482685353280161001960
float -0.0
int -26956884613812615069595717052358607698530339415168899308134335665835309296825513143646331675243932104460138032071056964628677467928883511110851891065600062612622336936645879807785955308825124254913808459629951854827793667750740541564674577012368993843260621172697
float 3.1597418080222165e+171
int -44154716008086430203671524225096858312223190333135085012913307900080704438814685545363499725921836754067564334579002549227296738111550691035624311811549402046867000031073628345240183932591672776783268291793062731550603415572423437104529651143418358161870903402747227951311682265409723868119423035928001491309613421649237414046447
int 0
float 0.0
''')

check_program('''try:
    value = round(9593880731313954873328632947869350043834873547248901271238116165286579917884256535225195749790832039823681497347662683074007440036988441670762619298195443685455516349608709540528895418838579663591213422023979266888015545075758264792562465422058266521126685162341068387404054000566266602977545216214024663977410033358233422578072881478775099, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.5378483341655843e+95, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(4069939930851597973864357661882767095783444318900722870733001537668536085639988330532856251010153639424528330544021815864642229782514766565058934860516676358282, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.5328342864397314e+239, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(87515994666671078834183772001356150855799205060958858634120729756424694081564393736762784581170442897383004144112893466161052122282060504024334389507819223780410184576669247945473358718684746576058766346072408482193999717340455096713663590752344505138879941313766444962251445032489545572307685873753516034695849700777565699604734198823765901064164263123235009128050038508073804602707575170927737818749475076962693555800287623203375005300456259756757233210387913040353854158625313155796763952315421731718739265820120491577712485562025708289314573795103427617353501623462660, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.0292543534264445e-222, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-6595417792696580391024852133173867131559304948795868235490314616100601553316253692354233867644772607714166408917647659730197423413829932682459296645149178444624642511965058962206219280854913019709063662189212144221061011298340076945194775777765302024054298201300283544166, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-2.673073815555552e+297, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1551372350720584627196321710776952898121692984365892871935079926517324755198311666557280920196805266373323061501675696398918215739885024093293849414388913416597113567075941348340823776730501981192190239203488092175561253458792624173954265561895295740973202553414638459949488288833884147914807715615770767450453335298089765746655254852691221462358417365317869046303586175919162, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''int 9593880731313954873328632947869350043834873547248901271238116165286579917884256535225195749790832039823681497347662683074007440036988441670762619298195443685455516349608709540528895418838579663591213422023979266888015545075758264792562465422058266521126685162341068387404054000566266602977545216214024663977410033358233422578072881478775099
float 1.5378483341655843e+95
int 4069939930851597973864357661882767095783444318900722870733001537668536085639988330532856251010153639424528330544021815864642229782514766565058934860516676358282
float 1.5328342864397314e+239
int 87515994666671078834183772001356150855799205060958858634120729756424694081564393736762784581170442897383004144112893466161052122282060504024334389507819223780410184576669247945473358718684746576058766346072408482193999717340455096713663590752344505138879941313766444962251445032489545572307685873753516034695849700777565699604734198823765901064164263123235009128050038508073804602707575170927737818749475076962693555800287623203375005300456259756757233210387913040353854158625313155796763952315421731718739265820120491577712485562025708289314573795103427617353501623462660
float 1.0292543534264445e-222
int -6595417792696580391024852133173867131559304948795868235490314616100601553316253692354233867644772607714166408917647659730197423413829932682459296645149178444624642511965058962206219280854913019709063662189212144221061011298340076945194775777765302024054298201300283544166
float -2.673073815555552e+297
int 1551372350720584627196321710776952898121692984365892871935079926517324755198311666557280920196805266373323061501675696398918215739885024093293849414388913416597113567075941348340823776730501981192190239203488092175561253458792624173954265561895295740973202553414638459949488288833884147914807715615770767450453335298089765746655254852691221462358417365317869046303586175919162
''')

check_program('''try:
    value = round(4.224096502629576e+40, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-39888339223111779606945554278071487895352913625649625162895648403053488199591234840550693206487642737801428404638302320603138230751539091175765936536050620251206008501147747598354599694938258115685748535848396350974289661067046011025538587475636898257389865582802015354261373682325716391392639030657852961199825182560661037116266939655817762108947452814103777903318174021635224479617331685745830980360514530250809, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-7.3309620054592005e+292, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.9531583689027274e+101)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-2926522121099709843445948281392106264358249254706032649138353056602761270446159638015108331905740758623294302957056516342463760156300126114908973083119592400097741059478533358565109140167225933308891612003148786580680179517494869587113823835213220035879129452139770260113, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-1.8478941694942394e-197, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(41020159387516703182247832639837144238108484353424764155789405301425325581934488612329581766683873531614725545875342369005536790890626606677594688722315490613669117619938182333147429783957528906786823694608459282633311895586108011328180254677310808564046611917657670532232419910808557454334223671141906614407059658653047872566632940028715332341966038793824539432114102267306540250668049466279418569320458223249029745872837731013859949806447069402393911200809765348013507637203386236345107, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(3.489632831804168e+115, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float 0.0
int -39888339223111779606945554278071487895352913625649625162895648403053488199591234840550693206487642737801428404638302320603138230751539091175765936536050620251206008501147747598354599694938258115685748535848396350974289661067046011025538587475636898257389865582802015354261373682325716391392639030657852961199825182560661037116266939655817762108947452814103777903318174021635224479617331685745830980360514530250809
float -0.0
int 195315836890272735550903150236881279862594932714439602224061395398918910581156522124169445250909077504
int -2926522121099709843445948281392106264358249254706032649138353056602761270446159638015108331905740758623294302957056516342463760156300126114908973083119592400097741059478533358565109140167225933308891612003148786580680179517494869587113823835213220035879129452139770260113
float -0.0
int 41020159387516703182247832639837144238108484353424764155789405301425325581934488612329581766683873531614725545875342369005536790890626606677594688722315490613669117619938182333147429783957528906786823694608459282633311895586108011328180254677310808564046611917657670532232419910808557454334223671141906614407059658653047872566632940028715332341966038793824539432114102267306540250668049466279418569320458223249029745872837731013859949806447069402393911200809765348013507637203386236345107
float 3.489632831804168e+115
''')

check_program('''try:
    value = round(148705092769093841915335900140982027020505785482025199125761149178910291087914296782669789753803005041802120912161702452525745872965756746961276556254380474541054103711939053688567419380925076279083315466379966595848897342939, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-3.321020144204e+301, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1615612465153499886737237096140785473081966286104767879345610467702974173062448512556781923652657199397949281596303331544785592590917573666189431560895347025533362096014395185924395271674945204787059820578325023476201688451329641120860259416007985643004792674136401625205150072568161049201376607311672361712274149398651412020537352558437166260225208610046577267473699076581616996783528147855718288441581148740104857414359351240772482720927662305450575485342225380020719484846862591830662818587548581214274215854018640109526, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-5.500727344769809e-231, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.3335375311123293e-240)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1628722414517531549360276858224330405971065702862376621623281277095228926435818485352962401171460460314907472607833555856036806601644334456598337527123582568184425127398501865857995748399874596264134305650397245785597539607108711602692608378866541722951622938, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-4.953024043270073e+140, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-271407561535317381132343142743674108373392387068588101296205731399412822423223969675318399930534354536858119743955512849099287355987302016019307498558357557736881310800159548257350510951463215720585851741058804725812676560681733275035612015586056676395333701532192194918576282477498681773948779746064893014782851870541219605297205296518293006304291841318305081219202420455545096394211785267758558251588764002204060779352398047085180522206255154244149725793748194193485883503999234755264661623890590, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''int 148705092769093841915335900140982027020505785482025199125761149178910291087914296782669789753803005041802120912161702452525745872965756746961276556254380474541054103711939053688567419380925076279083315466379966595848897342939
float -0.0
int 1615612465153499886737237096140785473081966286104767879345610467702974173062448512556781923652657199397949281596303331544785592590917573666189431560895347025533362096014395185924395271674945204787059820578325023476201688451329641120860259416007985643004792674136401625205150072568161049201376607311672361712274149398651412020537352558437166260225208610046577267473699076581616996783528147855718288441581148740104857414359351240772482720927662305450575485342225380020719484846862591830662818587548581214274215854018640109526
float -0.0
int 0
int 1628722414517531549360276858224330405971065702862376621623281277095228926435818485352962401171460460314907472607833555856036806601644334456598337527123582568184425127398501865857995748399874596264134305650397245785597539607108711602692608378866541722951622938
float -4.953024043270073e+140
int -271407561535317381132343142743674108373392387068588101296205731399412822423223969675318399930534354536858119743955512849099287355987302016019307498558357557736881310800159548257350510951463215720585851741058804725812676560681733275035612015586056676395333701532192194918576282477498681773948779746064893014782851870541219605297205296518293006304291841318305081219202420455545096394211785267758558251588764002204060779352398047085180522206255154244149725793748194193485883503999234755264661623890590
''')

check_program('''try:
    value = round(1.867452128974934e+165, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-467510175520250433823116846641614062215317012030109174591470134489669791260579393333345722245680666970297368910536142527957180342887500985217865315230033522416585991247993230636599345270278692630865869422029019798915443471334351453201186322141462246163216047874801419712781312723, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(4.718513787217484e+59, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1077163147692483645974240418762263733904707862703798616963347582707619916067119847794260928593340391284938943570597389403825567707268967157889126904674722575312059689133087967909810980201320706784052197844169821792479195455975948683494200608770845342088519417759441416422437634286948482847193542975334800418325422683119231641825217357114124896863280436102598912105394747345250159263619846343171106355670923639641278774327315569868324144123668698389465200173684379266397419358906529689428529246320566273753720301742055578944314868102666546123, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(6.241206819305561e-192, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(2783426244404245944738570506213783302076850530299083274036451390051245095445594043486077913187035265049307754287841970306889054558046071635526530963120612229154886120182483407302789059462211807183732254404217109731417273838284919168292344169853484827348361568739319084513611086060568799818696488931188717507933339452925781816411160610096890893722193637266936520903039343324115912747684746744832674890760013546672029177398608913065516617968822249543763441540982356950389809719822297742710831823004431816943357737585792310199629845536367662200498578341307810292301224640946217076871407670, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.6057868584741625e+115, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-18749920605442836536126469896974400914809834500497588441668577241793284626214075865254786429626043291345541365468304040942941710802648711464329281141366379366571280223991123616690041353054373695614845992582985182807869957, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-1.628545077475651e+296, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float 1.867452128974934e+165
int -467510175520250433823116846641614062215317012030109174591470134489669791260579393333345722245680666970297368910536142527957180342887500985217865315230033522416585991247993230636599345270278692630865869422029019798915443471334351453201186322141462246163216047874801419712781312700
float 4.718513787217484e+59
int 1077163147692483645974240418762263733904707862703798616963347582707619916067119847794260928593340391284938943570597389403825567707268967157889126904674722575312059689133087967909810980201320706784052197844169821792479195455975948683494200608770845342088519417759441416422437634286948482847193542975334800418325422683119231641825217357114124896863280436102598912105394747345250159263619846343171106355670923639641278774327315569868324144123668698389465200173684379266397419358906529689428529246320566273753720301742055578944314868102666546100
float 0.0
int 2783426244404245944738570506213783302076850530299083274036451390051245095445594043486077913187035265049307754287841970306889054558046071635526530963120612229154886120182483407302789059462211807183732254404217109731417273838284919168292344169853484827348361568739319084513611086060568799818696488931188717507933339452925781816411160610096890893722193637266936520903039343324115912747684746744832674890760013546672029177398608913065516617968822249543763441540982356950389809719822297742710831823004431816943357737585792310199629845536367662200498578341307810292301224640946217076871407700
float 1.6057868584741625e+115
int -18749920605442836536126469896974400914809834500497588441668577241793284626214075865254786429626043291345541365468304040942941710802648711464329281141366379366571280223991123616690041353054373695614845992582985182807870000
float -1.628545077475651e+296
''')

check_program('''try:
    value = round(1936824015216925833872521430608799475993518765784689230188995745918199798407659896632293264220101131998804685950326122915361742899560408154117718756901361546921776826724802448481940553989466229670047405311433671875800801973309279138616021128443716872227226227820940393070181570457, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(6.0203116899093085e+29, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(6.0203116899093085e+29, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-89143272217419552228730223984894984214410269250810022543151492595785573872388225760438, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(3.035524497111657e+59, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-17438260187726523685785362538290403838650520410040484591101253646676014602899584467900495910603320898261033599601695248910102894358981394305678736187497359862520359023499125941151329563634723196845453368956802246299450753359861586630116873, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-8.292247625665298e-109)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-8.292247625665298e-109, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(70428067484391860393133178285447636850122092499914455766948509176190869005222475292023095341500942573873511788, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.4169155078934538e+144, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(12282092836941076175617989317031917945435381866592106190455187933380756899184433188785326945643153713795515868147268519532923019832150981754375509439041356710067169972399475701948229340486711964212903727508478069544816283503921628925580061680734116819402495664941548952434966601860457438199013678725054737680253956213609, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(12282092836941076175617989317031917945435381866592106190455187933380756899184433188785326945643153713795515868147268519532923019832150981754375509439041356710067169972399475701948229340486711964212903727508478069544816283503921628925580061680734116819402495664941548952434966601860457438199013678725054737680253956213609, -10000)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''int 1936824015216925833872521430608799475993518765784689230188995745918199798407659896632293264220101131998804685950326122915361742899560408154117718756901361546921776826724802448481940553989466229670047405311433671875800801973309279138616021128443716872227226227820940393070181570457
int 602031168990930850274309308416
float 0.0
int 0
float 3.035524497111657e+59
int -17438260187726523685785362538290403838650520410040484591101253646676014602899584467900495910603320898261033599601695248910102894358981394305678736187497359862520359023499125941151329563634723196845453368956802246299450753359861586630116873
int 0
float -8.292247625665298e-109
int 70428067484391860393133178285447636850122092499914455766948509176190869005222475292023095341500942573873511788
float 1.4169155078934538e+144
int 12282092836941076175617989317031917945435381866592106190455187933380756899184433188785326945643153713795515868147268519532923019832150981754375509439041356710067169972399475701948229340486711964212903727508478069544816283503921628925580061680734116819402495664941548952434966601860457438199013678725054737680253956213609
int 0
''')

check_program('''try:
    value = round(-3.968170105784042e+252, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-776783889482218588403409183451317420431448146944019905037417054644258034525388163895404375757663001387276512690091525199944073286542674007207545826707341288563948334704358559737404150399647651871298414473811534041385500342815947401855660649342739780371266990435769765128610315874914712393109752888109155576538555882040079792146469177738800033882680693530719719311724261386860292792310930605590124306731777396935690089498768500402992911181608040898581002147768535451363108461965426121407378)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-776783889482218588403409183451317420431448146944019905037417054644258034525388163895404375757663001387276512690091525199944073286542674007207545826707341288563948334704358559737404150399647651871298414473811534041385500342815947401855660649342739780371266990435769765128610315874914712393109752888109155576538555882040079792146469177738800033882680693530719719311724261386860292792310930605590124306731777396935690089498768500402992911181608040898581002147768535451363108461965426121407378, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1090.3228256751397, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-69818075934462570654979949007022428487760009673254830998792993399345838091255082811835374664866967918166037967068543864244959755223298119976175290800024, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(77796251.71600814, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(77796251.71600814, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(403914206737751597091157978835809878438975578760999533850890077774, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-4.573839208254149e+106, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(173321176359156971326578863313943030872490654564568976179992604268873506251461411549200026774671617961668991584887801957909440590563643055769314802407243711891952827700460510595181847010596832111329766844872542805761673828920730487278449237491423616713732062157249392776673262082650312292967839405413459643023871031503433416791, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(3.205174794297463e-13)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(3.205174794297463e-13, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float -3.968170105784042e+252
int -776783889482218588403409183451317420431448146944019905037417054644258034525388163895404375757663001387276512690091525199944073286542674007207545826707341288563948334704358559737404150399647651871298414473811534041385500342815947401855660649342739780371266990435769765128610315874914712393109752888109155576538555882040079792146469177738800033882680693530719719311724261386860292792310930605590124306731777396935690089498768500402992911181608040898581002147768535451363108461965426121407378
int -776783889482218588403409183451317420431448146944019905037417054644258034525388163895404375757663001387276512690091525199944073286542674007207545826707341288563948334704358559737404150399647651871298414473811534041385500342815947401855660649342739780371266990435769765128610315874914712393109752888109155576538555882040079792146469177738800033882680693530719719311724261386860292792310930605590124306731777396935690089498768500402992911181608040898581002147768535451363108461965426121407378
float 1090.3228256751397
int -69818075934462570654979949007022428487760009673254830998792993399345838091255082811835374664866967918166037967068543864244959755223298119976175290800024
int 77796252
float 0.0
int 0
float -4.573839208254149e+106
int 173321176359156971326578863313943030872490654564568976179992604268873506251461411549200026774671617961668991584887801957909440590563643055769314802407243711891952827700460510595181847010596832111329766844872542805761673828920730487278449237491423616713732062157249392776673262082650312292967839405413459643023871031503433416791
int 0
float 3.205174794297463e-13
''')

check_program('''try:
    value = round(137110081043978382768, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(137110081043978382768, -10000)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-6.395186572246569e-215, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-751949967335046505956981176954344387713945600979238126398768014169613095786841909948175820535263673437308212760806680029034021716970210850677882971861840572017763061157173980399708851325605015864208204936944447507380625142429655677691431086658638, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.5622541422751436e-83, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(46085823803615)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(46085823803615, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(3.748604595054939e-268, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-142843559052488416327381512228853066531213921660565256700050682098278790200310648954088581943067, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(4.2163299041658165e+82, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(4.2163299041658165e+82, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(469011748063840631118230274227505978100274227967284301564123385938017622817821847188617023527256469494115934021687839459174972015911654501800987184564485701971217395054118525322971319905837167921777665119302845609277098285409374888545428601369328895896217830848409737016147049319396406672446851722488332527017540675237003248714613799057919121616557523047243560010798656235704310986182021, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''int 137110081043978382768
int 0
float -0.0
int -751949967335046505956981176954344387713945600979238126398768014169613095786841909948175820535263673437308212760806680029034021716970210850677882971861840572017763061157173980399708851325605015864208204936944447507380625142429655677691431086658600
float 0.0
int 46085823803615
int 46085823803615
float 3.748604595054939e-268
int -142843559052488416327381512228853066531213921660565256700050682098278790200310648954088581943067
int 42163299041658164927220828348193145916436065089952618485605711747531434109324754944
float 0.0
int 469011748063840631118230274227505978100274227967284301564123385938017622817821800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
''')

check_program('''try:
    value = round(4.775376383693252e+24)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(4.775376383693252e+24, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-76167512908047094202265975290674160871193780354026345878310957268575650814234343710563945313261538586514068755268115918811312836588172276440494929940473298775535718911758048929391098590991894679677767891800932664015786308960290355584314894297796836114008132813211786990432916998741076998049565208871643656553288077848575498568, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-4.530028936574411e+290, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(5089318768357786228208685886191035986556630285065100172002621709720631574805682828185605928097876236716460862847872246880685954301778530694335460279550312904156512201551467603326055539204677105854725922251078317974321716897672088752515511734123283267207371406263474662515566053746572404218764210886493837326925207490599260332956581337447946874595737196617313975097640263831185529666538530630641086301809705830104301847641709348287664593269117140924798056824116693635155146634362897990132858117617617206347679482759532959261923834158471086654601567278704500290215867577498124306853588512, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(4.397896400776868e-253, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(31566987165371993424096982812900555290068482795661107747461233511973555134373934720982361776299762555944550089488964106969727506938514647478302744637203792549378139920, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-2.2842717957954757e+42, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-1115396630509318118557419124481780985381888146110171171874530701602994232791827597696848617280724404147042704551753901527988548642046624524637891190987169877576510035, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-9.628349307875053e-261)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''int 4775376383693251841884160
float 0.0
int -76167512908047094202265975290674160871193780354026345878310957268575650814234343710563945313261538586514068755268115918811312836588172276440494929940473298775535718911758048929391098590991894679677767891800932664015786308960290355584314894297796836114008132813211786990432916998741076998049565208871643656553288077848575498568
float -0.0
int 5089318768357786228208685886191035986556630285065100172002621709720631574805682828185605928097876236716460862847872246880685954301778530694335460279550312904156512201551467603326055539204677105854725922251078317974321716897672088752515511734123283267207371406263474662515566053746572404218764210886493837326925207490599260332956581337447946874595737196617313975097640263831185529666538530630641086301809705830104301847641709348287664593269117140924798056824116693635155146634362897990132858117617617206347679482759532959261923834158471086654601567278704500290215867577498124306853588512
float 0.0
int 31566987165371993424096982812900555290068482795661107747461233511973555134373934720982361776299762555944550089488964106969727506938514647478302744637203792549378139920
float -2.2842717957954757e+42
int -1115396630509318118557419124481780985381888146110171171874530701602994232791827597696848617280724404147042704551753901527988548642046624524637891190987169877576510035
int 0
''')

check_program('''try:
    value = round(-9.628349307875053e-261, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-5.575595653090841e-93)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-8816624287155995454436704048577817894937696097320948967077774921407687155553653087337191685472038918495069554310154442169701821090000606730865869814824665938654664242158311343317246757843181048424224, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-1.4648580705077553e-272, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-1559632055615763272205245588760152449994945159824373986635071629403119606445791642698797025824215278751399310573801164836455891820781727939372228212926468193758636111914743410750667393838017983107691870986297531831398015229322287481195730017452394126884531484495607026501369251879604149859727371211476409399466658203611589016445968314315154113583105786764192522597918285611784398882679232290761273402683014204133284257467454867260129702156478605648990926136388380112090958326107290680580006132992709717192427030639659234811907394848493252118185832102249537421084994479813324849251029985596751, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-6.682518299064372e-299, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-164845186366344943582635675110348653998084498345215668878947206783166159230426277680551206088690970128124107731426563085692866143107610119704228622317965551524926023204488255700226776170932267105538613274995956984342986903844459994632339358297444899890231283626579318611631848772076478106373089432284165578863693201512709600827433687645026241935742786673836246447156758090951880765367872218040238067986594656852415872414306478311296883805563513963276165735978854633160002353735638118575424987744376315215269050246500124090160893718191656540700992101947244562964, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(2.1099335344240838e-237, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float -0.0
int 0
int -8816624287155995454436704048577817894937696097320948967077774921407687155553653087337191685472038918495069554310154442169701821090000606730865869814824665938654664242158311343317246757843181048424224
float -0.0
int -1559632055615763272205245588760152449994945159824373986635071629403119606445791642698797025824215278751399310573801164836455891820781727939372228212926468193758636111914743410750667393838017983107691870986297531831398015229322287481195730017452394126884531484495607026501369251879604149859727371211476409399466658203611589016445968314315154113583105786764192522597918285611784398882679232290761273402683014204133284257467454867260129702156478605648990926136388380112090958326107290680580006132992709717192427030639659234811907394848493252118185832102249537421084994479813324849251029985596751
float -0.0
int -164845186366344943582635675110348653998084498345215668878947206783166159230426277680551206088690970128124107731426563085692866143107610119704228622317965551524926023204488255700226776170932267105538613274995956984342986903844459994632339358297444899890231283626579318611631848772076478106373089432284165578863693201512709600827433687645026241935742786673836246447156758090951880765367872218040238067986594656852415872414306478311296883805563513963276165735978854633160002353735638118575424987744376315215269050246500124090160893718191656540700992101947244562964
float 0.0
''')

check_program('''try:
    value = round(-92802918571943025331400189891191912212681699084413720953859020163731740283653235806220194420166122397364924794367202025354847225777480065998883995909031687359569673157106524821883800943151344431311000578291576044151668989166158327218912674591781725633812941873278505568457081616703663027700955510565549284305249378763164764563335836882076338993697935358664067979881928238, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(3.0560793552679694e+131, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-23286490381029348907522668000647511054940848358890745288404319527444603984146621813016026950838318906420412419619046897255033038453326423421816749523351633622710339540056014952887405230913428987273813677111676994405372275552300657352175155144464808505689218660983460648569546885222717850381435172816766157019286758559837792632387636540130005308140187134937705761786217222011197326, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-1.6648030565513889e+249, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-7954914485872276418456793343457278735196569102169025207284231478709149247854614934144982321423431884452210653030503025100170674608343411080913094656404222393181453184323251621179732192148929308330812768862191678681438994227831665889357238857899131806308934716696663873594108324, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-1.1481515157657049e-282, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-430733092901444528969815482809821328734606546696098135029912923194475022120917387897676437977234563839968029050837086238688974933001599324881645230344885997429873469936633172157692913327854964643342568366217358321866115051312487913662727570774571604487687062331469139318925401592972272985243522105956903987998185842552267118064192489911084, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(3.995511611579398e+47)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(3.995511611579398e+47, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(4257621784653139119595265702283636300932089429609041259693855254049308506485011709061231412471399809325251113926, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''int -92802918571943025331400189891191912212681699084413720953859020163731740283653235806220194420166122397364924794367202025354847225777480065998883995909031687359569673157106524821883800943151344431311000578291576044151668989166158327218912674591781725633812941873278505568457081616703663027700955510565549284305249378763164764563335836882076338993697935358664067979881928238
float 0.0
int -23286490381029348907522668000647511054940848358890745288404319527444603984146621813016026950838318906420412419619046897255033038453326423421816749523351633622710339540056014952887405230913428987273813677111676994405372275552300657352175155144464808505689218660983460648569546885222717850381435172816766157019286758559837792632387636540130005308140187134937705761786217222011197326
float -1.6648030565513889e+249
int -7954914485872276418456793343457278735196569102169025207284231478709149247854614934144982321423431884452210653030503025100170674608343411080913094656404222393181453184323251621179732192148929308330812768862191678681438994227831665889357238857899131806308934716696663873594108324
float -0.0
int -430733092901444528969815482809821328734606546696098135029912923194475022120917387897676437977234563839968029050837086238688974933001599324881645230344885997429873469936633172157692913327854964643342568366217358321866115051312487913662727570774571604487687062331469139318925401592972272985243522105956903987998185842552267118064192489911084
int 399551161157939827830777343730959508779810422784
float 0.0
int 4257621784653139119595265702283636300932089429609041259693855254049308506485011709061231412471399809325251113926
''')

check_program('''try:
    value = round(1.2915128009944857e+275, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(78272530487440042638212226660014790667577504416469888363681567560424981766386019641013452874412862071526573795662004936025820404742424478184137936937623932200923325647428594162444757943222985700875325454897747351005620791921321987547465812278849170664748566672775841582617873659763061090507460026428866218319661493116, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(3.936128727349412e-212, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-2545875379139400628022528302042736486017478357733262276003477175944172718290204986379027975645833124250183432085024657826705161452853339609032199230553546848726586194921191115210351878691591682026508816385937900706647846427201498328120668876476375056836953118390704355302793574808898501701894622277975337503756302068, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-2.4142642069503576e-105, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-3649145341031486340302392041586123853163681544335064618600123402897630853462343525048599222262641570795185062945693478922479171927658905371554311265719844985401357060298105534967020084124804498040559271916823131673028732154685604160156639790481509684230801411026582401925203816048940618634999767477317949730554583017562624751271621492268946590998, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(3.5372177141763904e-179, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-8707175322866086635810312895648316204178390837307326453220299272386236731141596162416675143806053767876964431992111089360886100041969694368678096568128539896581550489843696230621071731386973266820249534506188698609174364134350266589290528535908569204568647849585799000791704584644707770266416404574048308723426862497149964713119573870143197956921825027643229007450406365341432050165557792910139817060280447870553244095982512221990335190529923692392200, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(2.7426634998912156e-166, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float 0.0
int 78272530500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
float 0.0
int -2545875400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
float -0.0
int -3649145341031486340302392041586123853200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
float 0.0
int -8707175322866086635810312895648316204178390837307326453220299272386236731141596162416675143806053767876964431992111089360886100041969694368678100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
float 0.0
''')
