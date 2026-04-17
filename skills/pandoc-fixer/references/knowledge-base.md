# Pandoc Fixer Knowledge Base

此文件由 `pandoc-fixer` 技能维护。用于存储已验证的“报错模式-修复方案”映射。

## 1. 全角字符冲突
- **Problem**: 公式块中混入中文括号或标点导致 `unexpected character`。
- **Solution**: 在数学块内全局执行正则替换：`（` -> `(`, `）` -> `)`, `，` -> `,`。

## 2. Array 环境兼容性
- **Problem**: `array{c c}` 环境在 Docx 导出时常报 `unexpected "c"` 错误。
- **Solution**: 
    - 简单分类讨论：将 `\left\{ \begin{array}{c c} ... \end{array} \right.` 替换为 `\begin{cases} ... \end{cases}`。
    - 矩阵/多行：转为 `aligned` 或标准的数学矩阵环境。

## 3. 不支持的排版命令
- **Problem**: `\hskip`, `\vskip` 等底层排版命令导致 `unexpected control sequence`。
- **Solution**: 直接移除此类命令。

## 4. 下标语法规范
- **Problem**: `approx_ {t r}` 等下标中带有空格，可能导致某些解析器误判。
- **Solution**: 统一格式为 `\approx_{tr}`（移除空格且使用花括号包裹多字符下标）。

## 7. OMML 渲染方框 Bug (求和号/变量冲突)
- **Problem**: 即使代码纯净，Word 内部渲染 `\sum_{j} w` 时仍可能在 $w$ 前出现方框。这是因为 Pandoc 转换 OMML 时对“求和号下标”与“紧随后变量”的物理间距计算溢出。
- **Solution**: 
    - **方法 1 (最有效，但受限)**: 明确写出上下限形式（如 `\sum_{j=1}^{n}`），强制 Word 进入标准的上下限渲染模式。**注意：此方法涉及数学内涵推断，严禁 AI 主动执行。必须作为建议询问并获得用户明确同意后方可应用。**
    - **方法 2 (推荐主动尝试)**: 强行在求和号与变量间插入数学空格 `\,`。此方法不改变数学原意，可作为默认修复手段。

## 9. \text{} 内部字母空格
- **Problem**: `\text{h i d d e n}` 这种在 `\text{}` 内部字母之间加空格的做法是不规范的。
- **Regex/Pattern**: `\\text\{([a-z] )+[a-z]\}` 或更通用的 `([a-z] )([a-z]\})`
- **Fix**: 移除 `\text{}` 内部字母之间的空格，如 `\text{h i d d e n}` -> `\text{hidden}`

## 10. 规范化：函数名与括号之间的空格
- **Problem**: `f (x)`, `\sin (x)` 等写法函数名与括号间有多余空格，不够规范。
- **Regex/Pattern**: `([A-Za-z]) \(` 
- **Fix**: `([A-Za-z]) \(` → `$1(`，移除函数名后多余的空格

## 11. 规范化：花括号内紧贴内容的空格
- **Problem**: `\frac {1}`, `\tag {3}`, `\sqrt {x}` 等写法，花括号内部前面有多余空格。
- **Regex/Pattern**: `\\([a-z]+) \{([^\s}])` 
- **Fix**: `\frac {1}` → `\frac{1}`，移除 `\{` 后紧跟的非空格字符前的空格

## 12. 规范化：花括号内尾部空格
- **Problem**: `\frac{1 }`, `\tag{3 }` 等写法，花括号内部末尾有多余空格。
- **Regex/Pattern**: `\{([^}]+) \}`
- **Fix**: `{1 }` → `{1}`，移除 `}` 前面的空格

## 13. HTML 表格转换为 Markdown 表格
- **Problem**: Obsidian 笔记中残留 `<table><tr><td>...</td></tr></table>` 格式的 HTML 表格，影响 Pandoc 导出的一致性和可读性。
- **Regex/Pattern**: `<table>.*?</table>` 或逐行解析 `<tr>` 和 `<td>`
- **Fix**: 转换为标准 Markdown 表格格式：
  ```markdown
  | col1 | col2 | col3 |
  |------|------|------|
  | val1 | val2 | val3 |
  ```

## 14. 公式排版规范 (Pandoc/Word 最佳实践)
- **Problem**: 紧凑的公式写法在转换为 Docx 时可能导致解析错误或自动编号失败。
- **Solution**:
    - **行间公式 (Block Math)**: 必须独占行，且 `$$` 标记应分别位于公式的首尾独立行。
      格式：
      $$
      [formula]
      $$
    - **行内公式 (Inline Math)**: 需要与前后文本保持一个半角空格的距离，以防止某些 Pandoc 版本将紧连的文字识别为 LaTeX 语法的一部分。
      格式：` 文本 $公式$ 文本 `
