# Pandoc LaTeX 支持与限制

> 调研时间：2026/04/16

---

## 一、支持的功能

### 1.1 AMSLaTeX 数学符号

Pandoc 内置支持标准 AMSMath 包的大量数学符号：

| 类别 | 示例 |
|------|------|
| **希腊字母** | `\alpha`, `\beta`, `\gamma`, `\delta`, `\epsilon`, `\theta`, `\pi`, `\omega` ... |
| **运算符号** | `\sum`, `\int`, `\partial`, `\nabla`, `\infty`, `\pm`, `\times`, `\div` |
| **关系符号** | `\rightarrow`, `\leftarrow`, `\Rightarrow`, `\Leftarrow`, `\mapsto`, `\subseteq`, `\supseteq`, `\approx`, `\equiv` |
| **逻辑符号** | `\forall`, `\exists`, `\neg`, `\land`, `\lor` |
| **集合符号** | `\in`, `\notin`, `\cup`, `\cap`, `\emptyset`, `\subset`, `\supset` |
| **省略号** | `\dots`, `\cdots`, `\vdots`, `\ddots` |
| **字体样式** | `\mathbf`, `\mathrm`, `\mathit`, `\mathsf`, `\mathtt`, `\mathbb`, `\mathcal`, `\mathfrak` |

### 1.2 常见命令

| 命令/环境 | 支持情况 |
|-----------|---------|
| `\cite` | ✅ 完整支持（需配合 bibliography） |
| `\includegraphics` | ✅ 支持 |
| `\hline`, `\tabular` | ✅ 支持 |
| `\begin/end` 已知环境 | ✅ 支持 |
| 行内公式 `$...$` | ✅ 完整支持 |
| 显示公式 `$$...$$` / `\[...\]` | ✅ 完整支持 |
| `\command`（已知命令） | ✅ 支持 |
| `\newcommand` / `\def` 简单宏 | ✅（需开启 `latex_macros` 扩展） |

### 1.3 近年改进（Pandoc 3.x）

- 未知环境不再被错误转为 `BlockQuote`，改为透明透传
- 未知命令的参数 `{}` 会被正确剥离
- 支持 `\figurename` 后空格处理
- 支持 `\makeatletter`（`@` 可作为控制序列中的字母）
- 支持 `lstinline` 带大括号
- 支持 `keyval` 风格选项解析
- `\[10pt]` 换行间距现在正确解析

---

## 二、不支持的功能

### 2.1 复杂自定义宏

| 类型 | 说明 |
|------|------|
| 复杂 `\newcommand` | 带条件判断、循环、嵌套展开的宏无法正确处理 |
| `\def` 高级用法 | 包含参数默认值、多级宏展开的定义 |
| LaTeX3 语法 | `\ExplSyntaxOn/Off`, `\cs_new:Npn` 等命令完全不支持 |

### 2.2 高级数学命令（部分格式限制）

| 命令 | 说明 |
|------|------|
| `\overset`, `\underset` | 某些非 LaTeX 输出格式下无法正确转换 |
| `\stackrel`, `\xrightarrow`, `\xleftarrow` | 部分输出格式可能丢失样式 |
| `\sideset`, `\substack` | 支持有限 |
| `\boxed`, `\cancel`, `\bcancel` | 依赖特定包，输出格式可能不认 |

### 2.3 特殊图形与宏包

| 类型 | 说明 |
|------|------|
| `pstricks` 语法 | 不支持 |
| `tikz-cd` 高级语法 | 部分支持，复杂图形可能丢失 |
| `\special` 命令 | 不支持 |
| `graphics` / `graphicx` 特有高级选项 | 部分支持 |

### 2.4 复杂表格命令

| 命令 | 说明 |
|------|------|
| `\multicolumn` | 支持有限 |
| `\multirow` | 不支持 |
| 列格式 `@{...}` 类型定义 | 不支持 |

### 2.5 文本符号与引用

| 命令 | 说明 |
|------|------|
| `\来不及`（特殊中文命令） | 不支持 |
| `\textcite`（biblatex） | 需要额外扩展 |
| `\parbox`, `\mbox` 复杂用法 | 部分支持 |

---

## 三、关键行为差异

### 3.1 Raw TeX 默认行为

Pandoc 默认使用 `-raw_tex`，即：
- Raw LaTeX 代码在转换为非 LaTeX 格式时通常被**忽略**
- 需明确使用 `+raw_tex` 扩展来保留 raw TeX 代码块

```bash
# 保留 raw tex
pandoc input.md -f markdown+raw_tex -t latex -o output.tex
```

### 3.2 宏展开限制

`latex_macros` 扩展的行为：
- ✅ 解析 `\newcommand` 定义并应用到所有 LaTeX math 和 raw LaTeX
- ❌ 不对 `raw_attribute` 标记的 raw span/block 应用宏
- ❌ 不处理复杂宏的完整语义

### 3.3 输出格式影响

| 输出格式 | Inline LaTeX 处理 |
|----------|------------------|
| LaTeX / ConTeXt / Markdown | 保留原始代码 |
| HTML / DOCX / EPUB | 通常被忽略（除非开启对应扩展） |
| PDF（通过 LaTeX 引擎） | 完整支持 |

---

## 四、应对策略

| 场景 | 建议方案 |
|------|---------|
| 保留复杂 LaTeX 代码 | 使用 `+raw_tex` 扩展，让后续 LaTeX 引擎处理 |
| 自定义宏在数学公式中失效 | 开启 `+raw_tex` 并确保 PDF 输出使用 LaTeX 引擎 |
| 复杂数学公式转换到 HTML | 使用 MathJax / KaTeax 渲染器：`--mathjax` 或 `--katex` |
| 不支持的命令导致内容丢失 | 通过 Lua filter 自定义解析逻辑 |
| 表格跨列/跨行丢失 | 先转为 LaTeX 再用 `pdflatex` 处理；或手动拆分为多个表格 |
| LaTeX3 / 特殊宏包命令 | 输出为 LaTeX 格式，不做格式转换 |

```bash
# 推荐：保留 raw tex + MathJax 渲染
pandoc input.tex -f latex+raw_tex --mathjax -o output.html

# 输出为 LaTeX（不做转换，保持原始）
pandoc input.tex -t latex -o output.tex
```

---

## 五、参考链接

- [Pandoc Lua Filters](https://pandoc.org/lua-filters.html)
- [Pandoc Demo - Raw TeX](https://pandoc.org/demo/example9.db)
- [Pandoc Releases - LaTeX Reader Improvements](https://pandoc.org/releases.html)
- [Pandoc Manual - Extensions](https://pandoc.org/demo/MANUAL.txt)
