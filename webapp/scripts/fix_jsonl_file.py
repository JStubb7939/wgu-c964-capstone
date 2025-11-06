import json
import re

# Read the file
with open('grounding-data/extracted_avm_data.jsonl', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Original file has {len(lines)} lines")

# The last line contains all the concatenated ptn modules
# We need to split it into individual JSON objects
last_line = lines[-1].strip()

# Find all complete JSON objects in the last line
# They start with {"id": and end with }
json_objects = []

# Use a simple state machine to extract JSON objects
depth = 0
current_obj = ""
for char in last_line:
    current_obj += char
    if char == '{':
        depth += 1
    elif char == '}':
        depth -= 1
        if depth == 0 and current_obj.strip():
            # We have a complete JSON object
            try:
                obj = json.loads(current_obj.strip())
                json_objects.append(obj)
                current_obj = ""
            except:
                pass

print(f"Found {len(json_objects)} JSON objects on the last line")

# Now rebuild the file: first 460 lines as-is, then all the JSON objects from line 461
with open('grounding-data/extracted_avm_data.jsonl', 'w', encoding='utf-8') as f:
    # Write first 460 lines unchanged
    for line in lines[:-1]:
        f.write(line)

    # Write each extracted JSON object as a separate line
    for obj in json_objects:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')

print(f"File repaired with {len(lines) - 1 + len(json_objects)} total lines")
