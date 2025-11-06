import json
import re
from pathlib import Path

# Base paths
base_path = Path(r"c:\Users\jostubbl.REDMOND\Downloads\c964-capstone")
input_file = base_path / "training-data" / "train_agent.jsonl"
output_file = base_path / "training-data" / "train_agent.jsonl"  # Will overwrite with updated version

def parse_bicep_parameters(bicep_code):
    """
    Parse Bicep code to extract parameter declarations.
    Returns a list of dicts with name, type, and optional default_value.
    """
    parameters = []

    # Pattern to match parameter declarations
    # Matches: param paramName type = defaultValue
    # Or: param paramName type
    # Handles multi-line declarations and various types (string, int, bool, object, array)
    param_pattern = r"@[^\n]*\n\s*param\s+(\w+)\s+([\w\[\]]+)(?:\s*=\s*([^\n]+))?"
    simple_param_pattern = r"(?<!@[^\n]*\n\s*)param\s+(\w+)\s+([\w\[\]]+)(?:\s*=\s*([^\n]+))?"

    # Combine patterns to catch both decorated and non-decorated params
    all_param_pattern = r"(?:@[^\n]*\n\s*)?param\s+(\w+)\s+([\w\[\]]+)(?:\s*=\s*([^\n]+))?"

    matches = re.finditer(all_param_pattern, bicep_code, re.MULTILINE)

    for match in matches:
        param_name = match.group(1)
        param_type = match.group(2)
        default_value = match.group(3)

        param_info = {
            "name": param_name,
            "type": param_type,
            "default_value": None
        }

        # Clean up and parse default value if present
        if default_value:
            default_value = default_value.strip()

            # Remove trailing comments
            if '//' in default_value:
                default_value = default_value.split('//')[0].strip()

            # Store the cleaned default value
            param_info["default_value"] = default_value

        parameters.append(param_info)

    return parameters

def generate_parameters_json(parameters):
    """
    Generate a parameters.json file content from parameter definitions.
    """
    param_values = {}

    for param in parameters:
        param_name = param["name"]
        param_type = param["type"]
        default_value = param["default_value"]

        if default_value:
            # Try to evaluate the default value to proper JSON type
            try:
                # Handle string literals
                if default_value.startswith("'") and default_value.endswith("'"):
                    param_values[param_name] = {"value": default_value.strip("'")}
                # Handle numeric values
                elif default_value.isdigit() or (default_value.replace('.', '', 1).isdigit()):
                    if '.' in default_value:
                        param_values[param_name] = {"value": float(default_value)}
                    else:
                        param_values[param_name] = {"value": int(default_value)}
                # Handle boolean values
                elif default_value.lower() in ['true', 'false']:
                    param_values[param_name] = {"value": default_value.lower() == 'true'}
                # Handle objects and arrays (keep as-is for now)
                elif default_value.startswith('{') or default_value.startswith('['):
                    # For complex types, use the literal value
                    param_values[param_name] = {"value": default_value}
                else:
                    # Default case - treat as string
                    param_values[param_name] = {"value": default_value}
            except:
                # If parsing fails, use the string value
                param_values[param_name] = {"value": default_value}
        else:
            # No default value - use placeholder
            param_values[param_name] = {"value": "<YOUR_VALUE_HERE>"}

    # Create the full parameters.json structure
    parameters_json = {
        "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
        "contentVersion": "1.0.0.0",
        "parameters": param_values
    }

    return json.dumps(parameters_json, indent=2, ensure_ascii=False)

def update_train_agent_with_parameters():
    """
    Read train_agent.jsonl, parse parameters, add parameters.json to files array.
    """
    print("Adding parameters.json to train_agent.jsonl...")
    print(f"Processing: {input_file}")
    print()

    updated_entries = []
    processed_count = 0
    params_added_count = 0

    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                # Parse the entry
                data = json.loads(line.strip())
                messages = data.get('messages', [])

                # Find the assistant message
                for msg in messages:
                    if msg['role'] == 'assistant':
                        # Parse the assistant content (which is a JSON string)
                        assistant_data = json.loads(msg['content'])

                        # Get the Bicep code from files array
                        bicep_file = None
                        for file in assistant_data.get('files', []):
                            if file.get('path') == 'main.bicep':
                                bicep_file = file
                                break

                        if bicep_file:
                            bicep_code = bicep_file.get('content', '')

                            # Parse parameters from Bicep code
                            parameters = parse_bicep_parameters(bicep_code)

                            # Generate parameters.json if there are parameters
                            if parameters:
                                params_json_content = generate_parameters_json(parameters)

                                # Add parameters.json to files array
                                assistant_data['files'].append({
                                    "path": "parameters.json",
                                    "content": params_json_content
                                })

                                params_added_count += 1

                            # Update the assistant message with new content
                            msg['content'] = json.dumps(assistant_data, ensure_ascii=False)

                updated_entries.append(data)
                processed_count += 1

                # Show progress
                if line_num % 100 == 0:
                    print(f"  Processed {line_num} lines...")

            except Exception as e:
                print(f"  Error on line {line_num}: {e}")
                # Keep the original entry even if there's an error
                updated_entries.append(data)

    # Write updated entries back to file
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in updated_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    print()
    print("=" * 80)
    print(f"Update complete!")
    print(f"  Processed: {processed_count} entries")
    print(f"  Parameters.json added: {params_added_count} entries")
    print(f"  Output file: {output_file}")
    print("=" * 80)

if __name__ == "__main__":
    update_train_agent_with_parameters()
