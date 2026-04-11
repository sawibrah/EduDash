# -*- coding: utf-8 -*-
"""
Report French translation gaps in translations/fr/LC_MESSAGES/messages.po.

Checks:
  - msgstr empty or exactly equal to msgid (Babel treats these as untranslated)
  - fuzzy flags

Usage (from repo root):
  python scripts/fr_translation_audit.py
  python scripts/fr_translation_audit.py --write translations/audit_fr_last_run.txt
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import polib
except ImportError:
    print("Install polib: pip install polib", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
FR_PO = ROOT / "translations/fr/LC_MESSAGES/messages.po"


def audit() -> tuple[list[polib.POEntry], list[polib.POEntry]]:
    po = polib.pofile(str(FR_PO))
    identical: list[polib.POEntry] = []
    fuzzy: list[polib.POEntry] = []
    for entry in po:
        if entry.obsolete or not entry.msgid:
            continue
        if "fuzzy" in entry.flags:
            fuzzy.append(entry)
        if not entry.msgstr or entry.msgstr == entry.msgid:
            identical.append(entry)
    return identical, fuzzy


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit French gettext catalog.")
    parser.add_argument(
        "--write",
        metavar="FILE",
        help="Write full report to this path (UTF-8).",
    )
    args = parser.parse_args()

    identical, fuzzy = audit()
    lines: list[str] = []
    lines.append(f"# French translation audit ({datetime.now(timezone.utc).isoformat()})")
    lines.append(f"# Catalog: {FR_PO.relative_to(ROOT)}")
    lines.append("")
    lines.append(f"Fuzzy entries: {len(fuzzy)}")
    lines.append(f'Entries with msgstr empty or msgstr == msgid: {len(identical)}')
    lines.append("")
    lines.append("--- msgstr equals msgid (or empty) ---")
    for e in sorted(identical, key=lambda x: x.msgid):
        occ = ", ".join(f"{fn}:{ln}" for fn, ln in e.occurrences[:5])
        if len(e.occurrences) > 5:
            occ += ", …"
        lines.append(f"msgid: {e.msgid!r}")
        lines.append(f"refs:  {occ or '(no file refs)'}")
        lines.append("")

    lines.append(
        "# Note: Identical msgstr/msgid is normal for cognates (Description, Question), "
        "abbreviations (min, pts, PDF), and UI loanwords (Quiz, Actions). "
        "Change msgstr only if you want distinct French wording."
    )

    text = "\n".join(lines)
    print(text)
    if args.write:
        out = Path(args.write)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"\nWrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
