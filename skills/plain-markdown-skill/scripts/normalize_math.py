"""Reusable in-place math/prose normaliser for plain-markdown-skill.

Orthogonal transforms, each individually toggleable:

1. collapse_math_whitespace: remove visually noisy, semantically inert spaces
   inside LaTeX expressions (`\\mathrm {d}` -> `\\mathrm{d}`; `^ {` -> `^{`;
   `_ {` -> `_{`; `x ^ {...}` / `) ^ {...}` -> `x^{...}` / `)^{...}`; adjacent
   `\\cmd \\cmd` pairs collapsed).

2. unify_integration_symbol: normalise the Lagrange-style integration symbol
   `S` / `SS` across several competing spellings to `\\mathbf{S}` /
   `\\mathbf{SS}`. Operates only on already-wrapped math (inside `$...$` or
   `$$...$$` is not required; the script does literal substitution of the
   LaTeX forms `\\mathrm{S}`, `\\mathbb{S}`, `\\mathbf{S S}`, etc.).

3. strip_bold_terms: remove `**...**` wrapping around a caller-supplied list
   of English terms (e.g. ["General Equation of Equilibrium"]).

4. unicode_to_latex: replace Unicode math glyphs (Greek letters, operators,
   super/subscript digits, arrows, ellipsis, ...) with their LaTeX commands.
   Intended to run only on math-mode content; pair with
   ``replace_in_math_regions`` to avoid clobbering prose.

5. split_block_math: expand single-line ``$$body$$`` into the three-line form
   ``$$\\nbody\\n$$`` to match the project-wide block-math convention.

6. promote_standalone_inline: convert paragraph-level ``$body$`` (a line
   containing nothing but a single inline-math expression) to the three-line
   ``$$\\nbody\\n$$`` block form.

7. normalize_blank_lines: ensure exactly one blank line between paragraphs,
   between paragraphs and headings, and between paragraphs and certain
   sentence-start words that indicate a new paragraph ("Therefore", "Thus",
   "Hence", "But", "Consequently" at the start of a non-heading line).
   Two or more consecutive blank lines are collapsed to one.
   Content inside fenced code blocks is left untouched.

8. simplify_array: flatten single-line ``\begin{array}`` environments to
   ``\quad``-separated elements (``A, & B`` → ``A, \quad B``).
   Multi-line arrays (containing newlines) are preserved unchanged.

Usage as a module:

    from normalize_math import normalize
    text = normalize(source, bold_terms=["Foo", "Bar"], convert_unicode=True)

Usage from the CLI:

    python normalize_math.py path/to/file.md \
        [--no-whitespace] [--no-s-unify] [--no-split-blocks] \
        [--no-standalone-inline] [--unicode-math] [--terms path/to/terms.txt] \
        [--no-blank-lines]

The terms file is one term per line (blank lines and `#` comments ignored).
The target path is written in place; no backup is created by this script
(plain-markdown-skill handles backups upstream).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# YAML frontmatter guard: match the opening/closing `---` at the top of a
# file. Everything between (inclusive) is extracted and left untouched by
# all transforms; only the body after the closing `---` is processed.
_FRONTMATTER = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)


def _split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter, body).  If no frontmatter, frontmatter is ''."""
    m = _FRONTMATTER.match(text)
    if m:
        return m.group(0), text[m.end():]
    return "", text


def _join_frontmatter(frontmatter: str, body: str) -> str:
    return frontmatter + body


_WS_CMD_BRACE = re.compile(r"(\\[a-zA-Z]+) \{")
_WS_CARET_BRACE = re.compile(r"\^ \{")
_WS_UNDER_BRACE = re.compile(r"_ \{")
_WS_BEFORE_CARET = re.compile(r"([a-zA-Z0-9\)\]\}]) \^")
_WS_BEFORE_UNDER = re.compile(r"([a-zA-Z0-9\)\]\}]) _")
_WS_ADJACENT_CMDS = re.compile(r"(\\[a-zA-Z]+) (\\[a-zA-Z]+)")


def collapse_math_whitespace(text: str) -> str:
    """Remove inert spaces inside LaTeX expressions."""
    text = _WS_CMD_BRACE.sub(r"\1{", text)
    text = _WS_BEFORE_CARET.sub(r"\1^", text)
    text = _WS_BEFORE_UNDER.sub(r"\1_", text)
    text = _WS_CARET_BRACE.sub(r"^{", text)
    text = _WS_UNDER_BRACE.sub(r"_{", text)
    prev: str | None = None
    while prev != text:
        prev = text
        text = _WS_ADJACENT_CMDS.sub(r"\1\2", text)
    return text


# Regex to match \begin{array}{...} ... \end{array} blocks
_ARRAY_PATTERN = re.compile(
    r'\\begin\{array\}\{[^}]*\}\s*(.*?)\s*\\end\{array\}',
    re.DOTALL
)


def simplify_array(text: str) -> str:
    """Flatten single-line array environments to qquad-separated elements.

    ``\\begin{array}{c c c} A, & B, & C \\end{array}`` → ``A, \\quad B, \\quad C``

    Multi-line arrays (containing newlines) are preserved unchanged.
    """
    def _replace(m: "re.Match[str]") -> str:
        content = m.group(1)
        # Only simplify single-line arrays (no internal newlines)
        if '\n' in content:
            return m.group(0)
        # Strip leading/trailing whitespace
        content = content.strip()
        # Replace column separators & with \quad spacing
        result = content.replace('&', r'\quad')
        return result
    return _ARRAY_PATTERN.sub(_replace, text)


# Order matters: double-S forms must be rewritten before the single-S form so
# that `\mathrm{SS}` does not first get chopped to `\mathbf{S}S}`.
_S_DOUBLE_REPLACEMENTS: list[tuple[str, str]] = [
    ("\\mathbf{S S}", "\\mathbf{SS}"),
    ("\\mathrm{SS}", "\\mathbf{SS}"),
    ("\\mathbb{SS}", "\\mathbf{SS}"),
]
_S_SINGLE_REPLACEMENTS: list[tuple[str, str]] = [
    ("\\mathbb{S}", "\\mathbf{S}"),
    ("\\mathrm{S}", "\\mathbf{S}"),
]


def unify_integration_symbol(text: str) -> str:
    """Collapse competing spellings of the Lagrange-style integration S."""
    for old, new in _S_DOUBLE_REPLACEMENTS:
        text = text.replace(old, new)
    for old, new in _S_SINGLE_REPLACEMENTS:
        text = text.replace(old, new)
    return text


def strip_bold_terms(text: str, terms: list[str]) -> str:
    """Remove `**...**` around each supplied term (exact literal match)."""
    for term in terms:
        text = text.replace(f"**{term}**", term)
    return text


# Unicode math glyph -> LaTeX command. Intentionally conservative: only
# glyphs whose LaTeX spelling is unambiguous and whose Unicode form is
# never legitimate plain-text inside math mode. Context-dependent cases
# (e.g. `...` as an operator vs. prose ellipsis) stay out.
UNICODE_MATH_MAP: dict[str, str] = {
    "·": "\\cdot", "×": "\\times", "÷": "\\div", "±": "\\pm",
    "≠": "\\neq", "≤": "\\leq", "≥": "\\geq", "≈": "\\approx", "≡": "\\equiv",
    "∂": "\\partial", "∇": "\\nabla", "∞": "\\infty",
    "∫": "\\int", "∑": "\\sum", "∏": "\\prod",
    "∈": "\\in", "∉": "\\notin", "∪": "\\cup", "∩": "\\cap",
    "⊂": "\\subset", "⊃": "\\supset",
    "→": "\\to", "←": "\\leftarrow",
    "↔": "\\leftrightarrow",
    "⇒": "\\Rightarrow", "⇐": "\\Leftarrow", "⇔": "\\Leftrightarrow",
    "…": "\\dots",
    "α": "\\alpha", "β": "\\beta", "γ": "\\gamma", "δ": "\\delta",
    "ε": "\\epsilon", "ζ": "\\zeta", "η": "\\eta", "θ": "\\theta",
    "ι": "\\iota", "κ": "\\kappa", "λ": "\\lambda", "μ": "\\mu",
    "ν": "\\nu", "ξ": "\\xi", "π": "\\pi", "ρ": "\\rho",
    "σ": "\\sigma", "τ": "\\tau", "υ": "\\upsilon", "φ": "\\varphi",
    "χ": "\\chi", "ψ": "\\psi", "ω": "\\omega",
    "Γ": "\\Gamma", "Δ": "\\Delta", "Θ": "\\Theta", "Λ": "\\Lambda",
    "Ξ": "\\Xi", "Π": "\\Pi", "Σ": "\\Sigma", "Υ": "\\Upsilon",
    "Φ": "\\Phi", "Ψ": "\\Psi", "Ω": "\\Omega",
    "⁰": "^{0}", "¹": "^{1}", "²": "^{2}", "³": "^{3}", "⁴": "^{4}",
    "⁵": "^{5}", "⁶": "^{6}", "⁷": "^{7}", "⁸": "^{8}", "⁹": "^{9}",
    "₀": "_{0}", "₁": "_{1}", "₂": "_{2}", "₃": "_{3}", "₄": "_{4}",
    "₅": "_{5}", "₆": "_{6}", "₇": "_{7}", "₈": "_{8}", "₉": "_{9}",
}


def unicode_to_latex(text: str, mapping: dict[str, str] | None = None) -> str:
    """Replace Unicode math glyphs with their LaTeX commands.

    Caller is responsible for calling this only on content known to be
    inside math mode (use :func:`replace_in_math_regions`); otherwise
    prose characters such as `·` (middle-dot in Chinese typography) or
    `→` (used as a prose arrow) would be clobbered.

    A single space is inserted after any ``\\cmd``-style replacement when
    the next character would end up as an unmapped letter in the output,
    so that ``·b`` -> ``\\cdot b`` rather than ``\\cdotb`` (which TeX would
    scan as an unknown control word). Adjacent mapped glyphs (whose
    replacements begin with ``\\``, ``^`` or ``_``) don't trigger padding,
    since TeX can already tokenise at that boundary.
    """
    m = UNICODE_MATH_MAP if mapping is None else mapping
    out: list[str] = []
    for i, ch in enumerate(text):
        repl = m.get(ch)
        if repl is None:
            out.append(ch)
            continue
        nxt = text[i + 1] if i + 1 < len(text) else ""
        next_is_unmapped_letter = bool(nxt) and nxt not in m and nxt.isalpha()
        if repl.startswith("\\") and next_is_unmapped_letter:
            out.append(repl + " ")
        else:
            out.append(repl)
    return "".join(out)


# Matches block math ($$...$$, non-greedy, newlines allowed) OR inline math
# ($...$, non-greedy, no newline, non-empty body). Block form is tried first
# thanks to alternation ordering.
_MATH_REGION = re.compile(r"(\$\$.*?\$\$|\$[^$\n]+?\$)", re.DOTALL)

# Matches a single line that is exactly `$$body$$` (body may not contain a
# newline, since `.` without DOTALL stops at line end). Trailing horizontal
# whitespace before the closing `$$` is tolerated.
_INLINE_BLOCK_MATH = re.compile(r"^\$\$(.+?)\$\$[ \t]*$", re.MULTILINE)


def split_block_math(text: str) -> str:
    """Expand single-line ``$$body$$`` to the three-line form.

    Only lines whose entire content is ``$$...$$`` are rewritten; mid-paragraph
    inline `$$...$$` (rare but possible) and already-split blocks are left
    untouched. The body is trimmed so the result does not carry incidental
    leading/trailing whitespace.
    """
    return _INLINE_BLOCK_MATH.sub(lambda m: f"$$\n{m.group(1).strip()}\n$$", text)


# Matches a line that contains only a single $...$ expression (whitespace OK).
_STANDALONE_INLINE = re.compile(r"^[ \t]*\$[^$\n]+\$[ \t]*$", re.MULTILINE)


def promote_standalone_inline(text: str) -> str:
    """Convert paragraph-level ``$body$`` to ``$$\\nbody\\n$$`` block form.

    A "paragraph-level" inline formula is one that occupies an entire line
    by itself (blank lines before/after are not required).  Each such
    ``$...$`` is replaced with the three-line ``$$...$$`` variant so that
    processors which treat ``$$...$$`` as display math render it correctly.
    """
    def _replace(m: "re.Match[str]") -> str:
        body = m.group(0)
        # strip the leading/trailing whitespace + delimiters
        inner = body.strip()[1:-1]  # remove leading `$` and trailing `$`
        return f"$$\n{inner}\n$$"
    return _STANDALONE_INLINE.sub(_replace, text)


def replace_in_math_regions(text: str, fn) -> str:
    """Apply ``fn`` only to the inside of each ``$...$`` / ``$$...$$`` region.

    The delimiters are preserved; prose between math regions is left
    untouched. ``fn`` receives the inner body (without delimiters) and
    returns the rewritten body.
    """
    def _apply(match: "re.Match[str]") -> str:
        body = match.group(0)
        if body.startswith("$$") and body.endswith("$$"):
            return "$$" + fn(body[2:-2]) + "$$"
        return "$" + fn(body[1:-1]) + "$"
    return _MATH_REGION.sub(_apply, text)


# Sentence-starter words that typically indicate a new paragraph when they
# appear at the start of a non-heading, non-blank line (after a period).
_NEW_PARAGRAPH_STARTERS = frozenset([
    "therefore", "thus", "hence", "consequently",
    "however", "moreover", "furthermore", "also",
    "but",
])


def normalize_blank_lines(text: str) -> str:
    """Normalise blank lines between paragraphs and around headings.

    Rules:
    - Two or more consecutive blank lines → exactly one blank line.
    - Any two non-blank, non-heading, non-numbered-item lines that are
      adjacent (no blank line between them) are separated by a blank line.
    - A blank line is always inserted before an ATX heading (lines starting
      with ``#{1,6} ``).
    - Code blocks (fenced with ````` ```` ``` ```` ``` ````) are left untouched.
    """
    lines = text.splitlines()
    result: list[str] = []
    i = 0
    in_code_block = False

    while i < len(lines):
        line = lines[i]

        # Track fenced code block state
        if line.strip().startswith("```"):
            result.append(line)
            i += 1
            if not in_code_block or (in_code_block and line.strip() == "```"):
                in_code_block = not in_code_block
            continue

        # Inside fenced code block: pass through unchanged
        if in_code_block:
            result.append(line)
            i += 1
            continue

        # --- Math-block protection ---
        # Lines inside a $...$ display-math block must not trigger
        # blank-line insertion between their internal lines.
        # We detect "inside a math block" by tracking state:
        # a line that is exactly ``$$`` opens/closes a math block.
        # While in_math_block, pass all lines through without blank-line logic.
        # After it closes, we resume normal processing.
        # (Nested/adjacent math blocks are uncommon enough to ignore.)
        if not hasattr(normalize_blank_lines, "_math_block_state"):
            normalize_blank_lines._math_block_state = False  # type: ignore[attr-defined]

        stripped = line.strip()

        # Detect display-math open/close ($$ on its own line)
        if stripped == "$$":
            normalize_blank_lines._math_block_state = not normalize_blank_lines._math_block_state  # type: ignore[attr-defined]
            result.append(line)
            i += 1
            continue

        if normalize_blank_lines._math_block_state:  # type: ignore[attr-defined]
            # Inside math block: pass through, no blank-line processing
            result.append(line)
            i += 1
            continue

        # --- Prose / heading / list processing ---
        # Rule 1: Collapse 2+ consecutive blank lines to one.
        if stripped == "":
            # Skip excess blank lines
            while i + 1 < len(lines) and lines[i + 1].strip() == "":
                i += 1
            result.append("")
            i += 1
            continue

        # Detect ATX heading (## Heading)
        is_heading = bool(re.match(r"^#{1,6}\s", line))

        # Detect numbered list item (1. 2. etc. at column 0)
        is_numbered_item = bool(re.match(r"^\d+\.\s", stripped))

        # Determine if this line starts a new paragraph:
        # headings always start a new paragraph; numbered items do not
        # (they are sub-structure within a section);
        # ordinary prose lines start a new paragraph whenever the previous
        # non-blank line was also ordinary prose (i.e., not a heading).
        starts_new_para = is_heading
        if not is_numbered_item and not is_heading and result:
            # Find last non-blank entry
            for prev in reversed(result):
                if prev == "":
                    continue
                starts_new_para = True  # previous line was ordinary prose
                break

        # Insert a blank line before the line if result doesn't already end
        # with a blank line.
        if starts_new_para and result and result[-1] != "":
            result.append("")

        result.append(line)
        i += 1

    # Post-process: strip trailing blank lines only (preserve trailing content lines)
    while result and result[-1] == "":
        result.pop()

    out = "\n".join(result)
    # Restore trailing newline if the original input had one (splitlines() does not
    # represent a trailing bare newline as an extra empty-string element)
    if text.endswith("\n") and not out.endswith("\n"):
        out += "\n"
    return out


def normalize(
    text: str,
    *,
    bold_terms: list[str] | None = None,
    collapse_ws: bool = True,
    unify_s: bool = True,
    convert_unicode: bool = False,
    split_blocks: bool = True,
    standalone_inline_to_block: bool = True,
    blank_lines: bool = True,
    simplify_arrays: bool = True,
) -> str:
    """Apply the enabled transforms in a stable order.

    YAML frontmatter (``---`` at top of file) is extracted and left
    completely untouched; only the body after the closing ``---`` is
    processed.
    """
    fm, body = _split_frontmatter(text)
    if bold_terms:
        body = strip_bold_terms(body, bold_terms)
    if convert_unicode:
        body = replace_in_math_regions(body, unicode_to_latex)
    if collapse_ws:
        body = collapse_math_whitespace(body)
    if unify_s:
        body = unify_integration_symbol(body)
    if simplify_arrays:
        body = simplify_array(body)
    if standalone_inline_to_block:
        body = promote_standalone_inline(body)
    if split_blocks:
        body = split_block_math(body)
    if blank_lines:
        body = normalize_blank_lines(body)
    return _join_frontmatter(fm, body)


def _load_terms(path: Path) -> list[str]:
    terms: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        terms.append(line)
    return terms


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", type=Path, help="markdown file to rewrite in place")
    parser.add_argument("--no-whitespace", action="store_true",
                        help="skip math-whitespace collapse")
    parser.add_argument("--no-s-unify", action="store_true",
                        help="skip integration-symbol unification")
    parser.add_argument("--no-split-blocks", action="store_true",
                        help="skip splitting single-line $$...$$ into three-line form")
    parser.add_argument("--no-standalone-inline", action="store_true",
                        help="skip converting standalone $...$ lines to block form")
    parser.add_argument("--unicode-math", action="store_true",
                        help="convert Unicode math glyphs inside $...$/$$...$$ to LaTeX")
    parser.add_argument("--no-blank-lines", action="store_true",
                        help="skip blank-line normalisation")
    parser.add_argument("--no-simplify-arrays", action="store_true",
                        help="skip array-environment simplification")
    parser.add_argument("--terms", type=Path, default=None,
                        help="path to a file of bold terms to strip (one per line)")
    args = parser.parse_args(argv)

    terms = _load_terms(args.terms) if args.terms else None
    original = args.path.read_text(encoding="utf-8")
    result = normalize(
        original,
        bold_terms=terms,
        collapse_ws=not args.no_whitespace,
        unify_s=not args.no_s_unify,
        convert_unicode=args.unicode_math,
        split_blocks=not args.no_split_blocks,
        standalone_inline_to_block=not args.no_standalone_inline,
        blank_lines=not args.no_blank_lines,
        simplify_arrays=not args.no_simplify_arrays,
    )
    with open(args.path, "w", encoding="utf-8", newline="\n") as f:
        f.write(result)
    print(f"wrote {args.path}  ({len(original)} -> {len(result)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
