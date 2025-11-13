import os
import re
import subprocess
import json
from concurrent.futures import ProcessPoolExecutor
import time

def process_bicep_file(bicep_file_path):
    """
    Processes a single Bicep file. This function is designed to be
    run in parallel by a ProcessPoolExecutor.
    """
    print(f"Processing: {bicep_file_path}")
    try:
        result = subprocess.run(
            ["az", "bicep", "build", "--file", bicep_file_path, "--stdout"],
            capture_output=True, text=True, check=True, encoding='utf-8', shell=True
        )

        if not result.stdout:
            print(f"  -> WARNING: No output from bicep build for {bicep_file_path}. Stderr: {result.stderr.strip()}")
            return None

        arm_json = json.loads(result.stdout)

        root = os.path.dirname(bicep_file_path)
        relative_path = os.path.normpath(root).replace('\\', '/')
        module_id = f"br/public:{relative_path}:<version>"

        # Sanitize the module_id to be a valid document key for Azure AI Search
        replacements = {".": "-", "/": "_", "#": "_"}
        pattern = re.compile("|".join(map(re.escape, replacements.keys())))
        module_id_sanitized = pattern.sub(lambda match: replacements[match.group(0)], module_id)

        parameters = []
        if "parameters" in arm_json:
            for param_name, param_details in arm_json["parameters"].items():
                parameters.append({
                    "name": param_name,
                    "type": param_details.get("type", "N/A"),
                    "description": param_details.get("metadata", {}).get("description", "No description.")
                })

        param_descriptions = "\n".join([f"- {p['name']} ({p['type']}): {p['description']}" for p in parameters])

        chunk_text = (
            f"Recommended AVM Module for '{os.path.basename(root)}'. "
            f"This is the preferred, verified module for Bicep.\n"
            f"Module ID: {module_id_sanitized}\nParameters:\n{param_descriptions}"
        )

        return {
            "id": module_id_sanitized,
            "source": bicep_file_path,
            "content_to_embed": chunk_text
        }

    except subprocess.CalledProcessError as e:
        print(f"  -> FAILED to process {bicep_file_path}. Stderr: {e.stderr.strip()}")
        return None
    except json.JSONDecodeError as e:
        print(f"  -> FAILED to parse JSON for {bicep_file_path}: {e}")
        return None
    except Exception as e:
        print(f"  -> An unexpected error occurred with {bicep_file_path}: {e}")
        return None

def main():
    """
    Main function to find all Bicep files, process them in parallel,
    and write the output to a .jsonl file.
    """
    start_time = time.time()

    # --- Step 1: Find all Bicep files ---
    modules_root = 'res'
    bicep_files_to_process = []
    for root, dirs, files in os.walk(modules_root):
        if "main.bicep" in files:
            bicep_files_to_process.append(os.path.join(root, "main.bicep"))

    print(f"Found {len(bicep_files_to_process)} Bicep modules to process.")

    # --- Step 2 & 3: Process files and write to JSONL in a streaming fashion ---
    output_filename = 'extracted_avm_data.jsonl'
    processed_count = 0

    with open(output_filename, 'w', encoding='utf-8') as f:
        with ProcessPoolExecutor() as executor:
            results = executor.map(process_bicep_file, bicep_files_to_process)

            for result in results:
                if result is not None:
                    f.write(json.dumps(result) + '\n')
                    processed_count += 1

    end_time = time.time()
    print("\n--- Data extraction complete! ---")
    print(f"Successfully processed and wrote {processed_count} modules in {end_time - start_time:.2f} seconds.")
    print(f"Full data saved to '{output_filename}'")


if __name__ == "__main__":
    main()
