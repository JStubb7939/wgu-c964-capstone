import json
import os
from pathlib import Path

# Base paths
base_path = Path(r"c:\Users\jostubbl.REDMOND\Downloads\c964-capstone\grounding-data")
ptn_path = base_path / "bicep-registry-modules" / "avm" / "ptn"
output_file = base_path / "extracted_avm_data.jsonl"

# Read existing res modules
existing_modules = []
with open(output_file, 'r', encoding='utf-8') as f:
    for line in f:
        module = json.loads(line.strip())
        existing_modules.append(module)

print(f"Found {len(existing_modules)} existing modules")

# Function to extract module info
def extract_ptn_module_info(main_bicep_path, relative_path):
    """Extract module information from a pattern module."""
    try:
        # Get version from version.json in the same directory
        version_json_path = main_bicep_path.parent / "version.json"
        version = "0.1.0"  # default

        if version_json_path.exists():
            with open(version_json_path, 'r', encoding='utf-8-sig') as vf:
                version_data = json.load(vf)
                version = version_data.get('version', '0.1.0')

        # Format version as major.minor.patch
        version_parts = version.split('.')
        if len(version_parts) == 2:
            version = f"{version}.0"

        # Create module ID from path
        path_parts = relative_path.replace('\\', '/').split('/')
        module_id = 'ptn_' + '_'.join(path_parts[:-1])  # Exclude main.bicep

        # Create module path for source
        module_path = '\\'.join(path_parts[:-1])

        # Extract module name (last part of path)
        module_name = path_parts[-2] if len(path_parts) > 1 else 'unknown'

        # Try to extract description from README
        readme_path = main_bicep_path.parent / "README.md"
        description = None

        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as rf:
                    readme_content = rf.read()
                    # Look for description in various formats
                    if '## Description' in readme_content:
                        desc_section = readme_content.split('## Description')[1].split('##')[0]
                        description = desc_section.strip().split('\n')[0].strip()
                    elif 'description:' in readme_content.lower():
                        for line in readme_content.split('\n'):
                            if 'description:' in line.lower():
                                description = line.split(':', 1)[1].strip()
                                break
            except:
                pass

        if not description:
            description = f"Pattern module for '{module_name}'"

        # Create module info
        module_info = {
            "id": module_id,
            "source": module_path + "\\main.bicep",
            "content_to_embed": f"Recommended AVM Module for '{module_name}'. This is the preferred, verified module for Bicep.\nModule ID: br_public:{module_id}:{version}\nDescription: {description}",
            "keywords": ["avm", "ptn", module_name, "bicep", "infrastructure", "deployment", "template", "pattern"]
        }

        return module_info
    except Exception as e:
        print(f"Error processing {main_bicep_path}: {e}")
        return None

# Collect new ptn modules
new_modules = []
print("\nScanning for pattern modules...")

for root, dirs, files in os.walk(ptn_path):
    if 'main.bicep' in files:
        main_bicep_path = Path(root) / 'main.bicep'
        relative_path = str(main_bicep_path.relative_to(ptn_path.parent))

        # Extract module info
        module_info = extract_ptn_module_info(main_bicep_path, relative_path)

        if module_info:
            new_modules.append(module_info)
            print(f"  Found: {module_info['id']} (version {module_info['content_to_embed'].split(':')[-1].split('\\n')[0]})")

print(f"\nFound {len(new_modules)} pattern modules")

# Write all modules (res + ptn) back to the file
with open(output_file, 'w', encoding='utf-8') as f:
    # Write all existing res modules
    for module in existing_modules:
        f.write(json.dumps(module, ensure_ascii=False) + '\n')

    # Write all new ptn modules
    for module in new_modules:
        f.write(json.dumps(module, ensure_ascii=False) + '\n')

print(f"\nSuccessfully rebuilt {output_file.name}")
print(f"Total modules: {len(existing_modules) + len(new_modules)}")
print(f"  - Resource (res) modules: {len(existing_modules)}")
print(f"  - Pattern (ptn) modules: {len(new_modules)}")
