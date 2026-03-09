# =========================
# Configuration
# =========================

PROJECT_ROOT := $(shell pwd)

# Dockerfiles
DOCKERFILE_PROD := docker-build-frontend/Dockerfile
DOCKERFILE_DEV  := docker-build-frontend/DockerfileDev

# Images
FRONTEND_BUILD_IMAGE := vue-frontend-builder-prod
FRONTEND_TEST_IMAGE  := vue-frontend-tester
FRONTEND_API_IMAGE   := vue-frontend-client-builder-prod

# Paths
FRONTEND_DIST_OUTPUT := app/front
TEST_RESULTS_OUTPUT  := component_tests
API_OUTPUT_PATH      := frontend/src/api

# Docker run user mapping (Linux-safe)
DOCKER_USER := $(shell id -u):$(shell id -g)

# =========================
# Targets
# =========================

.PHONY: help build-frontend test-frontend generate-api clean

help:
	@echo "Available targets:"
	@echo "  make build-frontend    Build frontend dist (app/front)"
	@echo "  make test-frontend     Run frontend component tests"
	@echo "  make generate-api      Generate OpenAPI frontend types"
	@echo "  make clean             Remove generated outputs"

# =========================
# Build frontend (prod)
# =========================

build-frontend:
	docker build \
		--file $(DOCKERFILE_PROD) \
		--tag $(FRONTEND_BUILD_IMAGE) \
		$(PROJECT_ROOT)

	mkdir -p $(FRONTEND_DIST_OUTPUT)

	docker run --rm \
		-u $(DOCKER_USER) \
		-v $(PROJECT_ROOT)/$(FRONTEND_DIST_OUTPUT):/output \
		$(FRONTEND_BUILD_IMAGE) \
		sh -c "cp -r /frontend/dist/* /output/"

# =========================
# Run frontend tests
# =========================

test-frontend:
	docker build \
		--file $(DOCKERFILE_DEV) \
		--build-arg BUILD_TYPE=development \
		--tag $(FRONTEND_TEST_IMAGE) \
		$(PROJECT_ROOT)

	mkdir -p $(TEST_RESULTS_OUTPUT)

	docker run --rm \
		-v $(PROJECT_ROOT)/$(TEST_RESULTS_OUTPUT):/frontend/test-results \
		$(FRONTEND_TEST_IMAGE) \
		sh -c "npm run test"

# =========================
# Generate frontend API types
# =========================

generate-api:
	docker build \
		--file $(DOCKERFILE_DEV) \
		--build-arg BUILD_TYPE=development \
		--tag $(FRONTEND_API_IMAGE) \
		$(PROJECT_ROOT)

	mkdir -p $(API_OUTPUT_PATH)

	docker run --rm \
		-u $(DOCKER_USER) \
		-v $(PROJECT_ROOT)/$(API_OUTPUT_PATH):/output \
		$(FRONTEND_API_IMAGE) \
		sh -c "npm run generate:type && cp /frontend/src/openapi.d.ts /output/openapi.d.ts"

# =========================
# Cleanup
# =========================

clean:
	rm -rf \
		$(FRONTEND_DIST_OUTPUT) \
		$(TEST_RESULTS_OUTPUT) \
		$(API_OUTPUT_PATH)
