#!/usr/bin/env bash
# test-frontend.sh
# Script Bash pour builder l'image Docker, exécuter les tests et copier les résultats dans component_tests/

set -e  # Stop on first error

# Variables
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKERFILE_PATH="$PROJECT_ROOT/docker-build-frontend/DockerfileDev"
RESULTS_PATH="$PROJECT_ROOT/component_tests"
DOCKER_IMAGE_NAME="vue-frontend-tester"

# 1. Build Docker image (image dédiée aux tests)
docker build \
  --file "$DOCKERFILE_PATH" \
  --build-arg BUILD_TYPE=development \
  --tag "$DOCKER_IMAGE_NAME" \
  "$PROJECT_ROOT"

# 2. Crée le dossier local de résultats s’il n’existe pas
mkdir -p "$RESULTS_PATH"

# 3. Lance les tests dans le conteneur Docker
# Hypothèses :
# - les tests écrivent dans /frontend/test-results
# - la commande de test est `npm run test`

docker run --rm \
  -v "$RESULTS_PATH:/frontend/test-results" \
  "$DOCKER_IMAGE_NAME" \
  sh -c "npm ci && npm run test"

# 💡 Si génération de rapports HTML ailleurs :
# docker run --rm \
#   -v \"$RESULTS_PATH:/results\" \
#   \"$DOCKER_IMAGE_NAME\" \
#   sh -c \"npm ci && npm run test && cp -r test-results/* /results/\"
