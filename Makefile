
.PHONY: test
test:
	python3 -m pytest test -vv

.PHONY: build-deb
build-deb:
	podman build --rm -t nosh-deb -f Dockerfile .
