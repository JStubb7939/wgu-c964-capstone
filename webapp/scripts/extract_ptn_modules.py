import json
import os
from pathlib import Path

# Base paths
base_path = Path(r"c:\Users\jostubbl.REDMOND\Downloads\c964-capstone\grounding-data")
ptn_path = base_path / "bicep-registry-modules" / "avm" / "ptn"
output_file = base_path / "extracted_avm_data.jsonl"

# Read existing data to avoid duplicates
existing_ids = set()
with open(output_file, 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line.strip())
        existing_ids.add(data['id'])

print(f"Found {len(existing_ids)} existing modules")

# Function to extract module info
def extract_ptn_module_info(main_bicep_path, relative_path):
    """Extract module information from a pattern module."""
    try:
        # Read the main.bicep file to get a description or module name
        with open(main_bicep_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Get version from version.json in the same directory
        version_json_path = main_bicep_path.parent / "version.json"
        version = "0.1"  # default

        if version_json_path.exists():
            with open(version_json_path, 'r', encoding='utf-8') as vf:
                version_data = json.load(vf)
                version = version_data.get('version', '0.1')

        # Format version as major.minor.patch
        version_parts = version.split('.')
        if len(version_parts) == 2:
            version = f"{version}.0"

        # Create module ID from path
        # e.g., ptn/virtual-machine-images/azure-image-builder -> ptn_virtual-machine-images_azure-image-builder
        path_parts = relative_path.replace('\\', '/').split('/')
        module_id = 'ptn_' + '_'.join(path_parts[:-1])  # Exclude main.bicep

        # Create module path for content
        # e.g., ptn/virtual-machine-images/azure-image-builder
        module_path = '/'.join(path_parts[:-1])

        # Extract module name (last part of path)
        module_name = path_parts[-2] if len(path_parts) > 1 else 'unknown'

        # Try to extract description from README
        readme_path = main_bicep_path.parent / "README.md"
        description = f"Pattern module for '{module_name}'"

        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as rf:
                    readme_content = rf.read()
                    # Try to get first paragraph or heading
                    lines = readme_content.split('\n')
                    for line in lines:
                        if line.strip() and not line.startswith('#') and len(line) > 20:
                            description = line.strip()[:200]
                            break
            except:
                pass

        # Create content_to_embed
        content_to_embed = f"Recommended AVM Module for '{module_name}'. This is the preferred, verified module for Bicep.\\n"
        content_to_embed += f"Module ID: br_public:ptn_{module_path.replace('/', '_')}:{version}\\n"
        content_to_embed += f"Description: {description}"

        # Create keywords
        keywords = ["avm", "ptn", module_name, "bicep", "infrastructure", "deployment", "template", "pattern"]

        return {
            "id": module_id,
            "source": relative_path.replace('/', '\\\\'),
            "content_to_embed": content_to_embed,
            "keywords": keywords
        }

    except Exception as e:
        print(f"Error processing {relative_path}: {e}")
        return None

# Find all main.bicep files in ptn directories
new_modules = []
print("\\nScanning for pattern modules...")

for root, dirs, files in os.walk(ptn_path):
    if 'main.bicep' in files:
        main_bicep_path = Path(root) / 'main.bicep'
        relative_path = str(main_bicep_path.relative_to(ptn_path.parent))

        # Extract module info
        module_info = extract_ptn_module_info(main_bicep_path, relative_path)

        if module_info and module_info['id'] not in existing_ids:
            new_modules.append(module_info)
            print(f"  Found: {module_info['id']}")

print(f"\\nFound {len(new_modules)} new pattern modules")

if new_modules:
    # Append new modules to the file
    with open(output_file, 'a', encoding='utf-8') as f:
        for module in new_modules:
            f.write(json.dumps(module, ensure_ascii=False) + '\\n')

    print(f"\\nSuccessfully added {len(new_modules)} pattern modules to {output_file.name}")
else:
    print("\\nNo new pattern modules to add")

# Print summary
total_count = len(existing_ids) + len(new_modules)
print(f"\\nTotal modules in file: {total_count}")
print(f"  - Resource (res) modules: {len(existing_ids)}")
print(f"  - Pattern (ptn) modules: {len(new_modules)}")
