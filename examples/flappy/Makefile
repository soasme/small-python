# Needs raylib (brew install raylib, or your distribution's package) and
# pkg-config. spyc builds one executable: the engine, flappy.py, the game
# package, its themes, the sprite, the raylib module in raylib.c, and,
# after --, raylib's static library.
ROOT = ../..
RAYLIB = $(shell pkg-config --cflags raylib) $(shell pkg-config --variable=libdir raylib)/libraylib.a
ifeq ($(shell uname),Darwin)
SYSTEM = -framework Cocoa -framework IOKit -framework CoreVideo -framework OpenGL -framework QuartzCore
else
SYSTEM = -lGL -lpthread -ldl -lrt -lX11
endif

# -D 'game.themes.*': the themes are imported by computed name. --deps
# rebuilds when any bundled file changes.
flappy: flappy.py raylib.c assets/sprite.py $(ROOT)/spyc $(ROOT)/libspy.a
	$(ROOT)/spyc -D 'game.themes.*' --minify --metafile flappy.json --deps flappy.d --analyze \
		-o $@ flappy.py raylib.c -- $(RAYLIB) $(SYSTEM)
-include flappy.d

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
	rm -rf flappy flappy.json flappy.d assets

.PHONY: run clean
