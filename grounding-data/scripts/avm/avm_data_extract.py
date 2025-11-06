import os
import subprocess
import json

def parse_local_avm_modules():
    """
    Finds all modules within the local 'res' directory and extracts their
    parameter information by compiling them to ARM JSON.
    
    ASSUMPTION: This script is located and run from the 'avm' directory.
    """
    modules_data = []
    # Start searching from the 'res' subdirectory of the current location.
    modules_root = 'res' 

    # Walk through the directory to find all 'main.bicep' files
    for root, dirs, files in os.walk(modules_root):
        if "main.bicep" in files:
            bicep_file_path = os.path.join(root, "main.bicep")
            print(f"Processing: {bicep_file_path}")

            try:
                # Use 'az bicep build' to compile Bicep to ARM JSON
                result = subprocess.run(
                    ["az", "bicep", "build", "--file", bicep_file_path, "--stdout"],
                    capture_output=True, text=True, check=True, shell=True
                )
                arm_json = json.loads(result.stdout)

                # Create the module ID from the relative path
                relative_path = os.path.normpath(root).replace('\\', '/')
                module_id = f"br/public:{relative_path}:<version>" # Version is a placeholder

                # Structure the extracted parameters
                parameters = []
                if "parameters" in arm_json:
                    for param_name, param_details in arm_json["parameters"].items():
                        parameters.append({
                            "name": param_name,
                            "type": param_details.get("type", "N/A"),
                            "description": param_details.get("metadata", {}).get("description", "No description.")
                        })
                
                # Create a text chunk for embedding
                param_descriptions = "\n".join([f"- {p['name']} ({p['type']}): {p['description']}" for p in parameters])

                chunk_text = (
                    f"Recommended AVM Module for '{os.path.basename(root)}'. "
                    f"This is the preferred, verified module for Bicep.\n"
                    f"Module ID: {module_id}\nParameters:\n{param_descriptions}"
                )

                modules_data.append({
                    "id": module_id,
                    "source": bicep_file_path,
                    "content_to_embed": chunk_text
                })

            except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
                print(f"  -> Failed to process {bicep_file_path}: {e}")

    return modules_data

if __name__ == "__main__":
    # 1. Run this script first to get the data.
    extracted_data = parse_local_avm_modules()
    
    # 2. Save the data to a file to be used by the next script.
    with open('extracted_avm_data.json', 'w') as f:
        json.dump(extracted_data, f, indent=2)
        
    print("\n--- Data extraction complete! ---")
    print("Sample of first item:")
    print(json.dumps(extracted_data[0], indent=2))
    print("\nFull data saved to 'extracted_avm_data.json'")