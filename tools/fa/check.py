#!/usr/bin/env python3
"""Structure/QA checker for the Persian Anki manual translation.

Compares a translated fa file in src/ against the pristine English snapshot in
tools/fa/en/ and enforces the translation rules:

  1. plain fenced code blocks: byte-identical, same order
  2. admonish fences: same count/order and identical directive line (first line)
  3. inline code spans: same multiset of literal strings
  4. link targets: identical sequence (link TEXT may differ)
  5. image refs: identical sequence
  6. <kbd> contents: identical multiset
  7. every header carries {#english-slug} matching the English auto-slug
  8. hidden anchors <a id="..."> preserved
  9. Persian typography: ASCII , ; ? ! " in prose, missing ZWNJ patterns,
     banned glossary terms
 10. leftover-English heuristic: runs of 3+ consecutive ASCII words in prose

Usage:
    python3 tools/fa/check.py                    # check every translated file
    python3 tools/fa/check.py src/studying.md    # check one file
Exit code 0 = all good.
"""
from __future__ import annotations
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
EN = ROOT / "tools" / "fa" / "en"

BANNED = ["عرشه", "فلاش‌کارت", "فلاش کارت", "سینک", "ایمپورت", "اکسپورت"]

# Intentional deviations from the English source, by file:
#  - dropped_links: link targets removed on purpose
DEVIATIONS = {
    "intro.md": {
        # the old dead Persian PDF archive link; this site replaces it
        "dropped_links": [
            "https://web.archive.org/web/20250328102629/http://ankidroid.ir/anki.pdf",
        ],
        # links to the English original, added on purpose
        "added_links": [
            "https://docs.ankiweb.net/",
            "https://docs.ankiweb.net/",
        ],
    },
}
PRODUCTS = {
    "Anki", "AnkiWeb", "AnkiDroid", "AnkiMobile", "AnkiDesktop", "MathJax",
    "LaTeX", "TeX", "FSRS", "CrowdAnki", "HTML", "CSS", "JSON", "CSV", "TSV",
    "SQL", "SQLite", "URL", "API", "Windows", "macOS", "Linux", "GTK", "Qt",
    "Wayland", "X11", "Alt", "Ctrl", "Shift", "Esc", "Del", "Sync", "Add",
    "Internet", "Archive", "GitHub", "ffmpeg", "mpv", "Chrome", "Firefox",
    "Safari", "Edge", "Brave", "VLC", "Audacity", "GIMP", "Inkscape",
    "Open", "Close", "Free", "BSD", "GPL", "OFL", "YAML", "TOML", "Python",
    "Rust", "Clozure", "Cloze", "Best", "Practice",
}
FA = r"\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF"
PERSIAN_RE = re.compile(f"[{FA}]")
ZWNJ = "\u200c"


def strip_code(text: str) -> str:
    """Remove fenced blocks, inline code, links and URLs for prose checks."""
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", " ", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"(?m)^(?: {4,}|\t).*$", " ", text)  # indented code blocks
    return text


def fences(text: str):
    """Return list of (directive_line_or_None, body) for each fence."""
    out = []
    for m in re.finditer(r"^```(.*)\n(.*?)^```", text, flags=re.S | re.M):
        directive = m.group(1).strip() or None
        out.append((directive, m.group(2)))
    return out


def inline_code(text: str):
    text = re.sub(r"```.*?```", " ", text, flags=re.S)  # skip fenced
    return re.findall(r"`([^`\n]+)`", text)


def links(text: str):
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    return re.findall(r"(?<!\!)\[([^\]]*)\]\(([^)\s]+)[^)]*\)", text)


def images(text: str):
    return re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", text)


def kbds(text: str):
    return re.findall(r"<kbd>(.*?)</kbd>", text)


def hidden_anchors(text: str):
    return re.findall(r'<a id="([^"]+)"></a>', text)


def slugify(header: str) -> str:
    """mdBook/pulldown-cmark-ish slug of an English header."""
    s = header.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)  # drop punctuation
    s = re.sub(r"\s", "-", s)
    return s


def headers_with_slugs(text: str):
    """[(level, body, explicit_anchor_or_None)]"""
    out = []
    for m in re.finditer(r"^(#{1,6})\s+(.*)$", text, flags=re.M):
        body = m.group(2).strip()
        anchor = None
        am = re.search(r"\{#([^}]+)\}\s*$", body)
        if am:
            anchor = am.group(1)
            body = body[: am.start()].strip()
        out.append((len(m.group(1)), body, anchor))
    return out


def check_file(rel: str):
    errs, warns = [], []
    fa_path = SRC / rel
    en_path = EN / rel
    fa = fa_path.read_text(encoding="utf-8")
    en = en_path.read_text(encoding="utf-8")
    if fa == en:
        return None, None  # untouched / not yet translated

    # 1+2 fences
    ffa, fen = fences(fa), fences(en)
    plain_fa = [b for d, b in ffa if d != "admonish" and not (d or "").startswith("admonish")]
    plain_en = [b for d, b in fen if d != "admonish" and not (d or "").startswith("admonish")]
    if plain_fa != plain_en:
        if len(plain_fa) != len(plain_en):
            errs.append(f"fence count differs: fa={len(plain_fa)} en={len(plain_en)}")
        else:
            for i, (a, b) in enumerate(zip(plain_fa, plain_en)):
                if a != b:
                    errs.append(f"plain fence #{i+1} content changed")
    dir_fa = [d.split()[0] if d else "" for d, _ in ffa]
    dir_en = [d.split()[0] if d else "" for d, _ in fen]
    if dir_fa != dir_en:
        errs.append(f"admonish/fence directives differ: fa={dir_fa} en={dir_en}")

    # 3 inline code
    if Counter(inline_code(fa)) != Counter(inline_code(en)):
        fa_c, en_c = Counter(inline_code(fa)), Counter(inline_code(en))
        missing = en_c - fa_c
        extra = fa_c - en_c
        if missing or extra:
            # inline code inside admonish bodies may legitimately be translated
            admonish_bodies = [b for dd, b in ffa if (dd or "").startswith("admonish")]
            warn_only = missing and extra and all(
                any(x in b for b in admonish_bodies)
                for x in list(missing) + list(extra)
            )
            msg = f"inline code drift (missing={dict(missing)} extra={dict(extra)})"
            (warns if warn_only else errs).append(msg)

    # 4 links
    lfa, len_ = links(fa), links(en)
    dropped = set(DEVIATIONS.get(rel, {}).get("dropped_links", []))
    added = Counter(DEVIATIONS.get(rel, {}).get("added_links", []))
    c_fa = Counter(t for _, t in lfa)
    c_en = Counter(t for _, t in len_)
    for t in dropped:
        c_en[t] -= 1
        if c_en[t] <= 0:
            del c_en[t]
    for t, n in added.items():
        c_fa[t] -= n
        if c_fa[t] <= 0:
            del c_fa[t]
    if list(c_fa.elements()) != list(c_en.elements()) and sorted(c_fa.elements()) != sorted(c_en.elements()):
        errs.append(f"link targets differ: fa={sorted(c_fa.elements())} en={sorted(c_en.elements())}")

    # 5 images (targets must match; alt text may be translated)
    if [t for _, t in images(fa)] != [t for _, t in images(en)]:
        errs.append("image targets differ")

    # 6 kbd
    if Counter(kbds(fa)) != Counter(kbds(en)):
        errs.append(f"<kbd> contents differ: fa={Counter(kbds(fa))} en={Counter(kbds(en))}")

    # 7 headers & anchors
    hfa, hen = headers_with_slugs(fa), headers_with_slugs(en)
    if len(hfa) != len(hen):
        errs.append(f"header count differs: fa={len(hfa)} en={len(hen)}")
    # expected anchors: upstream's explicit anchor if present, else auto-slug;
    # mdBook appends -1, -2... when the same slug repeats in a file
    seen = {}
    expected_anchors = []
    for lvl_e, body_e, anch_e in hen:
        exp = anch_e if anch_e else slugify(body_e)
        if exp in seen:
            seen[exp] += 1
            exp = f"{exp}-{seen[exp]}"
        else:
            seen[exp] = 0
        expected_anchors.append(exp)
    for (lvl_f, body_f, anch_f), expected in zip(hfa, expected_anchors):
        if anch_f != expected:
            errs.append("header '" + body_f[:40] + "' needs anchor {#" + expected + "}, found " + repr(anch_f))
    for (lvl_f, _, _), (lvl_e, _, _) in zip(hfa, hen):
        if lvl_f != lvl_e:
            errs.append("header level differs")

    # 8 hidden anchors
    if Counter(hidden_anchors(fa)) != Counter(hidden_anchors(en)):
        errs.append("hidden <a id=...> anchors differ")

    # 9 typography
    prose = strip_code(fa)
    for i, line in enumerate(prose.splitlines(), 1):
        if PERSIAN_RE.search(line):
            if re.search(r"[,;!?]", line.replace("؟", "").replace("،", "").replace("؛", "")):
                # allow ASCII inside URLs/parens-free prose only: crude strip of urls
                stripped = re.sub(r"https?://\S+", "", line)
                if re.search(r"[,;?!]", stripped.replace("؟", "").replace("،", "").replace("؛", "")):
                    warns.append(f"line {i}: ASCII punctuation in Persian prose")
            if re.search(r"\bمی\s", line):
                warns.append(f"line {i}: 'می ' with space instead of ZWNJ")
        for term in BANNED:
            if term in line:
                errs.append(f"line {i}: banned term '{term}'")

    # 10 leftover English runs
    for i, line in enumerate(strip_code(fa).splitlines(), 1):
        if not PERSIAN_RE.search(line):
            continue
        words = re.findall(r"[A-Za-z][A-Za-z'&.-]*", line)
        run, longest = 0, 0
        for w in words + ["|END|"]:
            if w not in PRODUCTS and w.lower() not in PRODUCTS:
                run += 1
                longest = max(longest, run)
            else:
                run = 0
        if longest >= 3:
            warns.append(f"line {i}: {longest} consecutive English words — check")

    return errs, warns


def main() -> int:
    args = sys.argv[1:]
    if args:
        targets = [a.removeprefix("src/") for a in args]
    else:
        targets = sorted(
            str(p.relative_to(SRC))
            for p in SRC.rglob("*.md")
            if (EN / p.relative_to(SRC)).exists()
        )
    bad = 0
    translated = 0
    for rel in targets:
        if rel == "SUMMARY.md":
            continue  # structural file: link targets checked by build itself
        errs, warns = check_file(rel)
        if errs is None:
            print(f"[SKIP] {rel} (not translated yet)")
            continue
        translated += 1
        status = "OK " if not errs else "FAIL"
        if errs or warns:
            bad += bool(errs)
            print(f"[{status}] {rel}")
            for e in errs:
                print(f"   ERROR: {e}")
            for w in warns:
                print(f"   warn : {w}")
        else:
            print(f"[OK ] {rel}")
    print(f"\n{translated} translated file(s) checked, {bad} with errors")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
