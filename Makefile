#
# Makefile
# postgres
# DEBUG OSX: verify /etc/exports using docker-machine-nfs
#

SHELL := /bin/bash
HIDE ?= @
DOCKER_IMAGE ?= kite:1.0
DOCKER_CONTAINER ?= connect


.PHONY: image start enter stop

image:
	$(HIDE)docker build -f Dockerfile -t $(DOCKER_IMAGE) .

start:
	$(HIDE)docker run --rm --hostname $(DOCKER_CONTAINER)  --name $(DOCKER_CONTAINER) \
		-v $(PWD):/app \
		$(DOCKER_IMAGE) \
		kite.py

enter:
	$(HIDE)docker exec -it $(DOCKER_CONTAINER) /bin/bash

stop:
	$(HIDE)docker rm -f $(DOCKER_CONTAINER)

clean-all:
	#$(HIDE)read -p "This will remove images and containers, continue (y/n)?" -n 1 -r yn;
	-$(HIDE)docker ps -aq | xargs docker stop
	-$(HIDE)docker ps -aq | xargs docker rm
	-$(HIDE)docker images -q| xargs docker rmi
