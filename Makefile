.PHONY: clean dist examples license wheel installer

version = $(shell perl -ne '/__version__ = "([^"]+)/ && print $$1;' escapepod_sdk/version.py)

license_targets = escapepod_sdk/LICENSE.txt examples/LICENSE.txt
example_targets = dist/escapepod_sdk_examples.tar.gz dist/escapepod_sdk_examples.zip

example_filenames = $(shell cd examples && find . -name '*.py' -o -name '*.txt' -o -name '*.png' -o -name '*.jpg' -o -name '*.md' -o -name '*.json')
example_pathnames = $(shell find examples -name '*.py' -o -name '*.txt' -o -name '*.png' -o -name '*.jpg' -o -name '*.md' -o -name '*.json')
sdist_filename = dist/escapepod_sdk-$(version).tar.gz
wheel_filename = dist/escapepod_sdk-$(version)-py3-none-any.whl

license: $(license_targets)

$(license_targets): LICENSE.txt
	for fn in $(license_targets); do \
		cp LICENSE.txt $$fn; \
	done

$(sdist_filename): escapepod_sdk/LICENSE.txt $(shell find escapepod_sdk -name '*.py' -o -name '*.mtl' -o -name '*.obj' -o -name '*.jpg')
	python3 setup.py sdist

$(wheel_filename): escapepod_sdk/LICENSE.txt $(shell find escapepod_sdk -name '*.py' -o -name '*.mtl' -o -name '*.obj' -o -name '*.jpg')
	python3 setup.py bdist_wheel

dist/escapepod_sdk_examples.zip: examples/LICENSE.txt $(example_pathnames)
	rm -f dist/escapepod_sdk_examples.zip dist/escapepod_sdk_examples_$(version).zip
	rm -rf dist/escapepod_sdk_examples_$(version)
	mkdir dist/escapepod_sdk_examples_$(version)
	tar -C examples -c $(example_filenames) | tar -C dist/escapepod_sdk_examples_$(version)  -xv
	cd dist && zip -r escapepod_sdk_examples.zip escapepod_sdk_examples_$(version)
	cd dist && zip -r escapepod_sdk_examples_$(version).zip escapepod_sdk_examples_$(version)

dist/escapepod_sdk_examples.tar.gz: examples/LICENSE.txt $(example_pathnames)
	rm -f dist/escapepod_sdk_examples.tar.gz dist/escapepod_sdk_examples_$(version).tar.gz
	rm -rf dist/escapepod_sdk_examples_$(version)
	mkdir dist/escapepod_sdk_examples_$(version)
	tar -C examples -c $(example_filenames) | tar -C dist/escapepod_sdk_examples_$(version)  -xv
	cd dist && tar -cvzf escapepod_sdk_examples.tar.gz escapepod_sdk_examples_$(version)
	cp -a dist/escapepod_sdk_examples.tar.gz dist/escapepod_sdk_examples_$(version).tar.gz

examples: dist/escapepod_sdk_examples.tar.gz dist/escapepod_sdk_examples.zip

dist: $(sdist_filename) $(wheel_filename) examples

clean:
	rm -rf dist
