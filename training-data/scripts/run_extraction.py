"""Entry-point script to generate agent training data from Azure Quickstart templates."""
from __future__ import annotations

import json
import os
import subprocess
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import List, Optional

from data_transformer import generate_parameters_json, generate_plan_and_warnings

SUPPORTED_FILES = {"azuredeploy.json", "main.bicep", "azuredeploy.bicep"}

def _decompile_bicep(file_path: Path) -> Optional[str]:
    """Run `bicep decompile` and return the resulting Bicep code."""
    try:
        completed = subprocess.run(
            ["az", "bicep", "decompile", "--file", str(file_path)],
            capture_output=True, text=True, check=True, shell=True
        )
    except FileNotFoundError:
        print(f"bicep CLI not found while processing {file_path}")
        return None
    except subprocess.CalledProcessError as e:
        print(f"  -> FAILED to process {file_path}. Stderr: {e.stderr.strip()}")
        return None
    except json.JSONDecodeError as e:
        print(f"  -> FAILED to parse JSON for {file_path}: {e}")
        return None
    except Exception as e:
        print(f"  -> An unexpected error occurred with {file_path}: {e}")
        return None

    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        print(f"Failed to decompile {file_path}: {stderr}")
        return None

    return completed.stdout


def _read_bicep(file_path: Path) -> Optional[str]:
    try:
        return file_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Failed to read {file_path}: {exc}")
        return None


def process_file(file_path: str, i: int) -> Optional[dict]:
    """Convert a single template file into an agent training example."""
    path = Path(file_path)
    bicep_code: Optional[str] = None

    print(f"Processing file {i}: {path}...")

    if path.name == "azuredeploy.json":
        bicep_code = _decompile_bicep(path)
    elif path.name in {"main.bicep", "azuredeploy.bicep"}:
        bicep_code = _read_bicep(path)

    if not bicep_code or not bicep_code.strip():
        return None

    plan, warnings = generate_plan_and_warnings(bicep_code)
    parameters_json = generate_parameters_json(bicep_code)

    bicep_filename = path.name
    if path.suffix.lower() == ".json":
        bicep_filename = path.with_suffix(".bicep").name

    example = {
        "plan": plan,
        "files": [
            {
                "path": bicep_filename,
                "language": "bicep",
                "content": bicep_code,
            },
            {
                "path": "parameters.json",
                "language": "json",
                "content": parameters_json,
            },
        ],
        "warnings": warnings,
    }

    return example


def _collect_supported_files(root: Path) -> List[str]:
    targets: List[str] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for filename in filenames:
            if filename in SUPPORTED_FILES:
                targets.append(str(Path(dirpath) / filename))
    return targets


def main() -> None:
    templates_root = Path(__file__).resolve().parents[1] / "azure-quickstart-templates"
    output_path = Path(__file__).resolve().parents[1] / "train_agent_v2.jsonl"

    template_files = _collect_supported_files(templates_root)
    print(f"Discovered {len(template_files)} template files to process.")

    def generate_index():
        for i in range(len(template_files)):
            yield i

    processed = 0

    with ProcessPoolExecutor() as executor:
        results = executor.map(process_file, template_files, generate_index())
        with output_path.open("a", encoding="utf-8") as f_out:
            for result in results:
                if result is None:
                    continue
                assistant_payload = json.dumps(result)
                record = {
                    "messages": [
                        {"role": "user", "content": ""},
                        {"role": "assistant", "content": assistant_payload},
                    ]
                }
                f_out.write(json.dumps(record) + "\n")
                processed += 1

    print(f"Wrote {processed} training records to {output_path}")


if __name__ == "__main__":
    main()
