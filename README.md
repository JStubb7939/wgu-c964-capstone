# Azure Bicep Template Generator

A web application that generates Azure Bicep Infrastructure as Code (IaC) templates using natural language prompts. Powered by Azure AI Search and a fine-tuned Azure OpenAI agent, this tool leverages Retrieval-Augmented Generation (RAG) with agentic reasoning to create accurate, best-practice Bicep code based on Azure Verified Modules (AVM) and ARM resource schemas.

## Features

- **Agentic AI Generation**: Uses a fine-tuned Azure OpenAI agent model that reasons about infrastructure requirements and generates structured outputs
- **Smart Context Retrieval**: Employs Azure AI Search with semantic and vector hybrid search to find relevant documentation
- **AVM Support**: Generates code using Azure Verified Modules (official, maintained modules) by default
- **Dual Mode**: Toggle between AVM-based templates or classic Bicep resource definitions
- **Real-Time Progress**: Live status updates show each stage of the generation process
- **Structured Output**: Agent returns JSON with plan, files (main.bicep + parameters.json), and warnings
- **User-Friendly Interface**: Clean, modern UI with syntax highlighting and code management tools
- **Code Tools**: Copy to clipboard, download as .bicep file, and word wrap toggle
- **Example Prompts**: Quick-start examples with one-click insertion
- **Version Display**: Application version shown in footer
- **Custom Favicon**: Branded Azure ARM icon
- **Build Automation**: Automated build scripts with logging for easy deployment

## Architecture

### Technology Stack

- **Backend**: Python Flask 3.x
- **Frontend**: HTML, JavaScript, Tailwind CSS, Prism.js
- **AI Services**:
  - Azure OpenAI (Fine-tuned GPT-4.1-mini agent model)
  - Azure AI Search (semantic + vector hybrid search)
- **Authentication**: Azure Managed Identity (DefaultAzureCredential)
- **Deployment**: Docker container on Azure Container Apps

### Agentic RAG Pipeline

The application uses an **agentic workflow** with a fine-tuned model that reasons about infrastructure requirements:

1. **User Input**: Natural language prompt describing desired Azure infrastructure
2. **Mode Selection**: User chooses between AVM or Classic Bicep generation
3. **Context Retrieval**: Azure AI Search performs hybrid search (semantic + vector) to find relevant:
   - Azure Verified Module documentation (filtered by mode)
   - ARM resource schema definitions (filtered by mode)
4. **Augmentation**: Retrieved context is combined with user prompt and provided to the agent
5. **Agentic Generation**: Fine-tuned agent model analyzes requirements and generates structured JSON output:
   - **Plan**: Rationale and list of resources to be created
   - **Files**: main.bicep and parameters.json with full content
   - **Warnings**: Fallback notices or caveats
6. **Extraction**: Backend extracts main.bicep from JSON response
7. **Display**: Client receives complete Bicep code via Server-Sent Events

**Real-Time Progress Updates**:

- Validating request
- Searching Azure AI Search for relevant context
- Processing search results
- Found N relevant documents
- Generating Bicep code with Azure OpenAI agent
- Template generated successfully

### Agent Model Behavior

The fine-tuned agent is trained to:
- Return responses **only as valid JSON** (no markdown, no conversational text)
- **Prioritize AVM modules** when user requests AVM mode
- **Generate classic Bicep** when user requests classic mode
- **Base responses strictly on context** to avoid hallucinations
- Include a **plan** with rationale for architectural decisions
- Generate both **main.bicep** and **parameters.json** when applicable
- **warnings** when falling back or making assumptions

**Agent JSON Schema**:
```json
{
  "plan": {
    "resources": [
      {"resourceType": "br/public:avm/res/storage/storage-account:0.8.0", "name": "storageAccount"}
    ],
    "rationale": "User requested an AVM for Storage Account with specific configuration"
  },
  "files": [
    {"path": "main.bicep", "language": "bicep", "content": "...full bicep code..."},
    {"path": "parameters.json", "language": "json", "content": "...full parameters..."}
  ],
  "warnings": [
    "Fell back to classic Bicep as no AVM module was found in context"
  ]
}
```

## Getting Started

### Prerequisites

- Python 3.13+
- Azure subscription
- Azure OpenAI resource with a fine-tuned GPT deployment
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
AZURE_OPENAI_DEPLOYMENT_NAME=your-fine-tuned-gpt-deployment-name
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
   - **Use Azure Verified Modules (AVM)** (Recommended): Agent generates code using official, maintained modules
   - **Classic Bicep**: Agent generates raw resource definitions

2. **Enter Your Prompt**: Describe the Azure infrastructure you want to create. Include:
   - Resource type (e.g., Storage Account, Virtual Machine)
   - Configuration details (SKU, tier, redundancy)
   - Location/region
   - Dependencies or related resources
   - Security requirements

3. **Generate**: Click "Generate Template" and watch real-time progress updates

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

```powershell
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

- Automatic version management
- Docker build with version tagging (`:version` and `:latest`)
- Azure Container Registry login and push
- Build logs saved to `build.log` (overwritten each run)
- Color-coded console output
- Error handling and exit codes

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
       AZURE_OPENAI_DEPLOYMENT_NAME=<fine-tuned-deployment-name>
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
wgu-c964-capstone/
├── README.md                    # This file (project overview and documentation)
├── requirements.txt             # Project-level Python dependencies
├── documentation/               # Project documentation and guides
├── grounding-data/              # RAG context data (AVM modules, ARM schemas)
│   ├── extracted_avm_data.jsonl
│   ├── extracted_schema_data_1-of-2.jsonl
│   ├── extracted_schema_data_2-of-2.jsonl
│   └── scripts/                 # Data extraction scripts
├── training-data/               # Fine-tuning datasets for agent model
│   ├── train_agent.jsonl
│   ├── train_agent_training.jsonl
│   ├── train_agent_validation.jsonl
│   └── scripts/                 # Training data processing scripts
└── webapp/                      # Flask web application
    ├── app.py                   # Flask application with agentic RAG pipeline
    ├── requirements.txt         # Web app Python dependencies
    ├── Dockerfile               # Container image definition
    ├── version.txt              # Application version
    ├── build.ps1                # PowerShell build automation script
    ├── build.sh                 # Bash build automation script
    ├── templates/
    │   └── index.html           # Main UI template with AVM/Classic toggle
    └── static/
        ├── index.js             # Client-side JavaScript with SSE handling
        └── azure_arm.png        # Favicon
        └── architecture_diagram.png
        └── rag_data_composition.png
        └── request-flow.png
        └── training-accuracy-graph.png
        └── training-loss-graph.png
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
{"status": "progress", "message": "Validating request..."}
{"status": "progress", "message": "Searching Azure AI Search for relevant context..."}
{"status": "progress", "message": "Found 2 relevant document(s)"}
{"status": "progress", "message": "Generating Bicep code with Azure OpenAI agent..."}
{"status": "complete", "bicep": "// Complete generated Bicep code from agent..."}
```

**Event Types**:

- `progress`: Status updates during processing
- `complete`: Final complete Bicep code extracted from agent response
- `error`: Error message if generation fails

**Note**: The agent does not support token-by-token streaming due to JSON mode requirements. The complete response is generated and then returned via SSE.

## Configuration

### Azure AI Search Index

The search index should contain:

- **AVM Module Documentation**: Descriptions, parameters, examples, module IDs
- **ARM Resource Schemas**: Resource type definitions, API versions, properties

Required fields:

- `content`: Text content for semantic search (should include "AVM Module" or "ARM Schema" markers)
- `vector`: Embeddings for vector search

Search configuration:

- Semantic configuration: `avm-semantic-config`
- Vector field: `vector`
- Top results: 2 (optimized for token limits)
- Context truncation: Max 3000 chars per document (~750 tokens)

**Search Filters**:

- AVM mode: `search.ismatch('AVM Module', 'content')`
- Classic mode: `search.ismatch('ARM Schema', 'content')`

### Agent System Message

The application uses a single `AGENT_SYSTEM_MESSAGE` that instructs the model to:

- Return only valid JSON (no markdown, no conversation)
- Prioritize AVM modules when requested
- Use classic Bicep when requested
- Base responses strictly on provided context
- Include plan, files, and warnings in structured output

**API Configuration**:

- API Version: `2024-02-15-preview` (supports JSON mode)
- Response Format: `{"type": "json_object"}` (forces JSON output)
- Temperature: `0.1` (deterministic for consistent JSON)
- Max Tokens: Dynamically calculated based on context size (up to 8192, respecting 128k context window)
- Timeout: 60 seconds

## Troubleshooting

### 403 Forbidden Errors

- **Cause**: Managed Identity lacks required RBAC roles
- **Solution**: Assign "Search Index Data Reader" and "Cognitive Services OpenAI User" roles
- **Note**: Role propagation can take 5-10 minutes

### No Search Results

- **Cause**: Index empty, query mismatch, or search service issues
- **Solution**: Verify index has data, check content includes "AVM Module" or "ARM Schema" markers
- **Fallback**: App continues generation with "No relevant context found" message

### Connection Errors

- **Cause**: Incorrect endpoints or credential issues
- **Solution**: Verify environment variables, check Managed Identity is enabled
- **Fallback**: App runs in local development mode with dummy responses

### JSON Parsing Errors

- **Cause**: Agent returned invalid JSON or response was truncated
- **Solution**: Check logs for "Raw response", verify model deployment, increase max_tokens if needed
- **Current Handling**: Returns error with JSON parse details

### Rate Limiting / Token Limits

- **Cause**: Exceeded OpenAI API quota or token context window
- **Solution**:
  - Context is automatically truncated to 3000 chars per document
  - Max output tokens calculated dynamically with safety buffer
  - Search reduced to 2 results to minimize input tokens
- **Current Handling**: Returns error to user with timeout or token limit message

## Security Considerations

- **Managed Identity**: Uses Azure AD authentication, no API keys in code
- **RBAC**: Least-privilege access with specific role assignments
- **Input Validation**: Validates user input before processing
- **Error Handling**: Sanitizes error messages, logs details server-side
- **Grounded Responses**: Agent trained to avoid hallucinations, uses only provided context
- **Rate Limiting**: Consider implementing request throttling for production
- **Content Filtering**: Azure OpenAI includes content filtering by default

## Performance Considerations

- **Search Latency**: Hybrid search typically ~100-500ms
- **Agent Generation**: Non-streaming JSON mode, typically 3-8 seconds depending on complexity
- **Total Time**: Expect 4-10 seconds end-to-end for most requests
- **Context Optimization**:
  - Limited to 2 search results
  - Each document truncated to 3000 chars
  - Total context kept under ~8000 tokens
  - Dynamic max_tokens calculation ensures responses complete within limits
- **Optimization**: Results cached in browser, consider server-side caching for common queries

## Fine-Tuning Details

The agent model is fine-tuned on:

- **Training Data**: Azure Verified Module examples and ARM template patterns
- **Format**: JSON-structured training examples with plan/files/warnings schema
- **Base Model**: GPT-4.1-mini (efficient for structured outputs)
- **Specialization**: Bicep syntax, AVM module usage, parameter patterns, best practices

See `training-data/` directory for training datasets and `webapp/APP_UPDATE_NOTES.md` for technical implementation details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Azure OpenAI Service](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
- Powered by [Azure AI Search](https://azure.microsoft.com/en-us/products/ai-services/ai-search)
- Uses [Azure Verified Modules](https://azure.github.io/Azure-Verified-Modules/)
- Syntax highlighting by [Prism.js](https://prismjs.com/)
- Styled with [Tailwind CSS](https://tailwindcss.com/)
