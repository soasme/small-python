"""Write assets/sprite.py, a module holding python.png's bytes, so spyc
bundles the image as it bundles code. The asset step is Python too, run by
the engine itself: ../../spy pack.py > assets/sprite.py"""
data = open("python.png", "rb").read()
print('"""python.png, written by pack.py; do not edit."""')
print(f"PYTHON_PNG = {data!r}")
