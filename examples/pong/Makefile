# Needs raylib (brew install raylib, or your distribution's package) and
# pkg-config. The engine is the top-level libspy.a; spyc -c embeds pong.py,
# leaving out raylib (-x), the C module pong.c registers,
# so the program needs no Python file at run time.
ROOT = ../..
CC = cc
CFLAGS = -O2 -std=c11 -Wall -Wextra -Wpedantic -I$(ROOT) $(shell pkg-config --cflags raylib)
LDLIBS = $(shell pkg-config --libs raylib) -lm

pong: pong.c pong_py.c $(ROOT)/libspy.a
	$(CC) $(CFLAGS) pong.c pong_py.c $(ROOT)/libspy.a $(LDLIBS) -o $@

pong_py.c: pong.py $(ROOT)/spyc
	$(ROOT)/spyc -c -x raylib -o $@ pong.py

$(ROOT)/libspy.a $(ROOT)/spyc:
	$(MAKE) -C $(ROOT) $(notdir $@)

run: pong
	./pong

clean:
	rm -f pong pong_py.c

.PHONY: run clean
