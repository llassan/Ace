#!/usr/bin/env python3
"""Extract Rapid-Fire Q&A (and file 21's '20 You Must Not Fumble' table) from the
React interview kit and emit an Anki-importable CSV.

Handles four source shapes:
  A. **Q: question?**            (answer on following line(s), optional "A:" prefix)
  B. - **question?** — answer    (single-line bullet)
  C. N. **question?** answer     (numbered, bold question + inline answer)
  D. - question? answer.         (plain bullet, split on first '?')
  E. N. declarative statement.   (no question -> 'complete-the-insight' recall card)
  F. file 21 markdown table:  | # | Question | One-line answer |

Output columns: Question, Answer, Tags  (Tags = ReactInterview::<file-slug>)
HTML enabled: content is HTML-escaped, then `code` -> <code>, **bold** -> <b>.
"""
import csv
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "react-interview-flashcards.csv"

BOLDQ = re.compile(r"^\*\*(.+?)\*\*\s*(.*)$")

def md_to_html(text: str) -> str:
    text = html.escape(text.strip())
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text.strip()

def clean_q(q: str) -> str:
    return re.sub(r"^Q[:.]\s*", "", q.strip()).strip()

def strip_sep(s: str) -> str:
    return re.sub(r"^[\s—–:\-]+", "", s).strip()

def strip_a(s: str) -> str:
    return re.sub(r"^A[:.]\s*", "", strip_sep(s)).strip()

def statement_card(text: str):
    """Turn a declarative one-liner into a 'complete the insight' recall card."""
    text = text.strip()
    for sep in [";", " — ", "—", ": "]:
        if sep in text:
            head = text.split(sep, 1)[0].strip()
            return (head + " …", text)
    words = text.split()
    head = " ".join(words[:6])
    return (head + " …", text)

def rapidfire_items(md: str):
    """Yield items (lists of lines) from the Rapid-Fire section."""
    capturing, block = False, []
    for ln in md.splitlines():
        st = ln.strip()
        if st.startswith("## ") and "Rapid-Fire" in st:
            capturing = True
            continue
        if capturing and st.startswith("## "):
            break
        if capturing:
            block.append(ln)

    items, cur = [], None
    for raw in block:
        s = raw.strip()
        if not s or s == "---":
            continue
        mnum = re.match(r"^\d+\.\s+(.*)$", s)
        mbul = re.match(r"^[-*]\s+(.*)$", s)
        if mnum:
            if cur:
                items.append(cur)
            cur = [mnum.group(1)]
        elif mbul:
            if cur:
                items.append(cur)
            cur = [mbul.group(1)]
        elif s.startswith("**"):
            if cur:
                items.append(cur)
            cur = [s]
        elif cur is not None:
            cur.append(s)          # answer continuation (format A)
        # else: intro prose before the first item -> ignore
    if cur:
        items.append(cur)
    return items

def parse_rapidfire(md: str):
    cards = []
    for item in rapidfire_items(md):
        first, rest = item[0], item[1:]
        if first.startswith("**"):                       # shapes A / B / C
            m = BOLDQ.match(first)
            if not m:
                continue
            q = clean_q(m.group(1))
            inline = strip_a(m.group(2))
            parts = ([inline] if inline else []) + [strip_a(x) for x in rest]
            a = " ".join(p for p in parts if p).strip()
            if q and a:
                cards.append((q, a))
            continue
        full = " ".join([first] + rest).strip()
        if "?" in full:                                  # shape D
            qpart, apart = full.split("?", 1)
            q, a = clean_q(qpart + "?"), strip_a(apart)
            cards.append((q, a) if a else statement_card(full))
        else:                                            # shape E
            cards.append(statement_card(full))
    return cards

def parse_must_not_fumble(md: str):                      # shape F
    cards, capturing = [], False
    for ln in md.splitlines():
        st = ln.strip()
        if st.startswith("## ") and "Must Not Fumble" in st:
            capturing = True
            continue
        if capturing and st.startswith("## "):
            break
        if capturing and st.startswith("|"):
            cells = [c.strip() for c in st.strip("|").split("|")]
            if len(cells) >= 3 and cells[0].isdigit():
                q = cells[1] if cells[1].endswith("?") else cells[1]
                cards.append((q, cells[2]))
    return cards

rows, per_file = [], {}
for md_path in sorted(ROOT.glob("[0-9][0-9]-*.md")):
    slug = md_path.stem
    text = md_path.read_text(encoding="utf-8")
    cards = parse_rapidfire(text)
    if slug == "21-common-interview-questions":
        cards += parse_must_not_fumble(text)
    per_file[slug] = len(cards)
    for q, a in cards:
        rows.append((md_to_html(q), md_to_html(a), f"ReactInterview::{slug}"))

seen, deduped = set(), []
for r in rows:
    if (r[0], r[1]) in seen:
        continue
    seen.add((r[0], r[1]))
    deduped.append(r)

with OUT.open("w", encoding="utf-8", newline="") as f:
    f.write("#separator:Comma\n#html:true\n#columns:Question,Answer,Tags\n#tags column:3\n")
    w = csv.writer(f, quoting=csv.QUOTE_ALL)
    w.writerows(deduped)

print(f"Wrote {len(deduped)} cards -> {OUT}  (deduped {len(rows) - len(deduped)})")
for k in sorted(per_file):
    print(f"  {per_file[k]:>3}  {k}")
