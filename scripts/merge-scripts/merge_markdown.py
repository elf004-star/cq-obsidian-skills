#!/usr/bin/env python3
"""Merge multiple markdown files into one, handling frontmatter appropriately."""

import re
import os
import sys
from pathlib import Path

# Default paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_DIR = PROJECT_ROOT / "process"
DEFAULT_OUTPUT = PROJECT_ROOT / "doc" / "result" / "merged.md"


def extract_frontmatter(content: str) -> tuple[str, str]:
    """Extract frontmatter from markdown content. Returns (frontmatter, body)."""
    if content.startswith('---'):
        match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
        if match:
            return match.group(1), match.group(2)
    return '', content


def remove_frontmatter(content: str) -> str:
    """Remove frontmatter from markdown content, returning only the body."""
    _, body = extract_frontmatter(content)
    return body


def merge_markdown_files(input_files: list[Path], output_path: Path) -> dict:
    """Merge markdown files with appropriate frontmatter handling."""
    result = {
        'input_files': [],
        'total_lines': 0,
        'output_path': str(output_path)
    }

    merged_content = []

    for i, file_path in enumerate(input_files):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.count('\n') + 1
        result['input_files'].append({
            'name': file_path.name,
            'lines': lines
        })
        result['total_lines'] += lines

        if i == 0:
            # Keep first file's full content (including frontmatter)
            merged_content.append(content.rstrip('\n'))
        else:
            # Remove frontmatter from subsequent files
            body = remove_frontmatter(content)
            # Strip trailing empty lines before joining
            merged_content.append(body.rstrip('\n'))

    # Join with two newlines (one blank line) between files
    final_content = '\n\n'.join(merged_content)
    # Ensure trailing newline
    final_content += '\n'

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)

    result['output_lines'] = final_content.count('\n') + 1
    result['output_size'] = len(final_content.encode('utf-8'))

    return result


def main():
    """Main entry point with command line arguments."""
    if len(sys.argv) > 1:
        input_dir = Path(sys.argv[1])
    else:
        input_dir = DEFAULT_INPUT_DIR

    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    else:
        output_path = DEFAULT_OUTPUT

    # Find all markdown files in input directory, sorted by name
    input_files = sorted(input_dir.glob("*.md"))

    if not input_files:
        print(f"No markdown files found in: {input_dir}")
        sys.exit(1)

    # Verify all input files exist
    for f in input_files:
        if not f.exists():
            print(f'ERROR: File not found: {f}')
            sys.exit(1)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = merge_markdown_files(input_files, output_path)

    print('Merge completed successfully!')
    print(f'Output file: {result["output_path"]}')
    print(f'Output size: {result["output_size"]:,} bytes')
    print(f'Output lines: {result["output_lines"]:,}')
    print()
    print('Input files processed:')
    for info in result['input_files']:
        print(f'  - {info["name"]}: {info["lines"]:,} lines')

    return result


if __name__ == '__main__':
    main()