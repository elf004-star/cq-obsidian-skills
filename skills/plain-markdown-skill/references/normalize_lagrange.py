"""Case study: one-shot normalizer for the Lagrange markdown test file.

This script is **not** a reusable tool. It is kept as a frozen example of how
档 3 "new pattern" fixes and plain-markdown-skill 档 1/档 2 transforms were
combined for a specific document (`01-SECTION-IV-A-MORE-GENERAL-AND-SIMPLER-
WAY-TO-USE-THE-FORMULA.md`). Do not invoke it on other documents.

The reusable transforms (math whitespace collapse / integration-symbol
unification / bold English term stripping) live in
`plain-markdown-skill/scripts/normalize_math.py`; this file shows how they
were combined with document-specific bold-math expansions and structural
fixes (paragraph merge, mis-labelled headings, heading demotion, footnote
bracketing, trailing-footer dedupe).

Applied transforms:
- footnote .76 -> .[76]; stray colon line; dedupe trailing footer
- merge broken paragraph around line 169 with missing 'It seems more'
- remove mis-labelled `## Article 1` / `## Article 2` headings
- demote `# Subsection III` to `## Subsection III`
- unwrap bold-math lines into $...$ / $$...$$ with LaTeX standardisation
- strip `**` from English emphasis terms
- collapse redundant whitespace in math (\\cmd {, ^ {, _ {, adjacent \\cmd \\cmd)
- unify integration symbol to \\mathbf{S} / \\mathbf{SS}
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


BOLD_MATH_REPLACEMENTS: list[tuple[str, str]] = [
    ("**P·dp + Q·dq + R·dr + ... + λ·dL + μ·dM + ν·dN + ... = 0**",
     "$$P \\cdot dp + Q \\cdot dq + R \\cdot dr + \\dots + \\lambda \\cdot dL + \\mu \\cdot dM + \\nu \\cdot dN + \\dots = 0$$"),
    ("**P·(∂p/∂x) + Q·(∂q/∂x) + R·(∂r/∂x) + ... + λ·(∂L/∂x) + μ·(∂M/∂x) + ν·(∂N/∂x) + ... = 0**",
     "$$P \\cdot (\\partial p/\\partial x) + Q \\cdot (\\partial q/\\partial x) + R \\cdot (\\partial r/\\partial x) + \\dots + \\lambda \\cdot (\\partial L/\\partial x) + \\mu \\cdot (\\partial M/\\partial x) + \\nu \\cdot (\\partial N/\\partial x) + \\dots = 0$$"),
    ("**λ·dL' = λ·[(∂L/∂x')·dx' + (∂L/∂y')·dy' + (∂L/∂z')·dz']**",
     "$$\\lambda \\cdot dL' = \\lambda \\cdot [(\\partial L/\\partial x') \\cdot dx' + (\\partial L/\\partial y') \\cdot dy' + (\\partial L/\\partial z') \\cdot dz']$$"),
    ("**√[(∂L/∂x')² + (∂L/∂y')² + (∂L/∂z')²]**",
     "$$\\sqrt{(\\partial L/\\partial x')^{2} + (\\partial L/\\partial y')^{2} + (\\partial L/\\partial z')^{2}}$$"),
    ('**√[(∂L/∂x")² + (∂L/∂y")² + (∂L/∂z")²]**',
     '$$\\sqrt{(\\partial L/\\partial x")^{2} + (\\partial L/\\partial y")^{2} + (\\partial L/\\partial z")^{2}}$$'),
    ('**λ·√[(∂L/∂x\')² + (∂L/∂y\')² + (∂L/∂z\')²] + λ·√[(∂L/∂x")² + (∂L/∂y")² + (∂L/∂z")²] + ...**',
     '$$\\lambda \\cdot \\sqrt{(\\partial L/\\partial x\')^{2} + (\\partial L/\\partial y\')^{2} + (\\partial L/\\partial z\')^{2}} + \\lambda \\cdot \\sqrt{(\\partial L/\\partial x")^{2} + (\\partial L/\\partial y")^{2} + (\\partial L/\\partial z")^{2}} + \\dots$$'),
    ("**(P·δp + Q·δq + R·δr + etc.)·dm**",
     "$(P \\cdot \\delta p + Q \\cdot \\delta q + R \\cdot \\delta r + \\dots) \\cdot dm$"),
    ("by the symbol **S**",
     "by the symbol $\\mathbf{S}$"),
    ("**S(P·δp + Q·δq + R·δr + etc.)·dm**",
     "$\\mathbf{S}(P \\cdot \\delta p + Q \\cdot \\delta q + R \\cdot \\delta r + \\dots) \\cdot dm$"),
    ("**S(λ·δL + μ·δM + etc.)**",
     "$\\mathbf{S}(\\lambda \\cdot \\delta L + \\mu \\cdot \\delta M + \\dots)$"),
    ("**S(P·δp + Q·δq + R·δr + ...)·dm + S(λ·δL + μ·δM + ...) + P'·δp' + Q'·δq' + R'·δr' + ... + P\"·δp\" + Q\"·δq\" + R\"·δr\" + ... + α·δA + β·δB + γ·δC + ... = 0**",
     "$$\\mathbf{S}(P \\cdot \\delta p + Q \\cdot \\delta q + R \\cdot \\delta r + \\dots) \\cdot dm + \\mathbf{S}(\\lambda \\cdot \\delta L + \\mu \\cdot \\delta M + \\dots) + P' \\cdot \\delta p' + Q' \\cdot \\delta q' + R' \\cdot \\delta r' + \\dots + P\" \\cdot \\delta p\" + Q\" \\cdot \\delta q\" + R\" \\cdot \\delta r\" + \\dots + \\alpha \\cdot \\delta A + \\beta \\cdot \\delta B + \\gamma \\cdot \\delta C + \\dots = 0$$"),
]

BOLD_ENGLISH_TERMS = [
    "General Equation of Equilibrium",
    "Particular Equations of Equilibrium",
    "variations",
    "differentials",
    "Undetermined Equations of Condition",
    "Determined Equations of Condition",
]

PROSE_SS_REPLACEMENTS = [
    ("integrable formula SS $\\Pi$ dm", "integrable formula $\\mathbf{SS}\\,\\Pi\\,dm$"),
    ("value of SS dm", "value of $\\mathbf{SS}\\,dm$"),
    ("integrable formula SS $", "integrable formula $\\mathbf{SS}$ $"),
    ("the integral SS $", "the integral $\\mathbf{SS}$ $"),
    ("double integral sign SS,", "double integral sign $\\mathbf{SS}$,"),
    ("double integral sign SS ", "double integral sign $\\mathbf{SS}$ "),
]


def normalize(s: str) -> str:
    s = s.replace(
        "similarly for the others.76 Therefore",
        "similarly for the others.[76] Therefore",
    )
    s = re.sub(r"(\$\$)\n\n：\n\n", r"\1\n\n", s)
    s = re.sub(
        r"(\*本章节来自 \[\[拉格朗日分析力学\]\]\*)\n+---\n+\*本章节来自 \[\[拉格朗日分析力学\]\]\*\s*$",
        r"\1\n",
        s,
    )
    s = s.replace(
        "changing the values of the differences.\n\n\n\njudicious to place",
        "changing the values of the differences. It seems more judicious to place",
    )
    s = re.sub(r"\n## Article 1\n\n1\. The functions", r"\n1. The functions", s)
    s = re.sub(r"\n## Article 2\n\n2\. Every term", r"\n2. Every term", s)
    s = s.replace("\n# Subsection III\n", "\n## Subsection III\n")

    for old, new in BOLD_MATH_REPLACEMENTS:
        s = s.replace(old, new)
    for t in BOLD_ENGLISH_TERMS:
        s = s.replace(f"**{t}**", t)

    s = re.sub(r"(\\[a-zA-Z]+) \{", r"\1{", s)
    s = re.sub(r"\^ \{", r"^{", s)
    s = re.sub(r"_ \{", r"_{", s)
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"(\\[a-zA-Z]+) (\\[a-zA-Z]+)", r"\1\2", s)

    s = s.replace("\\mathbb{S}", "\\mathbf{S}")
    s = s.replace("\\mathbf{S S}", "\\mathbf{SS}")
    s = s.replace("\\mathrm{SS}", "\\mathbf{SS}")
    for old, new in PROSE_SS_REPLACEMENTS:
        s = s.replace(old, new)

    return s


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: normalize_lagrange.py <path>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    original = path.read_text(encoding="utf-8")
    result = normalize(original)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(result)
    print(f"wrote {path}  ({len(original)} -> {len(result)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
