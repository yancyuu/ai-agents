# Makefile for ai-agents

.PHONY: build init

build:
	git pull
	git submodule update
	docker stop ai-agents || true
	docker rm ai-agents || true
	docker build -t ai-agents .
	docker tag ai-agents ai-agents:v1.0
	docker run -p 1706:1706 --name ai-agents -d ai-agents:v1.0

init:
	docker build -t ai-base -f init .
	docker tag ai-base ai-base:v1.0
