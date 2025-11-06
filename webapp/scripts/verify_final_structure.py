import json
from pathlib import Path

# Read and display a complete example
input_file = Path(r"c:\Users\jostubbl.REDMOND\Downloads\c964-capstone\training-data\train_agent.jsonl")

print("=" * 80)
print("COMPLETE ENTRY STRUCTURE VERIFICATION")
print("=" * 80)
print()

with open(input_file, 'r', encoding='utf-8') as f:
    # Read first entry
    line = f.readline()
    entry = json.loads(line.strip())

    print("TOP-LEVEL STRUCTURE:")
    print(f"  Keys: {list(entry.keys())}")
    print()

    messages = entry['messages']
    print(f"MESSAGES ARRAY: {len(messages)} messages")
    print()

    # User message
    user_msg = messages[0]
    print("1. USER MESSAGE:")
    print(f"   Role: {user_msg['role']}")
    print(f"   Content preview: {user_msg['content'][:150]}...")
    print()

    # Assistant message
    assistant_msg = messages[1]
    print("2. ASSISTANT MESSAGE:")
    print(f"   Role: {assistant_msg['role']}")
    print(f"   Content type: JSON string")
    print()

    # Parse assistant content
    assistant_data = json.loads(assistant_msg['content'])

    print("3. ASSISTANT CONTENT STRUCTURE:")
    print(f"   Keys: {list(assistant_data.keys())}")
    print()

    # Plan
    plan = assistant_data['plan']
    print("   a) PLAN:")
    print(f"      - Resources: {len(plan['resources'])} resource(s)")
    if plan['resources']:
        for res in plan['resources']:
            print(f"        * resourceType: {res['resourceType']}")
            print(f"        * name: {res['name']}")
    print(f"      - Rationale: {plan['rationale']}")
    print()

    # Files
    files = assistant_data['files']
    print(f"   b) FILES: {len(files)} file(s)")
    for file in files:
        print(f"      - path: {file['path']}")
        print(f"        language: {file['language']}")
        print(f"        content length: {len(file['content'])} characters")
        if file['path'] == 'parameters.json':
            # Show parameters.json structure
            params = json.loads(file['content'])
            print(f"        parameter count: {len(params['parameters'])} parameters")
    print()

    # Warnings
    warnings = assistant_data['warnings']
    print(f"   c) WARNINGS: {len(warnings)} warning(s)")
    print()

print("=" * 80)
print("EXAMPLE WITH PARAMETERS")
print("=" * 80)
print()

# Find an entry with parameters
with open(input_file, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
        entry = json.loads(line.strip())
        assistant_data = json.loads(entry['messages'][1]['content'])

        if len(assistant_data['files']) > 1:
            print(f"Entry #{line_num}:")
            print()

            print("USER PROMPT:")
            print(entry['messages'][0]['content'][:200])
            print("...")
            print()

            print("PLAN:")
            print(f"  Resources: {assistant_data['plan']['resources']}")
            print(f"  Rationale: {assistant_data['plan']['rationale']}")
            print()

            print("FILES:")
            for file in assistant_data['files']:
                print(f"  - {file['path']} ({file['language']})")
            print()

            print("PARAMETERS.JSON SAMPLE:")
            params_file = [f for f in assistant_data['files'] if f['path'] == 'parameters.json'][0]
            params = json.loads(params_file['content'])
            print(f"  Schema: {params['$schema']}")
            print(f"  Parameters ({len(params['parameters'])} total):")
            # Show first 3 parameters
            for i, (key, value) in enumerate(list(params['parameters'].items())[:3]):
                print(f"    - {key}: {value}")
            if len(params['parameters']) > 3:
                print(f"    ... and {len(params['parameters']) - 3} more")
            print()

            break

print("=" * 80)
print("TRANSFORMATION SUCCESSFUL!")
print("=" * 80)
