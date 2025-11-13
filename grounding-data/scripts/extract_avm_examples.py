import json
import re
from pathlib import Path
from typing import List, Optional

BASE_DIR = Path(__file__).resolve().parents[3]
MODULES_ROOT = BASE_DIR / "grounding-data" / "bicep-registry-modules-main"
OUTPUT_PATH = BASE_DIR / "grounding-data" / "extracted_avm_examples.jsonl"

EXAMPLE_HEADING_RE = re.compile(r"^###\s+Example\s+(\d+):\s+_([^_]+)_\s*$", re.MULTILINE)
BICEP_SNIPPET_RE = re.compile(r"<summary>via Bicep module</summary>\s*```bicep\s*(.*?)```", re.DOTALL)
TITLE_RE = re.compile(r"#\s*(.*?)\s*`?\[(.*?)\]`?")


def load_version(module_dir: Path) -> Optional[str]:
    version_file = module_dir / "version.json"
    if not version_file.exists():
        return None
    with version_file.open(encoding="utf-8-sig") as f:
        data = json.load(f)
    return data.get("version")


def extract_params_block(bicep_code: str) -> Optional[str]:
    lines = bicep_code.splitlines()
    params_start = None

    for idx, line in enumerate(lines):
        if line.strip().startswith("params:"):
            params_start = idx
            break

    if params_start is None:
        return None

    brace_balance = 0
    collected: List[str] = []
    for idx in range(params_start, len(lines)):
        line = lines[idx]
        collected.append(line)
        brace_balance += line.count("{")
        brace_balance -= line.count("}")

        if brace_balance == 0 and idx > params_start:
            break

    return "\n".join(collected).strip()


def clean_params_block(params_block: Optional[str]) -> str:
    if not params_block:
        return "(No explicit params block found.)"
    return params_block


def normalise_module_id(bicep_code: str, module_id: str) -> str:
    module_prefix = module_id.rsplit(":", maxsplit=1)[0]
    return bicep_code.replace("'" + module_prefix + ":<version>'", "'" + module_id + "'")


def derive_module_id(version: str, module_path: str) -> str:
    module_path_posix = module_path.replace("\\", "/")
    return f"br/public:{module_path_posix}:{version}"


def parse_examples(readme_text: str) -> List[re.Match]:
    return list(EXAMPLE_HEADING_RE.finditer(readme_text))


def extract_long_description(section: str) -> str:
    for line in section.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def extract_bicep_snippet(section: str) -> Optional[str]:
    match = BICEP_SNIPPET_RE.search(section)
    if not match:
        return None
    return match.group(1).strip()


def main() -> None:
    if not MODULES_ROOT.exists():
        raise FileNotFoundError(f"Modules root not found: {MODULES_ROOT}")

    results = []

    readme_paths = sorted(MODULES_ROOT.glob("avm/**/README.md"))

    for readme_path in readme_paths:
        relative_readme = readme_path.relative_to(MODULES_ROOT)

        with readme_path.open(encoding="utf-8") as f:
            readme_text = f.read()

        title_match = TITLE_RE.search(readme_text)
        if not title_match:
            continue

        title = title_match.group(1).strip()
        resource_type = title_match.group(2).strip()

        version = load_version(readme_path.parent)
        if not version:
            continue

        module_rel_path = str(relative_readme.parent).replace("\\", "/")
        module_id = derive_module_id(version, module_rel_path)

        resource_path_display = resource_type

        example_matches = parse_examples(readme_text)
        if not example_matches:
            continue

        for idx, match in enumerate(example_matches):
            example_number = match.group(1)
            example_short = match.group(2).strip()

            example_start = match.end()
            example_end = example_matches[idx + 1].start() if idx + 1 < len(example_matches) else len(readme_text)
            example_section = readme_text[example_start:example_end]

            example_long = extract_long_description(example_section)
            example_description = example_short if not example_long else f"{example_short} - {example_long}"

            bicep_snippet = extract_bicep_snippet(example_section)
            if not bicep_snippet:
                continue

            bicep_snippet = normalise_module_id(bicep_snippet, module_id)

            params_block = clean_params_block(extract_params_block(bicep_snippet))

            content_to_embed = "\n".join([
                f"Recommended AVM Module for {title}: {example_description}",
                f"Resource Type Path: {resource_path_display}",
                f"Module ID: {module_id}",
                "Parameters:",
                params_block,
            ])

            result = {
                "id": f"{module_rel_path.replace('/', '_')}_example_{example_number}",
                "source": relative_readme.as_posix(),
                "content_to_embed": content_to_embed,
                "bicep": bicep_snippet,
            }

            results.append(result)

    with OUTPUT_PATH.open("w", encoding="utf-8") as outfile:
        for entry in results:
            json.dump(entry, outfile, ensure_ascii=False)
            outfile.write("\n")

    print(f"Extracted {len(results)} examples to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
