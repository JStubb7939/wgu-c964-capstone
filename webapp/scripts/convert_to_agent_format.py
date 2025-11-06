import json
import re
from pathlib import Path

# Base paths
base_path = Path(r"c:\Users\jostubbl.REDMOND\Downloads\c964-capstone")
input_file = base_path / "training-data" / "training_set.jsonl"
output_file = base_path / "training-data" / "train_agent.jsonl"

def extract_module_info(bicep_code):
    """Extract module information from Bicep code."""
    # Pattern to match: module <name> 'br/public:avm/...:<version>' = {
    pattern = r"module\s+(\w+)\s+'(br/public:[^']+)'\s*="
    match = re.search(pattern, bicep_code)

    if match:
        module_name = match.group(1)
        module_path = match.group(2)
        return module_name, module_path

    # If no module declaration found, try to infer from content
    # This handles cases where the content might be a fragment
    return None, None

def create_rationale(user_prompt, module_path):
    """Create a rationale based on user prompt and module path."""
    if module_path:
        # Extract resource type from module path
        # e.g., br/public:avm/res/key-vault/vault:0.5.0 -> key-vault
        parts = module_path.split('/')
        if len(parts) >= 4:
            resource_type = parts[-1].split(':')[0]  # Get last part before version
            return f"AVM module for {resource_type}."

    # Fallback rationale based on user prompt
    return f"Deploying resources based on request: {user_prompt[:50]}..."

def convert_bicep_to_agent_format(bicep_code, user_prompt):
    """Convert raw Bicep code to structured agent format."""
    module_name, module_path = extract_module_info(bicep_code)

    # Create the structured response
    agent_response = {
        "plan": {
            "resources": [],
            "rationale": ""
        },
        "files": [
            {
                "path": "main.bicep",
                "content": bicep_code
            }
        ],
        "warnings": []
    }

    # Add resource information if we found a module
    if module_name and module_path:
        agent_response["plan"]["resources"].append({
            "resourceType": module_path,
            "name": module_name
        })
        agent_response["plan"]["rationale"] = create_rationale(user_prompt, module_path)
    else:
        # If no module found, still provide the file content
        agent_response["plan"]["rationale"] = create_rationale(user_prompt, None)

    # Convert to JSON string (this will be the new assistant content)
    return json.dumps(agent_response, ensure_ascii=False)

def transform_training_data():
    """Transform training_set.jsonl to train_agent.jsonl."""
    print("Transforming training data to agent format...")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print()

    converted_count = 0
    error_count = 0

    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:

        for line_num, line in enumerate(infile, 1):
            try:
                # Parse the original JSON
                data = json.loads(line.strip())
                messages = data.get('messages', [])

                # Find user and assistant messages
                user_content = None
                assistant_content = None

                for msg in messages:
                    if msg['role'] == 'user':
                        user_content = msg['content']
                    elif msg['role'] == 'assistant':
                        assistant_content = msg['content']

                if user_content and assistant_content:
                    # Convert the assistant content to agent format
                    new_assistant_content = convert_bicep_to_agent_format(
                        assistant_content,
                        user_content
                    )

                    # Create new message structure
                    new_messages = [
                        {"role": "user", "content": user_content},
                        {"role": "assistant", "content": new_assistant_content}
                    ]

                    # Write the new format
                    new_data = {"messages": new_messages}
                    outfile.write(json.dumps(new_data, ensure_ascii=False) + '\n')

                    converted_count += 1

                    # Show progress every 100 lines
                    if line_num % 100 == 0:
                        print(f"  Processed {line_num} lines...")
                else:
                    print(f"  Warning: Line {line_num} missing user or assistant content")
                    error_count += 1

            except Exception as e:
                print(f"  Error on line {line_num}: {e}")
                error_count += 1

    print()
    print("=" * 80)
    print(f"Transformation complete!")
    print(f"  Converted: {converted_count} entries")
    print(f"  Errors: {error_count} entries")
    print(f"  Output file: {output_file}")
    print("=" * 80)

if __name__ == "__main__":
    transform_training_data()
