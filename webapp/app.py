import os
import logging
import json
import time
from flask import Flask, render_template, request, jsonify, Response

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configuration constants from environment variables
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")
OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# Agent system message for the new fine-tuned model
AGENT_SYSTEM_MESSAGE = """
You are an expert Azure Bicep assistant. Your sole purpose is to generate accurate and best-practice Bicep code based *only* on the user's request and the provided context documents.

You MUST follow these rules strictly:
1.  **Prioritize AVM (Azure Verified Modules):** If the user's prompt or toggle (indicated in the augmented query) asks for an AVM, you **MUST** use the AVM `module` syntax. You **MUST** use the exact `Module ID` (including the version) provided in the context documents.
2.  **Use Classic Bicep:** If the user's prompt or toggle (indicated in the augmented query) explicitly asks for 'classic Bicep', 'non-AVM', or 'without a module', you **MUST** generate a classic Bicep `resource` definition. You **MUST** use the properties and resource types found in the "ARM Schema" context documents.
3.  **Strict Grounding:** Your response **MUST** be based *solely* on the information provided in the user request and the accompanying context documents. Do not hallucinate module paths.
4.  **Output Format:** You **MUST** return your final response as a single, valid JSON object. Do not provide any other text, conversation, or markdown formatting (like ```json).

**Required Output JSON Schema:**
```json
{
  "plan": {
    "resources": [
      {"resourceType": "e.g., br/public:avm/res/storage/storage-account:0.8.0", "name": "e.g., stg-prod-001"}
    ],
    "rationale": "A one-sentence explanation for the choice, e.g., 'User requested an AVM for Storage Account.'"
  },
  "files": [
    {"path": "main.bicep", "language": "bicep", "content": "The full, valid Bicep code."},
    {"path": "parameters.json", "language": "json", "content": "The full, valid parameters.json content."}
  ],
  "warnings": [
    "e.g., 'Fell back to classic Bicep as no AVM module was found in context.'"
  ]
}
```
"""

# Check if running in Azure (all required environment variables are set)
AZURE_ENABLED = all([SEARCH_ENDPOINT, SEARCH_INDEX_NAME, OPENAI_ENDPOINT, OPENAI_DEPLOYMENT_NAME])

# Initialize Azure clients only if Azure is enabled
search_client = None
openai_client = None

if AZURE_ENABLED:
    try:
        from openai import AzureOpenAI
        from azure.search.documents import SearchClient
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        # Initialize Azure credential
        credential = DefaultAzureCredential()

        # Initialize Azure Search client
        search_client = SearchClient(
            endpoint=SEARCH_ENDPOINT,
            index_name=SEARCH_INDEX_NAME,
            credential=credential
        )

        # Initialize Azure OpenAI client
        token_provider = get_bearer_token_provider(
            credential,
            "https://cognitiveservices.azure.com/.default"
        )

        openai_client = AzureOpenAI(
            azure_endpoint=OPENAI_ENDPOINT,
            api_version="2024-02-15-preview",  # Updated for JSON mode support
            azure_ad_token_provider=token_provider
        )

        print("✓ Azure services initialized successfully")
    except Exception as e:
        print(f"⚠ Warning: Failed to initialize Azure services: {e}")
        print("  Running in local development mode without Azure integration")
        AZURE_ENABLED = False
else:
    print("ℹ Running in local development mode (Azure environment variables not set)")

# Read version from version.txt
VERSION = "unknown"
try:
    version_path = os.path.join(os.path.dirname(__file__), 'version.txt')
    with open(version_path, 'r') as f:
        VERSION = f.read().strip()
except Exception as e:
    print(f"⚠ Warning: Could not read version.txt: {e}")

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', version=VERSION)

def generate_stream(user_query, unused_param, search_filter=None):
    """Generator function that yields SSE events for progress updates
    Note: unused_param is kept for backward compatibility but not used (agent uses AGENT_SYSTEM_MESSAGE)
    """
    try:
        yield f"data: {json.dumps({'status': 'progress', 'message': '🔍 Validating request...'})}\n\n"
        time.sleep(0.1)

        # Check if Azure services are available
        if not AZURE_ENABLED:
            yield f"data: {json.dumps({'status': 'progress', 'message': '⚠️ Running in local development mode...'})}\n\n"
            time.sleep(0.5)

            # Return a dummy response for local development
            dummy_bicep = f"""// Local development mode - Azure services not configured
// Received prompt: {user_query}

// Sample Bicep template
param location string = 'eastus'
param storageAccountName string

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {{
  name: storageAccountName
  location: location
  sku: {{
    name: 'Standard_LRS'
  }}
  kind: 'StorageV2'
}}

output storageAccountId string = storageAccount.id
"""
            yield f"data: {json.dumps({'status': 'complete', 'bicep': dummy_bicep})}\n\n"
            return

        # Perform Azure AI Search to retrieve relevant context
        yield f"data: {json.dumps({'status': 'progress', 'message': '🔎 Searching Azure AI Search for relevant context...'})}\n\n"
        app.logger.info(f"Performing AI Search with text: {user_query}")
        app.logger.info(f"Using search filter: {search_filter}")

        search_results = search_client.search(
            search_text=user_query,
            filter=search_filter,
            top=3,
            query_type="semantic",
            semantic_configuration_name='avm-semantic-config',
            vector_queries=[{
                "kind": "text",
                "text": user_query,
                "k": 3,
                "fields": "vector"
            }]
        )

        # Extract and format the retrieved content
        yield f"data: {json.dumps({'status': 'progress', 'message': '📚 Processing search results...'})}\n\n"

        retrieved_content = ""
        result_count = 0

        for result in search_results:
            result_count += 1
            content = result.get('content', 'No content available')
            retrieved_content += f"--- Context {result_count} ---\n{content}\n\n"

        # If no results found, set a default message
        if result_count == 0:
            retrieved_content = "No relevant context found."
            app.logger.warning("No search results found for the query")
            yield f"data: {json.dumps({'status': 'progress', 'message': '⚠️ No relevant context found, proceeding anyway...'})}\n\n"
        else:
            app.logger.info(f"Retrieved {result_count} context documents from AI Search")
            yield f"data: {json.dumps({'status': 'progress', 'message': f'✅ Found {result_count} relevant document(s)'})}\n\n"

        app.logger.info("--- Retrieved Context ---")
        app.logger.info(retrieved_content)
        app.logger.info("--- End Retrieved Context ---")

        # Construct the augmented prompt for the agent
        agent_user_prompt = f"""User Request: "{user_query}"

{retrieved_content}"""

        # Call Azure OpenAI with the agent model (JSON mode, no streaming)
        yield f"data: {json.dumps({'status': 'progress', 'message': '🤖 Generating Bicep code with Azure OpenAI agent...'})}\n\n"
        app.logger.info(f"Calling Azure OpenAI agent to generate Bicep code...\nAgent Prompt: {agent_user_prompt}")

        response = openai_client.chat.completions.create(
            model=OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": AGENT_SYSTEM_MESSAGE},
                {"role": "user", "content": agent_user_prompt}
            ],
            response_format={"type": "json_object"},  # Force JSON output
            temperature=0.1,  # Lower temperature for deterministic JSON
            max_tokens=4096
        )

        # Parse the JSON response from the model
        model_response_content = response.choices[0].message.content
        app.logger.info(f"Received JSON response from agent model")

        try:
            response_data = json.loads(model_response_content)
            app.logger.info(f"Successfully parsed JSON response")

            # Extract the Bicep code from the JSON structure
            generated_bicep = ""
            for file_obj in response_data.get("files", []):
                if file_obj.get("path") == "main.bicep":
                    generated_bicep = file_obj.get("content", "")
                    break

            if not generated_bicep:
                # Fallback if main.bicep is not found
                app.logger.error("Model response did not contain a 'main.bicep' file")
                generated_bicep = "# ERROR: Model did not generate a main.bicep file."

            # Log plan and warnings for debugging
            plan = response_data.get("plan", {})
            warnings = response_data.get("warnings", [])
            app.logger.info(f"Plan: {plan}")
            if warnings:
                app.logger.info(f"Warnings: {warnings}")

        except json.JSONDecodeError as e:
            app.logger.error(f"Failed to parse model's JSON response: {e}", exc_info=True)
            app.logger.error(f"Raw response: {model_response_content[:500]}")
            generated_bicep = f"# ERROR: Model returned invalid JSON\n# {str(e)}"

        app.logger.info('Successfully generated Bicep code')

        # Return the generated Bicep code
        yield f"data: {json.dumps({'status': 'complete', 'bicep': generated_bicep})}\n\n"

    except Exception as e:
        # Log the full error with traceback
        app.logger.error(f"Error during generation: {e}", exc_info=True)

        # Send error event
        yield f"data: {json.dumps({'status': 'error', 'error': 'An error occurred while generating the Bicep template. Please try again or contact support if the problem persists.'})}\n\n"

@app.route('/generate', methods=['POST'])
def generate():
    """Endpoint that streams progress updates using Server-Sent Events"""
    try:
        # Get JSON data from request body
        data = request.get_json()

        # Check if data exists
        if not data:
            app.logger.warning("Request received with no data")
            return jsonify({"error": "No data provided"}), 400

        # Extract the prompt value
        user_query = data.get('prompt')

        # Check if prompt is missing or empty
        if not user_query:
            app.logger.warning("Request received with empty prompt")
            return jsonify({"error": "Prompt is required"}), 400

        # Extract the mode (default to 'avm' if not provided)
        mode = data.get('mode', 'avm')

        # Validate mode
        if mode not in ['avm', 'classic']:
            app.logger.warning(f"Invalid mode received: {mode}, defaulting to 'avm'")
            mode = 'avm'

        # Initialize search filter and augmented query
        search_filter = None
        augmented_user_query = user_query

        # Set filter and query augmentation based on mode
        if mode == 'avm':
            search_filter = "search.ismatch('AVM Module', 'content')"
            augmented_user_query += " avm"
        else:  # mode == 'classic'
            search_filter = "search.ismatch('ARM Schema', 'content')"
            augmented_user_query += " classic non-avm"

        # Log the filter and augmented query
        app.logger.info(f'Search filter: {search_filter}')
        app.logger.info(f'Augmented user query: {augmented_user_query}')
        app.logger.info(f'Mode: {mode}')

        # Return SSE stream (note: system_message is no longer needed, agent uses AGENT_SYSTEM_MESSAGE)
        return Response(
            generate_stream(augmented_user_query, None, search_filter),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        # Log the full error with traceback
        app.logger.error(f"Error during generation: {e}", exc_info=True)

        # Return a user-friendly error message
        return jsonify({
            "error": "An error occurred while generating the Bicep template. Please try again or contact support if the problem persists."
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
