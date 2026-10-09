#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成结果自检：检查 docs/ 里的内部链接、图片、锚点、RSS / sitemap 是否正常。

用法:
    python tools/check_site.py
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SITE_URL = "https://daydaydream000.github.io"

ATTR_RE = re.compile(r'(?:href|src)\s*=\s*"([^"]*)"', re.I)
ID_RE = re.compile(r'\sid\s*=\s*"([^"]*)"', re.I)

errors: list[str] = []


def is_external(url: str) -> bool:
    return bool(re.match(r"^(?:[a-z][a-z0-9+.\-]*:|//|mailto:|tel:|data:|#)", url, re.I))


def main() -> int:
    if not DOCS.is_dir():
        print("docs/ 不存在，请先运行 python build.py")
        return 1

    checked_links = 0
    pages = sorted(DOCS.rglob("*.html"))
    ids_by_file: dict[Path, set[str]] = {}

    for page in pages:
        text = page.read_text(encoding="utf-8")
        ids_by_file[page] = set(re.findall(ID_RE, text))

    for page in pages:
        text = page.read_text(encoding="utf-8")
        rel_page = page.relative_to(DOCS).as_posix()
        for raw in ATTR_RE.findall(text):
            url = raw.strip()
            if not url or url.startswith(SITE_URL):
                url = url[len(SITE_URL):] or "/"
            if re.match(r"^(?:[a-z][a-z0-9+.\-]*:|//|mailto:|tel:|data:)", url, re.I):
                continue

            checked_links += 1
            parsed = urlparse(url)
            path_part = unquote(parsed.path)
            fragment = unquote(parsed.fragment)

            if not path_part or path_part == "":
                target = page
            elif path_part.startswith("/"):
                target = DOCS / path_part.lstrip("/")
            else:
                target = (page.parent / path_part).resolve()

            if target.is_dir():
                target = target / "index.html"

            if not target.exists():
                errors.append(f"{rel_page}: 链接目标不存在 → {raw}")
                continue

            if fragment and target.suffix == ".html":
                if fragment not in ids_by_file.get(target, set()):
                    errors.append(f"{rel_page}: 锚点不存在 → {raw}")

    # 必需文件
    for required in ("index.html", "404.html", "rss.xml", "sitemap.xml", "robots.txt", ".nojekyll",
                     "assets/style.css", "assets/app.js", "assets/search-index.js"):
        if not (DOCS / required).exists():
            errors.append(f"缺少必需文件: {required}")

    # XML 合法性
    for name in ("rss.xml", "sitemap.xml"):
        path = DOCS / name
        if path.exists():
            try:
                ET.fromstring(path.read_text(encoding="utf-8"))
            except ET.ParseError as exc:
                errors.append(f"{name}: XML 解析失败 → {exc}")

    # 搜索索引
    index_file = DOCS / "assets" / "search-index.js"
    if index_file.exists():
        text = index_file.read_text(encoding="utf-8")
        if "window.SEARCH_INDEX" not in text:
            errors.append("search-index.js 缺少 window.SEARCH_INDEX")

    # Jekyll 相关的下划线目录（发布目录里不应出现）
    for path in DOCS.rglob("*"):
        if path.is_dir() and path.name.startswith("_"):
            errors.append(f"目录名以下划线开头，会被 Jekyll 忽略: {path.relative_to(DOCS)}")

    print(f"检查 {len(pages)} 个页面，{checked_links} 条链接/资源引用")
    if errors:
        print(f"\n发现 {len(errors)} 个问题：")
        for item in errors:
            print(f"  ✗ {item}")
        return 1
    print("全部通过 ✓")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
