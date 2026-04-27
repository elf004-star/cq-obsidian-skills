#!/usr/bin/env python3
"""Plain Markdown Skill - Document Processing Script v3

Applies Tier 1 and Tier 2 text/format transformations. Handles:
  - Pandoc sub/superscript → LaTeX math (4 pattern passes)
  - Bold/italic removal (math-mode aware, split on $...$ blocks)
  - Heading normalization (escaped-dot + multi-level plain-dot)
  - LaTeX list number conversion, image attribute removal, special chars

Does NOT handle (by design):
  - Formula block splitting → normalize_math.py's exclusive job
  - Table conversion → Agent manual only (semantic judgment required)
  - Unicode math → LaTeX → normalize_math.py's job

See SKILL.md ## Script Responsibilities for the full boundary contract.
"""

import re
import sys


def remove_pandoc_subscript_superscript(text):
    """Convert Pandoc-style sub/superscript to LaTeX math wrapping.
    Handles patterns:
      *VAR*~sub~  → $VAR_{sub}$
      *VAR~sub~*  → $VAR_{sub}$   (italic wraps entire subscript expression)
      VAR~sub~    → $VAR_{sub}$   (bare subscript, uppercase vars)
      *VAR*^sup^  → $VAR^{sup}$
      VAR^sup^    → $VAR^{sup}$
      a~max~      → $a_{\max}$    (single lowercase + subscript)
    """
    # --- Pass 1: Italic wrapping subscript: *VAR~sub~* or **VAR~sub~** ---
    # Pattern: *{1,2} at start, then VAR, then ~sub~, then *{1,2} at end
    text = re.sub(
        r'(?<!\$)\*{1,2}([A-Za-z][A-Za-z0-9]*)~([^~]+)~\*{1,2}',
        r'$\1_{\2}$',
        text
    )

    # --- Pass 2: Italic only on variable name, separate subscript: *VAR*~sub~ ---
    text = re.sub(
        r'(?<!\$)\*{1,2}([A-Za-z][A-Za-z0-9]*)\*{1,2}~([^~]+)~',
        r'$\1_{\2}$',
        text
    )

    # --- Pass 3: Italic only on variable name, separate superscript: *VAR*^sup^ ---
    text = re.sub(
        r'(?<!\$)\*{1,2}([A-Za-z][A-Za-z0-9]*)\*{1,2}\^([^^]+)\^',
        r'$\1^{\2}$',
        text
    )

    # --- Pass 4: Bare uppercase variable with subscript: VAR~sub~ → $VAR_{sub}$ ---
    text = re.sub(
        r'(?<!\$)(?<![A-Za-z])([A-Z][A-Za-z]*)~([A-Za-z0-9\-\,]+)~',
        r'$\1_{\2}$',
        text
    )

    # --- Pass 5: Bare single lowercase with subscript: a~max~, h~f~, t~e~ ---
    text = re.sub(
        r'(?<!\$)(?<![A-Za-z])([a-z])~([A-Za-z0-9]+)~',
        r'$\1_{\2}$',
        text
    )

    # --- Pass 6: Bare variable with superscript: R^2^, r^2^ ---
    text = re.sub(
        r'(?<!\$)(?<![A-Za-z])([A-Za-z])\^(\-?\d+)\^',
        r'$\1^{\2}$',
        text
    )

    # --- Pass 7: Complex superscript units: r·min^-1^, CNY·m^-1^ ---
    text = re.sub(
        r'([A-Za-z·]+)\^(\-?\d+)\^',
        r'$\1^{\2}$',
        text
    )

    return text


def convert_headings(line):
    """Convert numbered headings to ATX format.
    Handles both '1\.' (escaped dot) and '2.1' (plain dot, multi-level) formats.
    Single-level plain-dot '1. ' is NOT treated as heading (could be list item).
    """
    # --- Pattern 1: Escaped dot format ---
    # Matches: 1\. Title, 2\. Title, or 2\.1\. Title
    m_esc = re.match(r'^(\d+)\\\.(\d+)?(?:\\\.(\d+))?\s+(.+)', line)
    if m_esc:
        n1, n2, n3, title = m_esc.groups()
        if n3:
            level = 3
        elif n2:
            level = 2
        else:
            level = 1
        return '#' * level + ' ' + title

    # --- Pattern 2: Multi-level plain dot format ---
    # Only matches when there are 2+ number segments (e.g., "2.1 Title", "4.1.1 Title")
    # Single "1. Title" is NOT matched (ambiguous with list items)
    m_plain = re.match(r'^(\d+)\.(\d+)(?:\.(\d+))?\s+(.+)', line)
    if m_plain:
        n1, n2, n3, title = m_plain.groups()
        if n3:
            level = 3
        else:
            level = 2
        return '#' * level + ' ' + title

    return line


def remove_bold_italic_outside_math(text):
    """Remove **bold** and *italic* markers outside math mode.
    Splits on $...$ and $$...$$ blocks, processes only non-math segments.
    """
    parts = re.split(r'(\$\$[^$]+\$\$|\$[^$]+\$)', text)
    result = []
    for part in parts:
        if part.startswith('$'):
            result.append(part)
        else:
            # Remove bold: **text** → text
            part = re.sub(r'\*\*(.+?)\*\*', r'\1', part)
            # Remove italic: *text* → text (careful with solitary *)
            part = re.sub(r'(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)', r'\1', part)
            result.append(part)
    return ''.join(result)


def wrap_plain_italic_variables(text):
    """After bold/italic removal, wrap remaining single variables in $...$.
    Handles patterns like *WOB* → $WOB$, *X* → $X$, *Y* → $Y$.
    This runs AFTER remove_bold_italic_outside_math, so italic markers are already
    stripped. We look for common patterns that should be in math mode.

    Actually this is better done BEFORE bold removal, as part of subscript handling.
    This function is kept as a post-process cleanup.
    """
    # Common variable acronyms that often appear in italics in academic text
    # After italic removal they're already plain, but we ensure math wrapping
    # for patterns like X(t), p(x,y), I(x,y) that lost their italic markers
    return text


def convert_latex_list_numbers(text):
    """Convert \\(n\\) used as list numbers to plain n."""
    return re.sub(r'\\\((\d+)\\\)', r'\1.', text)


def remove_image_attributes(text):
    """Remove {width="..." height="..."} from image embeds."""
    text = re.sub(r'\{width="[^"]*"\s*height="[^"]*"\}', '', text)
    # Also handle single attribute variants
    text = re.sub(r'\{width="[^"]*"\}', '', text)
    text = re.sub(r'\{height="[^"]*"\}', '', text)
    return text


def fix_escaped_greater(text):
    """Fix \\> to > in non-math text."""
    parts = re.split(r'(\$\$[^$]+\$\$|\$[^$]+\$)', text)
    result = []
    for part in parts:
        if part.startswith('$'):
            result.append(part)
        else:
            result.append(part.replace('\\>', '>'))
    return ''.join(result)


def clean_special_chars(text):
    """Replace special characters per user-habits."""
    text = text.replace('…', '...')  # …
    return text


def process_document(content):
    """Main processing pipeline."""
    lines = content.split('\n')
    result = []
    in_display_math = False

    for line in lines:
        stripped = line.strip()

        # Track $$ math block state for multiline blocks
        if stripped == '$$':
            in_display_math = not in_display_math
            result.append(line)
            continue

        if in_display_math:
            result.append(line)
            continue

        # Process line (order matters!)
        new_line = line

        # 1. Convert numbered headings FIRST (before \(n\) → n. conversion)
        new_line = convert_headings(new_line)

        # 2. Convert Pandoc sub/superscript to LaTeX math (BEFORE bold/italic removal)
        new_line = remove_pandoc_subscript_superscript(new_line)

        # 3. Remove bold/italic markers outside math
        new_line = remove_bold_italic_outside_math(new_line)

        # 4. Convert LaTeX list numbers: \\(n\\) → n. (AFTER heading conversion)
        new_line = convert_latex_list_numbers(new_line)

        # 5. Remove image size attributes
        new_line = remove_image_attributes(new_line)

        # 6. Fix escaped greater-than
        new_line = fix_escaped_greater(new_line)

        # 7. Clean special characters
        new_line = clean_special_chars(new_line)

        result.append(new_line)

    processed = '\n'.join(result)

    return processed


def main():
    if len(sys.argv) < 2:
        print("Usage: python _process_doc.py <file.md>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    processed = process_document(content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(processed)

    print(f"Processed: {filepath}")


if __name__ == '__main__':
    main()
