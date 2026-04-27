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

- `scripts/_process_doc.py` — **Tier 1+2 automation script** for bulk processing of non-math transformations (bold/italic removal, heading normalization, Pandoc subscript/superscript → LaTeX math, image attribute cleanup, etc.). See `## Script Responsibilities` below for what it handles vs. what stays manual.
- `scripts/normalize_math.py` — **Must be executed every time** math/style standardization script (as workflow step 4), currently 5 transformation groups, each independently toggleable:
  - **Formula block split/upgrade**: Standalone `$...$` on a single line upgrades to `$$\n...\n$$` three-line block format
  - **Intra-formula space compression**: `\mathrm {d}` → `\mathrm{d}`, `z _ {I}` → `z_{I}`, `\cmd \cmd` → `\cmd\cmd`
  - **Integral symbol S unification**: `\mathrm{S}` / `\mathbb{S}` / `\mathbf{S S}` all normalize to `\mathbf{S}` / `\mathbf{SS}`
  - **Bold term stripping**: Remove `**term**` wrapping per `--terms` file list
  - **Unicode math chars → LaTeX commands**: `·→\cdot`, `α→\alpha`, `²→^{2}`, `…→\dots`, etc. (only inside math, `--unicode-math` enables)
  - **Formula-Chinese wrapping**: `\cmd中文` → `\cmd{中文}` (pandoc compatibility)
  All enabled by default, no need to ask each time.

  **Command-line usage**:
  ```bash
  python normalize_math.py <file.md>                    # 默认全部启用
  python normalize_math.py <file.md> --no-whitespace    # 禁用空格压缩
  python normalize_math.py <file.md> --no-s-unify       # 禁用 S 符号统一
  python normalize_math.py <file.md> --no-split-blocks  # 禁用公式块拆分
  python normalize_math.py <file.md> --unicode-math     # 启用 Unicode 转换
  python normalize_math.py <file.md> --no-wrap-chinese # 禁用中文包裹
  python normalize_math.py <file.md> --terms path.txt  # 指定要移除的 bold 词列表
  ```
- `references/pandoc-latex-support.md` — Pandoc LaTeX compatibility command reference.
- `references/normalize_lagrange.py` — Reference script for one-time document processing; not for general tool use.
- `tests/` — pytest regression suite and fixtures for above scripts (`math_section_input.md` / `math_section_expected.md`), run `python -m pytest .claude/skills/plain-markdown-skill/tests -v` before modifying scripts.

---

## Script Responsibilities (Boundary Contract)

To avoid duplicate work and conflicting edits, scripts and Agent have a **strict division of labor**:

| Responsibility | `_process_doc.py` | Agent (Manual) | `normalize_math.py` |
|:---|---:|:---:|:---:|
| Bold/italic removal | ✅ | — | — |
| Heading normalization (`N.` → `#`) | ✅ | — | — |
| Pandoc sub/superscript → LaTeX math | ✅ | — | — |
| Image attribute removal `{width=...}` | ✅ | — | — |
| Escaped char fixes (`\>` → `>`) | ✅ | — | — |
| LaTeX list numbers `\(n\)` → `n.` | ✅ | — | — |
| Table conversion (any non-GFM) | ❌ | ✅ | — |
| Formula block split (`$$...$$`) | ❌ | ❌ | ✅ |
| Intra-formula space compression | ❌ | ❌ | ✅ |
| Unicode math → LaTeX | ❌ | ❌ | ✅ |
| Formula-Chinese wrapping | ❌ | ❌ | ✅ |
| Integral S unification | ❌ | ❌ | ✅ |

**Key rules:**
1. `_process_doc.py` MUST NOT do formula block splitting — that's `normalize_math.py`'s job. Doing it in both places causes blank-line artifacts.
2. Table conversion stays manual (Agent Tier 2) because multi-row headers, grid tables, and layout tables require semantic judgment that regex cannot handle reliably.
3. The pipeline order is: `_process_doc.py` → Agent table fixes → `normalize_math.py`. This order cannot be changed.

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

### 0. Load Configuration (MUST READ FIRST)

**Before processing any document, Agent MUST read `config/user-habits.md` first.**

This is the **single source of truth** for all user preferences. The Agent must:
1. Load and parse all rules from `config/user-habits.md`
2. Apply those rules during Tier 1/Tier 2 processing
3. Reference this file when converting math commands and handling patterns

Do NOT proceed to step 1 until config is loaded and internalized.

### 1. Read + Backup

User may provide **file path** or **pasted text**. Always backup first:

- With path: same directory as original file, naming `*original filename*.bak.orig`
- Plain text: `plain-markdown-backup-YYYYMMDD-HHMMSS.md` in current working directory

### 2. Scan + Auto-process

Run through Tier 1, Tier 2 in one pass: auto-delete + auto-convert. Collect Tier 3 new pattern list during process.

**Recommended approach**: Use `scripts/_process_doc.py` for bulk Tier 1/2 transformations, then handle tables manually:

```bash
python scripts/_process_doc.py <file.md>
```

**CRITICAL — Processing order inside the script:**

The order of operations matters. The script enforces this order:
1. **Headings first** — convert `N. Title` → `# Title` BEFORE converting `\(n\)` → `n.`. If reversed, `\(1\) Constraints` becomes `1. Constraints` and then gets falsely matched as a level-1 heading.
2. **Pandoc sub/superscript before bold/italic removal** — `*VAR*~sub~` patterns require the `*` markers to still be present for regex matching.
3. **Bold/italic removal after subscript conversion** — once subscripts are wrapped in `$...$`, remove remaining `**`/`*` markers.

**Table conversion — Agent manual only:**

Do NOT attempt to automate table conversion in `_process_doc.py`. Reasons:
- Multi-row headers require semantic merging (e.g., "BP training/testing/validation" rows)
- Grid tables (`+---+`) have fragile row/column detection
- Layout tables with images (e.g., side-by-side figure panels) should be flattened to `![]()\n(caption)` blocks
- Regex-based detection produces more false positives than correct conversions

Instead, the Agent reads each table section and converts with targeted `Edit` calls after the script runs.

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

**Key: `_process_doc.py` must NOT do formula block splitting.** If both scripts split formula blocks, each run introduces extra blank lines around `$$` markers. Formula block splitting is exclusively `normalize_math.py`'s job. See `## Script Responsibilities` for the full boundary contract.

The correct order is always:

1. `_process_doc.py` (Tier 1+2 automation: headings, bold/italic, sub/superscript, lists)
2. Agent table fixes (manual Tier 2: convert non-GFM tables with targeted `Edit` calls)
3. **normalize_math.py** (final math standardization of all outputs from steps 1-2)
4. Write back

As the skill's final delivery threshold, step 3 **must execute** after all other changes, cannot skip.

### 5. Write Back

Use normalized content to overwrite original file, keep backup. If user agrees to write new rules back, sync update `config/user-habits.md`.

---

## Output Language

All interactions with user use **Chinese(中文)**.
