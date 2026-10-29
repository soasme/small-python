# Needs raylib (brew install raylib, or your distribution's package) and
# pkg-config. The engine is the top-level libspy.a.
ROOT = ../..
CC = cc
CFLAGS = -O2 -std=c11 -Wall -Wextra -Wpedantic -I$(ROOT) $(shell pkg-config --cflags raylib)
LDLIBS = $(shell pkg-config --libs raylib) -lm

pong: pong.c $(ROOT)/libspy.a
	$(CC) $(CFLAGS) $< $(ROOT)/libspy.a $(LDLIBS) -o $@

$(ROOT)/libspy.a:
	$(MAKE) -C $(ROOT) libspy.a

run: pong
	./pong pong.py

clean:
	rm -f pong

.PHONY: run clean
