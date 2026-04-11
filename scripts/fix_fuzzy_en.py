# -*- coding: utf-8 -*-
"""Clear fuzzy flags in English catalog; set msgstr to msgid where fuzzy."""
import polib


def main():
    path = "translations/en/LC_MESSAGES/messages.po"
    po = polib.pofile(path)
    fixed = 0
    for entry in po:
        if "fuzzy" not in entry.flags or not entry.msgid:
            continue
        entry.msgstr = entry.msgid
        entry.flags = [f for f in entry.flags if f != "fuzzy"]
        fixed += 1
    po.save(path)
    print(f"Cleared {fixed} fuzzy flags in {path}")


if __name__ == "__main__":
    main()
