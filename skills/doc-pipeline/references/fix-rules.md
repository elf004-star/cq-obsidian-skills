# 修复规则参考

本文档定义了 doc-pipeline 中公式格式的详细修复规则。

---

## 规则 1: 字母间空格移除

### 问题描述

LaTeX 中多字母变量（如 `net`）常被错误地写成带空格的 `n e t`。

### 修复模式

| 修复前 | 修复后 | 备注 |
|--------|--------|------|
| `n e t` | `\operatorname{net}` | 使用 \operatorname 更规范 |
| `n e t _{i}` | `\operatorname{net}_{i}` | 下标保持 |
| `y ^{i}` | `y^{i}` | 移除上标空格 |
| `w _{i u}` | `w_{iu}` | 合并下标 |
| `f _{i}` | `f_{i}` | 函数名下标 |
| `g ^{\prime}` | `g^{\prime}` | 导数符号 |

### 特殊情况

- **行内公式中的 `net`**：如 `net_{k}(t)` 保持原样
- **已经是 `\operatorname{net}`**：无需修改
- ** `\text{}` 内部**：不适用，text 内部按文本处理

---

## 规则 2: 下标配对合并

### 问题描述

复杂下标被错误地写成多层分散的形式。

### 修复模式

| 修复前 | 修复后 |
|--------|--------|
| `_{i n _{j}}` | `_{in_j}` |
| `_{c _{j} ^{v}}` | `_{c_j^v}` |
| `^{i n _{j}}` | `^{in_j}` |
| `^{o u t _{j}}` | `^{out_j}` |
| `^{c _{j}}` | `^{c_j}` |
| `s _{c _{j}}` | `s_{c_j}` |
| `\vartheta_{s _{c _{j}}}` | `\vartheta_{s_{c_j}}` |

### 嵌套下标原则

- 先合并最内层：`_{c _{j}}` → `_{c_j}`
- 再合并外层：`_{c_j ^{v}}` → `_{c_j^v}`

---

## 规则 3: \frac 格式统一

### 问题描述

偏导数和分式格式不统一。

### 修复模式

| 修复前 | 修复后 |
|--------|--------|
| `\frac {\partial}{\partial}` | `\frac{\partial}{\partial}` |
| `\frac {x}{y}` | `\frac{x}{y}` |
| `\frac {\partial y}{\partial x}` | `\frac{\partial y}{\partial x}` |

### 特殊情况

- **多行 \frac**：保持换行，不合并
- **嵌套分式**：保持结构，只修格式

---

## 规则 4: \text{} 可读性

### 问题描述

`\text{}` 内部的文本应该保持可读性。

### 修复模式

| 修复前 | 修复后 | 说明 |
|--------|--------|------|
| `\text{hiddenunit}` | `\text{hidden unit}` | 单词间加空格 |
| `\text{notagate}` | `\text{not a gate}` | 保持词义 |
| `\text{outputunit}` | `\text{output unit}` | 单词分隔 |
| `\text{inputgates}` | `\text{input gates}` | 单词分隔 |
| `\text{memorycells}` | `\text{memory cells}` | 单词分隔 |
| `\text{nogateandnomemorycell}` | `\text{no gate and no memory cell}` | 完整句子 |

### 注意事项

- **简单下标 vs 文本**：如 `\text{out}_j` 应改为 `out_j`（简单下标不需要 text）
- **变量名 vs 文本**：`\text{net}` 在某些情况下是合理的（如表示文本 "net"）

---

## 规则 5: 括号间距

### 问题描述

括号内外的空格处理不当。

### 修复模式

| 修复前 | 修复后 | 说明 |
|--------|--------|------|
| `\left( expr \right)` | `\left(expr\right)` | 移除内部空格 |
| `\left( net_{i}(t) \right)` | `\left(\operatorname{net}_{i}(t)\right)` | 结合规则1 |
| `f \left( x \right)` | `f\!\left(x\right)` | 收紧函数与括号 |

### 间距命令参考

| 命令 | 效果 |
|------|------|
| `\,` | thin space (3/18 quad) |
| `\:` | medium space (4/18 quad) |
| `\;` | thick space (5/18 quad) |
| `\!` | negative thin space |
| `\quad` | 1 em space |
| `\qquad` | 2 em space |

### 常见应用

```
y^{in_j}(t)\,g\!\left(\operatorname{net}_{c_j^v}(t)\right)
```

---

## 规则 6: 导数符号

### 修复模式

| 修复前 | 修复后 |
|--------|--------|
| `^{\prime}` | `^{\prime}` 或 `'` |
| `g ^{\prime}` | `g^{\prime}` |
| `f ^{\prime}` | `f^{\prime}` |
| `h ^{\prime}` | `h^{\prime}` |
| `^{\prime}\!\left(` | `^{\prime}\!\left(` |

### 特殊符号

| 符号 | 用途 |
|------|------|
| `^{\prime}` | 一阶导数 |
| `^{\prime\prime}` | 二阶导数 |
| `^{(n)}` | n 阶导数 |

---

## 规则 7: \operatorname 使用规范

### 适用场景

多字母运算符应使用 `\operatorname`：

| 场景 | 错误 | 正确 |
|------|------|------|
| net 输入 | `n e t` | `\operatorname{net}` |
| 无穷 | `i n f` | `\operatorname{inf}` |
| 最大/最小 | `m a x` / `m i n` | `\max` / `\min` |

### 已有命令

这些命令已定义，无需 `\operatorname`：
- `\log`, `\sin`, `\cos`, `\tan`
- `\max`, `\min`, `\sup`, `\inf`
- `\det`, `\deg`, `\dim`, `\exp`
- `\lim`

---

## 规则 8: 时间参数格式

### 修复模式

| 修复前 | 修复后 |
|--------|--------|
| `( t - 1 )` | `(t-1)` |
| `( t + 1 )` | `(t+1)` |
| `(t - k)` | `(t-k)` |
| `(t - k - 1)` | `(t-k-1)` |

### 特殊情况

- `\quad =` 保持：`\quad =` 用于公式对齐
- `\tag{10}` 保持原样

---

## 规则 9: 矩阵/cases 环境

### 来自 pandoc-fixer

来自 `pandoc-fixer` 的知识库：

| 问题 | 修复 |
|------|------|
| `\begin{array}{c c}` | 替换为 `\begin{cases}...\end{cases}` |
| `\begin{array}{l}` | 替换为 `\begin{aligned}...\end{aligned}` |
| `\end{array}` | 对应替换 |

---

## 规则 10: 特殊符号

### \approx_{tr} 格式

| 修复前 | 修复后 |
|--------|--------|
| `\approx_{t r}` | `\approx_{tr}` |
| `\approx_{t r} 0` | `\approx_{tr} 0` |
| `\approx_{tr} 0 \forall` | `\approx_{tr} 0 \quad \forall` |

### \forall 符号

| 修复前 | 修复后 |
|--------|--------|
| `0 \forall u` | `0 \quad \forall u` |
| `0 \forall u,` | `0 \quad \forall u,` |

---

## 规则 11: 禁止修改的内容

以下内容**不应修改**：

| 类型 | 示例 | 说明 |
|------|------|------|
| 行内公式变量 | `$k$`, `$i$` | 普通行内公式 |
| 行内公式语义 | `$\frac{a}{b}$` | 保持原样 |
| 文本内容 | 段落文字 | 不修改 |
| Markdown 格式 | `#`, `##`, `**` | 不修改 |
| Wiki-links | `[[note]]` | 不修改 |
| 代码块 | ` ``` ` | 不修改 |

---

## 规则 12: 函数名与括号间距

### 问题描述

函数名与括号之间的多余空格导致格式不统一。

### 修复模式

| 修复前 | 修复后 |
|--------|--------|
| `f (x)` | `f(x)` |
| `\sin (x)` | `\sin(x)` |
| `\exp (- x)` | `\exp(-x)` |
| `g (x)` | `g(x)` |
| `h (s_{c_j^v}(t))` | `h(s_{c_j^v}(t))` |

### 注意事项

- 保留必要的数学间距命令：`\,`, `\!`, `\,`
- 如 `f\!\left(x\right)` 中的 `\!` 用于收紧间距，应保留

---

## 规则 13: 常见错误修正

### 错误示例与修正

| 行号 | 错误内容 | 修正为 |
|------|----------|--------|
| 123 | `g^{prime}!\left(` | `g^{\prime}\!\left(` |
| 456 | `net_{c_j}` | `\operatorname{net}_{c_j}` |
| 789 | `\delta_{c_j^{vl}}` | `\delta_{c_j^v l}` 或核实意图 |

### 语法错误检测

- 未闭合的 `\left(`
- 未闭合的 `{` 或 `}`
- 未匹配的 `\begin{...}/\end{...}`
