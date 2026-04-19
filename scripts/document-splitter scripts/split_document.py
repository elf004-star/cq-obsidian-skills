#!/usr/bin/env python3
"""
Split a markdown file using the minimum principle:
Accumulate content line by line; once the cumulative character count reaches the
THRESHOLD (default: 3600), break at the nearest following legal break point
(heading or blank line) while keeping protected blocks (fenced code, display
math) intact. The resulting chunks are as small as possible once the threshold
is crossed.
"""

import re
import os
import argparse

DEFAULT_THRESHOLD = 3600


def get_heading_info(line):
    """Return (level, text) for a Markdown heading line, or (None, None)."""
    m = re.match(r'^(#{1,6})\s+(.+)', line)
    if m:
        return len(m.group(1)), m.group(2).strip()
    return None, None


def generate_filename(title, index, max_length=60):
    """Build a safe filename from the first heading in a chunk."""
    safe = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', title)
    safe = re.sub(r'\s+', '-', safe).strip('-')
    if len(safe) > max_length:
        safe = safe[:max_length].rstrip('-')
    if not safe:
        safe = "section"
    return f"{index:02d}_{safe}.md"


def strip_empty_lines(lines):
    """Remove leading and trailing blank lines."""
    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1
    end = len(lines)
    while end > start and not lines[end - 1].strip():
        end -= 1
    return lines[start:end]


def extract_frontmatter(lines):
    """Extract YAML frontmatter block if present. Returns (fm_lines, offset)."""
    if lines and lines[0].strip() == '---':
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                return lines[:i + 1], i + 1
    return [], 0


def mark_protected(lines):
    """Mark each line with True if it belongs to a protected block.

    Protected blocks:
      - Fenced code blocks (``` ... ```)
      - Display math blocks whose opening/closing $$ sit on their own lines
    """
    n = len(lines)
    protected = [False] * n
    in_code = False
    in_math = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        if in_code:
            protected[i] = True
            if re.match(r'^`{3,}\s*$', stripped):
                in_code = False
            continue

        if in_math:
            protected[i] = True
            if stripped.count('$$') % 2 == 1:
                in_math = False
            continue

        if re.match(r'^`{3,}', stripped):
            in_code = True
            protected[i] = True
            continue

        dollar_count = stripped.count('$$')
        if dollar_count % 2 == 1:
            in_math = True
            protected[i] = True
            continue
        if dollar_count >= 2 and stripped.startswith('$$'):
            protected[i] = True

    return protected


def compute_legal_breaks(lines, protected):
    """Return list `legal` where legal[p] is True iff a chunk boundary may be
    placed immediately before line index p (0 <= p <= n)."""
    n = len(lines)
    legal = [False] * (n + 1)
    legal[0] = True
    legal[n] = True

    for p in range(1, n):
        if protected[p - 1] or protected[p]:
            continue
        if get_heading_info(lines[p])[0] is not None:
            legal[p] = True
            continue
        if not lines[p - 1].strip():
            legal[p] = True
    return legal


def split_minimal(lines, threshold):
    """Split `lines` into chunks using the minimum principle."""
    n = len(lines)
    if n == 0:
        return []

    protected = mark_protected(lines)
    legal = compute_legal_breaks(lines, protected)

    cum = [0] * (n + 1)
    for i in range(n):
        cum[i + 1] = cum[i] + len(lines[i]) + 1

    chunks = []
    start = 0
    while start < n:
        chosen = None
        for p in range(start + 1, n + 1):
            if not legal[p]:
                continue
            length = cum[p] - cum[start]
            if length >= threshold:
                chosen = p
                break
            chosen = p
        if chosen is None:
            chosen = n
        chunks.append(lines[start:chosen])
        start = chosen
    return chunks


def split_file(input_file, output_dir=None, threshold=DEFAULT_THRESHOLD):
    """Split a markdown file into smaller chunks and write them to disk."""
    input_file = os.path.abspath(input_file)
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(input_file), "process")
    os.makedirs(output_dir, exist_ok=True)

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('\r\n', '\n').replace('\r', '\n')
    lines = content.split('\n')

    frontmatter, fm_end = extract_frontmatter(lines)
    body = lines[fm_end:]

    print(f"Input: {input_file}")
    print(f"Frontmatter: {len(frontmatter)} lines")
    print(f"Body: {len(body)} lines, {sum(len(l) + 1 for l in body)} chars")
    print(f"Threshold: {threshold} chars")

    chunks = split_minimal(body, threshold)
    print(f"\nTotal output chunks: {len(chunks)}")

    for idx, chunk_lines in enumerate(chunks):
        chunk_lines = strip_empty_lines(chunk_lines)

        if idx == 0 and frontmatter:
            chunk_lines = list(frontmatter) + [''] + chunk_lines

        title = None
        for line in chunk_lines:
            level, text = get_heading_info(line)
            if level is not None:
                title = text
                break
        if title is None:
            title = f"Part-{idx + 1}"

        filename = generate_filename(title, idx + 1)
        output_path = os.path.join(output_dir, filename)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(chunk_lines))

        chars = sum(len(l) + 1 for l in chunk_lines)
        print(f"  {idx + 1:02d}. {filename} ({len(chunk_lines)} lines, {chars} chars)")
        print(f"      Title: {title}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Split a markdown file using the minimum principle (character-based threshold).'
    )
    parser.add_argument('input_file', help='Input markdown file path')
    parser.add_argument('output_dir', nargs='?', default=None,
                        help='Output directory (default: <input_dir>/process)')
    parser.add_argument('-t', '--threshold', type=int, default=DEFAULT_THRESHOLD,
                        help=f'Character threshold per chunk (default: {DEFAULT_THRESHOLD})')
    args = parser.parse_args()

    split_file(args.input_file, args.output_dir, args.threshold)
    print("\nDone!")
