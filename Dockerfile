FROM debian:12

ENV DEBIAN_FRONTEND nointeractive

# match the stop signal to systemd's.
STOPSIGNAL SIGRTMIN+3

RUN set -ex && apt-get update -y	\
	&& apt-get install -y --no-install-recommends ca-certificates  \
	python3 python3-pip flit \
	build-essential devscripts debhelper dh-python pybuild-plugin-pyproject

COPY . /nosh

RUN cd /nosh && debuild -us -uc

CMD [ "/bin/bash" ]
