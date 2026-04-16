---
name: pandoc-fixer
description: 自动修复 Pandoc 导出过程中出现的 TeX math 转换错误、格式化不兼容问题，并可选地规范化 LaTeX 公式格式（如移除多余空格、统一 `\frac{}` 写法）。当用户报告 "Could not convert TeX math"、"导出失败" 或请求 "规范化公式" 时触发。内置自我升级模块，可学习并固化新修复规则。
---

# Pandoc Fixer Skill

此技能用于解决从 Markdown 导出到 Docx 时因 LaTeX 语法不规范导致的各类报错，并提供公式规范化功能。

## 执行流程
1. **分析错误**：读取 Pandoc 报错截图或命令行输出中的具体公式片段。
2. **知识库匹配**：读取 `references/knowledge-base.md`，使用已知模式（Patterns）进行比对。
3. **物理修复**：
    - 全角标点（（、）、，、。）转为半角。
    - 替换不兼容的环境（如 `array{c c}` 转换为 `cases`）。
    - 移除不支持的控制符（如 `\hskip`）。
4. **公式规范化**（可选，根据用户需求执行）：
    - 函数名与括号：`f (x)` → `f(x)`
    - 花括号内前导空格：`\frac {1}` → `\frac{1}`
    - 花括号内尾部空格：`\frac{1 }` → `\frac{1}`
    - `\tag{}` 格式：`\tag {3}` → `\tag{3}`
5. **标准化公式排版**：
    - **行间公式 (Block Math)**: 必须独占行，且 `$$` 标记应分别位于公式的首尾独立行。
      格式：
      $$
      [formula]
      $$
    - **行内公式 (Inline Math)**: 需要与前后文本保持一个半角空格的距离，以防止某些 Pandoc 版本将紧连的文字识别为 LaTeX 语法的一部分。
      格式：` 文本 $公式$ 文本 `
6. **验证与升级**：
    - 修复后提醒用户使用 Pandoc 导出确认警告消失。
    - **自我升级**：如果遇到新的错误类型并修复成功，必须将该 `Pattern -> Solution` 对条目追加到 `references/knowledge-base.md`。

## 升级准则
每当发现 `knowledge-base.md` 中缺失的修复逻辑并手动修复成功后，请使用以下格式更新知识库：
- **Problem**: 描述新发现的问题现象。
- **Regex/Pattern**: 用于定位该问题的正则表达式或特征字符串。
- **Fix**: 具体的代码层面修改方案。
