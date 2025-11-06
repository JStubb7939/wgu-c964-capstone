import json
from pathlib import Path

# Final validation report
input_file = Path(r"c:\Users\jostubbl.REDMOND\Downloads\c964-capstone\training-data\train_agent.jsonl")

print("=" * 80)
print("FINAL VALIDATION REPORT")
print("=" * 80)
print()

# Count statistics
total_entries = 0
entries_with_params = 0
entries_without_params = 0
total_resources = 0
total_parameters = 0

with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        total_entries += 1
        entry = json.loads(line.strip())
        assistant_data = json.loads(entry['messages'][1]['content'])

        # Count files
        if len(assistant_data['files']) > 1:
            entries_with_params += 1
            # Count parameters
            params_file = [f for f in assistant_data['files'] if f['path'] == 'parameters.json'][0]
            params = json.loads(params_file['content'])
            total_parameters += len(params['parameters'])
        else:
            entries_without_params += 1

        # Count resources
        total_resources += len(assistant_data['plan']['resources'])

print(f"Total entries: {total_entries}")
print(f"Entries with parameters.json: {entries_with_params}")
print(f"Entries without parameters: {entries_without_params}")
print(f"Total resources defined: {total_resources}")
print(f"Total parameters extracted: {total_parameters}")
print(f"Average parameters per entry (with params): {total_parameters/entries_with_params:.2f}")
print()

print("=" * 80)
print("STRUCTURE VALIDATION")
print("=" * 80)
print()

# Validate structure of all entries
valid_count = 0
invalid_count = 0

with open(input_file, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
        try:
            entry = json.loads(line.strip())

            # Check top-level structure
            assert 'messages' in entry
            assert len(entry['messages']) == 2

            # Check message roles
            assert entry['messages'][0]['role'] == 'user'
            assert entry['messages'][1]['role'] == 'assistant'

            # Parse assistant content
            assistant_data = json.loads(entry['messages'][1]['content'])

            # Check assistant content structure
            assert 'plan' in assistant_data
            assert 'files' in assistant_data
            assert 'warnings' in assistant_data

            # Check plan structure
            assert 'resources' in assistant_data['plan']
            assert 'rationale' in assistant_data['plan']
            assert isinstance(assistant_data['plan']['resources'], list)
            assert isinstance(assistant_data['plan']['rationale'], str)

            # Check files structure
            assert len(assistant_data['files']) >= 1
            assert assistant_data['files'][0]['path'] == 'main.bicep'
            assert assistant_data['files'][0]['language'] == 'bicep'
            assert 'content' in assistant_data['files'][0]

            # If there are parameters, validate parameters.json
            if len(assistant_data['files']) > 1:
                params_file = assistant_data['files'][1]
                assert params_file['path'] == 'parameters.json'
                assert params_file['language'] == 'json'

                # Validate parameters.json content
                params = json.loads(params_file['content'])
                assert '$schema' in params
                assert 'contentVersion' in params
                assert 'parameters' in params
                assert isinstance(params['parameters'], dict)

            # Check warnings structure
            assert isinstance(assistant_data['warnings'], list)

            valid_count += 1

        except Exception as e:
            print(f"Validation error on line {line_num}: {e}")
            invalid_count += 1

print(f"Valid entries: {valid_count}")
print(f"Invalid entries: {invalid_count}")
print(f"Validation success rate: {valid_count/total_entries*100:.2f}%")
print()

if invalid_count == 0:
    print("✓ ALL ENTRIES PASSED VALIDATION!")
else:
    print(f"✗ {invalid_count} entries failed validation")

print()
print("=" * 80)
print("TRANSFORMATION COMPLETE AND VALIDATED")
print("=" * 80)
