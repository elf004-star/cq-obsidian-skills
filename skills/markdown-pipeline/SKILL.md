---
name: markdown-pipeline
description: ""
  长 markdown 文档的编排器：先按“最小原则拆分”切块，再并行处理子块，最后合并回单文件。 只负责拆分—并行—合并这三步本身。触发条件：用户明确要求"拆分并行处理 markdown 文档"；短文档不经本技能。
---

# Markdown Pipeline

## 定位

本技能**只做编排**，不定义任何内容转换规则。任何关于"去 HTML、包数学、转上下标、合并段落、统一 LaTeX 命令"等内容处理工作，全部委托给 `plain-markdown-skill`。

备份命名、用户偏好、LaTeX 支持查询等均由被委托的技能按其 `user-habits.md` 决定，本文件不再复述。

## 工作流程

```
输入文档（单个文档） → document-splitter → n 个子文档
                            ↓
                    ≤6 个 markdown-processor（并行，内部调用 plain-markdown-skill）
                            ↓
                        markdown-merger → 输出文档
```

## 操作步骤

### 0. 清空 process 目录

执行前先清空输入同目录的 `process/` 子目录（如果存在），避免残留旧文件干扰。

### 1. 拆分

调用 `document-splitter` agent：

- **目标**：最小原则拆分，默认阈值 3600 字符
- 输出到与输入同目录的 `process/` 子目录
- 内部按累积字符数而非行数构建 chunks

### 2. 并行处理（优化版）

根据拆分后子文档数量，采用**分批并行**策略：

- **最大并发代理数**：每次最多派出 6 个 `markdown-processor` agent
- **任务分配规则**：
  - 计算子文档总数 n
  - 每批最多处理 6 个子文档
  - 将 n 个子文档平均分配给最多 6 个代理（若 n ≤ 6，则直接使用 n 个代理）
  - 每批处理完成后，再启动下一批（直到所有子文档处理完毕）
- 每个 `markdown-processor` 内部调用 `plain-markdown-skill` 完成实际转换
- 所有转换规则、备份命名、新模式询问策略等，一律由 `plain-markdown-skill` 负责

### 3. 合并

调用 `markdown-merger` agent：

- 按文件名数字前缀顺序合并
- 输出覆盖原始输入文件
- frontmatter 保留第一个文件的，其余文件的 frontmatter 移除

## 调用示例

```
用户输入：处理 doc/01-SECTION-II-A-GENERAL-FORMULA-OF-STATICS.md

步骤 1：调用 document-splitter
- 输入：doc/01-SECTION-II-A-GENERAL-FORMULA-OF-STATICS.md
- 目标：最小原则拆分（每个子文档约 3600 字符）
- 输出：doc/process/01_xxx.md, 02_xxx.md, ..., 0k_xxx.md

步骤 2：并行处理（示例：共 14 个子文档）
- 第一批：派出 6 个 markdown-processor，处理 01~06
- 第二批：派出 6 个 markdown-processor，处理 07~12
- 第三批：派出 2 个 markdown-processor，处理 13~14
- 每批内部均调用 plain-markdown-skill

步骤 3：所有子文档处理完成后，调用 markdown-merger
- 输入：doc/process/ 目录下所有处理后的文件
- 输出：替换原始 doc/01-SECTION-II-A-GENERAL-FORMULA-OF-STATICS.md
```

## 最终清理

**在询问用户同意后**，再清除 `process/` 目录中的所有文件，并删除该目录。

## 错误处理

- 任意子文档处理失败：报告失败文件，继续处理其他文件
- 合并失败：不替换原文件，保留 `process/` 目录供手动恢复