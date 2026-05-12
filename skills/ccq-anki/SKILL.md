---
name: ccq-anki
description: Create and manage Anki flashcards. Use when the user wants to create flashcards, add notes to Anki, manage decks, or work with spaced repetition learning. Also use when user mentions "anki", "make cards", "add to anki", "learn this", "memorize", "remember this", "SRS", or asks to turn content into flashcards.
---

# Anki Flashcard Management

Use `anki.sh` to talk to AnkiConnect. Requires `curl` and `jq` on PATH, and
Anki desktop running with the AnkiConnect add-on enabled.

```bash
ANKI="$(dirname "$SKILL_PATH")/scripts/anki.sh"
```

On Windows run from **Git Bash** (`C:\Program Files\Git\bin\bash.exe`), not
WSL — WSL cannot reach the Windows host's `localhost:8765`.

## Preflight (REQUIRED, in this order)

```bash
$ANKI sync                                  # 1. AnkiConnect reachable
$ANKI models | jq 'index("Anki Markdown")'  # 2. required note type installed (non-null)
$ANKI fields "Anki Markdown"                # 3. confirm fields are ["Front","Back"]
$ANKI decks  | jq 'has("<TargetDeck>")'     # 4. target deck exists (true)
```

If `Anki Markdown` / `Anki Markdown Cloze` is missing, **stop and ask the
user to install that note type**. The formatting rules below depend on its
markdown template — do NOT silently fall back to another model (e.g. the
localized built-ins `问答题` / `填空题` / `图片遮盖`), the cards will look
wrong or fail to create.

## CRITICAL: User Approval

NEVER add / update / delete / rate cards without explicit user approval.

1. Print every proposed card in full (front + back, exactly as it will be stored)
2. Ask: "Ready to add these cards?"
3. Proceed only on explicit "yes"

For `delete` / `update` / `rate`: confirm IDs and the exact change first.

## Note Types

| Use case                              | Model                 | Fields           |
| ------------------------------------- | --------------------- | ---------------- |
| Question/answer (you write the Q)     | `Anki Markdown`       | `Front`, `Back`  |
| Fill-in-the-blank (hide part of text) | `Anki Markdown Cloze` | `Text`, `Extra`  |

Both fields are full markdown.

## Cloze Syntax

- `{{c1::answer}}` — front shows `[...]`
- `{{c1::answer::hint}}` — front shows `[hint]`
- `{{c1::answer::blur}}` — front shows blurred shape
- Different numbers (`c1`, `c2`, ...) → separate cards from the same note
- Same number repeated → all hidden together on one card
- Nested allowed: `{{c1::Canberra was {{c2::founded}}}} in 1913.`
- Inline code inside cloze: `` `{{c1::`code`{js}}}` `` — note the triple `}}}`
  (one closes `{js}`, two close the cloze)

`Extra` appears on the back of every cloze card; use it for context.

## Card Quality

- One atomic fact per card; exactly one unambiguous answer
- Front: short, specific question; bold or `==highlight==` the term being tested
- Back: **bold one-liner answer**, blank line, optional context
- Multiple cards from different angles for important concepts; avoid orphan facts
- Always tag code blocks with a language

## Markdown Conventions (rendered by `Anki Markdown` template)

- `**bold**` for critical concepts, `==highlight==` for skimmable key terms
- `<kbd>Cmd</kbd>+<kbd>K</kbd>` for keyboard shortcuts
- Fenced ` ```lang ` for code blocks; inline `` `code`{lang} ``
- GitHub callouts (use sparingly): `> [!TIP]`, `> [!NOTE]`, `> [!WARNING]`

Example back:

```
**Invokes the ==vertex shader== 3 times.**

The shader uses `@builtin(vertex_index)`{wgsl} to generate positions ==procedurally==.

> [!TIP]
> Useful for fullscreen quads without geometry data.
```

## Commands

| Action     | Example                                                                |
| ---------- | ---------------------------------------------------------------------- |
| `sync`     | `$ANKI sync`                                                           |
| `decks`    | `$ANKI decks --stats`                                                  |
| `models`   | `$ANKI models`                                                         |
| `fields`   | `$ANKI fields "Anki Markdown"`                                         |
| `find`     | `$ANKI find "deck:MyDeck Front:HTML"`                                  |
| `info`     | `$ANKI info 1234 5678`                                                 |
| `add`      | `$ANKI add "MyDeck" "Anki Markdown" "$fields_json" --tags "t1 t2"`     |
| `add-bulk` | `$ANKI add-bulk "MyDeck" "Anki Markdown" "$notes_json" --tags "t1 t2"` |
| `update`   | `$ANKI update 1234 "$fields_json"`                                     |
| `delete`   | `$ANKI delete 1234 5678`                                               |
| `due`      | `$ANKI due "MyDeck" --limit 5`                                         |
| `review`   | `$ANKI review 1234`                                                    |
| `rate`     | `$ANKI rate 1234 3`                                                    |
| `tags`     | `$ANKI tags --pattern verb`                                            |

## Build JSON Safely — always use `jq -n`

Hand-concatenated JSON breaks on quotes, backslashes, newlines and Unicode.
Build the field map / note array with `jq -n --arg`, never with shell string
interpolation:

```bash
# One note
fields=$(jq -n \
  --arg f 'What does `passEncoder.draw(3)`{js} do?' \
  --arg b '**Invokes the ==vertex shader== 3 times.**' \
  '{Front:$f, Back:$b}')
$ANKI add "MyDeck" "Anki Markdown" "$fields" --tags "wgsl"

# Many notes — preferred for >1 card (one HTTP round-trip)
notes=$(jq -n '[
  {Front:"What is **HTML**?", Back:"**HyperText Markup Language**"},
  {Front:"What is **CSS**?",  Back:"**Cascading Style Sheets**"},
  {Front:"What is **JS**?",   Back:"**JavaScript**, a scripting language"}
]')
$ANKI add-bulk "MyDeck" "Anki Markdown" "$notes" --tags "web basics"
```

`add-bulk` returns a JSON array of new note IDs; entries are `null` for
duplicates that were skipped.

Cloze example — same pattern, different model and fields:

```bash
text=$(jq -n --arg t 'The {{c1::CPU}} executes {{c2::instructions}}.' \
              --arg e 'Basic computer architecture.' \
              '{Text:$t, Extra:$e}')
$ANKI add "MyDeck" "Anki Markdown Cloze" "$text" --tags "cs"
```

## Recommended Workflow

```bash
$ANKI sync                                  # 1
$ANKI models | jq 'index("Anki Markdown")'  # 2 verify model
$ANKI fields "Anki Markdown"                # 3 verify fields
$ANKI decks  | jq 'has("MyDeck")'           # 4 verify deck
$ANKI find   "deck:MyDeck Front:HTML"       # 5 dedupe
notes=$(jq -n '[ ... ]')                    # 6 build payload with jq -n
# 7 print full cards; await explicit user approval
$ANKI add-bulk "MyDeck" "Anki Markdown" "$notes" --tags "..."
$ANKI sync                                  # 8
```

## Implementation Notes

- `invoke()` posts the body via `curl --data-binary @-` (stdin), not
  `-d "$body"`. This is intentional: on Git Bash / MSYS2 (Windows) non-ASCII
  argv is re-encoded to the system codepage (e.g. GBK), corrupting deck /
  tag / field names before they reach AnkiConnect. Don't revert this.
- Regression tests: `bash skills/anki/tests/test_anki.sh` (creates and
  cleans up a temporary `_anki_regression_测试_<pid>` deck).
