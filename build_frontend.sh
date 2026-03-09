#!/bin/bash
set -e

docker build -t vue-frontend-builder -f docker-build-frontend/Dockerfile .

# Crée le répertoire static s'il n'existe pas
mkdir -p app/front

# Lance un conteneur temporaire pour extraire les fichiers buildés
docker run --rm -v $(pwd)/app/front:/output vue-frontend-builder \
    sh -c "cp -r /frontend/dist/* /output/"
