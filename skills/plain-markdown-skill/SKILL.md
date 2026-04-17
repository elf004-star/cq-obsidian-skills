---
name: plain-markdown-skill
description: |
  把一份杂乱的 markdown 文档规范化并极简化为 CommonMark/GFM 纯 markdown。本技能适合处理单个文档，模型能力越强，支持的文档越长。
---

# Plain Markdown Skill

## 目标

把任意来源的 markdown 收敛成**规范、极简**的 CommonMark/GFM：只留标准元素、修明显错误、清不规范语法，不添加装饰。学术内容（数学公式、符号）全部保留，仅规范化语法。

## 单一真源

- **用户偏好全部以 `user-habits.md` 为准**。本文件不再复述具体规则，只写流程与分类。两处描述若有冲突，以 `user-habits.md` 为准。
- Pandoc LaTeX 兼容性查 `references/pandoc-latex-support.md`。

之所以这么做：用户偏好会变，规则表只放一处，改动不会漂移，技能本身保持稳定。

## 资源目录

- `scripts/normalize_math.py`——**每次处理都必须执行**的数学/样式标准化脚本（作为工作流第 4 步），当前 4 组变换，均可单独开关：
  - **公式块拆分/升级**：单独一行的 `$...$` 升级为 `$$\n...\n$$` 三行块格式
  - **公式内空格压缩**：`\mathrm {d}` → `\mathrm{d}`、`z _ {I}` → `z_{I}`、`\cmd \cmd` → `\cmd\cmd`（默认开启，`--no-whitespace` 关闭）
  - **积分符号 S 统一**：`\mathrm{S}` / `\mathbb{S}` / `\mathbf{S S}` 一律归到 `\mathbf{S}` / `\mathbf{SS}`（默认开启，`--no-s-unify` 关闭）
  - **bold 术语剥除**：按 `--terms` 文件清单去掉 `**术语**` 包裹
  - **Unicode 数学字符 → LaTeX 命令**（`·→\cdot`、`α→\alpha`、`²→^{2}`、`…→\dots` 等；仅在 `$...$` / `$$...$$` 内生效，不碰正文，`--unicode-math` 开启）
  脚本默认全部开启，无需每次询问。
- `references/pandoc-latex-support.md`——Pandoc LaTeX 兼容命令速查。
- `references/normalize_lagrange.py`——一次性文档专用脚本的留样，供后续相似文档参考；不作通用工具使用。
- `tests/`——对上述脚本的 pytest 回归套件与 fixture（`math_section_input.md` / `math_section_expected.md`），改脚本前先跑 `python -m pytest .claude/skills/plain-markdown-skill/tests -v`。

---

## 处理分类

分三档，决定"做不做、问不问"。

### 档 1：自动删除（不询问）

出现即移除或平铺为纯文本：

- HTML 标签：`<span>`、`<div>`、`<font>`、`<br>` 等所有行内/块级 HTML（HTML 表格例外，转成 GFM 表格）
- 自定义容器：`:::warning`、`:::tip`、`:::info`、`:::note` 等非标准块
- emoji 代码：`:warning:`、`:smile:` 等
- 脚注标记 `[^n]` → 按 `user-habits.md` 转成 `[n]`
- 任务列表 `- [x]` / `- [ ]` → 普通无序列表 `- `

### 档 2：自动转换（不询问，按 user-habits.md）

按 `user-habits.md` 就地改写，无须每次打扰用户：

- 上下标形式（`<sub>/<sup>`、`^`、Unicode 上下标、math-mode 脚注引用 `$^{n}$` 等）
- 加粗、斜体、删除线等样式标记
- 段落错行合并
- 数学公式包裹（行内 `$...$`、行间 `$$...$$`）与 LaTeX 命令标准化
- 已知特殊符号 / OCR 乱码替换表
- 链接空白清理：`[ 文本 ]( URL )` → `[文本](URL)`

**非 Pandoc 兼容的 LaTeX 命令**与**未登记的 OCR 乱码**也归到这一档：参照 `references/pandoc-latex-support.md` 做就近等价替换，无把握的个别字符归到档 3。

### 档 3：需询问（仅一种情形）

发现 `user-habits.md` 尚未登记的**新模式**——例如新的脚注变体、新的乱码字符、新的非标准宏——向用户说明模式并提议规则，**确认后应用到当前文档**，并**询问是否把规则回写 `user-habits.md`**，以便以后自动化。

> 其他 CommonMark/GFM 标准元素（标题、列表、代码块、表格、水平线、引用块、wiki 链接 `[[...]]`、附件引用 `![[...]]`、普通链接、YAML frontmatter 等）一律原样保留，只做下面的排版兜底。

---

## 排版兜底（自动，不记入 user-habits）

这些是 CommonMark/GFM 通用排版礼貌：

- 段落之间一个空行；代码块、数学块、列表、标题前后留空行
- ATX 标题最多 6 级；标题行尾不带标点
- YAML frontmatter 放文档开头；出现在中间/末尾的就合并或删除
- GFM 表格对齐符 `|:--|` 原样保留；清理单元格多余空格
- 代码块原样保留，不擅改语言标注
- 公式包裹后复核 `$` 成对、括号匹配

---

## 工作流程

### 1. 读入 + 备份

用户可能给**文件路径**或**粘贴文本**。一律先备份：

- 有路径：与原文件同目录，命名 `*原文件名*.bak.orig`
- 纯文本：当前工作目录下 `plain-markdown-backup-YYYYMMDD-HHMMSS.md`

### 2. 扫描 + 自动处理

一次性跑完档 1、档 2：自动删除 + 自动转换。过程中收集档 3 的新模式清单。

### 3. 报告 + （若有）询问

给用户一份精简摘要，例如：

```
自动处理：
  - 移除 HTML X 处、自定义容器 X 处、字体标记 X 处
  - 上下标 X 处、脚注 X 处、段落合并 X 处、链接空白 X 处
  - 数学公式包裹 X 处、LaTeX 命令标准化 X 处
    （含 X 处 Pandoc 兼容替换、X 处 OCR 乱码替换）
新模式 X 个（请确认）：
  1. 「模式描述」→ 建议规则：……   是否加入 user-habits.md？
```

没有新模式 → 直接进入第 4 步；有新模式 → 逐条等待用户"采纳 / 否决 / 修改"。

### 4. 数学标准化（必须执行）

在档 2 所有转换完成之后、写回之前，对文件执行 `scripts/normalize_math.py`：

```bash
python scripts/normalize_math.py <文件路径>
```

这会将所有行间公式统一为 `$$\n...\n$$` 三行块格式，并完成公式内空格压缩、积分符号 S 统一等批量标准化。

**关键：无论之前是否跑过 normalize_math.py，档 2 产生的任何新数学公式都需要它再跑一遍才能交付。**因此正确的顺序永远是：

1. 档 1 → 档 2（手工或脚本的转换）
2. **normalize_math.py**（此时对第 1 步的所有产出做最终标准化）
3. 写回

作为技能的最终交付门槛，这一步**必须执行**，不可跳过。

### 5. 写回

用规范化后的内容覆盖原文件，备份保留。若用户同意把新规则回写，同步更新 `user-habits.md`。

---

## 输出语言

与用户的一切交互使用**中文**。
