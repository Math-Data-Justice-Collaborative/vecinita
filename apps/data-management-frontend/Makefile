SHELL := /bin/bash

.PHONY: install dev build test coverage test-integration test-integration-modal e2e lint validate-runtime

install:
	npm install

dev:
	npm run dev

build:
	npm run build

lint:
	npm run lint

test:
	npm run test

coverage:
	npm run test:coverage

test-integration:
	npm run test:integration

test-integration-modal:
	npm run test:integration:modal

e2e:
	npx playwright install --with-deps chromium
	npm run e2e

validate-runtime:
	@echo "Authentication now uses direct backend API keys. Validate the configured API base URL and issue a live backend key before signing in."
