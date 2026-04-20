---
name: plain-markdown-skill
description: "Normalize messy markdown documents into clean CommonMark/GFM plain text. This skill works on single documents; stronger model capabilities support longer documents."
---

# Plain Markdown Skill

## Goal

Convert any markdown source into **standard, minimal** CommonMark/GFM: keep only standard elements, fix obvious errors, remove non-standard syntax, no decorations. Academic content (math formulas, symbols) is preserved entirely; only syntax is normalized.

## Single Source of Truth

- **All user preferences are based on `config/user-habits.md`**. This file only describes workflow and categorization. If descriptions conflict, `config/user-habits.md` takes precedence.
- Pandoc LaTeX compatibility reference: `references/pandoc-latex-support.md`.

Why: User preferences change; keeping rules in one place prevents drift and keeps the skill stable.

## Resource Directory

- `scripts/normalize_math.py` — **Must be executed every time** math/style standardization script (as workflow step 4), currently 4 transformation groups, each independently toggleable:
  - **Formula block split/upgrade**: Standalone `$...$` on a single line upgrades to `$$\n...\n$$` three-line block format
  - **Intra-formula space compression**: `\mathrm {d}` → `\mathrm{d}`, `z _ {I}` → `z_{I}`, `\cmd \cmd` → `\cmd\cmd` (enabled by default, `--no-whitespace` disables)
  - **Integral symbol S unification**: `\mathrm{S}` / `\mathbb{S}` / `\mathbf{S S}` all normalize to `\mathbf{S}` / `\mathbf{SS}` (enabled by default, `--no-s-unify` disables)
  - **Bold term stripping**: Remove `**term**` wrapping per `--terms` file list
  - **Unicode math chars → LaTeX commands** (`·→\cdot`, `α→\alpha`, `²→^{2}`, `…→\dots`, etc.; only effective inside `$...$` / `$$...$$`, does not affect body text, `--unicode-math` enables)
  All enabled by default, no need to ask each time.
- `references/pandoc-latex-support.md` — Pandoc LaTeX compatibility command reference.
- `references/normalize_lagrange.py` — Reference script for one-time document processing; not for general tool use.
- `tests/` — pytest regression suite and fixtures for above scripts (`math_section_input.md` / `math_section_expected.md`), run `python -m pytest .claude/skills/plain-markdown-skill/tests -v` before modifying scripts.

---

## Processing Categories

Three tiers, determining "whether to do, whether to ask".

### Tier 1: Auto-delete (No confirmation)

Remove or flatten to plain text on sight:

- HTML tags: `<span>`, `<div>`, `<font>`, `<br>`, etc. all inline/block HTML (HTML tables are an exception, convert to GFM tables)
- Custom containers: `:::warning`, `:::tip`, `:::info`, `:::note`, etc. non-standard blocks
- Emoji codes: `:warning:`, `:smile:`, etc.
- Footnote markers `[^n]` → Convert to `[n]` per `config/user-habits.md`
- Task lists `- [x]` / `- [ ]` → Plain unordered list `- `

### Tier 2: Auto-convert (No confirmation, per config/user-habits.md)

Rewrite in-place per `config/user-habits.md`, no need to disturb user each time:

- Subscript/superscript forms (`<sub>/<sup>`, `^`, Unicode subscripts/superscripts, math-mode footnote references `$^{n}$`, etc.)
- Bold, italic, strikethrough markers
- Paragraph line-break merging
- Math formula wrapping (inline `$...$`, display `$$...$$`) and LaTeX command standardization
- Known special symbol / OCR artifact replacement table
- Link whitespace cleanup: `[ text ]( URL )` → `[text](URL)`

**Non-Pandoc-compatible LaTeX commands** and **unregistered OCR artifacts** also belong to this tier: refer to `references/pandoc-latex-support.md` for nearest equivalent replacement; uncertain individual characters fall to tier 3.

### Tier 3: Need Confirmation (Only one scenario)

Discover **new patterns** not yet registered in `config/user-habits.md` — for example new footnote variants, new artifact characters, new non-standard macros — explain pattern to user and propose rule, **confirm before applying to current document**, and **ask whether to write rule back to `config/user-habits.md`** for future automation.

> Other CommonMark/GFM standard elements (headings, lists, code blocks, tables, horizontal rules, blockquotes, wiki links `[[...]]`, attachment references `![[...]]`, regular links, YAML frontmatter, etc.) are preserved as-is, except for the following typography fallback.

---

## Typography Fallback (Automatic, not recorded in user-habits)

These are CommonMark/GFM universal typography courtesies:

- One blank line between paragraphs; blank lines before/after code blocks, math blocks, lists, headings
- ATX headings up to 6 levels; heading lines do not end with punctuation
- YAML frontmatter at document beginning; those appearing in middle/end are merged or removed
- GFM table alignment `|:--|` preserved as-is; clean extra spaces in cells
- Code blocks preserved as-is, do not modify language annotations
- After formula wrapping, verify `$` pairing and bracket matching

---

## Workflow

### 1. Read + Backup

User may provide **file path** or **pasted text**. Always backup first:

- With path: same directory as original file, naming `*original filename*.bak.orig`
- Plain text: `plain-markdown-backup-YYYYMMDD-HHMMSS.md` in current working directory

### 2. Scan + Auto-process

Run through Tier 1, Tier 2 in one pass: auto-delete + auto-convert. Collect Tier 3 new pattern list during process.

### 3. Report + (If any) Confirm

Give user a concise summary, for example:

```
Auto-processed:
  - Removed HTML X times, custom containers X times, font markers X times
  - Converted subscript/superscript X times, footnotes X times, paragraph merges X times, link whitespace X times
  - Standardized math formula wrapping X times, LaTeX commands X times
    (including X Pandoc-compatible replacements, X OCR artifact replacements)
New patterns X (please confirm):
  1. 「Pattern description」→ Suggested rule: ...   Add to config/user-habits.md?
```

No new patterns → proceed to step 4; new patterns → wait for user "adopt / reject / modify" one by one.

### 4. Math Standardization (Must Execute)

After all Tier 2 conversions complete and before write-back, execute `scripts/normalize_math.py` on the file:

```bash
python scripts/normalize_math.py <file path>
```

This will unify all display formulas to `$$\n...\n$$` three-line block format, and complete batch standardization like intra-formula space compression, integral symbol S unification.

**Key: Regardless of whether normalize_math.py was run before, any new math formulas produced by Tier 2 need it to run again before delivery.** Therefore the correct order is always:

1. Tier 1 → Tier 2 (manual or script conversion)
2. **normalize_math.py** (final standardization of all outputs from step 1)
3. Write back

As the skill's final delivery threshold, this step **must execute**, cannot skip.

### 5. Write Back

Use normalized content to overwrite original file, keep backup. If user agrees to write new rules back, sync update `config/user-habits.md`.

---

## Output Language

All interactions with user use **Chinese(中文)**.
