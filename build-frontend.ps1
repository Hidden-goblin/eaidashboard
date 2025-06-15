# build-frontend.ps1
# Script PowerShell pour builder le frontend Vue.js dans Docker et copier le résultat dans app/static

$ErrorActionPreference = "Stop"

# Variables
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$dockerfilePath = Join-Path $projectRoot "docker-build-frontend\Dockerfile"
$frontendPath = Join-Path $projectRoot "frontend"
$outputPath = Join-Path $projectRoot "app\front"

# 1. Build de l'image Docker
docker build --file $dockerfilePath --tag vue-frontend-builder $projectRoot

# 2. Création du dossier de sortie si nécessaire
if (-Not (Test-Path -Path $outputPath)) {
    New-Item -ItemType Directory -Force -Path $outputPath | Out-Null
}

# 3. Exécution d’un conteneur temporaire pour copier les fichiers buildés
docker run --rm -v "${outputPath}:/output" vue-frontend-builder `
    sh -c "cp -r /frontend/dist/* /output/"
