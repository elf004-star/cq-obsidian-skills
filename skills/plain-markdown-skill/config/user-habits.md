# User Habits

> This file records user preferences for plain-markdown-skill.
> The skill references rules in this file during document processing to ensure conversion results match the user's consistent style.
> Update this file anytime preferences change.

---

## Automation Status Overview

| Category | Rule | Auto (Script) | Auto (Agent) | Manual |
|----------|------|:---:|:---:|:---:|
| **Math** | Formula block split (`$$...$$`) | ✅ | - | - |
| **Math** | Inline formula wrapping (`$...$`) | - | ✅ | - |
| **Math** | Formula variable wrapping (`$S_{limit}$`) | - | ✅ | - |
| **Math** | Standalone formula → `$$...$$` upgrade | - | ✅ | - |
| **Math** | Intra-formula space compression | ✅ | - | - |
| **Math** | Integral symbol S unification | ✅ | - | - |
| **Math** | Unicode math → LaTeX | ✅ | - | - |
| **Math** | `array` environment simplification | ✅ | - | - |
| **Math** | `\sqrt[...]` → `\sqrt(...)` | ❌ | - | ⚠️ |
| **Math** | `\etc` → `\dots` | ❌ | - | ⚠️ |
| **Math** | `\const` → `\text{const.}` | ❌ | - | ⚠️ |
| **Math** | Bare `SS` → `\mathbf{SS}` (body text) | ❌ | - | ⚠️ |
| **Math** | Formula-Chinese spacing (`{中文}`) | ✅ | - | - |
| **Text** | Subscript/superscript conversion | ✅ | - | - |
| **Text** | Bold/italic → plain text | ✅ | - | - |
| **Text** | Footnote `[^n]` → `[n]` | ✅ | - | - |
| **Text** | Paragraph merge rules | - | ✅ | - |
| **Text** | Link whitespace cleanup | - | ✅ | - |
| **Text** | OCR artifact replacement | - | ✅ | - |
| **Delete** | HTML tags removal | - | ✅ | - |
| **Delete** | Custom containers removal | - | ✅ | - |
| **Delete** | Emoji codes removal | - | ✅ | - |
| **Delete** | Task list conversion | - | ✅ | - |
| **Format** | Wiki/attachment links preserved | - | ✅ | - |
| **Format** | Heading level normalization | ✅ | - | - |
| **Format** | Table conversion (non-GFM → GFM) | - | ✅ | - |

**Legend**: ✅ = Implemented | ⚠️ = Partially/Manual | ❌ = Not implemented | - = Not applicable

**Key**:
- **Auto (Script)**: `scripts/_process_doc.py` (text/format) or `scripts/normalize_math.py` (math) handles automatically
- **Auto (Agent)**: Agent applies rule during Tier 1/2 processing (e.g., table conversion, paragraph merging)
- **Manual**: Must be applied manually or requires special attention

---

## Subscript/Superscript Handling

**Current preference**: Math variables use `$...$` wrapping with LaTeX `_{sub}` / `^{sup}` syntax. Non-math superscripts (footnote markers) use `[n]` form.

### Pandoc Subscript/Superscript → LaTeX Math (Script: `_process_doc.py`)

Academic documents from DOCX conversion frequently use Pandoc-style `~sub~` / `^sup^` syntax. The script handles **4 distinct pattern variants** — a single regex cannot cover all cases:

| # | Pattern | Example | → Result | Description |
|---|---------|---------|----------|-------------|
| 1 | `*VAR~sub~*` | `*C~pm~*` | `$C_{pm}$` | Italic wraps entire subscript expression |
| 2 | `*VAR*~sub~` | `*T*~max~` | `$T_{\max}$` | Italic only on variable name, separate subscript |
| 3 | `VAR~sub~` | `G~best~`, `h~f~` | `$G_{best}$`, `$h_{f}$` | Bare subscript (no italic), uppercase or lowercase |
| 4 | `*VAR*` (standalone) | `*WOB*`, `*RPM*` | `WOB`, `RPM` | Italic-only variable → plain text (or `$WOB$` if in math context) |

**Order matters**: The script processes these in order (1 → 2 → 3) because:
- Pattern 1 (`*C~pm~*`) would be partially matched by Pattern 2 (`*C*~pm~`), leaving a dangling `*`
- Pattern 3 (bare subscript) must run last to avoid interfering with patterns 1-2

**Also handled**:
- Superscript: `*VAR*^sup^` → `$VAR^{sup}$`, `VAR^sup^` → `$VAR^{sup}$`
- Units: `r·min^-1^` → `$\text{r}\cdot\text{min}^{-1}$`
- R-squared: `R^2^` → `$R^{2}$`

### Non-math Superscripts

**Current preference**: `[superscript]` / `[subscript]` form for footnote markers.

```
Examples: 深度学习<sub>2</sub> → 深度学习 [2]    Deep learning$^2$ → Deep learning [2]   Deep learning $_2$ → Deep learning [2]
```

| Status | Implementation |
|--------|----------------|
| ✅ Script | `_process_doc.py` handles Pandoc ~/^ patterns; Agent handles remaining edge cases |

---

## Bold / Italic Handling

**Current preference**: Convert to plain text, do not preserve any style markers.

| Status | Implementation |
|--------|----------------|
| ✅ Agent | Agent removes `**bold**`, `*italic*`, `~~strikethrough~~` during Tier 2 |

---

## Footnote References

**Current preference**: Only keep superscript numbers of formulas/symbols in body text (e.g., the `2` in `x²`), do not keep footnote reference markers `[^1]`, etc.

**Example**: Mark `<sup>52</sup>` should be preserved as `[52]` form.

**Superscript references in Math mode**: Superscript or subscript references like `$^{number}$` and `$_{number}$` that appear outside LaTeX math formulas (footnote markers) should be converted to `[number]` form.

**Example**:
- Original: `the water $^{56}$` → Normalized: `the water [56]`

| Status | Implementation |
|--------|----------------|
| ✅ Agent | `[^n]` → `[n]`, `$^{n}$` → `[n]` during Tier 2 |

---

## Special Symbols & OCR Artifacts

**Known symbols that need replacement**:

| Original | Replace with | Note | Status |
|----------|-------------|------|--------|
| `™` | (delete) | OCR artifact | ✅ Agent |
| `©` | `(C)` | Copyright symbol | ✅ Agent |
| `®` | `(R)` | Registered trademark | ✅ Agent |
| `­­` | (delete) | Caret/artifact | ✅ Agent |
| `…` | `...` | Ellipsis | ✅ Agent |
| Other | Ask user | New pattern | ⚠️ Tier 3 |

---

## Paragraph Merge Rules

When two adjacent paragraphs satisfy ALL of the following conditions, automatically merge into one paragraph:

1. End of first paragraph is **NOT** period `.`, question mark `?`, exclamation mark `!`, semicolon `;`, colon `:`
2. First letter of second paragraph **is lowercase** or **starts with number**
3. There is **only one** blank line between the two paragraphs

| Status | Implementation |
|--------|----------------|
| ✅ Agent | Agent applies during Tier 2 |

---

## Attachment / Wiki Link Format

**Current preference**: Keep `![[...]]` and `[[...]]` syntax as-is.

| Status | Implementation |
|--------|----------------|
| ✅ Agent | No conversion needed, preserve as-is |

---

## Table Conversion (Non-GFM → GFM)

**Current preference**: All tables must be in GFM pipe-table format (`| col | col |`).

**Status**: **Agent manual only** — not automated in scripts. Reasons:
- Multi-row headers require semantic merging (e.g., "BP / training / testing / validation" spanning rows)
- Grid tables (`+---+`) have fragile row/column boundary detection
- Layout tables containing images should be flattened to `![]()\n(caption)` blocks
- Regex-based detection produces more false positives than correct conversions

**Agent workflow for tables**:
1. Identify non-GFM table by scanning for `------` separators, `+---+` borders, or `+=+` markers
2. Read the table section
3. Convert with targeted `Edit` calls to GFM format
4. For layout/image tables: flatten to individual `![]()\n(caption)` blocks

**Conversion examples**:

| Non-GFM | → GFM |
|---------|-------|
| Underline-style (`------` separators) | `\| col1 \| col2 \|` with `\|:---\|` alignment |
| Grid-style (`+---+` borders) | Parse cell contents to GFM rows |
| Layout tables with `![]()` | Flatten to sequential `![]()\n(caption)` blocks |

---

## Math Formulas

All math formulas and pure math symbols must be wrapped with `$...$` or `$$...$$`.

### Wrapping Rules

| Rule | Status | Implementation |
|------|--------|----------------|
| Inline formula: `$...$` | ✅ Script | `normalize_math.py` |
| Display formula: `$$\n...\n$$` | ✅ Script | `normalize_math.py` |

---

### Math Symbol Standardization

**Implemented by `scripts/normalize_math.py`** (✅ = auto via script):

| Original | Standard form | Script | Agent |
|----------|---------------|:------:|:-----:|
| `\sqrt[...]` | `\sqrt(...)` | ❌ | ⚠️ |
| `·` | `\cdot` | ✅ | - |
| `×` | `\times` | ✅ | - |
| `÷` | `\div` | ✅ | - |
| `≠` | `\neq` | ✅ | - |
| `≤` | `\leq` | ✅ | - |
| `≥` | `\geq` | ✅ | - |
| `α` `β` `γ` | `\alpha` `\beta` `\gamma` | ✅ | - |
| `π` | `\pi` | ✅ | - |
| `∞` | `\infty` | ✅ | - |
| `∂` | `\partial` | ✅ | - |
| `∇` | `\nabla` | ✅ | - |
| `...` / `…` | `\dots` | ✅ | - |
| `\etc` (in math) | `\dots` | ❌ | ⚠️ |
| `\const` | `\text{const.}` | ❌ | ⚠️ |
| `\text{c o n s t a n t}` | `\text{constant}` | ❌ | ⚠️ |

**Legend**: ✅ = Done | ❌ = Not implemented | ⚠️ = Manual required | - = N/A

---

### Integral / Summation Symbol S Unification

**In LaGrange-style text, `S` / `SS` represents total integral (equivalent to `∫`).**

| Form | Target | Script | Agent |
|------|--------|:------:|:-----:|
| `\mathrm{S}`, `\mathbb{S}`, `\mathbf{S S}` | `\mathbf{S}` | ✅ | - |
| `\mathrm{SS}`, `\mathbb{SS}`, `\mathbf{S S}` | `\mathbf{SS}` | ✅ | - |
| Bare `SS` in body text | `\mathbf{SS}` wrapped | ❌ | ⚠️ |

**Agent task**: When `SS` appears immediately after math expressions in body text (e.g., `SS dm`, `SS Π`), wrap as inline formula with `\mathbf{SS}`.

---

### Intra-formula Space Compression

**Implemented by `scripts/normalize_math.py`**:

| Original | Standard form |
|----------|---------------|
| `\mathrm {d}` | `\mathrm{d}` |
| `\frac {a}{b}` | `\frac{a}{b}` |
| `\Omega^ {\prime \prime}` | `\Omega^{\prime\prime}` |
| `z _ {I}` | `z_{I}` |
| `\lambda \cdot` | `\lambda\cdot` |
| `\cmd \cmd` (adjacent) | `\cmd\cmd` |

| Status |
|--------|
| ✅ Script |

---

### `array` Environment Simplification

**Multi-column single-line arrays → flatten**:

| Original | Standard form | Script |
|----------|---------------|:------:|
| `\begin{array}{c c c} A, & B, & C \end{array}` | `A, \quad B, \quad C` | ✅ |

**Single-column multi-line arrays**: Keep as-is (e.g., multi-line integral derivations).

| Status |
|--------|
| ✅ Script |

---

### Unregistered Non-Pandoc Commands

**For cases not listed above**: prioritize nearest equivalent replacement per `references/pandoc-latex-support.md`.

| Status | Implementation |
|--------|----------------|
| ⚠️ Tier 3 | Ask user for confirmation, then write rule back here |

---

## Heading Levels

| Rule | Status | Implementation |
|------|--------|----------------|
| `SECTION` / `Chapter` → `#` | ⚠️ Manual | Agent should verify and fix |
| `Subsection` / `Part` → `##` | ⚠️ Manual | Agent should verify and fix |
| `Article N` → `##` | ⚠️ Manual | Agent should verify and fix |
| Numbered lists keep as `- ` | ✅ Agent | - |

---

## Backup Strategy

- Always backup original file before processing
- Backup file naming: `*original filename*.bak.orig`
- Backup files saved in same directory

| Status |
|--------|
| ✅ Agent |

---

## Other Preferences

(Please supplement according to actual situation)

---

## Formula Variable Wrapping Rules

**数学公式中的变量必须用 `$...$` 包裹**，即使在公式块内部：

| Pattern | Example | Rule |
|---------|---------|------|
| 变量名（下划线/大写） | `S_limit`, `S_sorted`, `MSE` | 必须包裹 `$S_{limit}$` |
| 数组索引 | `S_sorted[0]` | 必须包裹 `$S_{sorted}[0]$` |
| 列表中的公式 | `S_limit = ...` | 必须包裹 `$S_{limit} = \dots$` |
| 条件判断 | `n=1`, `n≥4` | 必须包裹 `$n=1$`, `$n\geq 4$` |
| **注意下标格式** | `S_limit`, `S\_limit` | **规范是`S_{limit}`，不是 `S\_limit`** |

| Status | Implementation |
|--------|----------------|
| ✅ Agent | Tier 2 自动包裹 |

**Examples**:

| Original | ❌ Wrong | ✅ Correct |
|----------|----------|------------|
| `S_limit` | `$S\_limit$` | `$S_{limit}$` |
| `F1` (下标) | `$F\_1$` | `$F_1$` |

---

## Formula-Chinese Spacing Rules

**公式与中文之间必须有分隔符**，否则 pandoc 会报错。由 `normalize_math.py` 脚本自动处理。

| Pattern | Rule |
|---------|------|
| LaTeX 命令后接中文 | 用 `{}` 包裹中文，如 `\cmd中文` → `\cmd{中文}` |
| 中文后接 LaTeX 命令 | 用 `{}` 包裹中文，如 `中文\cmd` → `{中文}\cmd` |

| Status | Implementation |
|--------|----------------|
| ✅ Script | `wrap_chinese_in_math()` in `normalize_math.py` |

**Examples**:

| Original | ✅ Correct |
|----------|------------|
| `\times苹果` | `\times{苹果}` |
| `苹果\times` | `{苹果}\times` |
| `k_1\times进尺 + k_2\times机械钻速` | `k_1\times{进尺} + k_2\times{机械钻速}` |

---

## Unicode Math Symbols (Additional)

除 `×` 外，以下符号也需要转换：

| Symbol | LaTeX | Status |
|--------|-------|--------|
| `×` | `\times` | ✅ Script |
| `·` | `\cdot` | ✅ Script |
| `÷` | `\div` | ✅ Script |
| `≤` | `\leq` | ✅ Script |
| `≥` | `\geq` | ✅ Script |
| `≠` | `\neq` | ✅ Script |
| `≤50` | `\leq50` (无空格) | ✅ Script |
| `>200` | `\geq200` (无空格) | ✅ Script |

---

## Formula Block Upgrade Rules

**独立一行的公式必须升级为 `$$...$$` 块级格式**：

| Original | Target |
|----------|--------|
| 单独一行: `F1 = k1×进尺 + ...` | `$$\nF1 = k1\times进尺 + ...\n$$` |
| 单独一行: `置信度 = 有效重叠长度 / 总钻井长度` | `$$\n置信度 = 有效重叠长度 / 总钻井长度\n$$` |
| 单独一行: `进尺命中率 = 单趟进尺 / 总进尺` | `$$\n进尺命中率 = 单趟进尺 / 总进尺\n$$` |

**判断标准**：单独一行且包含 `=` 符号的数学表达式。

| Status | Implementation |
|--------|----------------|
| ✅ Agent | Tier 2 自动升级为 `$$...$$` |

---

## Implementation Checklist for New Rules

When adding a new rule, specify:

```markdown
### New Rule Name

**Original**: `...`
**Target**: `...`
**Implementation**: 
- [ ] Script (`scripts/normalize_math.py`)
- [ ] Agent (Tier 1/Tier 2)
- [ ] Manual
**Priority**: Low / Medium / High
```

---

## Processing Pipeline Notes

> These are operational lessons learned from real document processing. They guide the Agent's behavior but are not conversion rules per se.

### Script Execution Order (CRITICAL)

The `_process_doc.py` script enforces this order internally:

1. **Headings first** → `N. Title` → `# Title` BEFORE `\(n\)` → `n.`
2. **Pandoc sub/superscript before bold/italic removal** → `*VAR*~sub~` patterns need `*` markers present
3. **Bold/italic removal after subscript conversion** → once subscripts are wrapped in `$...$`, remove remaining `**`/`*`

**Why**: If `\(n\)` conversion runs first, `\(1\) Constraints...` becomes `1. Constraints...`, which the heading regex would falsely match as a level-1 heading.

### Script Boundary Contract

| Do in `_process_doc.py` | Do NOT do in `_process_doc.py` |
|---|---|
| Bold/italic removal | Formula block splitting (`normalize_math.py`'s job) |
| Heading normalization | Table conversion (Agent manual) |
| Pandoc ~/^ → LaTeX math | Unicode math → LaTeX (`normalize_math.py`) |
| Image attribute removal | Formula-Chinese wrapping (`normalize_math.py`) |
| LaTeX list numbers `\(n\)` → `n.` | Intra-formula space compression (`normalize_math.py`) |

**Why the formula-block rule**: If both scripts split `$$...$$` blocks, each run introduces extra blank lines.

### Pipeline Order (Must Follow)

```
1. _process_doc.py     → bulk text/format standardization
2. Agent table fixes   → convert non-GFM tables with targeted Edit calls
3. normalize_math.py   → final math standardization (ALWAYS LAST)
```

### Table Conversion Strategy

**Never script, always Agent manual**. Three table types need different handling:
- **Data tables** (underline `------` or grid `+---+`): Convert to GFM pipe tables row by row
- **Multi-row-header tables**: Flatten header rows into `| Col1 | Col2 |` then map data
- **Layout tables** with images: Flatten to sequential `![]()\n(caption)` blocks
