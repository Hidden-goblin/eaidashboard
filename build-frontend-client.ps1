# build-frontend.ps1
# Script PowerShell pour builder le frontend Vue.js dans Docker et copier le résultat dans app/static

$ErrorActionPreference = "Stop"

# Variables
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$dockerfilePath = Join-Path $projectRoot "docker-build-frontend\DockerfileDev"
$outputPath = Join-Path $projectRoot "frontend\src\api"

# 1. Build de l'image Docker
docker build --file $dockerfilePath --build-arg BUILD_TYPE=development --tag vue-frontend-client-builder-prod $projectRoot

# 2. Création du dossier de sortie si nécessaire
if (-Not (Test-Path -Path $outputPath)) {
    New-Item -ItemType Directory -Force -Path $outputPath | Out-Null
}

# 3. Exécution d’un conteneur temporaire pour copier les fichiers buildés
#docker run --rm -v "${outputPath}:/output" vue-frontend-client-builder-prod `
#    sh -c "npm run generate:api && cp -r /frontend/src/api/ /output/"
docker run --rm -v "${outputPath}:/output" vue-frontend-client-builder-prod `
    sh -c "npm run generate:type && cp -r /frontend/src/openapi.d.ts /output/openapi.d.ts"