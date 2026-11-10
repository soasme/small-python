# Needs cargo. cargo builds the json module (src/lib.rs) as libjson.a, and
# spyc links it into the program as module json, beside jsonify.py and sys.
ROOT = ../..
ARCHIVE = target/release/libjson.a
# What Rust's standard library needs from the system on Linux, as rustc
# --print native-static-libs lists it; macOS's C library has it all.
RUSTLIBS = $(if $(filter Linux,$(shell uname -s)),-lgcc_s -lutil -lrt -lpthread -lm -ldl -lc)
SPYC = $(ROOT)/bin/spyc $(ROOT)/libspy.a $(ROOT)/libspy-std.a

jsonify: jsonify.py $(ARCHIVE) $(SPYC)
	$(ROOT)/bin/spyc -M sys -o $@ jsonify.py $(ARCHIVE) -- $(RUSTLIBS)

# probe.py prints what json does with many values, to compare with CPython.
probe: probe.py $(ARCHIVE) $(SPYC)
	$(ROOT)/bin/spyc -o $@ probe.py $(ARCHIVE) -- $(RUSTLIBS)

$(ARCHIVE): Cargo.toml src/lib.rs
	cargo build --release

$(ROOT)/bin/spyc $(ROOT)/libspy.a $(ROOT)/libspy-std.a:
	$(MAKE) -C $(ROOT) $(patsubst $(ROOT)/%,%,$@)

test: jsonify probe
	python3 test.py $(RUSTLIBS)

clean:
	rm -rf jsonify probe target

.PHONY: test clean
