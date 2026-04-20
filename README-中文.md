# Claude Skills Wiki

一个基于 Obsidian Wiki 和 Claude Code 的知识管理技能库。

## 核心目标

**mark every-documents down** —— 将所有文档转为纯文本 Markdown 保存，构建 AI 可高效理解的知识图谱。

## 技能库

### plain-markdown-skill

将任意杂乱的 Markdown 文档规范化为 CommonMark/GFM 纯文本格式。

**功能**：
- 自动删除 HTML 标签、自定义容器、emoji 代码
- 转换上下标、脚注、段落错行等格式问题
- 数学公式标准化（LaTeX 命令统一、积分符号规范化）
- OCR 乱码智能替换

**详情**：[skills/plain-markdown-skill/SKILL.md](skills/plain-markdown-skill/SKILL.md)

### markdown-pipeline

长 Markdown 文档的编排器：先拆分、再并行处理、最后合并。

**流程**：
```
输入文档 → document-splitter → n 个子文档
                    ↓
           ≤6 个 markdown-processor（并行）
                    ↓
              markdown-merger → 输出文档
```

**详情**：[skills/markdown-pipeline/SKILL.md](skills/markdown-pipeline/SKILL.md)

## 设计理念

### 知识图谱的 AI 友好格式

为提高 AI 理解效率、节省 tokens，本仓库对非文本资源采用**引用式抽象**：

| 资源类型 | 处理方式 |
|---------|---------|
| 图片 | 引用到 `图片描述.md` |
| 音频 | 引用到 `.srt.md` |
| 表格/数据库 | 引用到 `说明书/操作指南.md` |

**优势**：
- AI 无需重复识别图片/音频，可直接读取描述
- 知识图谱结构清晰，关联明确
- 节省 tokens，提高处理效率

### 图片引用示例

```markdown
![[diagram-architecture.png]]

<!-- 对应图片描述.md -->
## 图 1：系统架构图

该图展示了微服务架构的三个层次...
```

### 音频引用示例

```markdown
![[lecture-01.srt]]

<!-- 对应 lecture-01.srt.md -->
## 音频转录文本

00:00 - 开场介绍
00:30 - 主题阐述...
```

## 许可证

本仓库基于 MIT 许可证开源。

**核心约束**：
- 可自由使用、修改、商业使用
- 必须保留署名和许可证声明
- 不承担任何担保责任

详见 [LICENSE](LICENSE) 文档。

## 致谢

本仓库大部分技能来自：
- Obsidian 官方技能库
- Claude 官方 Skill 市场

在此感谢所有开源贡献者。
