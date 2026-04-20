# Claude Skills Wiki

> **Note**: This is the English version. For Chinese documentation, see [README-中文.md](README-中文.md).

A knowledge management skill library based on Obsidian Wiki and Claude Code.

## Core Goal

**mark every-documents down** — Convert all documents into plain-text Markdown, building an AI-friendly knowledge graph.

## Skills

### plain-markdown-skill

Normalizes messy Markdown documents into clean CommonMark/GFM format.

**Features**:
- Auto-removes HTML tags, custom containers, emoji codes
- Converts subscript/superscript, footnotes, paragraph line breaks
- Math formula standardization (LaTeX commands, integral symbols)
- Smart OCR artifact replacement

**Details**: [skills/plain-markdown-skill/SKILL.md](skills/plain-markdown-skill/SKILL.md)

### markdown-pipeline

Orchestrator for long Markdown documents: split → parallel process → merge.

**Flow**:
```
Input → document-splitter → n sub-documents
                    ↓
           ≤6 markdown-processor (parallel)
                    ↓
              markdown-merger → Output
```

**Details**: [skills/markdown-pipeline/SKILL.md](skills/markdown-pipeline/SKILL.md)

## Design Philosophy

### AI-Friendly Knowledge Graph Format

To improve AI comprehension efficiency and save tokens, this repository uses **referential abstraction** for non-text resources:

| Resource Type | Approach |
|--------------|----------|
| Images | Reference to `图片描述.md` |
| Audio | Reference to `.srt.md` |
| Tables/Databases | Reference to `说明书/操作指南.md` |

**Benefits**:
- AI reads descriptions directly without reprocessing images/audio
- Clear knowledge graph structure with explicit relationships
- Reduced tokens, improved processing efficiency

### Image Reference Example

```markdown
![[diagram-architecture.png]]

<!-- Corresponding 图片描述.md -->
## Figure 1: System Architecture

This diagram shows the three layers of microservices architecture...
```

### Audio Reference Example

```markdown
![[lecture-01.srt]]

<!-- Corresponding lecture-01.srt.md -->
## Audio Transcription

00:00 - Introduction
00:30 - Topic explanation...
```

## License

This repository is open-sourced under the MIT License.

**Core terms**:
- Free to use, modify, commercial use allowed
- Must retain attribution and license notice
- No warranty provided

See [LICENSE](LICENSE) for details.

## Acknowledgments

Most skills in this repository come from:
- Obsidian official skills
- Claude official Skill marketplace

Thanks to all open-source contributors.
