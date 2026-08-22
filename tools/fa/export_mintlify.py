#!/usr/bin/env python3
"""Export the Persian mdBook manual into Anki's Mintlify docs tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "src"
SUMMARY = SOURCE_ROOT / "SUMMARY.md"
EXCLUDED = {Path("SUMMARY.md"), Path("faqs.md")}

CALLOUTS = {
    "summary": "Note",
    "caution": "Warning",
    "info": "Info",
    "note": "Note",
    "example": "Info",
    "danger": "Danger",
    "warning": "Warning",
    "tip": "Tip",
}

IMAGE_ALTS = {
    "decks_screen.png": "صفحهٔ دسته‌ها",
    "study_overview.png": "صفحهٔ نمای کلی مطالعه",
    "study_overview_buried_cards.png": "کارت‌های کنار گذاشته‌شده در نمای کلی",
}

AUTOLINK_LABELS = {
    "https://addon-docs.ankiweb.net/sharing.html": "راهنمای اشتراک‌گذاری افزونه‌ها",
    "https://translating.ankiweb.net": "راهنمای ترجمه",
    "https://addon-docs.ankiweb.net/porting2.0.html#webview-changes": "انتقال افزونه‌های آنکی ۲.۰",
}

LINK_RE = re.compile(
    r"(?P<prefix>!?\[[^\]\n]*\]\()"
    r"(?P<target><[^>\n]+>|[^)\s]+)"
    r"(?P<suffix>(?:\s+[\"'][^\"']*[\"'])?\))"
)
AUTOLINK_RE = re.compile(r"<(?P<url>https?://[^>\s]+)>")
HEADING_ID_RE = re.compile(r"\s+\{#[^}]+\}\s*$")
H1_RE = re.compile(r"^#\s+(?P<title>.+?)\s*$", re.MULTILINE)
SUMMARY_LINK_RE = re.compile(r"\[(?P<title>[^]]+)\]\((?P<path>[^)#]+\.md)(?:#[^)]+)?\)")


def summary_titles() -> dict[Path, str]:
    return {
        Path(match.group("path")): match.group("title").strip()
        for match in SUMMARY_LINK_RE.finditer(SUMMARY.read_text(encoding="utf-8"))
    }


def strip_page_suffix(path: str) -> str:
    return re.sub(r"\.(?:md|html)$", "", path)


def consolidated_route(url: str) -> str | None:
    parsed = urlsplit(url)
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")
    fragment = f"#{parsed.fragment}" if parsed.fragment else ""

    if host == "faqs.ankiweb.net":
        if not path:
            return "/faqs/"
        return f"/faqs/{strip_page_suffix(path)}{fragment}"

    if host == "addon-docs.ankiweb.net":
        if not path:
            return "/addons/intro"
        return f"/addons/{strip_page_suffix(path)}{fragment}"

    if host == "translating.ankiweb.net":
        if not path:
            return "/translators"
        return f"/translators/{strip_page_suffix(path)}{fragment}"

    if host == "docs.ankiweb.net" and path:
        return f"/manual/{strip_page_suffix(path)}{fragment}"

    return None


def rewrite_link_target(target: str, *, image: bool) -> str:
    wrapped = target.startswith("<") and target.endswith(">")
    value = target[1:-1] if wrapped else target

    if value.startswith(("http://", "https://")):
        return consolidated_route(value) or value

    if value.startswith(("mailto:", "#", "/")):
        return target

    if image:
        return f"/media/{Path(value).name}"

    match = re.match(r"^(?P<path>[^?#]+)(?P<tail>[?#].*)?$", value)
    if match is None:
        return target

    path = strip_page_suffix(match.group("path"))
    tail = match.group("tail") or ""
    if not path.startswith(("./", "../")):
        path = f"./{path}"
    return f"{path}{tail}"


def rewrite_links(content: str) -> str:
    def replace_link(match: re.Match[str]) -> str:
        prefix = match.group("prefix")
        image = prefix.startswith("!")
        target = rewrite_link_target(match.group("target"), image=image)

        if image:
            basename = Path(target).name
            if prefix == "!" + "[](" and basename in IMAGE_ALTS:
                prefix = f"![{IMAGE_ALTS[basename]}]("

        return f"{prefix}{target}{match.group('suffix')}"

    content = LINK_RE.sub(replace_link, content)

    def replace_autolink(match: re.Match[str]) -> str:
        url = match.group("url")
        target = consolidated_route(url) or url
        label = AUTOLINK_LABELS.get(url, url)
        return f"[{label}]({target})"

    return AUTOLINK_RE.sub(replace_autolink, content)


def convert_callouts(content: str) -> str:
    output: list[str] = []
    lines = content.splitlines()
    index = 0

    while index < len(lines):
        match = re.match(r"^```admonish\s+(\S+)\s*$", lines[index])
        if match is None:
            output.append(lines[index])
            index += 1
            continue

        kind = match.group(1).lower()
        component = CALLOUTS.get(kind)
        if component is None:
            raise ValueError(f"unsupported admonition type: {kind}")

        index += 1
        body: list[str] = []
        while index < len(lines) and lines[index] != "```":
            body.append(lines[index])
            index += 1
        if index == len(lines):
            raise ValueError(f"unterminated {kind} admonition")

        output.extend([f"<{component}>", *body, f"</{component}>"])
        index += 1

    return "\n".join(output) + "\n"


def fence_indented_code(content: str) -> str:
    """Convert mdBook's four-space code blocks to explicit MDX fences."""

    lines = content.splitlines()
    output: list[str] = []
    index = 0
    in_fence = False

    while index < len(lines):
        line = lines[index]
        if line.startswith(("```", "~~~")):
            in_fence = not in_fence
            output.append(line)
            index += 1
            continue

        if in_fence or not line.startswith("    "):
            output.append(line)
            index += 1
            continue

        block: list[str] = []
        while index < len(lines):
            line = lines[index]
            if line.startswith("    "):
                block.append(line[4:])
                index += 1
                continue
            if not line.strip():
                lookahead = index + 1
                while lookahead < len(lines) and not lines[lookahead].strip():
                    lookahead += 1
                if lookahead < len(lines) and lines[lookahead].startswith("    "):
                    block.append("")
                    index += 1
                    continue
            break

        output.extend(["```text", *block, "```"])

    return "\n".join(output) + "\n"


def escape_prose_templates(content: str) -> str:
    """Escape Anki {{field}} examples in prose, but not in code."""

    output: list[str] = []
    in_fence = False

    for line in content.splitlines():
        if line.startswith(("```", "~~~")):
            in_fence = not in_fence
            output.append(line)
            continue

        if in_fence or line.startswith(("    ", "\t")):
            output.append(line)
            continue

        # Preserve inline code spans and Mintlify custom heading IDs.
        parts = re.split(r"(`+[^`]*`+)", line)
        for index in range(0, len(parts), 2):
            parts[index] = parts[index].replace("{{", r"\{\{").replace("}}", r"\}\}")
        output.append("".join(parts))

    return "\n".join(output) + "\n"


def page_title(relative: Path, content: str, titles: dict[Path, str]) -> tuple[str, str]:
    match = H1_RE.search(content)
    if match is not None:
        title = HEADING_ID_RE.sub("", match.group("title")).strip()
        content = content[: match.start()] + content[match.end() :]
        return title, content.lstrip("\n")

    title = titles.get(relative)
    if title is None:
        first_heading = re.search(r"^#{2,6}\s+(.+?)\s*$", content, re.MULTILINE)
        if first_heading is None:
            raise ValueError(f"cannot determine title for {relative}")
        title = HEADING_ID_RE.sub("", first_heading.group(1)).strip()
    return title, content


def source_pages() -> list[Path]:
    return sorted(
        path
        for path in SOURCE_ROOT.rglob("*.md")
        if path.relative_to(SOURCE_ROOT) not in EXCLUDED
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_media(anki_root: Path, pages: list[Path]) -> None:
    central_media = anki_root / "docs-site" / "media"
    image_re = re.compile(r"!\[[^]]*\]\((?P<target>[^)\s]+)")

    for page in pages:
        for match in image_re.finditer(page.read_text(encoding="utf-8")):
            target = match.group("target")
            if target.startswith(("http://", "https://")):
                continue
            source = (page.parent / target).resolve()
            destination = central_media / Path(target).name
            if not source.exists():
                raise ValueError(f"missing source image: {source}")
            if not destination.exists():
                raise ValueError(f"missing central image: {destination}")
            if sha256(source) != sha256(destination):
                raise ValueError(f"image differs from central copy: {source}")


def convert_page(relative: Path, titles: dict[Path, str]) -> str:
    content = (SOURCE_ROOT / relative).read_text(encoding="utf-8")
    content = content.replace("<!-- toc -->\n", "")
    content = re.sub(r"<!--.*?-->\n?", "", content, flags=re.DOTALL)
    content = re.sub(r"^(#{1,6}\s+.*?)<(?=\d)", r"\1&lt;", content, flags=re.MULTILINE)
    title, content = page_title(relative, content, titles)
    content = convert_callouts(content)
    content = fence_indented_code(content)
    content = rewrite_links(content)
    content = escape_prose_templates(content)
    content = "\n".join(line.rstrip() for line in content.splitlines()) + "\n"
    frontmatter = f"---\ntitle: {json.dumps(title, ensure_ascii=False)}\n---\n\n"
    return frontmatter + content.lstrip("\n")


def export(anki_root: Path) -> None:
    english_root = anki_root / "docs-site" / "manual"
    destination_root = anki_root / "docs-site" / "fa" / "manual"
    if not english_root.is_dir():
        raise SystemExit(f"not an Anki checkout: {anki_root}")

    pages = source_pages()
    source_relatives = {page.relative_to(SOURCE_ROOT).with_suffix("") for page in pages}
    english_relatives = {
        page.relative_to(english_root).with_suffix("") for page in english_root.rglob("*.mdx")
    }
    if source_relatives != english_relatives:
        missing = sorted(english_relatives - source_relatives)
        extra = sorted(source_relatives - english_relatives)
        raise SystemExit(f"manual path mismatch; missing={missing}, extra={extra}")

    verify_media(anki_root, pages)
    titles = summary_titles()
    destination_root.mkdir(parents=True, exist_ok=True)

    expected_outputs: set[Path] = set()
    for page in pages:
        relative = page.relative_to(SOURCE_ROOT).with_suffix(".mdx")
        destination = destination_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(convert_page(relative.with_suffix(".md"), titles), encoding="utf-8")
        expected_outputs.add(destination)

    for old_page in destination_root.rglob("*.mdx"):
        if old_page not in expected_outputs:
            old_page.unlink()

    print(f"exported {len(expected_outputs)} Persian pages to {destination_root}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--anki-repo",
        type=Path,
        default=Path.home() / "anki",
        help="path to the ankitects/anki checkout (default: ~/anki)",
    )
    args = parser.parse_args()
    export(args.anki_repo.expanduser().resolve())


if __name__ == "__main__":
    main()
