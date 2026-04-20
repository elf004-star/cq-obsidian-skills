# User Habits

> This file records user preferences for plain-markdown-skill.
> The skill references rules in this file during document processing to ensure conversion results match the user's consistent style.
> Update this file anytime preferences change.

---

## Subscript/Superscript Handling

**Current preference**: `[superscript]` / `[subscript]` form, do not use `^` or Unicode superscript characters.

```
Examples: x^2 → $x^2$    深度学习<sub>2</sub> → 深度学习[2]    H₂O → $H_2 O$    参考文献$^2$ → 参考文献[2]   参考文献$_2$ → 参考文献[2]
```

**Always apply**: Yes (default, no need to ask each time)

---

## Bold / Italic Handling

**Current preference**: Convert to plain text, do not preserve any style markers.

**Always apply**: Yes (default, no need to ask each time)

---

## Footnote References (Python script batch processing allowed)

**Current preference**: Only keep superscript numbers of formulas/symbols in body text (e.g., the `2` in `x²`), do not keep footnote reference markers `[^1]`, etc.

**Example**: Mark `<sup>52</sup>` should be preserved as `[52]` form.

**Superscript references in Math mode**: Superscript or subscript references like `$^{number}$` and `$_{number}$` that appear outside LaTeX math formulas (footnote markers) should be converted to `[number]` form.

**Example**:
- Original: `the water $^{56}$` → Normalized: `the water [56]`

---

## Special Symbols & OCR Artifacts

**Known symbols that need replacement**:

| Original | Replace with | Note |
|----------|-------------|------|
| `™` | (delete or replace with plain quote) | OCR artifact |
| `©` | `©` or `(C)` | Copyright symbol |
| `®` | `®` or `(R)` | Registered trademark |
| `­­` | (delete) | Caret/artifact |
| `…` | `...` | Ellipsis unified to three dots |

**Other OCR artifacts**: Ask user for confirmation when discovered.

---

## Paragraph Merge Rules

When two adjacent paragraphs satisfy ALL of the following conditions, automatically merge into one paragraph:

1. End of first paragraph is **NOT** period `.`, question mark `?`, exclamation mark `!`, semicolon `;`, colon `:`
2. First letter of second paragraph **is lowercase** or **starts with number**
3. There is **only one** blank line between the two paragraphs

**Example**:

```
Original:
it only remains to add to the actual accelerating forces

the new accelerating forces

Normalized:
it only remains to add to the actual accelerating forces the new accelerating forces
```

---

## Attachment Reference Format

**Current preference**: Keep `![[...]]` syntax as-is.

---

## Wiki Link Format

**Current preference**: Keep `[[...]]` syntax as-is.

---

## Math Formulas

All math formulas and pure math symbols must be wrapped with `$...$` or `$$...$$`.

### Wrapping Rules
- Inline formula: `$...$`
- Display formula (blank line above and below): `$$\n...\n$$`
  - Automated: `scripts/normalize_math.py`'s `split_block_math()` (enabled by default, `--no-split-blocks` disables).

### Standardization Rules

| Original | Standard form |
|----------|---------------|
| `sqrt[...]` | `\sqrt[...]` |
| `·` | `\cdot` |
| `×` | `\times` |
| `÷` | `\div` |
| `≠` | `\neq` |
| `≤` | `\leq` |
| `≥` | `\geq` |
| `α` `β` `γ` | `\alpha` `\beta` `\gamma` |
| `π` | `\pi` |
| `∞` | `\infty` |
| `∂` | `\partial` |
| `∇` | `\nabla` |
| `...` / `…` | `\dots` |
| `\etc` (in math formulas) | `\dots` |
| `\const` | `\text{const.}` |
| `\text{c o n s t a n t}` | `\text{constant}` |

### Integral / Summation Symbol S Unification

- In Lagrangian-style text, `S` / `SS` represents total integral (equivalent to `∫`).
- All occurrences in math context (including bare write, `\mathrm{S}`, `\mathbb{S}`, `\mathbf{S S}`, etc.) unify to:
  - Single: `\mathbf{S}`
  - Double: `\mathbf{SS}`
- Bare `S` / `SS` in body text that immediately follows math expressions (`S(...)`, `S dm`, `SS Π dm`, etc.) should be wrapped as inline formula, with S written as `\mathbf{S}`.

### Redundant Spaces Inside Formulas

Spaces that are semantically meaningless and visually cluttered in Pandoc/KaTeX should be compressed, for example:

| Original | Standard form |
|----------|---------------|
| `\mathrm {d}` | `\mathrm{d}` |
| `\frac {a}{b}` | `\frac{a}{b}` |
| `\Omega^ {\prime \prime}` | `\Omega^{\prime\prime}` |
| `z _ {I}` | `z_{I}` |
| `\lambda \cdot` | `\lambda\cdot` |

For batch cases, recommend using `plain-markdown-skill/scripts/normalize_math.py` or one-time regex, no need to ask for each instance.

### `array` Environment Simplification

Multi-column single-line `\begin{array}{c c c} A, & B, & C \end{array}` → flatten to `A, \quad B, \quad C` (remove `begin/end{array}`, alignment parameters, column separators `&`). Single-column multi-line `{l}` arrays (e.g., multi-line integral derivations) keep as-is.

| Original | Standard form |
|----------|---------------|
| `\begin{array}{c c c} A, & B, & C \end{array}` | `A, \quad B, \quad C` |

### Unregistered Non-Pandoc Commands / Unregistered OCR Artifacts

For cases not listed above, prioritize nearest equivalent replacement automatically per `references/pandoc-latex-support.md`, no need to disturb user each time; only when uncertain (e.g., unidentifiable rare characters) raise as "new pattern" for user confirmation, and invite writing rule back to this file.

---

## Heading Levels

- Top-level sections (`SECTION`, `Chapter`) use `#`.
- Secondary blocks (`Subsection`, `Part`) all use `##`, even if original text has `# Subsection III` it should be demoted to `## Subsection III`.
- Item-level (`Article N`) use `##`.
- Numbered lists inside items (`1.` / `2.` etc.) keep as list items, do not separately promote to headings; if upstream extraction mistakenly treats list items as `## Article 1` / `## Article 2`, remove the extra heading.

---

## Backup Strategy

- Always backup original file before processing
- Backup file naming: `*original filename*.bak.orig`
- Backup files saved in same directory

---

## Other Preferences

(Please supplement according to actual situation)
