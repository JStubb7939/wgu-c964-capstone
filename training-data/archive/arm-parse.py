import os
import json
from concurrent.futures import ProcessPoolExecutor
import time

MAX_FILE_SIZE_KB = 100

def process_bicep_file(bicep_file_path):
    """
    Reads a Bicep file and prepares a training data object with a placeholder
    for the prompt. Returns a single dictionary.
    """
    try:
        # 1. Check file size
        if os.path.getsize(bicep_file_path) > MAX_FILE_SIZE_KB * 1024:
            return None

        # 2. Read the Bicep code (this is the 'completion')
        with open(bicep_file_path, 'r', encoding='utf-8') as f:
            bicep_code = f.read()

        # 3. Create a single training data pair with an empty prompt placeholder.
        training_pair = {
            "prompt": "",
            "completion": bicep_code
        }
        return training_pair

    except Exception as e:
        print(f"  -> An unexpected error occurred with {bicep_file_path}: {e}")
        return None

def main():
    """
    Main function to find all Bicep files, process them in parallel,
    and write the output to a .jsonl template file.
    """
    start_time = time.time()

    # --- Step 1: Find all Bicep files ---
    root_dir = '.'
    bicep_files_to_process = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".bicep"):
                bicep_files_to_process.append(os.path.join(root, file))

    print(f"Found {len(bicep_files_to_process)} Bicep files to process.")

    # --- Step 2 & 3: Process files and write to JSONL ---
    output_filename = 'classic-training-data-template.jsonl'
    total_pairs = 0

    with open(output_filename, 'w', encoding='utf-8') as f_out:
        with ProcessPoolExecutor() as executor:
            results = executor.map(process_bicep_file, bicep_files_to_process)

            for i, result in enumerate(results):
                if result is not None:
                    f_out.write(json.dumps(result) + '\n')
                    total_pairs += 1

                if (i + 1) % 100 == 0:
                    print(f"Progress: Processed {i+1}/{len(bicep_files_to_process)} files...")

    end_time = time.time()
    print("\n--- Classic data extraction complete! ---")
    print(f"Successfully generated {total_pairs} training templates in {end_time - start_time:.2f} seconds.")
    print(f"Template file saved to '{output_filename}'")


if __name__ == "__main__":
    main()
