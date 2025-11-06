# APP.PY UPDATE SUMMARY
# Updated: November 6, 2025

## Changes Made to Support Agentic Model

### 1. Model Configuration
- **New Model**: `gpt-4o-mini-2024-07-18-ft-f5669b4111424563a3951e228c98ea96`
- **Environment Variable**: Can be overridden via `AZURE_OPENAI_DEPLOYMENT_NAME`
- **API Version**: Updated from `2023-12-01-preview` to `2024-02-15-preview` for JSON mode support

### 2. Agent System Message (New)
Added `AGENT_SYSTEM_MESSAGE` constant that instructs the model to:
- Return responses as valid JSON only
- Include `plan`, `files`, and `warnings` keys
- Use AVM modules when appropriate or classic Bicep when requested
- Base responses strictly on provided context (no hallucination)

**JSON Schema Expected from Model:**
```json
{
  "plan": {
    "resources": [{"resourceType": "...", "name": "..."}],
    "rationale": "..."
  },
  "files": [
    {"path": "main.bicep", "language": "bicep", "content": "..."},
    {"path": "parameters.json", "language": "json", "content": "..."}
  ],
  "warnings": ["..."]
}
```

### 3. API Call Changes
**Before:**
```python
response = openai_client.chat.completions.create(
    model=OPENAI_DEPLOYMENT_NAME,
    messages=[...],
    temperature=0.2,
    max_tokens=2000,
    stream=True  # Streaming enabled
)
```

**After:**
```python
response = openai_client.chat.completions.create(
    model=OPENAI_DEPLOYMENT_NAME,
    messages=[...],
    response_format={"type": "json_object"},  # NEW: Force JSON
    temperature=0.1,  # Lower for deterministic output
    max_tokens=4096,  # Increased for larger responses
    # No streaming - JSON mode requires non-streaming
)
```

### 4. Response Processing Changes
**Before:**
- Streamed response token by token
- Removed markdown code fences (```bicep)
- Returned raw Bicep code directly

**After:**
- Non-streaming response (JSON mode requirement)
- Parse JSON response with `json.loads()`
- Extract `main.bicep` from `files` array
- Log `plan` and `warnings` for debugging
- Error handling for invalid JSON responses

### 5. Removed Code
- Removed mode-specific system messages (AVM vs Classic)
  - Previously had two different system messages
  - Now uses single `AGENT_SYSTEM_MESSAGE` for both modes
- Removed streaming logic (incompatible with JSON mode)
- Removed markdown fence cleanup (model returns structured JSON)

### 6. Backward Compatibility
✅ Maintains existing functionality:
- `/generate` endpoint unchanged
- Mode toggle (avm/classic) still works
- Search filter logic preserved
- SSE progress updates still work
- Local development mode still functional

### 7. Testing Checklist
Before deploying, test:
- [ ] AVM mode: Request a Storage Account AVM module
- [ ] Classic mode: Request a classic Bicep resource
- [ ] Error handling: Invalid requests
- [ ] JSON parsing: Model returns valid JSON
- [ ] Bicep extraction: main.bicep extracted correctly
- [ ] Parameters: parameters.json included when applicable
- [ ] Logging: Plan and warnings logged properly
- [ ] Local dev mode: Still returns dummy response

### 8. Environment Variables Required
```bash
AZURE_SEARCH_SERVICE_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_INDEX_NAME=your-index-name
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini-2024-07-18-ft-f5669b4111424563a3951e228c98ea96
```

### 9. Expected Model Behavior
The fine-tuned model should:
1. Parse user request and context
2. Determine if AVM or classic is appropriate
3. Generate valid Bicep code
4. Return structured JSON with plan, files, warnings
5. Include parameters.json when parameters are detected

### 10. Troubleshooting
If issues occur:
1. Check logs for "Successfully parsed JSON response"
2. Verify model deployment name is correct
3. Ensure API version supports JSON mode (2024-02-15-preview+)
4. Check raw response in logs if JSON parsing fails
5. Verify fine-tuned model is deployed and accessible

---

**Status**: ✅ Ready for testing
**Next Steps**: Deploy and test with sample prompts
