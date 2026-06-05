# Anki Flashcard Deck — React Senior Interview Prep

`react-interview-flashcards.csv` — **257 cards** auto-extracted from the **Rapid-Fire** sections of every file in the kit (plus file 21's *"20 You Must Not Fumble"* table).

## What's inside

- **Columns:** `Question, Answer, Tags`
- **Tags** are hierarchical per source file, e.g. `ReactInterview::04-hooks`, `ReactInterview::10-security`. In Anki you can browse/filter by tag, build filtered decks per topic, or study everything at once.
- **Formatting:** HTML is enabled. `inline code` renders as `<code>`, `**bold**` as `<b>`, and literal JSX like `<Link>` is escaped so it shows as text.
- The CSV starts with Anki config directives (`#separator`, `#html`, `#columns`, `#tags column`) so a fresh Anki import auto-maps the fields — no manual column mapping needed.

> ⚠️ A handful of file-14 cards are "complete-the-insight" style (front = first clause + `…`, back = full statement) because that file's Rapid-Fire is declarative one-liners, not Q&A. Everything else is a true question → answer.

## How to import (Anki desktop)

1. **File → Import…** and choose `react-interview-flashcards.csv`.
2. Note type: **Basic** (Front/Back). Anki reads the header directives, so:
   - Field separator → **Comma** (auto)
   - **Allow HTML in fields** → **on** (auto)
   - Column 1 → **Front**, Column 2 → **Back**, Column 3 → **Tags** (auto)
3. Pick/create a deck (e.g. *React Senior Prep*) and click **Import**.
4. (Optional) Make per-topic filtered decks: **Tools → Create Filtered Deck**, search e.g. `tag:ReactInterview::07-performance`.

On **AnkiMobile / AnkiDroid**, import the same file (or sync from desktop via AnkiWeb).

## Card count by source

| Cards | Source file |
|------:|-------------|
| 20 | 01-javascript-core |
| 20 | 02-typescript |
| 12 | 03-react-fundamentals |
| 11 | 04-hooks |
| 8  | 05-rendering-reconciliation |
| 10 | 06-state-management |
| 10 | 07-performance |
| 10 | 08-nextjs |
| 10 | 09-testing |
| 10 | 10-security |
| 10 | 11-accessibility |
| 7  | 12-system-design |
| 15 | 13-senior-interview |
| 20 | 14-react-patterns |
| 10 | 15-data-fetching |
| 10 | 16-routing |
| 10 | 17-frontend-architecture |
| 10 | 18-browser-internals |
| 10 | 19-build-tools-bundlers |
| 14 | 20-cicd |
| 20 | 21-common-interview-questions (incl. "20 You Must Not Fumble") |
| **257** | **total** |

## Regenerating

The deck is reproducible. After editing any Rapid-Fire section, rebuild with:

```bash
python3 build_deck.py
```

`build_deck.py` re-parses all `NN-*.md` files, de-dupes identical Q/A pairs, and rewrites the CSV.
