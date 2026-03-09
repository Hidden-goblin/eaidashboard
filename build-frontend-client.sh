#!/usr/bin/env bash
# build-frontend.sh
# Script Bash pour builder le frontend Vue.js dans Docker et copier le résultat dans frontend/src/api

set -e  # Stop on first error

# Variables
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKERFILE_PATH="$PROJECT_ROOT/docker-build-frontend/DockerfileDev"
OUTPUT_PATH="$PROJECT_ROOT/frontend/src/api"
DOCKER_IMAGE_NAME="vue-frontend-client-builder-prod"

# 1. Build de l'image Docker
docker build \
  --file "$DOCKERFILE_PATH" \
  --build-arg BUILD_TYPE=development \
  --tag "$DOCKER_IMAGE_NAME" \
  "$PROJECT_ROOT"

# 2. Création du dossier de sortie si nécessaire
mkdir -p "$OUTPUT_PATH"

# 3. Exécution d’un conteneur temporaire pour copier les fichiers buildés
docker run --rm \
  -v "$OUTPUT_PATH:/output" \
  "$DOCKER_IMAGE_NAME" \
  sh -c "npm run generate:type && cp -r /frontend/src/openapi.d.ts /output/openapi.d.ts"
