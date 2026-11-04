# Needs raylib (brew install raylib, or your distribution's package) and
# pkg-config. spyc builds the program: pong.py, the raylib module in
# raylib.c, and raylib, after --, so it needs no Python file at run time.
ROOT = ../..

pong: pong.py raylib.c $(ROOT)/spyc $(ROOT)/libspy.a
	$(ROOT)/spyc -o $@ pong.py raylib.c -- $(shell pkg-config --cflags --libs raylib)

$(ROOT)/libspy.a $(ROOT)/spyc:
	$(MAKE) -C $(ROOT) $(notdir $@)

run: pong
	./pong

clean:
	rm -f pong

.PHONY: run clean
