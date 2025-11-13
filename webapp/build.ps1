param(
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"

$REGISTRY_NAME = "c964registry"
$REGISTRY = "${REGISTRY_NAME}.azurecr.io"
$IMAGE_NAME = "arm-template-generator"
$VERSION_FILE = "version.txt"
$LOG_FILE = "build.log"

Start-Transcript -Path $LOG_FILE -Force

Write-Host "=== ARM Template Generator - Build & Deploy ===" -ForegroundColor Cyan
Write-Host "Build log will be saved to: $LOG_FILE" -ForegroundColor Gray
Write-Host ""

if ($Version) {
    Write-Host "Updating version to: $Version" -ForegroundColor Yellow
    $Version | Out-File -FilePath $VERSION_FILE -Encoding utf8 -NoNewline
    Write-Host "✓ Version updated in $VERSION_FILE" -ForegroundColor Green
} else {
    if (Test-Path $VERSION_FILE) {
        $Version = Get-Content $VERSION_FILE -Raw
        $Version = $Version.Trim()
        Write-Host "Using current version: $Version" -ForegroundColor Yellow
    } else {
        Write-Host "Error: version.txt not found and no version specified!" -ForegroundColor Red
        Write-Host "Usage: .\build.ps1 [version]" -ForegroundColor Yellow
        Stop-Transcript
        exit 1
    }
}

Write-Host ""

Write-Host "Building Docker image..." -ForegroundColor Cyan
$IMAGE_TAG = "${REGISTRY}/${IMAGE_NAME}:${Version}"
$IMAGE_LATEST = "${REGISTRY}/${IMAGE_NAME}:latest"

docker build -t $IMAGE_TAG -t $IMAGE_LATEST .

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Docker build failed!" -ForegroundColor Red
    Stop-Transcript
    exit $LASTEXITCODE
}

Write-Host "✓ Docker image built successfully" -ForegroundColor Green
Write-Host "  Tags: $IMAGE_TAG, $IMAGE_LATEST" -ForegroundColor Gray
Write-Host ""

Write-Host "Logging into Azure Container Registry..." -ForegroundColor Cyan
az acr login --name $REGISTRY_NAME
Write-Host "✓ Logged in successfully" -ForegroundColor Green

Write-Host "Pushing to Azure Container Registry..." -ForegroundColor Cyan

docker push $IMAGE_TAG
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to push versioned image!" -ForegroundColor Red
    docker logout $REGISTRY
    Stop-Transcript
    exit $LASTEXITCODE
}
Write-Host "✓ Pushed: $IMAGE_TAG" -ForegroundColor Green

docker push $IMAGE_LATEST
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to push latest image!" -ForegroundColor Red
    docker logout $REGISTRY
    Stop-Transcript
    exit $LASTEXITCODE
}
Write-Host "✓ Pushed: $IMAGE_LATEST" -ForegroundColor Green

Write-Host "Logging out of ACR..." -ForegroundColor Cyan
docker logout $REGISTRY
Write-Host "✓ Logged out of ACR" -ForegroundColor Green

Write-Host ""
Write-Host "=== Build & Deploy Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Restart your Azure Container App to use the new image" -ForegroundColor Gray
Write-Host "     az containerapp revision restart --name arm-template-generator --resource-group <your-rg>" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Or trigger automatic deployment if configured" -ForegroundColor Gray
Write-Host ""

Stop-Transcript
Write-Host "Build log saved to: $LOG_FILE" -ForegroundColor Gray
Write-Host "     az containerapp revision restart --name arm-template-generator --resource-group <your-rg>" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Or trigger automatic deployment if configured" -ForegroundColor Gray
Write-Host ""
