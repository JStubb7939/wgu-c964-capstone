import os
import json
import re

def parse_arm_schemas_to_jsonl():
    """
    Finds all ARM schemas, iterates through the 'resourceDefinitions',
    and writes each one as a new line in a .jsonl file.

    ASSUMPTION: This script is in the root of the 'azure-resource-manager-schemas' repo.
    """
    schemas_root = 'schemas'
    output_filename = 'extracted_schema_data.jsonl'
    processed_count = 0

    with open(output_filename, 'w', encoding='utf-8') as f:
        print(f"Starting schema extraction, output will be in '{output_filename}'")

        # Walk through the directory to find all schema files
        for root, dirs, files in os.walk(schemas_root):
            for file in files:
                if not file.endswith('.json'):
                    continue

                file_path = os.path.join(root, file)
                relative_path = os.path.normpath(file_path).replace('\\', '/')

                try:
                    with open(file_path, 'r', encoding='utf-8') as schema_file:
                        schema = json.load(schema_file)

                    resource_definitions = schema.get('resourceDefinitions')
                    if not resource_definitions:
                        continue

                    # Loop through each definition in the file
                    for resource_name, resource_def in resource_definitions.items():
                        properties = resource_def.get('properties', {})
                        if not properties:
                            continue

                        resource_type = resource_def.get('description', resource_name)
                        unique_id = f"{relative_path}_{resource_type}"

                        replacements = {
                            ".": "-",
                            " ": "-",
                            "/": "_",
                            "#": "_",
                            ":": "_"
                        }
                        pattern = re.compile("|".join(map(re.escape, replacements.keys())))
                        unique_id_sanitized = pattern.sub(lambda match: replacements[match.group(0)], unique_id).strip('-')

                        prop_descriptions = "\n".join(
                            f"- {prop_name} (type: {prop.get('type', 'N/A')}) - {prop.get('description', '')}"
                            for prop_name, prop in properties.items()
                        )

                        chunk_text = (
                            f"ARM Schema for Resource Type: '{resource_type}'\n"
                            f"Schema ID: {unique_id_sanitized}\n"
                            f"Valid Top-Level Properties:\n{prop_descriptions}"
                        )

                        line_object = {
                            "id": unique_id_sanitized,
                            "source": file_path,
                            "content_to_embed": chunk_text
                        }

                        f.write(json.dumps(line_object) + '\n')
                        processed_count += 1
                        if processed_count % 500 == 0:
                            print(f"Processed {processed_count} definitions...")


                except Exception as e:
                    print(f"  -> Failed to process {file_path}: {e}")

    return processed_count

if __name__ == "__main__":
    total_processed = parse_arm_schemas_to_jsonl()
    print("\n--- Schema extraction complete! ---")
    print(f"Found and wrote {total_processed} resource definitions to 'extracted_schema_data.jsonl'")