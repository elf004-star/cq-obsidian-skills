#!/usr/bin/env python3
"""
Markdown processor - cleans and standardizes markdown documents.
Processes files in place, creates .bak.orig backups, and generates reports.
"""

import re
import os
import sys
import shutil
from pathlib import Path

# Default paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_INPUT_DIR = PROJECT_ROOT / "doc"
OUTPUT_DIR = PROJECT_ROOT / "doc" / "result"


def collect_markdown_files(path: str | Path) -> list[Path]:
    """Collect all markdown files from given path."""
    path = Path(path)
    if path.is_file() and path.suffix == '.md':
        return [path]
    return list(path.rglob("*.md"))


def create_backup(file_path: Path) -> Path | None:
    """Create backup of original file."""
    backup_path = file_path.with_name(f"{file_path.stem}.original.bak.orig")
    shutil.copy2(file_path, backup_path)
    return backup_path


def clean_backup_files(path: str | Path) -> list[Path]:
    """Remove backup files (*.bak.orig, *original*.bak, etc.)."""
    path = Path(path)
    removed = []
    for pattern in ["*.bak.orig", "*original*.bak*", "*.orig", "*.backup"]:
        for f in path.rglob(pattern):
            if f.is_file():
                f.unlink()
                removed.append(f)
    return removed


def clean_temp_files(path: str | Path) -> list[Path]:
    """Remove temporary/process files."""
    path = Path(path)
    removed = []
    for pattern in ["*.tmp", "*_temp_*", "*.swp", "*.swo"]:
        for f in path.rglob(pattern):
            if f.is_file():
                f.unlink()
                removed.append(f)
    return removed


def normalize_headings(content: str) -> str:
    """Ensure consistent heading format."""
    lines = content.split('\n')
    result = []
    for line in lines:
        match = re.match(r'^(#{1,6})\s+(.+)', line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            result.append(f"{'#' * level} {text}")
        else:
            result.append(line)
    return '\n'.join(result)


def normalize_code_blocks(content: str) -> str:
    """Ensure consistent code block format."""
    lines = content.split('\n')
    result = []
    in_code_block = False
    code_start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_start = i
                result.append(line)
            else:
                in_code_block = False
                result.append(line)
        elif not in_code_block:
            result.append(line)
    return '\n'.join(result)


def remove_empty_lines(content: str) -> str:
    """Remove excessive empty lines (more than 2 consecutive)."""
    lines = content.split('\n')
    result = []
    empty_count = 0
    for line in lines:
        if not line.strip():
            empty_count += 1
            if empty_count <= 2:
                result.append(line)
        else:
            empty_count = 0
            result.append(line)
    return '\n'.join(result)


def process_markdown(content: str) -> str:
    """Apply all normalization rules."""
    content = normalize_headings(content)
    content = normalize_code_blocks(content)
    content = remove_empty_lines(content)
    return content


def process_file(file_path: Path) -> dict:
    """Process a single markdown file."""
    result = {
        "path": file_path,
        "backup": None,
        "changes": [],
        "success": False,
        "error": None
    }
    try:
        content = file_path.read_text(encoding='utf-8')
        original_len = len(content)

        # Create backup
        backup_path = create_backup(file_path)
        result["backup"] = backup_path

        # Process content
        processed = process_markdown(content)

        # Track changes
        if processed != content:
            result["changes"].append("formatting normalized")

        # Write processed content
        file_path.write_text(processed, encoding='utf-8')
        result["success"] = True

    except Exception as e:
        result["error"] = str(e)

    return result


def process_directory(input_dir: Path, output_dir: Path | None = None) -> dict:
    """Process all markdown files in directory."""
    summary = {
        "files_processed": 0,
        "files_failed": 0,
        "files_removed": 0,
        "modifications": [],
        "processed_files": [],
        "removed_files": [],
        "errors": []
    }

    files = collect_markdown_files(input_dir)

    for file_path in files:
        result = process_file(file_path)
        if result["success"]:
            summary["files_processed"] += 1
            summary["processed_files"].append(result["path"])
            if result["changes"]:
                summary["modifications"].append({
                    "file": result["path"].name,
                    "changes": result["changes"],
                    "backup": result["backup"]
                })
        else:
            summary["files_failed"] += 1
            summary["errors"].append({
                "file": file_path.name,
                "error": result["error"]
            })

    # Cleanup
    if input_dir.exists():
        backups = clean_backup_files(input_dir)
        temps = clean_temp_files(input_dir)
        summary["files_removed"] = len(backups) + len(temps)
        summary["removed_files"] = [str(f) for f in backups + temps]

    return summary


def generate_report(summary: dict) -> str:
    """Generate markdown report."""
    report = ["## Markdown Processing Summary", ""]
    report.append("**Statistics:**")
    report.append(f"- Folders Processed: 1")
    report.append(f"- Files Successfully Processed: {summary['files_processed']}")
    report.append(f"- Files Failed: {summary['files_failed']}")
    report.append("")

    if summary["modifications"]:
        report.append("**Modifications Made:**")
        for mod in summary["modifications"]:
            changes_str = ", ".join(mod["changes"])
            report.append(f"- {mod['file']}: {changes_str}")
        report.append("")

    if summary["processed_files"]:
        report.append("**Processed Files:**")
        for f in summary["processed_files"]:
            report.append(f"- {f}")
        report.append("")

    if summary["files_removed"] > 0:
        report.append("**Cleanup Results:**")
        report.append(f"- Files Removed: {summary['files_removed']}")
        for f in summary["removed_files"]:
            report.append(f"  - {f}")
        report.append("")

    if summary["errors"]:
        report.append("**Errors:**")
        for err in summary["errors"]:
            report.append(f"- {err['file']}: {err['error']}")

    return '\n'.join(report)


def main():
    """Main entry point."""
    input_path = sys.argv[1] if len(sys.argv) > 1 else str(DEFAULT_INPUT_DIR)
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    input_dir = Path(input_path)
    output_dir = Path(output_path) if output_path else None

    if not input_dir.exists():
        print(f"Error: Path does not exist: {input_dir}")
        sys.exit(1)

    print(f"Processing: {input_dir}")

    summary = process_directory(input_dir, output_dir)
    report = generate_report(summary)

    print("\n" + report)

    return summary


if __name__ == "__main__":
    main()
