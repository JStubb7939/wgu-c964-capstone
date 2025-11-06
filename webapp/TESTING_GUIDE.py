"""
Quick Testing Guide for Updated Agentic Webapp
================================================

ENVIRONMENT SETUP
-----------------
Set these environment variables before running:

export AZURE_SEARCH_SERVICE_ENDPOINT="https://your-search.search.windows.net"
export AZURE_SEARCH_INDEX_NAME="your-index-name"
export AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini-2024-07-18-ft-f5669b4111424563a3951e228c98ea96"

Or in PowerShell:
$env:AZURE_SEARCH_SERVICE_ENDPOINT="https://your-search.search.windows.net"
$env:AZURE_SEARCH_INDEX_NAME="your-index-name"
$env:AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com"
$env:AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini-2024-07-18-ft-f5669b4111424563a3951e228c98ea96"


RUNNING THE APP
---------------
cd webapp
python app.py

Or with Flask:
flask run


TESTING ENDPOINTS
-----------------

1. Test AVM Mode (Default):
   curl -X POST http://localhost:5000/generate \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Deploy a Storage Account using AVM", "mode": "avm"}'

2. Test Classic Mode:
   curl -X POST http://localhost:5000/generate \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Deploy a Storage Account with classic Bicep", "mode": "classic"}'


EXPECTED RESPONSES
------------------

The endpoint returns Server-Sent Events (SSE) with progress updates:

1. Initial validation:
   data: {"status": "progress", "message": "🔍 Validating request..."}

2. Search phase:
   data: {"status": "progress", "message": "🔎 Searching Azure AI Search..."}
   data: {"status": "progress", "message": "✅ Found X relevant document(s)"}

3. Generation phase:
   data: {"status": "progress", "message": "🤖 Generating Bicep code with Azure OpenAI agent..."}

4. Final response:
   data: {"status": "complete", "bicep": "<bicep_code_here>"}

Or on error:
   data: {"status": "error", "error": "<error_message>"}


WHAT TO CHECK IN LOGS
----------------------

✅ SUCCESS INDICATORS:
- "Successfully parsed JSON response"
- "Plan: {'resources': [...]}"
- "Successfully generated Bicep code"

❌ ERROR INDICATORS:
- "Failed to parse model's JSON response"
- "Model response did not contain a 'main.bicep' file"
- "JSONDecodeError"

Sample successful log output:
  [INFO] Calling Azure OpenAI agent to generate Bicep code...
  [INFO] Received JSON response from agent model
  [INFO] Successfully parsed JSON response
  [INFO] Plan: {'resources': [{'resourceType': 'br/public:avm/res/storage/storage-account:0.8.0', 'name': 'storageAccount'}], 'rationale': 'User requested an AVM for Storage Account.'}
  [INFO] Successfully generated Bicep code


DEBUGGING TIPS
--------------

1. If model returns invalid JSON:
   - Check logs for "Raw response:" to see what model returned
   - Verify model deployment name is correct
   - Ensure API version supports JSON mode (2024-02-15-preview+)

2. If no Bicep code is extracted:
   - Check if files array contains "main.bicep"
   - Review the full JSON response in logs
   - Model might have returned an error in warnings array

3. If search returns no results:
   - Verify search index is populated
   - Check search filter is correct for mode
   - Review augmented query in logs

4. Authentication issues:
   - Ensure DefaultAzureCredential has access
   - Check Azure RBAC permissions
   - Verify endpoint URLs are correct


SAMPLE TEST PROMPTS
-------------------

AVM Mode:
- "Deploy a Storage Account using AVM with geo-redundant storage"
- "Create a Key Vault using the AVM module"
- "Set up an App Service with AVM"

Classic Mode:
- "Deploy a Virtual Network using classic Bicep"
- "Create a Network Security Group with classic resources"
- "Deploy a Load Balancer without using modules"


MONITORING CHECKLIST
--------------------

□ Model responds with valid JSON
□ JSON contains plan, files, warnings keys
□ main.bicep is extracted successfully
□ parameters.json included when applicable
□ Plan shows correct resource types
□ Warnings array populated when needed
□ Error handling works for invalid JSON
□ Both AVM and Classic modes work
□ Search filters correctly by mode
□ Logs show detailed debugging info
"""

if __name__ == "__main__":
    print(__doc__)
