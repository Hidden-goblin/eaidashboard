#!/usr/bin/env bash
# build-frontend.sh
# Script Bash pour builder le frontend Vue.js dans Docker et copier le résultat dans app/front

set -e  # Stop on first error

# Variables
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKERFILE_PATH="$PROJECT_ROOT/docker-build-frontend/Dockerfile"
OUTPUT_PATH="$PROJECT_ROOT/app/front"

# 1. Build de l'image Docker
docker build \
  --file "$DOCKERFILE_PATH" \
  --tag vue-frontend-builder-prod \
  "$PROJECT_ROOT"

# 2. Création du dossier de sortie si nécessaire
mkdir -p "$OUTPUT_PATH"

# 3. Exécution d’un conteneur temporaire pour copier les fichiers buildés
docker run --rm \
  -v "$OUTPUT_PATH:/output" \
  vue-frontend-builder-prod \
  sh -c "cp -r /frontend/dist/* /output/"
