"""Extract AVM README examples into JSONL training data."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional


MODULE_DECL_RE = re.compile(r"module\s+(?P<name>[A-Za-z_][\w]*)\s+'(?P<type>[^']+)'")
RESOURCE_DECL_RE = re.compile(r"resource\s+(?P<name>[A-Za-z_][\w]*)\s+'(?P<type>[^']+)'")
EXAMPLE_HEADER_RE = re.compile(r"^###\s+Example\s+\d+\s*:?(?P<label>.*)$", re.IGNORECASE)


@dataclass
class ExampleRecord:
    """Structured data extracted from a README example section."""

    module_title: str
    resource_type: str
    module_description: str
    short_description: str
    long_description: str
    bicep_code: str


def _readme_paths() -> List[Path]:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    avm_root = (
        project_root
        / "grounding-data"
        / "bicep-registry-modules-main"
        / "avm"
    )
    if not avm_root.exists():
        raise FileNotFoundError(f"AVM repository not found at {avm_root}")

    return sorted(avm_root.glob("**/README.md"))


def _strip_markdown_heading(line: str) -> str:
    return line.lstrip("# ").strip()


def _clean_markdown(text: str) -> str:
    cleaned = text.replace("`", "").strip()
    cleaned = cleaned.strip("*_ ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    if cleaned.startswith(">"):
        cleaned = cleaned.lstrip("> ")
    return cleaned.strip()


def _collect_examples(path: Path) -> List[ExampleRecord]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Identify module title and resource type
    title = ""
    resource_type = ""
    description = ""

    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            continue
        if not title:
            title = _strip_markdown_heading(line)
            match = re.search(r"\[([^\]]+)\]", line)
            if match:
                resource_type = _clean_markdown(match.group(1))
            # find module description on subsequent non-empty line
            for desc_line in lines[idx + 1 :]:
                desc = desc_line.strip()
                if desc:
                    description = _clean_markdown(desc)
                    break
            break

    module_title = _clean_markdown(title.split("[")[0])
    examples: List[ExampleRecord] = []

    i = 0
    total_lines = len(lines)
    while i < total_lines:
        match = EXAMPLE_HEADER_RE.match(lines[i].strip())
        if not match:
            i += 1
            continue

        short_description = _clean_markdown(match.group("label").strip()).rstrip(".")
        if short_description.lower().startswith(":"):
            short_description = short_description[1:].strip()

        long_description = ""
        j = i + 1
        while j < total_lines:
            candidate = lines[j].strip()
            if not candidate:
                j += 1
                continue
            if candidate.startswith("####"):
                break
            long_description = _clean_markdown(candidate)
            break
        if not long_description:
            long_description = description

        bicep_code = _extract_bicep_block(lines, start_index=i + 1)
        if bicep_code:
            examples.append(
                ExampleRecord(
                    module_title=module_title,
                    resource_type=resource_type,
                    module_description=description,
                    short_description=short_description or module_title,
                    long_description=long_description,
                    bicep_code=bicep_code,
                )
            )

        i = j if j > i else i + 1

    return examples


def _extract_bicep_block(lines: List[str], start_index: int) -> Optional[str]:
    """Locate the first fenced bicep code block following start_index."""

    i = start_index
    total = len(lines)
    while i < total:
        line = lines[i].strip().lower()
        if line.startswith("### ") and "example" in line:
            return None
        if line.startswith("```bicep"):
            i += 1
            code_lines: List[str] = []
            while i < total and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            return "\n".join(code_lines).strip()
        i += 1
    return None


def _derive_request_subject(description: str, fallback: str) -> str:
    desc = description.strip().rstrip(".")
    lowered = desc.lower()
    prefixes = [
        "this module deploys",
        "this module creates",
        "this module provisions",
    ]
    for prefix in prefixes:
        if lowered.startswith(prefix):
            subject = desc[len(prefix) :].strip()
            return subject if subject else fallback
    return fallback


def _build_user_prompt(example: ExampleRecord, include_resource_type: bool = True) -> str:
    subject = _derive_request_subject(example.module_description, example.module_title).strip()
    subject_phrase = subject

    def format_detail(detail: str) -> str:
        detail = detail.strip().rstrip(".")
        if not detail:
            return "."
        normalized = detail
        if normalized and normalized[0].isupper():
            normalized = normalized[0].lower() + normalized[1:]
        leading_phrases = (
            "using ",
            "with ",
            "including ",
            "deploying ",
            "creating ",
            "configuring ",
        )
        for phrase in leading_phrases:
            if normalized.startswith(phrase):
                return f" {normalized}."
        return f" using the {detail} configuration."

    request = f"Generate a Bicep template for {subject_phrase}"
    if include_resource_type and example.resource_type:
        request += f" [{example.resource_type}]"

    short_detail = example.short_description or ""
    if short_detail:
        request += format_detail(short_detail)
    else:
        request += "."

    return request.strip()


def _build_plan(bicep_code: str, rationale: str) -> dict:
    resources = []
    for pattern in (MODULE_DECL_RE, RESOURCE_DECL_RE):
        for match in pattern.finditer(bicep_code):
            resources.append(
                {
                    "resourceType": match.group("type"),
                    "name": match.group("name"),
                }
            )
    return {
        "resources": resources,
        "rationale": _clean_markdown(rationale).strip(),
    }


def _build_assistant_payload(example: ExampleRecord) -> str:
    payload = {
        "plan": _build_plan(example.bicep_code, example.module_description),
        "files": [
            {
                "path": "main.bicep",
                "language": "bicep",
                "content": example.bicep_code,
            }
        ],
        "warnings": [],
    }
    return json.dumps(payload)


def _record_to_jsonl(example: ExampleRecord, include_resource_type: bool = True) -> str:
    record = {
        "messages": [
            {
                "role": "user",
                "content": _build_user_prompt(
                    example, include_resource_type=include_resource_type
                ),
            },
            {"role": "assistant", "content": _build_assistant_payload(example)},
        ]
    }
    return json.dumps(record)


def _flatten(iterables: Iterable[Iterable[ExampleRecord]]) -> List[ExampleRecord]:
    collected: List[ExampleRecord] = []
    for chunk in iterables:
        collected.extend(chunk)
    return collected


def main() -> None:
    output_path = Path(__file__).resolve().parent.parent / "avm_examples.jsonl"
    examples = _flatten(_collect_examples(path) for path in _readme_paths())

    with output_path.open("w", encoding="utf-8") as handle:
        for example in examples:
            handle.write(_record_to_jsonl(example, include_resource_type=True) + "\n")
        for example in examples:
            handle.write(
                _record_to_jsonl(example, include_resource_type=False) + "\n"
            )

    print(f"Extracted {len(examples)} examples to {output_path}")


if __name__ == "__main__":
    main()
