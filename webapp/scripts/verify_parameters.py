import json
from pathlib import Path

# Read train_agent.jsonl and find an entry with parameters
input_file = Path(r"c:\Users\jostubbl.REDMOND\Downloads\c964-capstone\training-data\train_agent.jsonl")

print("Searching for entries with parameters.json...")
print()

with open(input_file, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
        data = json.loads(line.strip())
        assistant_msg = [msg for msg in data['messages'] if msg['role'] == 'assistant'][0]
        assistant_data = json.loads(assistant_msg['content'])

        # Check if this entry has parameters.json
        if len(assistant_data['files']) > 1:
            print(f"Found entry #{line_num} with {len(assistant_data['files'])} files:")
            print()

            for file in assistant_data['files']:
                print(f"  File: {file['path']}")
                if file['path'] == 'parameters.json':
                    print(f"  Content:")
                    # Pretty print the JSON
                    params = json.loads(file['content'])
                    print(json.dumps(params, indent=4))

            print()
            print("=" * 80)

            # Show a few more examples
            if line_num > 50:
                break
