import json
import re
from pathlib import Path

# Base path
base_path = Path(r"c:\Users\jostubbl.REDMOND\Downloads\c964-capstone")

# Load the version mapping from extracted_avm_data.jsonl
version_map = {}
grounding_file = base_path / "grounding-data" / "extracted_avm_data.jsonl"

print("Loading version data from extracted_avm_data.jsonl...")
with open(grounding_file, 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line.strip())
        content = data.get('content_to_embed', '')

        # Extract module ID with version
        # Format: "Module ID: br_public:res_xxx_xxx:0.5.0"
        match = re.search(r'Module ID: br_public:([^:]+):(\d+\.\d+\.\d+)', content)
        if match:
            module_id = match.group(1)
            version = match.group(2)
            # Convert underscores to slashes for matching
            # br_public:res_aad_domain-service -> avm/res/aad/domain-service
            # br_public:ptn_ptn_virtual-machine-images_azure-image-builder -> avm/ptn/virtual-machine-images/azure-image-builder

            # Split by underscore and rebuild with slashes
            parts = module_id.split('_')
            if len(parts) >= 2:
                # First part is the type (res, ptn, etc.)
                module_type = parts[0]
                # Rest are the path components - but skip duplicate type prefix
                path_parts = parts[1:]
                # For ptn modules, they have ptn_ptn_ format, so skip the second ptn
                if module_type == 'ptn' and len(path_parts) > 0 and path_parts[0] == 'ptn':
                    path_parts = path_parts[1:]
                module_path = f"avm/{module_type}/" + '/'.join(path_parts)
                version_map[module_path] = version

print(f"Loaded {len(version_map)} module versions")

def update_versions_in_file(file_path, max_lines_to_update):
    """Update version placeholders in a JSONL file."""
    print(f"\nProcessing {file_path.name}...")

    # Use utf-8-sig to handle BOM if present
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()

    updated_lines = []
    updates_made = 0
    errors = []

    for line_num, line in enumerate(lines, 1):
        try:
            data = json.loads(line.strip())

            # Only process the first N lines (AVM examples)
            if line_num <= max_lines_to_update:
                # Get the assistant's response
                messages = data.get('messages', [])
                assistant_msg = None
                for msg in messages:
                    if msg.get('role') == 'assistant':
                        assistant_msg = msg
                        break

                if assistant_msg:
                    content = assistant_msg.get('content', '')

                    # Find all module declarations with <version>
                    # Pattern: module <name> 'br/public:avm/res/<module>:<version>'
                    pattern = r"module\s+\w+\s+'br/public:(avm/[^:]+):<version>'"

                    def replace_version(match):
                        nonlocal updates_made
                        module_path = match.group(1)

                        if module_path in version_map:
                            version = version_map[module_path]
                            updates_made += 1
                            return match.group(0).replace('<version>', version)
                        else:
                            errors.append(f"Line {line_num}: No version found for module '{module_path}'")
                            return match.group(0)

                    updated_content = re.sub(pattern, replace_version, content)
                    assistant_msg['content'] = updated_content

            # Write the line (updated or not)
            updated_lines.append(json.dumps(data, ensure_ascii=False) + '\n')

        except json.JSONDecodeError as e:
            errors.append(f"Line {line_num}: JSON parse error - {e}")
            updated_lines.append(line)
        except Exception as e:
            errors.append(f"Line {line_num}: Unexpected error - {e}")
            updated_lines.append(line)

    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)

    print(f"  Processed {len(lines)} lines")
    print(f"  Made {updates_made} version updates")
    if errors:
        print(f"  Errors: {len(errors)}")
        for error in errors[:5]:  # Show first 5 errors
            print(f"    {error}")
        if len(errors) > 5:
            print(f"    ... and {len(errors) - 5} more errors")

    return updates_made, len(errors)

# Update training_set.jsonl (first 165 lines are AVM)
training_file = base_path / "training-data" / "training_set.jsonl"
training_updates, training_errors = update_versions_in_file(training_file, 165)

# Update validation_set.jsonl (first 42 lines are AVM)
validation_file = base_path / "training-data" / "validation_set.jsonl"
validation_updates, validation_errors = update_versions_in_file(validation_file, 42)

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"Training set: {training_updates} updates, {training_errors} errors")
print(f"Validation set: {validation_updates} updates, {validation_errors} errors")
print(f"Total updates: {training_updates + validation_updates}")
