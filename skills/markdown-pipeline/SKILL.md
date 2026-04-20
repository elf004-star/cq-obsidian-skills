---
name: markdown-pipeline
description: "Orchestrator for long markdown documents: split by minimum-principle first, then process sub-blocks in parallel, finally merge back into single file. Only handles the three steps of split → parallel → merge itself."
---

# Markdown Pipeline

## Position

This skill **only does orchestration**, does not define any content transformation rules. Any work on "remove HTML, wrap math, convert subscript/superscript, merge paragraphs, unify LaTeX commands" etc. is delegated to `plain-markdown-skill`.

Backup naming, user preferences, LaTeX support queries are all determined by the delegated skill per its `user-habits.md`; this file does not repeat them.

## Workflow

```
Input document (single file) → document-splitter → n sub-documents
                            ↓
                    ≤6 markdown-processor (parallel, internally call plain-markdown-skill)
                            ↓
                        markdown-merger → Output document
```

## Operation Steps

### 0. Clear process Directory

Before execution, clear the `process/` subdirectory in the same directory as input (if exists) to avoid residual old files interfering.

### 1. Split

Call `document-splitter` agent:

- **Goal**: Minimum-principle split, default threshold 3600 characters
- Output to `process/` subdirectory in same directory as input
- Internally builds chunks by cumulative character count, not line count

### 2. Parallel Processing (Optimized)

Use **batch parallel** strategy based on number of split sub-documents:

- **Max concurrent agents**: Launch up to 6 `markdown-processor` agents at a time
- **Task allocation rules**:
  - Calculate total sub-document count n
  - Each batch processes up to 6 sub-documents
  - Distribute n sub-documents across up to 6 agents (if n ≤ 6, directly use n agents)
  - After each batch completes, launch next batch (until all sub-documents are processed)
- Each `markdown-processor` internally calls `plain-markdown-skill` for actual conversion
- All conversion rules, backup naming, new pattern confirmation strategy, etc. are handled by `plain-markdown-skill`

### 3. Merge

**Must use script**, manual read-merge is prohibited.

```bash
python ".claude/scripts/merge-scripts/merge_markdown.py" "[process directory path]" "[output file path]"
```

- Script automatically merges in file name numeric prefix order
- Frontmatter kept for first file, removed for others
- Output overwrites original input file

**Fallback**: When script fails, fallback to calling `markdown-merger` agent to merge.

## Invocation Example

```
User input: process doc/01-SECTION-II-A-GENERAL-FORMULA-OF-STATICS.md

Step 1: Call document-splitter
- Input: doc/01-SECTION-II-A-GENERAL-FORMULA-OF-STATICS.md
- Goal: Minimum-principle split (each sub-document ~3600 characters)
- Output: doc/process/01_xxx.md, 02_xxx.md, ..., 0k_xxx.md

Step 2: Parallel processing (Example: 14 sub-documents total)
- Batch 1: Launch 6 markdown-processor, process 01~06
- Batch 2: Launch 6 markdown-processor, process 07~12
- Batch 3: Launch 2 markdown-processor, process 13~14
- Each batch internally calls plain-markdown-skill

Step 3: After all sub-documents processed, call markdown-merger
- Input: All processed files in doc/process/
- Output: Replaces original doc/01-SECTION-II-A-GENERAL-FORMULA-OF-STATICS.md
```

Note: The 3 agents referenced by this skill are all project-level agents, installed in `.claude\agents` folder

## Final Cleanup

**Ask user for consent** before clearing all files in `process/` directory and deleting that directory.

## Error Handling

- Any sub-document processing failure: Report failed file, continue processing others
- Merge failure: Do not replace original file, keep `process/` directory for manual recovery

## Output Language

All interactions with user use **Chinese(中文)**.
