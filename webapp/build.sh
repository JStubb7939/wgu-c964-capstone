#!/bin/bash
# Build and Deploy Script for ARM Template Generator
# Usage: ./build.sh [version]
# Example: ./build.sh 1.0.1

set -e

# Configuration
REGISTRY_NAME="c964registry"
REGISTRY="${REGISTRY_NAME}.azurecr.io"
IMAGE_NAME="arm-template-generator"
VERSION_FILE="version.txt"
LOG_FILE="build.log"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Start logging (overwrite existing log file)
exec > >(tee "$LOG_FILE") 2>&1

echo -e "${CYAN}=== ARM Template Generator - Build & Deploy ===${NC}"
echo -e "${GRAY}Build log will be saved to: $LOG_FILE${NC}"
echo ""

# Update version if provided
if [ -n "$1" ]; then
    VERSION="$1"
    echo -e "${YELLOW}Updating version to: $VERSION${NC}"
    echo -n "$VERSION" > "$VERSION_FILE"
    echo -e "${GREEN}✓ Version updated in $VERSION_FILE${NC}"
else
    # Read current version
    if [ -f "$VERSION_FILE" ]; then
        VERSION=$(cat "$VERSION_FILE" | tr -d '\n')
        echo -e "${YELLOW}Using current version: $VERSION${NC}"
    else
        echo -e "${RED}Error: version.txt not found and no version specified!${NC}"
        echo -e "${YELLOW}Usage: ./build.sh [version]${NC}"
        exit 1
    fi
fi

echo ""

# Build Docker image
echo -e "${CYAN}Building Docker image...${NC}"
IMAGE_TAG="${REGISTRY}/${IMAGE_NAME}:${VERSION}"
IMAGE_LATEST="${REGISTRY}/${IMAGE_NAME}:latest"

docker build -t "$IMAGE_TAG" -t "$IMAGE_LATEST" .

echo -e "${GREEN}✓ Docker image built successfully${NC}"
echo -e "${GRAY}  Tags: $IMAGE_TAG, $IMAGE_LATEST${NC}"
echo ""

# Log into registry
echo -e "${CYAN}Logging into Azure Container Registry...${NC}"
az acr login --name $REGISTRY_NAME
echo -e "${GREEN}✓ Logged in successfully${NC}"

# Push to registry
echo -e "${CYAN}Pushing to Azure Container Registry...${NC}"

# Push versioned tag
docker push "$IMAGE_TAG"
echo -e "${GREEN}✓ Pushed: $IMAGE_TAG${NC}"

# Push latest tag
docker push "$IMAGE_LATEST"
echo -e "${GREEN}✓ Pushed: $IMAGE_LATEST${NC}"

# Log out of ACR
echo -e "${CYAN}Logging out of ACR...${NC}"
docker logout $REGISTRY
echo -e "${GREEN}✓ Logged out of ACR${NC}"

echo ""
echo -e "${GREEN}=== Build & Deploy Complete ===${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "${GRAY}  1. Restart your Azure Container App to use the new image${NC}"
echo -e "${GRAY}     az containerapp revision restart --name arm-template-generator --resource-group <your-rg>${NC}"
echo ""
echo -e "${GRAY}  2. Or trigger automatic deployment if configured${NC}"
echo ""
echo -e "${GRAY}Build log saved to: $LOG_FILE${NC}"
