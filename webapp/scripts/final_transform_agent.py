import json
import re
from pathlib import Path

# Base paths
base_path = Path(r"c:\Users\jostubbl.REDMOND\Downloads\c964-capstone")
input_file = base_path / "training-data" / "training_set.jsonl"
output_file = base_path / "training-data" / "train_agent.jsonl"

def extract_module_info(bicep_code):
    """Extract module name and path from Bicep code."""
    pattern = r"module\s+(\w+)\s+'(br/public:[^']+)'\s*="
    match = re.search(pattern, bicep_code)

    if match:
        module_name = match.group(1)
        module_path = match.group(2)
        return module_name, module_path
    return None, None

def create_plan(bicep_code):
    """Generate plan with resources and rationale."""
    module_name, module_path = extract_module_info(bicep_code)

    plan = {
        "resources": [],
        "rationale": ""
    }

    if module_path:
        # Extract the module type (e.g., avm/res/web/connection)
        # Format: br/public:avm/res/web/connection:0.4.0
        match = re.search(r'br/public:([^:]+)', module_path)
        if match:
            module_type = match.group(1)
            parts = module_type.split('/')

            # Create rationale based on module type
            if len(parts) >= 3:
                category = parts[1]  # res, ptn, utl
                service = parts[2] if len(parts) > 2 else "resource"

                if category == "res":
                    plan["rationale"] = f"AVM module for {service}."
                elif category == "ptn":
                    plan["rationale"] = f"AVM pattern module for {service}."
                elif category == "utl":
                    plan["rationale"] = f"AVM utility module for {service}."
                else:
                    plan["rationale"] = f"AVM module for {service}."
            else:
                plan["rationale"] = "AVM module deployment."

            # Add resource to plan
            plan["resources"].append({
                "resourceType": module_path,
                "name": module_name if module_name else "resource"
            })
    else:
        plan["rationale"] = "Bicep deployment."

    return plan

def create_warnings(bicep_code):
    """Generate warnings array (empty for now, can be extended)."""
    warnings = []

    # Could add logic here to detect potential issues:
    # - Missing @secure() on password params
    # - Hardcoded values
    # - etc.

    return warnings

def parse_bicep_parameters(bicep_code):
    """
    Parse Bicep code to extract parameter declarations.
    Returns a list of dicts with name, type, and optional default_value.
    """
    parameters = []

    # Pattern to match parameter declarations
    # Matches: param paramName type = defaultValue
    # Or: param paramName type
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
    Returns the JSON string.
    """
    if not parameters:
        return None

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
                elif default_value.replace('-', '', 1).replace('.', '', 1).isdigit():
                    if '.' in default_value:
                        param_values[param_name] = {"value": float(default_value)}
                    else:
                        param_values[param_name] = {"value": int(default_value)}
                # Handle boolean values
                elif default_value.lower() in ['true', 'false']:
                    param_values[param_name] = {"value": default_value.lower() == 'true'}
                # Handle objects and arrays (keep as-is)
                elif default_value.startswith('{') or default_value.startswith('['):
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

def transform_to_agent_format(input_file, output_file):
    """
    Transform training_set.jsonl to train_agent.jsonl with complete structure.
    """
    print("=" * 80)
    print("FINAL TRANSFORMATION TO AGENT FORMAT")
    print("=" * 80)
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    print()

    processed_count = 0
    success_count = 0
    error_count = 0
    with_params_count = 0
    without_params_count = 0

    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:

        for line_num, line in enumerate(infile, 1):
            try:
                # Parse the original entry
                original_data = json.loads(line.strip())
                messages = original_data.get('messages', [])

                # Extract user and assistant messages
                user_message = None
                assistant_message = None

                for msg in messages:
                    if msg['role'] == 'user':
                        user_message = msg
                    elif msg['role'] == 'assistant':
                        assistant_message = msg

                if not user_message or not assistant_message:
                    print(f"  Warning: Line {line_num} missing user or assistant message")
                    error_count += 1
                    continue

                # Get the original Bicep code from assistant message
                bicep_code = assistant_message['content']

                # Generate plan
                plan = create_plan(bicep_code)

                # Generate warnings
                warnings = create_warnings(bicep_code)

                # Parse parameters and generate parameters.json
                parameters = parse_bicep_parameters(bicep_code)
                parameters_json_string = generate_parameters_json(parameters)

                # Create files list
                files = [
                    {
                        "path": "main.bicep",
                        "language": "bicep",
                        "content": bicep_code
                    }
                ]

                # Add parameters.json if parameters exist
                if parameters_json_string:
                    files.append({
                        "path": "parameters.json",
                        "language": "json",
                        "content": parameters_json_string
                    })
                    with_params_count += 1
                else:
                    without_params_count += 1

                # Assemble the complete assistant content object
                assistant_content_object = {
                    "plan": plan,
                    "files": files,
                    "warnings": warnings
                }

                # Convert to JSON string
                assistant_content_json_string = json.dumps(assistant_content_object, ensure_ascii=False)

                # Create the new entry with updated assistant message
                new_entry = {
                    "messages": [
                        {
                            "role": "user",
                            "content": user_message['content']
                        },
                        {
                            "role": "assistant",
                            "content": assistant_content_json_string
                        }
                    ]
                }

                # Write to output file
                outfile.write(json.dumps(new_entry, ensure_ascii=False) + '\n')

                success_count += 1
                processed_count += 1

                # Show progress
                if line_num % 100 == 0:
                    print(f"  Processed {line_num} lines... ({success_count} successful, {error_count} errors)")

            except Exception as e:
                print(f"  Error on line {line_num}: {e}")
                error_count += 1
                processed_count += 1

    print()
    print("=" * 80)
    print("TRANSFORMATION COMPLETE")
    print("=" * 80)
    print(f"Total lines processed:        {processed_count}")
    print(f"Successfully transformed:     {success_count}")
    print(f"Errors:                       {error_count}")
    print(f"Entries with parameters.json: {with_params_count}")
    print(f"Entries without parameters:   {without_params_count}")
    print(f"Success rate:                 {success_count/processed_count*100:.2f}%")
    print()
    print(f"Output written to: {output_file}")
    print("=" * 80)

if __name__ == "__main__":
    transform_to_agent_format(input_file, output_file)
