# Azure Bicep Template Generator

A web application that generates Azure Bicep Infrastructure as Code (IaC) templates using natural language prompts. Powered by Azure AI Search and Azure OpenAI, this tool leverages Retrieval-Augmented Generation (RAG) to create accurate, best-practice Bicep code based on Azure Verified Modules (AVM) and ARM resource schemas.

## Features

- 🤖 **AI-Powered Generation**: Uses Azure OpenAI with streaming to generate Bicep templates from natural language descriptions
- 🔍 **Smart Context Retrieval**: Employs Azure AI Search with semantic and vector hybrid search to find relevant documentation
- 📚 **AVM Support**: Generates code using Azure Verified Modules (official, maintained modules) by default
- ⚙️ **Dual Mode**: Toggle between AVM-based templates or classic Bicep resource definitions
- 📊 **Real-Time Progress**: Live status updates show each stage of the generation process
- ⚡ **Streaming Responses**: Token-by-token streaming creates a typewriter effect for improved perceived speed
- 💻 **User-Friendly Interface**: Clean, modern UI with syntax highlighting and code management tools
- 📋 **Code Tools**: Copy to clipboard, download as .bicep file, and word wrap toggle
- 📝 **Example Prompts**: Quick-start examples with one-click insertion
- 🔢 **Version Display**: Application version shown in footer
- 🎨 **Custom Favicon**: Branded Azure ARM icon
- 🔨 **Build Automation**: Automated build scripts with logging for easy deployment

## Architecture

### Technology Stack

- **Backend**: Python Flask 3.x
- **Frontend**: HTML, JavaScript, Tailwind CSS, Prism.js
- **AI Services**:
  - Azure OpenAI (GPT models)
  - Azure AI Search (semantic + vector search)
- **Authentication**: Azure Managed Identity (DefaultAzureCredential)
- **Deployment**: Docker container on Azure Container Apps

### RAG Pipeline with Streaming

1. **User Input**: Natural language prompt describing desired Azure infrastructure
2. **Mode Selection**: User chooses between AVM or Classic Bicep generation
3. **Context Retrieval**: Azure AI Search performs hybrid search (semantic + vector) to find relevant:
   - Azure Verified Module documentation
   - ARM resource schema definitions
4. **Augmentation**: Retrieved context is combined with user prompt and mode-specific system instructions
5. **Streaming Generation**: Azure OpenAI generates Bicep code token-by-token with real-time display
6. **Post-Processing**: Code is cleaned and formatted for final display

**Real-Time Progress Updates**:

- 🔍 Validating request
- 🔎 Searching Azure AI Search for relevant context
- 📚 Processing search results
- ✅ Found N relevant documents
- ✨ Streaming code (token-by-token display)
- ✅ Template generated successfully

## Getting Started

### Prerequisites

- Python 3.13+
- Azure subscription
- Azure OpenAI resource with a GPT deployment
- Azure AI Search service with indexed AVM and schema data
- Docker (for containerized deployment)

### Environment Variables

Create a `.env` file or set the following environment variables:

```bash
# Azure AI Search
AZURE_SEARCH_SERVICE_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_INDEX_NAME=your-index-name

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-gpt-deployment-name
```

### Local Development

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd webapp
   ```

2. **Create a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables** (or create `.env` file)

5. **Run the application**:

   ```bash
   python app.py
   ```

6. **Open in browser**: Navigate to `http://localhost:5000`

### Local Development Mode

If Azure services are not configured, the app runs in local development mode and returns dummy Bicep templates. This is useful for UI testing without Azure dependencies.

## Usage

### Basic Workflow

1. **Choose Generation Mode**:
   - **Use Azure Verified Modules (AVM)** (Recommended): Generates code using official, maintained modules
   - **Classic Bicep**: Generates raw resource definitions

2. **Enter Your Prompt**: Describe the Azure infrastructure you want to create. Include:
   - Resource type (e.g., Storage Account, Virtual Machine)
   - Configuration details (SKU, tier, redundancy)
   - Location/region
   - Dependencies or related resources
   - Security requirements

3. **Generate**: Click "Generate Bicep Template" and watch real-time progress updates

4. **Review & Use**: Copy the generated code to clipboard or download as a `.bicep` file

### Example Prompts

- "Create a storage account with blob storage, geo-redundant storage, and HTTPS-only access in East US"
- "Deploy an App Service with B1 tier, .NET 8 runtime, and integrate with Application Insights"
- "Set up a virtual network with two subnets: one for web tier and one for database tier"
- "Create a Key Vault with RBAC enabled and soft-delete protection"

### Best Practices for Prompts

- **Be Specific**: Include exact SKUs, tiers, and configuration values
- **Mention Dependencies**: Note related resources or connections
- **Specify Security**: Include access controls, encryption requirements
- **Name Locations**: Mention Azure regions if specific placement is needed
- **Use Azure Terminology**: Reference Azure-specific names (e.g., "geo-redundant storage" not "GRS")

## Deployment

### Automated Build Scripts

The repository includes automated build scripts that handle version management, Docker build, and registry push:

**PowerShell (Windows)**:

```bash
# Build with current version
.\build.ps1

# Build with new version (updates version.txt automatically)
.\build.ps1 1.0.1
```

**Bash (Linux/Mac/Git Bash)**:

```bash
# Build with current version
./build.sh

# Build with new version (updates version.txt automatically)
./build.sh 1.0.1
```

**Features**:

- ✅ Automatic version management
- ✅ Docker build with version tagging (`:version` and `:latest`)
- ✅ Azure Container Registry login and push
- ✅ Build logs saved to `build.log` (overwritten each run)
- ✅ Color-coded console output
- ✅ Error handling and exit codes

### Manual Docker Build & Push

If you prefer manual deployment:

1. **Build the Docker image**:

   ```bash
   docker build -t c964registry.azurecr.io/arm-template-generator:latest .
   ```

2. **Push to Azure Container Registry**:

   ```bash
   az acr login --name c964registry
   docker push c964registry.azurecr.io/arm-template-generator:latest
   ```

### Azure Container Apps Deployment

1. **Create Container App**:

   ```bash
   az containerapp create \
     --name arm-template-generator \
     --resource-group <your-rg> \
     --image your-registry.azurecr.io/arm-template-generator:latest \
     --environment <your-environment> \
     --ingress external \
     --target-port 8000
   ```

2. **Enable Managed Identity**:

   ```bash
   az containerapp identity assign \
     --name arm-template-generator \
     --resource-group <your-rg> \
     --system-assigned
   ```

3. **Set Environment Variables**:

   ```bash
   az containerapp update \
     --name arm-template-generator \
     --resource-group <your-rg> \
     --set-env-vars \
       AZURE_SEARCH_SERVICE_ENDPOINT=<endpoint> \
       AZURE_SEARCH_INDEX_NAME=<index-name> \
       AZURE_OPENAI_ENDPOINT=<endpoint> \
       AZURE_OPENAI_DEPLOYMENT_NAME=<deployment-name>
   ```

4. **Assign RBAC Roles**:

   Get the Managed Identity principal ID:

   ```bash
   PRINCIPAL_ID=$(az containerapp identity show \
     --name arm-template-generator \
     --resource-group <your-rg> \
     --query principalId -o tsv)
   ```

   Assign Search Index Data Reader role:

   ```bash
   az role assignment create \
     --role "Search Index Data Reader" \
     --assignee $PRINCIPAL_ID \
     --scope /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Search/searchServices/<search-service>
   ```

   Assign Cognitive Services OpenAI User role:

   ```bash
   az role assignment create \
     --role "Cognitive Services OpenAI User" \
     --assignee $PRINCIPAL_ID \
     --scope /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<openai-resource>
   ```

5. **Restart the Container App** (after role propagation):

   ```bash
   az containerapp revision restart \
     --name arm-template-generator \
     --resource-group <your-rg>
   ```

## Project Structure

```txt
webapp/
├── app.py                 # Flask application with RAG pipeline
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container image definition
├── version.txt           # Application version
├── build.ps1             # PowerShell build automation script
├── build.sh              # Bash build automation script
├── .gitignore            # Git exclusions (build.log, etc.)
├── templates/
│   └── index.html        # Main UI template with AVM/Classic toggle
├── static/
│   ├── index.js          # Client-side JavaScript with SSE handling
│   └── azure_arm.png     # Favicon
└── README.md             # This file
```

## API Endpoints

### `GET /`

Serves the main application interface.

### `POST /generate`

Generates Bicep code from a natural language prompt using Server-Sent Events (SSE) for real-time progress updates.

**Request Body**:

```json
{
  "prompt": "Create a storage account...",
  "mode": "avm"  // or "classic"
}
```

**Response**: SSE stream with JSON events:

```json
{"status": "progress", "message": "🔍 Validating request..."}
{"status": "progress", "message": "🔎 Searching Azure AI Search..."}
{"status": "progress", "message": "✅ Found 3 relevant document(s)"}
{"status": "streaming", "message": "✨ Streaming code..."}
{"status": "chunk", "content": "resource "}
{"status": "chunk", "content": "storageAccount "}
{"status": "complete", "bicep": "// Complete generated Bicep code..."}
```

**Event Types**:

- `progress`: Status updates during processing
- `streaming`: Indicates token-by-token streaming has begun
- `chunk`: Individual code tokens for real-time display
- `complete`: Final complete Bicep code
- `error`: Error message if generation fails

## Configuration

### Azure AI Search Index

The search index should contain:

- **AVM Module Documentation**: Descriptions, parameters, examples
- **ARM Resource Schemas**: Resource type definitions, API versions, properties

Required fields:

- `content`: Text content for semantic search
- `vector`: Embeddings for vector search

Search configuration:

- Semantic configuration: `avm-semantic-config`
- Vector field: `vector`
- Top results: 3 (configurable in code)

### System Messages

Two system messages guide AI behavior:

**AVM Mode**: Prioritizes Azure Verified Modules, uses them when sufficient for user requirements

**Classic Mode**: Generates classic Bicep resource definitions, avoids AVM modules

## Troubleshooting

### 403 Forbidden Errors

- **Cause**: Managed Identity lacks required RBAC roles
- **Solution**: Assign "Search Index Data Reader" and "Cognitive Services OpenAI User" roles
- **Note**: Role propagation can take 5-10 minutes

### No Search Results

- **Cause**: Index empty, query mismatch, or search service issues
- **Solution**: Verify index has data, test queries in Azure portal
- **Fallback**: App continues generation with "No relevant context found" message

### Connection Errors

- **Cause**: Incorrect endpoints or credential issues
- **Solution**: Verify environment variables, check Managed Identity is enabled
- **Fallback**: App runs in local development mode with dummy responses

### Rate Limiting

- **Cause**: Exceeded OpenAI API quota
- **Solution**: Increase quota or implement retry logic
- **Current Handling**: Returns error to user

## Security Considerations

- ✅ **Managed Identity**: Uses Azure AD authentication, no API keys in code
- ✅ **RBAC**: Least-privilege access with specific role assignments
- ✅ **Input Validation**: Validates user input before processing
- ✅ **Error Handling**: Sanitizes error messages, logs details server-side
- ⚠️ **Rate Limiting**: Consider implementing request throttling for production
- ⚠️ **Content Filtering**: Azure OpenAI includes content filtering by default

## Performance Considerations

- **Search Latency**: Hybrid search typically ~100-500ms
- **OpenAI Generation**: Varies by model and output length, typically 2-10 seconds
- **Total Time**: Expect 3-15 seconds end-to-end for most requests
- **Optimization**: Results cached in browser, consider server-side caching for common queries

## License

[Specify your license here]

## Contributing

[Add contribution guidelines if applicable]

## Support

[Add support contact information]

## Acknowledgments

- Built with [Azure OpenAI Service](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
- Powered by [Azure AI Search](https://azure.microsoft.com/en-us/products/ai-services/ai-search)
- Uses [Azure Verified Modules](https://azure.github.io/Azure-Verified-Modules/)
- Syntax highlighting by [Prism.js](https://prismjs.com/)
- Styled with [Tailwind CSS](https://tailwindcss.com/)
