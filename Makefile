OS := $(shell uname -s)
ARCH := $(shell uname -m)
SRC := matching.c

ifneq ($(filter arm64 aarch64,$(ARCH)),)
SRC += matching_aarch64.S
endif

ifeq ($(OS),Darwin)
LIB := libmatch.dylib
SHARED := -dynamiclib
else
LIB := libmatch.so
SHARED := -shared -fPIC
endif

all: $(LIB)

$(LIB): $(SRC)
	$(CC) -O3 $(SHARED) $(SRC) -o $@

clean:
	rm -f libmatch.so libmatch.dylib

.PHONY: all clean
