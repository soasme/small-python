# Needs raylib (brew install raylib, or your distribution's package) and
# pkg-config. Everything goes into one executable: the engine (libspy.a),
# raylib's static library, and the bundle spyc writes, which holds
# flappy.py, the game package, its themes, and the sprite.
ROOT = ../..
CC = cc
CFLAGS = -O2 -std=c11 -Wall -Wextra -Wpedantic -I$(ROOT) $(shell pkg-config --cflags raylib)
RAYLIB = $(shell pkg-config --variable=libdir raylib)/libraylib.a
ifeq ($(shell uname),Darwin)
SYSTEM = -framework Cocoa -framework IOKit -framework CoreVideo -framework OpenGL -framework QuartzCore
else
SYSTEM = -lGL -lpthread -ldl -lrt -lX11
endif

flappy: flappy.c flappy_py.c $(ROOT)/libspy.a
	$(CC) $(CFLAGS) flappy.c flappy_py.c $(ROOT)/libspy.a $(RAYLIB) $(SYSTEM) -lm -o $@

# -c -N flappy: the sources and flappy_load, for flappy.c's own main.
# -x raylib: flappy.c registers raylib. -D 'game.themes.*': the themes are
# imported by computed name. --deps rebuilds when any bundled file changes.
flappy_py.c: flappy.py assets/sprite.py $(ROOT)/spyc
	$(ROOT)/spyc -c -N flappy -x raylib -D 'game.themes.*' --minify \
		--metafile flappy.json --deps flappy_py.d --analyze -o $@ flappy.py
-include flappy_py.d

# The sprite becomes a module (assets is a namespace package: no
# __init__.py), written by pack.py running on the engine itself.
assets/sprite.py: python.png pack.py $(ROOT)/spy
	mkdir -p assets
	$(ROOT)/spy pack.py > $@

$(ROOT)/libspy.a $(ROOT)/spyc $(ROOT)/spy:
	$(MAKE) -C $(ROOT) $(notdir $@)

run: flappy
	./flappy

clean:
	rm -rf flappy flappy_py.c flappy_py.d flappy.json assets

.PHONY: run clean
