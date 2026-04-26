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
| **Text** | Subscript/superscript conversion | - | ⚠️ | ⚠️ |
| **Text** | Bold/italic → plain text | - | ✅ | - |
| **Text** | Footnote `[^n]` → `[n]` | - | ✅ | - |
| **Text** | Paragraph merge rules | - | ✅ | - |
| **Text** | Link whitespace cleanup | - | ✅ | - |
| **Text** | OCR artifact replacement | - | ✅ | - |
| **Delete** | HTML tags removal | - | ✅ | - |
| **Delete** | Custom containers removal | - | ✅ | - |
| **Delete** | Emoji codes removal | - | ✅ | - |
| **Delete** | Task list conversion | - | ✅ | - |
| **Format** | Wiki/attachment links preserved | - | ✅ | - |
| **Format** | Heading level normalization | - | ⚠️ | ⚠️ |

**Legend**: ✅ = Implemented | ⚠️ = Partially/Manual | ❌ = Not implemented | - = Not applicable

**Key**:
- **Auto (Script)**: `scripts/normalize_math.py` handles automatically
- **Auto (Agent)**: Agent applies rule during Tier 1/2 processing
- **Manual**: Must be applied manually or requires special attention

---

## Subscript/Superscript Handling

**Current preference**: `[superscript]` / `[subscript]` form, do not use `^` or Unicode superscript characters. Add one space before the brackets.

```
Examples: x^2 → $x^2$    深度学习<sub>2</sub> → 深度学习 [2]    H₂O → $H_2 O$    Deep learning$^2$ → Deep learning [2]   Deep learning $_2$ → Deep learning [2]
```

| Status | Implementation |
|--------|----------------|
| ⚠️ Manual | Agent must identify patterns like `<sub>`, `^`, Unicode subscripts during Tier 2 scan |

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
