.PHONY: all package deb clean

all: package

package:
	./build.sh

deb:
	./make-deb.sh

clean:
	./clean.sh
