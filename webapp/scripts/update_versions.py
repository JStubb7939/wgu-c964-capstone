import json
import os
from pathlib import Path

# Base path for the grounding data
base_path = Path(r"c:\Users\jostubbl.REDMOND\Downloads\c964-capstone\grounding-data")
jsonl_file = base_path / "extracted_avm_data.jsonl"

# Read all lines from the JSONL file
with open(jsonl_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

updated_lines = []
errors = []

for line_num, line in enumerate(lines, 1):
    try:
        # Parse the JSON line
        data = json.loads(line.strip())

        # Get the source path
        source = data.get('source', '')
        if not source:
            errors.append(f"Line {line_num}: No source found")
            updated_lines.append(line)
            continue

        # Convert backslashes to forward slashes for path manipulation
        source_parts = source.replace('\\', '/')

        # Build the path to version.json
        # Source is relative to bicep-registry-modules/avm
        # Start from the directory containing the source file and walk up to find version.json
        current_dir = base_path / "bicep-registry-modules" / "avm" / source_parts.rsplit('/', 1)[0]
        version_json_path = None

        # Walk up the directory tree to find version.json
        while current_dir != base_path / "bicep-registry-modules" / "avm":
            test_path = current_dir / "version.json"
            if test_path.exists():
                version_json_path = test_path
                break
            current_dir = current_dir.parent

        # Special case: If no version.json found and this is a wrapper module (main.bicep at root),
        # look for version.json in the first scope subdirectory (e.g., mg-scope, rg-scope, sub-scope)
        if version_json_path is None:
            module_dir = base_path / "bicep-registry-modules" / "avm" / source_parts.rsplit('/', 1)[0]
            for scope_name in ['mg-scope', 'rg-scope', 'sub-scope']:
                scope_version_path = module_dir / scope_name / "version.json"
                if scope_version_path.exists():
                    version_json_path = scope_version_path
                    break

        # Check if version.json exists
        if version_json_path is None:
            errors.append(f"Line {line_num}: version.json not found for {source}")
            updated_lines.append(line)
            continue

        # Read the version from version.json
        with open(version_json_path, 'r', encoding='utf-8') as vf:
            version_data = json.load(vf)
            version = version_data.get('version', '')

        if not version:
            errors.append(f"Line {line_num}: No version found in {version_json_path}")
            updated_lines.append(line)
            continue

        # Format version as major.minor.patch
        # If it's already in that format, keep it; otherwise add .0
        version_parts = version.split('.')
        if len(version_parts) == 2:
            version = f"{version}.0"
        elif len(version_parts) != 3:
            errors.append(f"Line {line_num}: Unexpected version format '{version}' in {version_json_path}")
            updated_lines.append(line)
            continue

        # Update the content_to_embed with the new version
        content = data.get('content_to_embed', '')
        if 'br_public:' in content and ':<version>' in content:
            # Replace <version> with the actual version
            updated_content = content.replace(':<version>', f':{version}')
            data['content_to_embed'] = updated_content

            # Convert back to JSON and add to updated lines
            updated_lines.append(json.dumps(data, ensure_ascii=False) + '\n')
            print(f"Line {line_num}: Updated version to {version}")
        else:
            errors.append(f"Line {line_num}: Could not find module ID pattern in content")
            updated_lines.append(line)

    except json.JSONDecodeError as e:
        errors.append(f"Line {line_num}: JSON parse error - {e}")
        updated_lines.append(line)
    except Exception as e:
        errors.append(f"Line {line_num}: Unexpected error - {e}")
        updated_lines.append(line)

# Write the updated lines back to the file
with open(jsonl_file, 'w', encoding='utf-8') as f:
    f.writelines(updated_lines)

print(f"\nProcessed {len(lines)} lines")
print(f"Errors: {len(errors)}")
if errors:
    print("\nError details:")
    for error in errors[:10]:  # Show first 10 errors
        print(f"  {error}")
    if len(errors) > 10:
        print(f"  ... and {len(errors) - 10} more errors")
