
.PHONY: help build push all

help:
	    @echo "Makefile commands:"
	    @echo "build"
	    @echo "push"
	    @echo "all"

.DEFAULT_GOAL := all

build:
	    docker build -t jiggyai/jingbot:${TAG} .

push:
	    docker push jiggyai/jingbot:${TAG}

all: build push
