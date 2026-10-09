#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DayDayDream 博客 —— 自建静态站点生成器（零第三方依赖）

用法:
    python build.py              # 生成站点到 docs/
    python build.py --clean      # 先清空 docs/ 再生成（默认行为就是全量重建）

目录约定:
    posts/*.md     文章（front matter + Markdown），进入首页列表 / 标签 / RSS
    pages/*.md     独立单页（如 about），只出现在导航里
    images/*       文章引用的本地图片，会自动复制到 docs/assets/images/
    assets/        样式与脚本，原样复制到 docs/assets/
    templates/     HTML / XML 模板
    docs/          生成的站点（GitHub Pages 发布目录，不要手改）

GitHub Pages 发布源:
    仓库 Settings → Pages → Build and deployment → Source: Deploy from a branch
    Branch: main    Folder: /docs
    （见 https://docs.github.com/en/pages/getting-started-with-github-pages/
      configuring-a-publishing-source-for-your-github-pages-site）

图片用法（Markdown）:
    ![图片说明](images/photo.png)      独立成段时渲染为 <figure> + 图注
    ![](images/photo.png)              只放图片，不加图注
    ![说明](https://example.com/a.png) 外链图片原样保留
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import shutil
import sys
import unicodedata
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import quote

# --------------------------------------------------------------------------
# 站点配置：改这里就够了
# --------------------------------------------------------------------------
CONFIG = {
    "title": "DayDayDream",
    "subtitle": "醒着做梦，落笔成诗——记所思，存所学。",
    "description": "DayDayDream 的个人博客：醒着做梦，落笔成诗——记所思，存所学。",
    "url": "https://daydaydream000.github.io",
    "author": "DayDayDream",
    # 头像放在 assets/ 里，站点不依赖任何第三方域名；换成 "https://…" 也可以
    "avatar": "assets/avatar.png",
    "email": "daydaydream000@users.noreply.github.com",
    "github": "https://github.com/daydaydream000",
    "repo": "https://github.com/daydaydream000/daydaydream000.github.io",
    "footer": "转载请注明出处",
    "lang": "zh-CN",
    "per_page": 10,
    "nav": [
        ("首页", "index.html"),
        ("标签", "tags/index.html"),
        ("关于", "about.html"),
    ],
}

ROOT = Path(__file__).resolve().parent
POSTS_DIR = ROOT / "posts"
PAGES_DIR = ROOT / "pages"
IMAGES_DIR = ROOT / "images"
ASSETS_DIR = ROOT / "assets"
TEMPLATES_DIR = ROOT / "templates"
OUT_DIR = ROOT / "docs"
IMAGE_OUT_SUBDIR = "assets/images"

# --------------------------------------------------------------------------
# 基础工具
# --------------------------------------------------------------------------

WARNINGS: list[str] = []


def warn(message: str) -> None:
    WARNINGS.append(message)
    print(f"  [warn] {message}")


def read_text(path: Path) -> str:
    # utf-8-sig: 容忍 Windows 记事本保存的 BOM，否则 front matter 会解析失败
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def esc(text: str) -> str:
    """转义为 HTML 文本。"""
    return html.escape(str(text), quote=False)


def esc_attr(text: str) -> str:
    return html.escape(str(text), quote=True)


CJK_RE = re.compile(r"[\u2e80-\u9fff\uf900-\ufaff\uff00-\uffef\u3000-\u303f]")


def is_cjk(ch: str) -> bool:
    return bool(CJK_RE.match(ch))


def smart_join(prev: str, nxt: str) -> str:
    """中文之间换行不加空格，西文之间换行加空格。"""
    if not prev or not nxt:
        return ""
    if is_cjk(prev[-1]) or is_cjk(nxt[0]):
        return ""
    return " "


def slugify(text: str, fallback: str = "section") -> str:
    """生成锚点 / 文件名友好的 slug，保留中文。"""
    text = unicodedata.normalize("NFKC", text).strip().lower()
    text = re.sub(r"[\s\u3000]+", "-", text)
    text = re.sub(r"[^\w\u2e80-\u9fff-]", "", text, flags=re.UNICODE)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or fallback


def strip_markup(text: str) -> str:
    """把渲染后的 HTML 压成纯文本，用于摘要、字数、搜索。"""
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.S | re.I)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</(p|div|li|h[1-6]|blockquote|tr|figure)>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def truncate(text: str, limit: int = 110) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "…"


def reading_minutes(text: str) -> int:
    cjk = len(CJK_RE.findall(text))
    latin = len(re.findall(r"[A-Za-z0-9]+", text))
    minutes = cjk / 400 + latin / 200
    return max(1, math.ceil(minutes))


def format_date(value: datetime, fmt: str = "%Y 年 %m 月 %d 日") -> str:
    return value.strftime(fmt)


def parse_date(value, fallback_path: Path) -> datetime:
    if isinstance(value, datetime):
        return value
    if value:
        raw = str(value).strip().strip("'\"")
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
    warn(f"{fallback_path.name}: 缺少或无法解析 date，已回退到文件修改时间")
    return datetime.fromtimestamp(fallback_path.stat().st_mtime)


# --------------------------------------------------------------------------
# front matter（YAML 的一个很小的子集）
# --------------------------------------------------------------------------

def split_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    match = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", text, re.S)
    if not match:
        return {}, text
    raw, body = match.group(1), text[match.end():]
    return parse_front_matter(raw), body


def parse_front_matter(raw: str) -> dict:
    data: dict = {}
    current_key: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        list_match = re.match(r"^\s*-\s+(.*)$", line)
        if list_match and current_key:
            data.setdefault(current_key, [])
            if not isinstance(data[current_key], list):
                data[current_key] = []
            data[current_key].append(parse_scalar(list_match.group(1)))
            continue
        kv = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
        if not kv:
            continue
        key, value = kv.group(1), kv.group(2).strip()
        current_key = key
        if value == "":
            data[key] = ""
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [parse_scalar(v) for v in re.split(r"\s*,\s*", inner)] if inner else []
        else:
            data[key] = parse_scalar(value)
    return data


def parse_scalar(value: str):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    low = value.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low in ("null", "~", "none"):
        return None
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


# --------------------------------------------------------------------------
# Markdown 渲染器
# --------------------------------------------------------------------------

BLOCK_TAGS = (
    "div|details|summary|img|figure|figcaption|table|thead|tbody|tr|td|th|p|ul|ol|li|br|hr|"
    "iframe|video|audio|section|article|span|a|center|blockquote|pre|code|h1|h2|h3|h4|h5|h6|"
    "svg|path|g|rect|circle|line|polygon|polyline|defs|linearGradient|stop|text|tspan|canvas|"
    "kbd|sup|sub|dl|dt|dd|mark|small|strong|em|b|i|u|picture|source|input|label|form|button"
)
HTML_BLOCK_RE = re.compile(rf"^\s*</?(?:{BLOCK_TAGS})(?:\s|/?>|$)", re.I)

LIST_RE = re.compile(r"^(\s*)([-*+]|\d{1,9}[.)])\s+(.*)$")
FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})[ \t]*([\w#+.\-]*)[ \t]*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
HR_RE = re.compile(r"^\s*(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})$")
SETEXT_RE = re.compile(r"^\s*(=+|-{2,})\s*$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
QUOTE_RE = re.compile(r"^\s{0,3}>\s?(.*)$")
TASK_RE = re.compile(r"^\[([ xX])\]\s+(.*)$")

ALERT_TYPES = {
    "NOTE": ("📘", "提示"),
    "TIP": ("💡", "技巧"),
    "IMPORTANT": ("📌", "重要"),
    "WARNING": ("⚠️", "警告"),
    "CAUTION": ("🚨", "注意"),
}

ROOT_TOKEN = "@@ROOT@@"


class RenderContext:
    """一次渲染所需的外部信息（图片解析、标题收集、来源目录）。"""

    def __init__(self, source_path: Path):
        self.source_dir = source_path.parent
        self.toc: list[dict] = []
        self.images: dict[Path, str] = {}
        self.used_slugs: dict[str, int] = {}

    def unique_slug(self, text: str) -> str:
        base = slugify(text, "section")
        count = self.used_slugs.get(base, 0)
        self.used_slugs[base] = count + 1
        return base if count == 0 else f"{base}-{count + 1}"

    def resolve_image(self, src: str) -> str:
        if re.match(r"^(?:[a-z][a-z0-9+.\-]*:|//)", src, re.I):
            return src  # 外链、data: 等原样保留
        clean = src.split("#", 1)[0].split("?", 1)[0]
        candidates = [
            (self.source_dir / clean),
            (ROOT / clean.lstrip("/")),
        ]
        for candidate in candidates:
            if candidate.is_file():
                path = candidate.resolve()
                if path not in self.images:
                    self.images[path] = self.image_output_rel(path)
                return f"{ROOT_TOKEN}{self.images[path]}"
        warn(f"{self.source_dir.name}: 找不到图片 {src}")
        return src

    @staticmethod
    def image_output_rel(path: Path) -> str:
        stem = slugify(path.stem, "image")
        suffix = path.suffix.lower() or ".png"
        return f"{IMAGE_OUT_SUBDIR}/{stem}{suffix}"


def _stash(store: list[str], fragment: str) -> str:
    store.append(fragment)
    return f"\x00{len(store) - 1}\x00"


def render_inline(text: str, ctx: RenderContext) -> str:
    store: list[str] = []

    # 1) 行内代码
    text = re.sub(
        r"(`+)(.+?)\1",
        lambda m: _stash(store, "<code>" + esc(m.group(2).strip()) + "</code>"),
        text,
        flags=re.S,
    )
    # 2) 自动链接
    text = re.sub(
        r"<(https?://[^ >]+)>",
        lambda m: _stash(store, _anchor(m.group(1), m.group(1))),
        text,
    )
    text = re.sub(
        r"<([\w.+-]+@[\w-]+\.[\w.]+)>",
        lambda m: _stash(store, _anchor("mailto:" + m.group(1), m.group(1))),
        text,
    )
    # 3) 保留作者手写的行内 HTML 标签
    text = re.sub(r"</?[A-Za-z][^<>]*?/?>", lambda m: _stash(store, m.group(0)), text)
    # 4) 转义其余内容
    text = esc(text)
    # 5) 图片 / 链接
    text = re.sub(
        r"!\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+[\"']([^\"']*)[\"'])?\s*\)",
        lambda m: _stash(store, _image(m, ctx)),
        text,
    )
    text = re.sub(
        r"\[([^\]]+)\]\(\s*([^)\s]+)(?:\s+[\"']([^\"']*)[\"'])?\s*\)",
        lambda m: _stash(store, _link(m)),
        text,
    )
    # 6) 删除线 / 高亮 / 粗体 / 斜体
    text = re.sub(r"~~(?=\S)(.+?)(?<=\S)~~", r"<del>\1</del>", text, flags=re.S)
    text = re.sub(r"==(?=\S)(.+?)(?<=\S)==", r"<mark>\1</mark>", text, flags=re.S)
    text = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", r"<strong>\1</strong>", text, flags=re.S)
    text = re.sub(r"__(?=\S)(.+?)(?<=\S)__", r"<strong>\1</strong>", text, flags=re.S)
    text = re.sub(r"(?<![\w*])\*(?=\S)([^*]+?)(?<=\S)\*(?![\w*])", r"<em>\1</em>", text)
    text = re.sub(r"(?<![\w_])_(?=\S)([^_]+?)(?<=\S)_(?![\w_])", r"<em>\1</em>", text)

    # 7) 还原占位符（含未转义实体）
    def restore(match: re.Match) -> str:
        return store[int(match.group(1))]

    text = re.sub(r"\x00(\d+)\x00", restore, text)
    return text


def _anchor(href: str, label: str, title: str | None = None) -> str:
    title_attr = f' title="{esc_attr(title)}"' if title else ""
    external = bool(re.match(r"^(?:https?:)?//", href, re.I))
    rel = ' target="_blank" rel="noopener noreferrer"' if external else ""
    return f'<a href="{esc_attr(href)}"{title_attr}{rel}>{label}</a>'


def _link(match: re.Match) -> str:
    label, href, title = match.group(1), html.unescape(match.group(2)), match.group(3)
    # 支持 [文字](post:slug) 指向文章
    if href.startswith("post:"):
        href = f"post/{href[5:]}.html"
    return _anchor(href, label, html.unescape(title) if title else None)


def _image(match: re.Match, ctx: RenderContext) -> str:
    alt, src, title = html.unescape(match.group(1)), html.unescape(match.group(2)), match.group(3)
    resolved = ctx.resolve_image(src)
    # 占位符已在 store 里被占用了编号，这里直接生成最终 img 标签字符串
    attrs = [
        f'src="{esc_attr(resolved)}"',
        f'alt="{esc_attr(alt)}"',
        'loading="lazy"',
        'decoding="async"',
    ]
    if title:
        attrs.append(f'title="{esc_attr(title)}"')
    return f"<img {' '.join(attrs)}>"


def _image_figure(alt: str, img_tag: str) -> str:
    if not alt.strip():
        return f'<p class="post-image">{img_tag}</p>'
    return (
        '<figure class="post-figure">'
        f"{img_tag}"
        f"<figcaption>{esc(alt)}</figcaption>"
        "</figure>"
    )


def render_paragraph_text(text: str, ctx: RenderContext) -> str:
    """把一段（可能多行的）文本渲染为 <p>，处理硬换行与中英文软换行。"""
    pieces: list[str] = []
    previous_plain = ""
    previous_hard = False

    for raw in text.split("\n"):
        hard = raw.endswith("  ") or raw.rstrip().endswith("\\")
        stripped = raw.rstrip()
        if stripped.endswith("\\"):
            stripped = stripped[:-1].rstrip()
        rendered = render_inline(stripped, ctx)
        plain = strip_markup(rendered)
        if pieces:
            pieces.append("<br>" if previous_hard else smart_join(previous_plain, plain))
        pieces.append(rendered)
        previous_plain = plain
        previous_hard = hard

    return f"<p>{''.join(pieces)}</p>"


def render_blocks(lines: list[str], ctx: RenderContext, tight: bool = False) -> str:
    out: list[str] = []
    i = 0
    total = len(lines)

    while i < total:
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        # 围栏代码块
        fence = FENCE_RE.match(line)
        if fence:
            marker = fence.group(2)
            lang = fence.group(3)
            i += 1
            code: list[str] = []
            while i < total and not re.match(rf"^\s*{re.escape(marker[0])}{{{len(marker)},}}\s*$", lines[i]):
                code.append(lines[i])
                i += 1
            i += 1
            cls = f' class="language-{esc_attr(lang)}"' if lang else ""
            label = f'<span class="code-lang">{esc(lang or "text")}</span>' if lang else ""
            out.append(
                '<div class="code-block">'
                f'<div class="code-head">{label}<button class="copy-btn" type="button" '
                'data-copy aria-label="复制代码">复制</button></div>'
                f"<pre><code{cls}>{esc(chr(10).join(code))}</code></pre>"
                "</div>"
            )
            continue

        # 标题
        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            text = heading.group(2)
            slug = ctx.unique_slug(strip_markup(render_inline(text, ctx)))
            attrs = f' id="{esc_attr(slug)}"'
            if level >= 2:
                ctx.toc.append({"level": level, "id": slug, "text": strip_markup(render_inline(text, ctx))})
            out.append(f"<h{level}{attrs}>{render_inline(text, ctx)}</h{level}>")
            i += 1
            continue

        # Setext 标题 / 分隔线
        if i + 1 < total and line.strip() and SETEXT_RE.match(lines[i + 1]) and not LIST_RE.match(line):
            underline = SETEXT_RE.match(lines[i + 1]).group(1)
            if underline.startswith("="):
                slug = ctx.unique_slug(strip_markup(render_inline(line, ctx)))
                ctx.toc.append({"level": 2, "id": slug, "text": strip_markup(render_inline(line, ctx))})
                out.append(f'<h2 id="{esc_attr(slug)}">{render_inline(line, ctx)}</h2>')
            else:
                out.append(f"<h3>{render_inline(line, ctx)}</h3>")
            i += 2
            continue

        if HR_RE.match(line):
            out.append("<hr>")
            i += 1
            continue

        # 引用 / 提示框
        if QUOTE_RE.match(line):
            quote_lines: list[str] = []
            while i < total and (QUOTE_RE.match(lines[i]) or (quote_lines and lines[i].strip() and not HR_RE.match(lines[i]) and not HEADING_RE.match(lines[i]))):
                match = QUOTE_RE.match(lines[i])
                if match:
                    quote_lines.append(match.group(1))
                else:
                    quote_lines.append(lines[i])
                i += 1
            alert = None
            if quote_lines:
                alert_match = re.match(r"^\[!(\w+)\]\s*(.*)$", quote_lines[0].strip())
                if alert_match and alert_match.group(1).upper() in ALERT_TYPES:
                    alert = alert_match.group(1).upper()
                    title = alert_match.group(2).strip()
                    quote_lines = quote_lines[1:]
                    icon, default_title = ALERT_TYPES[alert]
                    body = render_blocks(quote_lines, ctx)
                    out.append(
                        f'<div class="alert alert-{alert.lower()}">'
                        f'<p class="alert-title"><span class="alert-icon">{icon}</span>'
                        f"{esc(title or default_title)}</p>{body}</div>"
                    )
                    continue
            body = render_blocks(quote_lines, ctx)
            out.append(f"<blockquote>{body}</blockquote>")
            continue

        # 表格
        if "|" in line and i + 1 < total and TABLE_SEP_RE.match(lines[i + 1]) and "-" in lines[i + 1]:
            header_cells = split_table_row(line)
            aligns = [cell_alignment(c) for c in split_table_row(lines[i + 1])]
            i += 2
            rows: list[list[str]] = []
            while i < total and "|" in lines[i] and lines[i].strip():
                rows.append(split_table_row(lines[i]))
                i += 1
            head_html = "".join(
                f'<th{style}>{render_inline(cell, ctx)}</th>'
                for cell, style in zip(header_cells, aligns + [""] * len(header_cells))
            )
            body_html = ""
            for row in rows:
                cells = "".join(
                    f'<td{style}>{render_inline(cell, ctx)}</td>'
                    for cell, style in zip(row, aligns + [""] * len(row))
                )
                body_html += f"<tr>{cells}</tr>"
            out.append(
                '<div class="table-wrap"><table>'
                f"<thead><tr>{head_html}</tr></thead>"
                f"<tbody>{body_html}</tbody>"
                "</table></div>"
            )
            continue

        # 列表
        if LIST_RE.match(line):
            html_list, i = render_list(lines, i, ctx)
            out.append(html_list)
            continue

        # 手写 HTML 块
        if HTML_BLOCK_RE.match(line):
            container = re.match(r"^\s*<(details|div|section|figure|table|article|aside|blockquote|ul|ol|dl|pre)\b", line, re.I)
            block: list[str] = []
            if container and f"</{container.group(1)}" not in line.lower():
                closing = re.compile(rf"</{container.group(1)}\s*>", re.I)
                while i < total:
                    block.append(lines[i])
                    found = closing.search(lines[i])
                    i += 1
                    if found:
                        break
            else:
                while i < total and lines[i].strip():
                    block.append(lines[i])
                    i += 1
            out.append("\n".join(block))
            continue

        # 段落
        para: list[str] = []
        while i < total and lines[i].strip():
            if para and (
                HEADING_RE.match(lines[i])
                or FENCE_RE.match(lines[i])
                or HR_RE.match(lines[i])
                or QUOTE_RE.match(lines[i])
                or LIST_RE.match(lines[i])
                or HTML_BLOCK_RE.match(lines[i])
            ):
                break
            para.append(lines[i])
            i += 1
        if not para:
            i += 1
            continue
        paragraph = render_paragraph_text("\n".join(para), ctx)

        # 单独成段的图片 → figure + 图注
        single = re.fullmatch(r"<p>\s*(<img [^>]*>)\s*</p>", paragraph)
        if single:
            alt = re.search(r'alt="([^"]*)"', single.group(1))
            out.append(_image_figure(html.unescape(alt.group(1)) if alt else "", single.group(1)))
        elif tight:
            # 紧凑列表：条目内的段落不套 <p>
            out.append(paragraph[len("<p>"):-len("</p>")])
        else:
            out.append(paragraph)

    return "".join(out)


def split_table_row(line: str) -> list[str]:
    line = line.strip().strip("|")
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", line)]


def cell_alignment(separator: str) -> str:
    separator = separator.strip()
    if separator.startswith(":") and separator.endswith(":"):
        return ' style="text-align:center"'
    if separator.endswith(":"):
        return ' style="text-align:right"'
    return ""


def render_list(lines: list[str], start: int, ctx: RenderContext) -> tuple[str, int]:
    total = len(lines)
    first = LIST_RE.match(lines[start])
    base_indent = len(first.group(1))
    ordered = first.group(2)[0].isdigit()
    items: list[list[str]] = []
    i = start

    while i < total:
        match = LIST_RE.match(lines[i])
        if not match or len(match.group(1)) != base_indent or match.group(2)[0].isdigit() != ordered:
            break
        content_indent = match.start(3)
        item_lines = [match.group(3)]
        i += 1
        while i < total:
            current = lines[i]
            if not current.strip():
                look = i
                while look < total and not lines[look].strip():
                    look += 1
                if look >= total:
                    i = look
                    break
                nxt_match = LIST_RE.match(lines[look])
                if nxt_match and len(nxt_match.group(1)) == base_indent:
                    break
                indent = len(lines[look]) - len(lines[look].lstrip())
                if indent >= content_indent:
                    item_lines.append("")
                    i += 1
                    continue
                break
            nxt_match = LIST_RE.match(current)
            if nxt_match and len(nxt_match.group(1)) == base_indent:
                break
            indent = len(current) - len(current.lstrip())
            if indent >= content_indent or (not nxt_match and indent > base_indent):
                item_lines.append(current[content_indent:] if len(current) > content_indent else current.lstrip())
                i += 1
            else:
                break
        items.append(item_lines)

    tag = "ol" if ordered else "ul"
    start_attr = ""
    if ordered:
        start_number = re.match(r"^(\d+)", first.group(2))
        if start_number and start_number.group(1) != "1":
            start_attr = f' start="{start_number.group(1)}"'

    html_items = []
    loose = any("" in item_lines for item_lines in items)
    for item_lines in items:
        task = TASK_RE.match(item_lines[0]) if item_lines else None
        checkbox = ""
        if task:
            checked = " checked" if task.group(1).lower() == "x" else ""
            checkbox = f'<input type="checkbox" disabled{checked}> '
            item_lines = [task.group(2)] + item_lines[1:]
        inner = render_blocks(item_lines, ctx, tight=not loose)
        if checkbox:
            inner = re.sub(r"^<p>", f"<p>{checkbox}", inner, count=1)
            if "<p>" not in inner:
                inner = checkbox + inner
        html_items.append(f"<li>{inner}</li>")

    cls = ' class="task-list"' if any(TASK_RE.match(item[0]) for item in items if item) else ""
    return f"<{tag}{start_attr}{cls}>{''.join(html_items)}</{tag}>", i


def render_markdown(text: str, ctx: RenderContext) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return render_blocks(lines, ctx)


# --------------------------------------------------------------------------
# 内容模型
# --------------------------------------------------------------------------

class Doc:
    def __init__(self, path: Path, kind: str):
        self.path = path
        self.kind = kind  # "post" | "page"
        raw = read_text(path)
        meta, body = split_front_matter(raw)

        self.slug = str(meta.get("slug") or slugify(path.stem, "untitled"))
        self.title = str(meta.get("title") or self._title_from_body(body) or path.stem)
        self.date = parse_date(meta.get("date"), path)
        self.updated = parse_date(meta.get("updated"), path) if meta.get("updated") else None
        self.tags = normalize_tags(meta.get("tags"))
        self.summary_override = str(meta.get("summary") or meta.get("description") or "").strip()
        self.cover = str(meta.get("cover") or "").strip()
        self.draft = bool(meta.get("draft"))
        self.pinned = bool(meta.get("pinned"))
        self.author = str(meta.get("author") or CONFIG["author"])

        self.dir = "post" if kind == "post" else ""
        self.url = f"{self.dir}/{self.slug}.html" if self.dir else f"{self.slug}.html"

        self.ctx = RenderContext(path)
        self.html = render_markdown(strip_leading_title(body, self.title), self.ctx)
        self.toc = self.ctx.toc
        self.images = self.ctx.images
        self.plain = strip_markup(self.html)
        self.summary = self.summary_override or truncate(self.plain, 110)
        self.reading = reading_minutes(self.plain)
        self.word_count = len(CJK_RE.findall(self.plain)) + len(re.findall(r"[A-Za-z0-9]+", self.plain))
        if self.cover:
            self.cover = self.ctx.resolve_image(self.cover)

    @staticmethod
    def _title_from_body(body: str) -> str | None:
        match = re.search(r"^#\s+(.+)$", body, re.M)
        return match.group(1).strip() if match else None

    @property
    def date_str(self) -> str:
        return self.date.strftime("%Y-%m-%d")

    @property
    def date_display(self) -> str:
        return format_date(self.date)

    @property
    def out_path(self) -> Path:
        return Path(self.url)

    @property
    def tag_links(self) -> list[dict]:
        return [
            {"name": tag, "anchor": tag_anchor(tag), "color": tag_color(tag)}
            for tag in self.tags
        ]


def _plain_key(text: str) -> str:
    return re.sub(r"[\s\u3000·。，,、：:!！?？\-—_]+", "", text).lower()


def strip_leading_title(body: str, title: str) -> str:
    """正文开头的 h1 若与标题重复，去掉它（模板已经渲染了标题）。"""
    match = re.match(r"^\s*#\s+(.+?)\s*\n+", body)
    if match and _plain_key(match.group(1)) == _plain_key(title):
        return body[match.end():]
    return body


def normalize_tags(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        parts = re.split(r"[,，、\s]+", value.strip())
    elif isinstance(value, list):
        parts = [str(v) for v in value]
    else:
        parts = [str(value)]
    seen, result = set(), []
    for part in parts:
        part = part.strip()
        if part and part.lower() not in seen:
            seen.add(part.lower())
            result.append(part)
    return result


def tag_anchor(tag: str) -> str:
    return "tag-" + slugify(tag, "tag")


PALETTE = ["#0969da", "#1f883d", "#bc4c00", "#8250df", "#bf3989", "#0550ae", "#953800", "#116329"]


def tag_color(tag: str) -> str:
    digest = hashlib.md5(tag.encode("utf-8")).hexdigest()
    return PALETTE[int(digest[:8], 16) % len(PALETTE)]


def load_docs() -> tuple[list[Doc], list[Doc]]:
    posts, pages = [], []
    for directory, kind, bucket in ((POSTS_DIR, "post", posts), (PAGES_DIR, "page", pages)):
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            doc = Doc(path, kind)
            if doc.draft:
                print(f"  - 跳过草稿 {path.name}")
                continue
            bucket.append(doc)
    posts.sort(key=lambda d: (d.pinned, d.date), reverse=True)
    pages.sort(key=lambda d: d.date)
    return posts, pages


# --------------------------------------------------------------------------
# 模板
# --------------------------------------------------------------------------

TEMPLATE_CACHE: dict[str, str] = {}
PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def template(name: str) -> str:
    if name not in TEMPLATE_CACHE:
        path = TEMPLATES_DIR / name
        if not path.is_file():
            raise SystemExit(f"缺少模板文件: {path}")
        TEMPLATE_CACHE[name] = read_text(path)
    return TEMPLATE_CACHE[name]


def fill(text: str, context: dict) -> str:
    """单次占位符替换：值里的 {{...}} 不会被再次解析，内容永远原样输出。"""

    def replace(match: re.Match) -> str:
        key = match.group(1)
        value = context.get(key, "")
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    return PLACEHOLDER_RE.sub(replace, text)


def root_prefix(out_path: Path) -> str:
    depth = len(out_path.parts) - 1
    return "../" * depth


def resolve_root(value: str, root: str) -> str:
    """把资源里的 @@ROOT@@ 占位符换成当前页面的相对根路径。"""
    return value.replace(ROOT_TOKEN, root)


EXTERNAL_RE = re.compile(r"^(?:[a-z][a-z0-9+.\-]*:|//)", re.I)


def asset_url(value: str, root: str) -> str:
    """站点内资源 → 相对当前页面的路径；外链原样返回。"""
    value = resolve_root(value, root)
    if not value or EXTERNAL_RE.match(value) or value.startswith("#"):
        return value
    return root + value.lstrip("/")


def absolute_url(value: str) -> str:
    """站点内资源 → 完整 URL（用于 og:image、RSS）。"""
    if value.startswith(ROOT_TOKEN):
        return CONFIG["url"] + "/" + value[len(ROOT_TOKEN):]
    if not value or EXTERNAL_RE.match(value) or value.startswith("#"):
        return value
    return CONFIG["url"] + "/" + value.lstrip("/")


def render_page(
    *,
    out_path: Path,
    page_title: str,
    body: str,
    description: str = "",
    nav_active: str = "",
    extra_head: str = "",
    body_class: str = "",
    og_type: str = "website",
    canonical: str = "",
    image: str = "",
) -> None:
    root = root_prefix(out_path)
    nav_html = []
    for label, target in CONFIG["nav"]:
        active = ' class="active" aria-current="page"' if target == nav_active else ""
        nav_html.append(f'<a href="{root}{target}"{active}>{esc(label)}</a>')

    if not canonical:
        posix = out_path.as_posix()
        if posix == "index.html":
            canonical = CONFIG["url"] + "/"
        elif posix.endswith("/index.html"):
            canonical = f"{CONFIG['url']}/{posix[:-len('index.html')]}"
        else:
            canonical = f"{CONFIG['url']}/{posix}"

    context = {
        "lang": CONFIG["lang"],
        "root": root,
        "site_title": esc(CONFIG["title"]),
        "site_subtitle": esc(CONFIG["subtitle"]),
        "page_title": esc(page_title),
        "title_tag": esc(page_title if page_title == CONFIG["title"] else f"{page_title} · {CONFIG['title']}"),
        "description": esc_attr(description or CONFIG["description"]),
        "og_type": og_type,
        "canonical": esc_attr(canonical),
        "og_image": esc_attr(absolute_url(image or CONFIG["avatar"])),
        "nav": "".join(nav_html),
        "body": body,
        "body_class": body_class,
        "extra_head": extra_head,
        "footer_text": esc(CONFIG["footer"]),
        "author": esc(CONFIG["author"]),
        "github": esc_attr(CONFIG["github"]),
        "repo": esc_attr(CONFIG["repo"]),
        "email": esc_attr(CONFIG["email"]),
        "avatar": esc_attr(asset_url(CONFIG["avatar"], root)),
        "year": datetime.now().year,
        "url": CONFIG["url"],
    }
    write_text(OUT_DIR / out_path, fill(template("base.html"), context))


def render_post_list(posts: list[Doc], root: str) -> str:
    if not posts:
        return '<p class="empty">还没有文章，去 <code>posts/</code> 里写下第一篇吧。</p>'
    items = []
    for doc in posts:
        tags = "".join(
            f'<a class="tag" href="{root}tags/index.html#{t["anchor"]}" '
            f'style="--tag-color:{t["color"]}">{esc(t["name"])}</a>'
            for t in doc.tag_links
        )
        cover = ""
        if doc.cover:
            cover = (
                f'<a class="card-cover" href="{root}{doc.url}" tabindex="-1" aria-hidden="true">'
                f'<img src="{resolve_root(doc.cover, root)}" alt="" loading="lazy" decoding="async"></a>'
            )
        items.append(
            '<article class="card">'
            f"{cover}"
            '<div class="card-body">'
            f'<h2 class="card-title"><a href="{root}{doc.url}">{esc(doc.title)}</a></h2>'
            f'<p class="card-summary">{esc(doc.summary)}</p>'
            '<div class="card-meta">'
            f'<time datetime="{doc.date_str}">{esc(doc.date_display)}</time>'
            f'<span class="dot">·</span><span>{doc.reading} 分钟</span>'
            f'<span class="tags">{tags}</span>'
            "</div></div></article>"
        )
    return "".join(items)


def toc_html(toc: list[dict]) -> str:
    entries = [item for item in toc if item["level"] in (2, 3)]
    if len(entries) < 2:
        return ""
    links = []
    for item in entries:
        cls = ' class="toc-h3"' if item["level"] == 3 else ""
        links.append(f'<a href="#{esc_attr(item["id"])}"{cls}>{esc(item["text"])}</a>')
    return (
        '<nav class="toc" aria-label="目录">'
        '<p class="toc-title">目录</p>'
        f'<div class="toc-list">{"".join(links)}</div>'
        "</nav>"
    )


def neighbors_html(posts: list[Doc], index: int, root: str) -> str:
    newer = posts[index - 1] if index > 0 else None
    older = posts[index + 1] if index + 1 < len(posts) else None
    if not newer and not older:
        return ""
    parts = ['<nav class="post-nav" aria-label="上下篇">']
    if newer:
        parts.append(
            f'<a class="post-nav-item prev" href="{root}{newer.url}">'
            '<span class="post-nav-label">← 更新的一篇</span>'
            f'<span class="post-nav-title">{esc(newer.title)}</span></a>'
        )
    else:
        parts.append('<span class="post-nav-item placeholder"></span>')
    if older:
        parts.append(
            f'<a class="post-nav-item next" href="{root}{older.url}">'
            '<span class="post-nav-label">更早的一篇 →</span>'
            f'<span class="post-nav-title">{esc(older.title)}</span></a>'
        )
    parts.append("</nav>")
    return "".join(parts)


# --------------------------------------------------------------------------
# 构建流程
# --------------------------------------------------------------------------

def clean_output() -> None:
    resolved = OUT_DIR.resolve()
    if resolved.parent != ROOT.resolve() or resolved.name != "docs":
        raise SystemExit(f"拒绝清理意料之外的目录: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)


def copy_assets() -> None:
    if ASSETS_DIR.is_dir():
        shutil.copytree(ASSETS_DIR, OUT_DIR / "assets", dirs_exist_ok=True)
    write_text(OUT_DIR / ".nojekyll", "")


def copy_images(images: dict[Path, str]) -> None:
    for source, rel in images.items():
        target = OUT_DIR / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def collect_images(posts: list[Doc], pages: list[Doc]) -> dict[Path, str]:
    images: dict[Path, str] = {}
    for doc in list(posts) + list(pages):
        for path, rel in doc.images.items():
            if path in images and images[path] != rel:
                warn(f"图片命名冲突: {path.name}")
            images.setdefault(path, rel)
    return images


def build_index(posts: list[Doc], per_page: int) -> None:
    total = max(1, math.ceil(len(posts) / per_page))
    for page_no in range(1, total + 1):
        chunk = posts[(page_no - 1) * per_page: page_no * per_page]
        out_path = Path("index.html") if page_no == 1 else Path(f"page/{page_no}/index.html")
        root = root_prefix(out_path)

        pager = ""
        if total > 1:
            bits = []
            if page_no > 1:
                prev = "index.html" if page_no == 2 else f"page/{page_no - 1}/index.html"
                bits.append(f'<a class="pager-link" href="{root}{prev}">← 上一页</a>')
            bits.append(f'<span class="pager-info">第 {page_no} / {total} 页</span>')
            if page_no < total:
                bits.append(f'<a class="pager-link" href="{root}page/{page_no + 1}/index.html">下一页 →</a>')
            pager = f'<nav class="pager">{"".join(bits)}</nav>'

        intro = ""
        if page_no == 1:
            intro = fill(
                '<section class="hero">'
                '<img class="hero-avatar" src="{{avatar}}" alt="{{site_title}}" width="84" height="84" loading="lazy">'
                '<div><h1 class="hero-title">{{site_title}}</h1>'
                '<p class="hero-subtitle">{{site_subtitle}}</p></div></section>',
                {
                    "avatar": esc_attr(asset_url(CONFIG["avatar"], root)),
                    "site_title": esc(CONFIG["title"]),
                    "site_subtitle": esc(CONFIG["subtitle"]),
                },
            )

        body = fill(
            template("index.html"),
            {
                "hero": intro,
                "posts": render_post_list(chunk, root),
                "pager": pager,
                "count": len(posts),
            },
        )
        render_page(
            out_path=out_path,
            page_title=CONFIG["title"] if page_no == 1 else f"第 {page_no} 页",
            body=body,
            description=CONFIG["description"],
            nav_active="index.html",
            body_class="page-index",
        )


def build_posts(posts: list[Doc], pages: list[Doc]) -> None:
    for index, doc in enumerate(posts):
        out_path = Path(doc.url)
        root = root_prefix(out_path)
        tags = "".join(
            f'<a class="tag" href="{root}tags/index.html#{t["anchor"]}" '
            f'style="--tag-color:{t["color"]}">{esc(t["name"])}</a>'
            for t in doc.tag_links
        )
        cover = ""
        if doc.cover:
            cover = (
                f'<figure class="post-cover"><img src="{resolve_root(doc.cover, root)}" '
                f'alt="{esc_attr(doc.title)}" loading="lazy" decoding="async"></figure>'
            )
        body = fill(
            template("post.html"),
            {
                "title": esc(doc.title),
                "date": esc(doc.date_display),
                "date_iso": doc.date_str,
                "updated": esc(format_date(doc.updated)) if doc.updated else "",
                "updated_block": (
                    f'<span class="dot">·</span><span>更新于 {esc(format_date(doc.updated))}</span>'
                    if doc.updated
                    else ""
                ),
                "reading": doc.reading,
                "words": doc.word_count,
                "tags": tags,
                "cover": cover,
                "content": doc.html.replace(ROOT_TOKEN, root),
                "toc": toc_html(doc.toc),
                "neighbors": neighbors_html(posts, index, root),
                "source": (
                    f'<a href="{esc_attr(CONFIG["repo"])}/blob/main/{doc.path.relative_to(ROOT).as_posix()}">'
                    "在 GitHub 上查看源文件</a>"
                ),
            },
        )
        render_page(
            out_path=out_path,
            page_title=doc.title,
            body=body,
            description=doc.summary,
            nav_active="",
            og_type="article",
            body_class="page-post",
            image=absolute_url(doc.cover) if doc.cover else "",
        )

    for doc in pages:
        out_path = Path(doc.url)
        root = root_prefix(out_path)
        body = fill(
            template("page.html"),
            {
                "title": esc(doc.title),
                "content": doc.html.replace(ROOT_TOKEN, root),
                "toc": toc_html(doc.toc),
                "source": (
                    f'<a href="{esc_attr(CONFIG["repo"])}/blob/main/{doc.path.relative_to(ROOT).as_posix()}">'
                    "在 GitHub 上查看源文件</a>"
                ),
            },
        )
        render_page(
            out_path=out_path,
            page_title=doc.title,
            body=body,
            description=doc.summary,
            nav_active=doc.url,
            body_class="page-single",
        )


def build_tags(posts: list[Doc]) -> None:
    groups: dict[str, list[Doc]] = {}
    for doc in posts:
        for tag in doc.tags:
            groups.setdefault(tag, []).append(doc)

    out_path = Path("tags/index.html")
    root = root_prefix(out_path)

    if groups:
        cloud = "".join(
            f'<a class="tag tag-lg" href="#{tag_anchor(tag)}" style="--tag-color:{tag_color(tag)}">'
            f"{esc(tag)}<span class=\"tag-count\">{len(items)}</span></a>"
            for tag, items in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))
        )
        sections = []
        for tag, items in sorted(groups.items()):
            rows = "".join(
                f'<li><time datetime="{d.date_str}">{d.date_str}</time>'
                f'<a href="{root}{d.url}">{esc(d.title)}</a></li>'
                for d in items
            )
            sections.append(
                f'<section class="tag-section" id="{tag_anchor(tag)}">'
                f'<h2><span class="tag" style="--tag-color:{tag_color(tag)}">{esc(tag)}</span>'
                f'<span class="tag-count">{len(items)} 篇</span></h2>'
                f"<ul class=\"tag-posts\">{rows}</ul></section>"
            )
        content = f'<div class="tag-cloud">{cloud}</div>{"".join(sections)}'
    else:
        content = '<p class="empty">还没有标签。</p>'

    body = fill(
        template("tags.html"),
        {
            "content": content,
            "tag_count": len(groups),
            "post_count": len(posts),
        },
    )
    render_page(
        out_path=out_path,
        page_title="标签",
        body=body,
        description=f"{CONFIG['title']} 的全部标签",
        nav_active="tags/index.html",
        body_class="page-tags",
    )


def build_rss(posts: list[Doc]) -> None:
    items = []
    for doc in posts[:20]:
        published = doc.date.replace(tzinfo=timezone.utc)
        content = doc.html.replace(ROOT_TOKEN, f"{CONFIG['url']}/").replace("]]>", "]]&gt;")
        items.append(
            fill(
                template("rss-item.xml"),
                {
                    "title": esc(doc.title),
                    "url": f"{CONFIG['url']}/{doc.url}",
                    "date": format_datetime(published),
                    "author": esc(doc.author),
                    "email": esc(CONFIG["email"]),
                    "tags": "".join(f"<category>{esc(t)}</category>" for t in doc.tags),
                    "summary": esc(doc.summary),
                    "content": content,
                },
            )
        )
    last_build = posts[0].date if posts else datetime.now()
    write_text(
        OUT_DIR / "rss.xml",
        fill(
            template("rss.xml"),
            {
                "site_title": esc(CONFIG["title"]),
                "site_subtitle": esc(CONFIG["subtitle"]),
                "site_url": CONFIG["url"],
                "description": esc(CONFIG["description"]),
                "language": CONFIG["lang"],
                "author": esc(CONFIG["author"]),
                "email": esc(CONFIG["email"]),
                "build_date": format_datetime(datetime.now(timezone.utc)),
                "last_build": format_datetime(last_build.replace(tzinfo=timezone.utc)),
                "items": "".join(items),
            },
        ),
    )


def build_sitemap(posts: list[Doc], pages: list[Doc]) -> None:
    urls = [("", None)] + [(d.url, d.date) for d in posts] + [(d.url, d.date) for d in pages]
    urls.append(("tags/index.html", None))
    entries = []
    for url, date in urls:
        loc = f"{CONFIG['url']}/{url}".rstrip("/") or CONFIG["url"] + "/"
        lastmod = f"<lastmod>{date.strftime('%Y-%m-%d')}</lastmod>" if date else ""
        entries.append(f"<url><loc>{esc(loc)}</loc>{lastmod}</url>")
    write_text(
        OUT_DIR / "sitemap.xml",
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(entries)
        + "</urlset>\n",
    )
    write_text(OUT_DIR / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {CONFIG['url']}/sitemap.xml\n")


def build_search_index(posts: list[Doc], pages: list[Doc]) -> None:
    payload = []
    for doc in list(posts) + list(pages):
        payload.append(
            {
                "title": doc.title,
                "url": doc.url,
                "date": doc.date_str,
                "tags": doc.tags,
                "summary": doc.summary,
                "content": truncate(doc.plain, 600),
            }
        )
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    write_text(
        OUT_DIR / "assets" / "search-index.js",
        "/* 由 build.py 生成，勿手改 */\nwindow.SEARCH_INDEX = " + data + ";\n",
    )


def build_404() -> None:
    body = fill(template("404.html"), {"root": ""})
    render_page(
        out_path=Path("404.html"),
        page_title="页面走丢了",
        body=body,
        description="找不到这个页面",
        body_class="page-404",
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            pass

    parser = argparse.ArgumentParser(description="生成 DayDayDream 静态站点")
    parser.add_argument("--keep", action="store_true", help="保留 docs/ 中已有的未生成文件")
    args = parser.parse_args()

    print(f"读取内容: {POSTS_DIR.relative_to(ROOT)}/ , {PAGES_DIR.relative_to(ROOT)}/")
    posts, pages = load_docs()
    print(f"  文章 {len(posts)} 篇，单页 {len(pages)} 个")

    TEMPLATE_CACHE.clear()
    print(f"清理输出目录: {OUT_DIR.relative_to(ROOT)}/")
    clean_output()
    copy_assets()

    images = collect_images(posts, pages)
    copy_images(images)
    print(f"  复制图片 {len(images)} 张")

    build_index(posts, max(1, int(CONFIG["per_page"])))
    build_posts(posts, pages)
    build_tags(posts)
    build_rss(posts)
    build_sitemap(posts, pages)
    build_search_index(posts, pages)
    build_404()

    total_files = sum(1 for p in OUT_DIR.rglob("*") if p.is_file())
    print(f"完成: {total_files} 个文件 → {OUT_DIR.relative_to(ROOT)}/")
    if WARNINGS:
        print(f"有 {len(WARNINGS)} 条警告，请检查上面的输出。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
