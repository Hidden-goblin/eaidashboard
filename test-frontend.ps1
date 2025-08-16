# test-frontend.ps1
# Script PowerShell pour builder l'image Docker, exécuter les tests et copier les résultats dans component_tests/

$ErrorActionPreference = "Stop"

# Variables
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$dockerfilePath = Join-Path $projectRoot "docker-build-frontend\DockerfileDev"
$resultsPath = Join-Path $projectRoot "component_tests"
$dockerImageName = "vue-frontend-tester"

# 1. Build Docker image (réutilise celle du build ou une dédiée aux tests)
docker build --file $dockerfilePath --build-arg BUILD_TYPE=development --tag $dockerImageName $projectRoot

# 2. Crée le dossier local de résultats s’il n’existe pas
if (-Not (Test-Path -Path $resultsPath)) {
    New-Item -ItemType Directory -Force -Path $resultsPath | Out-Null
}

# 3. Lance les tests dans le conteneur Docker
# On suppose ici que :
# - les tests génèrent des résultats dans /frontend/test-results dans le conteneur
# - la commande de test est `npm run test` (ou `vitest run --reporter=...`)

docker run --rm -v "${resultsPath}:/frontend/test-results" $dockerImageName `
    sh -c "npm ci && npm run test"

# 💡 Adaptation si tu génères du HTML :
# sh -c "npm ci && npm run test && cp -r test-results/* /results/"