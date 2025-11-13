#!/bin/bash

set -e

REGISTRY_NAME="c964registry"
REGISTRY="${REGISTRY_NAME}.azurecr.io"
IMAGE_NAME="arm-template-generator"
VERSION_FILE="version.txt"
LOG_FILE="build.log"

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
GRAY='\033[0;37m'
NOCOLOR='\033[0m'

exec > >(tee "$LOG_FILE") 2>&1

echo -e "${CYAN}=== ARM Template Generator - Build & Deploy ===${NOCOLOR}"
echo -e "${GRAY}Build log will be saved to: $LOG_FILE${NOCOLOR}"
echo ""

if [ -n "$1" ]; then
    VERSION="$1"
    echo -e "${YELLOW}Updating version to: $VERSION${NOCOLOR}"
    echo -n "$VERSION" > "$VERSION_FILE"
    echo -e "${GREEN}✓ Version updated in $VERSION_FILE${NOCOLOR}"
else
    if [ -f "$VERSION_FILE" ]; then
        VERSION=$(cat "$VERSION_FILE" | tr -d '\n')
        echo -e "${YELLOW}Using current version: $VERSION${NOCOLOR}"
    else
        echo -e "${RED}Error: version.txt not found and no version specified!${NOCOLOR}"
        echo -e "${YELLOW}Usage: ./build.sh [version]${NOCOLOR}"
        exit 1
    fi
fi

echo ""

echo -e "${CYAN}Building Docker image...${NOCOLOR}"
IMAGE_TAG="${REGISTRY}/${IMAGE_NAME}:${VERSION}"
IMAGE_LATEST="${REGISTRY}/${IMAGE_NAME}:latest"

docker build -t "$IMAGE_TAG" -t "$IMAGE_LATEST" .

echo -e "${GREEN}✓ Docker image built successfully${NOCOLOR}"
echo -e "${GRAY}  Tags: $IMAGE_TAG, $IMAGE_LATEST${NOCOLOR}"
echo ""

echo -e "${CYAN}Logging into Azure Container Registry...${NOCOLOR}"
az acr login --name $REGISTRY_NAME
echo -e "${GREEN}✓ Logged in successfully${NOCOLOR}"

echo -e "${CYAN}Pushing to Azure Container Registry...${NOCOLOR}"

docker push "$IMAGE_TAG"
echo -e "${GREEN}✓ Pushed: $IMAGE_TAG${NOCOLOR}"

docker push "$IMAGE_LATEST"
echo -e "${GREEN}✓ Pushed: $IMAGE_LATEST${NOCOLOR}"

echo -e "${CYAN}Logging out of ACR...${NOCOLOR}"
docker logout $REGISTRY
echo -e "${GREEN}✓ Logged out of ACR${NOCOLOR}"

echo ""
echo -e "${GREEN}=== Build & Deploy Complete ===${NOCOLOR}"
echo ""
echo -e "${YELLOW}Next steps:${NOCOLOR}"
echo -e "${GRAY}  1. Restart your Azure Container App to use the new image${NOCOLOR}"
echo -e "${GRAY}     az containerapp revision restart --name arm-template-generator --resource-group <your-rg>${NOCOLOR}"
echo ""
echo -e "${GRAY}  2. Or trigger automatic deployment if configured${NOCOLOR}"
echo ""
echo -e "${GRAY}Build log saved to: $LOG_FILE${NOCOLOR}"
