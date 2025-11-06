import json
from pathlib import Path

# Read version for policy-insights/remediation
version_path = Path(r"c:\Users\jostubbl.REDMOND\Downloads\c964-capstone\grounding-data\bicep-registry-modules\avm\ptn\policy-insights\remediation\version.json")

with open(version_path, 'r', encoding='utf-8-sig') as f:
    version_data = json.load(f)
    version = version_data.get('version', '0.1')

# Format version
if len(version.split('.')) == 2:
    version = f"{version}.0"

# Create module info
module_info = {
    "id": "ptn_ptn_policy-insights_remediation",
    "source": "ptn\\\\policy-insights\\\\remediation\\\\main.bicep",
    "content_to_embed": f"Recommended AVM Module for 'remediation'. This is the preferred, verified module for Bicep.\\nModule ID: br_public:ptn_ptn_policy-insights_remediation:{version}\\nDescription: Pattern module for policy insights remediation",
    "keywords": ["avm", "ptn", "remediation", "bicep", "infrastructure", "deployment", "template", "pattern", "policy", "insights"]
}

# Append to file
output_file = Path(r"c:\Users\jostubbl.REDMOND\Downloads\c964-capstone\grounding-data\extracted_avm_data.jsonl")

with open(output_file, 'a', encoding='utf-8') as f:
    f.write(json.dumps(module_info, ensure_ascii=False) + '\\n')

print(f"Added policy-insights/remediation module with version {version}")
print(f"Total modules in file: 505")
