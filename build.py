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
    # 头像与横幅都放在 assets/ 里，站点不依赖任何第三方域名；换成 "https://…" 也可以
    "avatar": "assets/avatar.jpg",
    "banner": "assets/banner.jpg",
    "greeting": "Hello, I'm DayDayDream.",
    "notice": "欢迎来到 DayDayDream —— 醒着做梦，落笔成诗，记所思，存所学。",
    "notice_link": ("前往关于", "about.html"),
    "social": [
        ("GitHub", "https://github.com/daydaydream000", "github"),
        ("邮箱", "mailto:daydaydream000@users.noreply.github.com", "mail"),
        ("RSS 订阅", "rss.xml", "rss"),
    ],
    "email": "daydaydream000@users.noreply.github.com",
    "github": "https://github.com/daydaydream000",
    "repo": "https://github.com/daydaydream000/daydaydream000.github.io",
    "footer": "转载请注明出处",
    "lang": "zh-CN",
    "per_page": 10,
    "nav": [
        ("首页", "index.html", "home"),
        ("标签", "tags/index.html", "tag"),
        ("关于", "about.html", "user"),
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
                f'<div class="code-head"><span>{label}</span>'
                '<button class="code-copy" type="button" '
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
    """站点内资源 → 相对当前页面的路径；外链原样返回。

    带 @@ROOT@@ 占位符的值（Markdown 渲染出来的图片）已经知道自己的站点内位置，
    只需替换占位符，千万不能再拼一次 root。
    """
    if not value:
        return value
    if ROOT_TOKEN in value:
        return value.replace(ROOT_TOKEN, root)
    if EXTERNAL_RE.match(value) or value.startswith("#"):
        return value
    return root + value.lstrip("/")


def absolute_url(value: str) -> str:
    """站点内资源 → 完整 URL（用于 og:image、RSS）。"""
    if value.startswith(ROOT_TOKEN):
        return CONFIG["url"] + "/" + value[len(ROOT_TOKEN):]
    if not value or EXTERNAL_RE.match(value) or value.startswith("#"):
        return value
    return CONFIG["url"] + "/" + value.lstrip("/")


# --------------------------------------------------------------------------
# 界面组件（Firefly 风格：整屏横幅 + 悬浮胶囊导航 + 三栏卡片）
# --------------------------------------------------------------------------

# name: (SVG 内部内容, 是否是填充型图标)
ICONS: dict[str, tuple[str, bool]] = {
    "home": ('<path d="M3 10.5 12 3l9 7.5"/><path d="M5.5 9.5V20h13V9.5"/>', False),
    "tag": ('<path d="M3 12.5V4a1 1 0 0 1 1-1h8.5L21 11.5 12.5 20 3 12.5Z"/>'
            '<circle cx="7.8" cy="7.8" r="1.4"/>', False),
    "user": ('<circle cx="12" cy="8" r="3.6"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/>', False),
    "search": ('<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>', False),
    "sun": ('<circle cx="12" cy="12" r="4.2"/><path d="M12 2.6v2.4M12 19v2.4M2.6 12H5M19 12h2.4'
            'M5.4 5.4l1.7 1.7M16.9 16.9l1.7 1.7M18.6 5.4l-1.7 1.7M7.1 16.9l-1.7 1.7"/>', False),
    "moon": ('<path d="M20.5 14.3A8.6 8.6 0 1 1 9.7 3.5a7 7 0 0 0 10.8 10.8z"/>', False),
    "arrow-up": ('<path d="M12 19V5M5 12l7-7 7 7"/>', False),
    "arrow-right": ('<path d="M5 12h14M13 5l7 7-7 7"/>', False),
    "calendar": ('<rect x="3.5" y="5" width="17" height="15.5" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/>', False),
    "folder": ('<path d="M3.5 7.5a2 2 0 0 1 2-2h4l2 2.5h6.5a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-13'
               'a2 2 0 0 1-2-2v-10Z"/>', False),
    "pin": ('<path d="M9 4h6l-1 6 4 3v2H6v-2l4-3-1-6Z"/><path d="M12 15v5"/>', False),
    "clock": ('<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>', False),
    "file": ('<path d="M13 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V9l-6-6Z"/><path d="M13 3v6h6"/>', False),
    "chart": ('<path d="M4 20V10M10 20V4M16 20v-7M2 20h20"/>', False),
    "mail": ('<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="m4 7 8 6 8-6"/>', False),
    "rss": ('<circle cx="5" cy="18.5" r="1.4" fill="currentColor" stroke="none"/>'
            '<path d="M4 11a9 9 0 0 1 9 9M4 4a16 16 0 0 1 16 16"/>', False),
    "close": ('<path d="M6 6l12 12M18 6 6 18"/>', False),
    "megaphone": ('<path d="M4 10.5v3A1.5 1.5 0 0 0 5.5 15H7l1 4h2l-1-4h2l7 3.5V6.5L11 10H5.5A1.5 1.5 0 0 0 4 10.5Z"/>', False),
    "github": ('<path d="M12 2C6.48 2 2 6.58 2 12.26c0 4.5 2.87 8.32 6.84 9.67.5.09.68-.22.68-.48 '
               '0-.24-.01-.87-.01-1.7-2.78.62-3.37-1.37-3.37-1.37-.45-1.18-1.11-1.5-1.11-1.5-.91-.64.07-.62.07-.62 '
               '1 .07 1.53 1.06 1.53 1.06.89 1.56 2.34 1.11 2.91.85.09-.66.35-1.11.63-1.37-2.22-.26-4.56-1.14-4.56-5.07 '
               '0-1.12.39-2.03 1.03-2.75-.1-.26-.45-1.3.1-2.71 0 0 .84-.28 2.75 1.05a9.4 9.4 0 0 1 5 0c1.91-1.33 '
               '2.75-1.05 2.75-1.05.55 1.41.2 2.45.1 2.71.64.72 1.03 1.63 1.03 2.75 0 3.94-2.34 4.8-4.57 5.06.36.32.68.94.68 '
               '1.9 0 1.37-.01 2.47-.01 2.81 0 .27.18.58.69.48A10.04 10.04 0 0 0 22 12.26C22 6.58 17.52 2 12 2z"/>', True),
}


def icon_svg(name: str, size: int = 16) -> str:
    body, filled = ICONS.get(name, ICONS["file"])
    head = (f'class="i" viewBox="0 0 24 24" width="{size}" height="{size}" '
            'aria-hidden="true" focusable="false"')
    if filled:
        return f'<svg {head} fill="currentColor">{body}</svg>'
    return (f'<svg {head} fill="none" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round">{body}</svg>')


def link_href(href: str, root: str) -> str:
    """站内链接补上当前页面的相对根路径，外链原样返回。"""
    if EXTERNAL_RE.match(href) or href.startswith("#"):
        return href
    return root + href.lstrip("/")


def external_attrs(href: str) -> str:
    return ' target="_blank" rel="noopener noreferrer"' if href.startswith("http") else ""


def render_page(
    *,
    out_path: Path,
    page_title: str,
    body: str,
    description: str = "",
    nav_active: str = "",
    body_class: str = "",
    og_type: str = "website",
    canonical: str = "",
    image: str = "",
    banner: str = "",
    left: str = "",
    right: str = "",
    extra_head: str = "",
) -> None:
    root = root_prefix(out_path)

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
        "og_image": esc_attr(absolute_url(image or CONFIG["banner"])),
        "topbar": render_topbar(root, nav_active),
        "banner": banner,
        "left": left,
        "right": right,
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


def render_topbar(root: str, nav_active: str) -> str:
    items = []
    for label, target, icon in CONFIG["nav"]:
        active = ' class="active" aria-current="page"' if target == nav_active else ""
        items.append(
            f'<a href="{root}{target}"{active}>{icon_svg(icon, 17)}<span>{esc(label)}</span></a>'
        )
    return (
        '<header class="topbar">'
        '<div class="topbar-inner">'
        f'<a class="topbar-brand" href="{root}index.html">'
        f'<img src="{asset_url(CONFIG["avatar"], root)}" alt="" width="30" height="30">'
        f'<span class="topbar-brand-text">{esc(CONFIG["title"])}</span></a>'
        f'<nav class="topbar-nav" aria-label="主导航">{"".join(items)}</nav>'
        '<div class="topbar-tools">'
        '<button id="search-toggle" class="icon-btn" type="button" aria-label="搜索文章" title="搜索（按 /）">'
        f'{icon_svg("search", 18)}</button>'
        '<button id="theme-toggle" class="icon-btn" type="button" aria-label="切换深浅色主题" title="切换主题">'
        f'<span class="icon-sun">{icon_svg("sun", 18)}</span>'
        f'<span class="icon-moon">{icon_svg("moon", 18)}</span></button>'
        "</div></div></header>"
    )


def render_banner(
    root: str,
    title: str,
    subtitle: str = "",
    *,
    social: bool = False,
    short: bool = False,
) -> str:
    background = esc_attr(asset_url(CONFIG["banner"], root))
    socials = ""
    if social:
        socials = '<div class="banner-social">' + "".join(
            f'<a class="social-btn" href="{link_href(href, root)}" title="{esc(label)}" '
            f'aria-label="{esc(label)}"{external_attrs(href)}>{icon_svg(name, 18)}</a>'
            for label, href, name in CONFIG["social"]
        ) + "</div>"
    subtitle_html = f'<p class="banner-subtitle">{esc(subtitle)}</p>' if subtitle else ""
    classes = "banner banner-short" if short else "banner"
    # 首页的横幅是整页的大标题（h1）；内页正文里已有 h1，横幅只作装饰
    tag = "p" if short else "h1"
    return (
        f'<header class="{classes}">'
        f'<img class="banner-bg" src="{background}" alt="" aria-hidden="true" decoding="async">'
        '<div class="banner-scrim"></div>'
        '<div class="banner-inner">'
        f'<{tag} class="banner-title">{esc(title)}</{tag}>'
        f"{subtitle_html}{socials}"
        "</div></header>"
    )


def render_profile_card(root: str) -> str:
    socials = "".join(
        f'<a class="social-chip" href="{link_href(href, root)}" title="{esc(label)}" '
        f'aria-label="{esc(label)}"{external_attrs(href)}>{icon_svg(name, 17)}</a>'
        for label, href, name in CONFIG["social"]
    )
    return (
        '<section class="card-panel profile-card">'
        f'<img class="profile-avatar" src="{asset_url(CONFIG["avatar"], root)}" '
        f'alt="{esc_attr(CONFIG["title"])}" decoding="async">'
        f'<p class="profile-name">{esc(CONFIG["title"])}</p>'
        f'<p class="profile-greeting">{esc(CONFIG["greeting"])}</p>'
        f'<div class="profile-social">{socials}</div>'
        "</section>"
    )


def render_notice_card(root: str) -> str:
    text = CONFIG.get("notice") or ""
    if not text:
        return ""
    link = ""
    if CONFIG.get("notice_link"):
        label, href = CONFIG["notice_link"]
        link = f'<a class="notice-more" href="{link_href(href, root)}">{esc(label)}</a>'
    return (
        '<section class="card-panel notice-card" id="notice">'
        f'<h2 class="widget-title">{icon_svg("megaphone", 16)}<span>公告</span></h2>'
        f'<p class="notice-text">{esc(text)}</p>'
        f'<div class="notice-foot">{link}'
        '<button class="notice-close" type="button" aria-label="关闭公告" title="关闭">'
        f'{icon_svg("close", 15)}</button></div>'
        "</section>"
    )


def render_sidebar_left(root: str) -> str:
    return render_profile_card(root) + render_notice_card(root)


def render_stats_card(posts: list[Doc]) -> str:
    tags: set[str] = set()
    words = 0
    latest = None
    for doc in posts:
        tags.update(doc.tags)
        words += doc.word_count
        if latest is None or doc.date > latest:
            latest = doc.date
    rows = [
        ("file", "文章", str(len(posts))),
        ("tag", "标签", str(len(tags))),
        ("chart", "总字数", f"{words:,}"),
        ("clock", "最近更新", latest.strftime("%Y-%m-%d") if latest else "—"),
    ]
    body = "".join(
        f'<li>{icon_svg(icon, 15)}<span class="stat-label">{esc(label)}</span>'
        f'<span class="stat-value">{esc(value)}</span></li>'
        for icon, label, value in rows
    )
    return (
        '<section class="card-panel">'
        f'<h2 class="widget-title">{icon_svg("chart", 16)}<span>站点统计</span></h2>'
        f'<ul class="stat-list">{body}</ul>'
        "</section>"
    )


def render_recent_card(posts: list[Doc], root: str, limit: int = 5) -> str:
    if not posts:
        return ""
    items = "".join(
        f'<li><a href="{root}{doc.url}">'
        f'<time datetime="{doc.date_str}">{doc.date_str}</time>'
        f'<span class="recent-title">{esc(doc.title)}</span></a></li>'
        for doc in posts[:limit]
    )
    return (
        '<section class="card-panel">'
        f'<h2 class="widget-title">{icon_svg("file", 16)}<span>最新文章</span></h2>'
        f'<ul class="recent-list">{items}</ul>'
        "</section>"
    )


def render_toc_card(toc: list[dict], root: str) -> str:
    entries = [item for item in toc if item["level"] in (2, 3)]
    if not entries:
        return ""
    links = "".join(
        f'<a class="{"toc-h3" if item["level"] == 3 else ""}" '
        f'href="#{esc_attr(item["id"])}">{esc(item["text"])}</a>'
        for item in entries
    )
    return (
        '<nav class="card-panel toc-card" aria-label="文章目录">'
        f'<h2 class="widget-title">{icon_svg("file", 16)}<span>文章目录</span></h2>'
        f'<div class="toc-list">{links}</div>'
        "</nav>"
    )


def render_tag_bar(posts: list[Doc], root: str, limit: int = 6) -> str:
    counts: dict[str, int] = {}
    for doc in posts:
        for tag in doc.tags:
            counts[tag] = counts.get(tag, 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
    pills = [f'<a class="pill active" href="{root}index.html">{icon_svg("home", 16)}<span>全部</span></a>']
    for tag, count in ordered:
        pills.append(
            f'<a class="pill" href="{root}tags/index.html#{tag_anchor(tag)}">'
            f'<span>{esc(tag)}</span><b>{count}</b></a>'
        )
    return (
        '<div class="card-panel tag-bar">'
        f'{"".join(pills)}'
        f'<a class="pill-more" href="{root}tags/index.html">更多{icon_svg("arrow-right", 14)}</a>'
        "</div>"
    )


def tags_html(doc: Doc, root: str) -> str:
    return "".join(
        f'<a class="tag" href="{root}tags/index.html#{t["anchor"]}">{esc(t["name"])}</a>'
        for t in doc.tag_links
    )


def post_meta_html(doc: Doc, root: str) -> str:
    """文章页标题下方的一行信息：日期 · 更新 · 字数 · 用时 · 标签。"""
    parts = [
        f'<span class="badge">{icon_svg("calendar", 13)}'
        f'<time datetime="{doc.date_str}">{esc(doc.date_display)}</time></span>'
    ]
    if doc.updated:
        parts.append(
            f'<span class="badge">{icon_svg("clock", 13)}更新于 {esc(format_date(doc.updated))}</span>'
        )
    parts.append(f'<span class="badge">{icon_svg("file", 13)}约 {doc.word_count} 字</span>')
    parts.append(f'<span class="badge">{icon_svg("clock", 13)}{doc.reading} 分钟阅读</span>')
    for tag in doc.tag_links:
        parts.append(
            f'<a class="badge badge-pin" href="{root}tags/index.html#{tag["anchor"]}">'
            f'{icon_svg("tag", 13)}{esc(tag["name"])}</a>'
        )
    return f'<div class="post-badges">{"".join(parts)}</div>'


def render_post_card(doc: Doc, root: str) -> str:
    badges = []
    if doc.pinned:
        badges.append(f'<span class="badge badge-pin">{icon_svg("pin", 13)}置顶</span>')
    badges.append(f'<span class="badge">{icon_svg("calendar", 13)}{doc.date_str}</span>')
    if doc.tags:
        badges.append(f'<span class="badge">{icon_svg("folder", 13)}{esc(doc.tags[0])}</span>')
    badges.append(f'<span class="badge">{icon_svg("clock", 13)}{doc.reading} 分钟</span>')

    thumb = ""
    if doc.cover:
        thumb = (
            f'<a class="post-thumb" href="{root}{doc.url}" tabindex="-1" aria-hidden="true">'
            f'<img src="{asset_url(doc.cover, root)}" alt="" loading="lazy" decoding="async"></a>'
        )
    chips = "".join(
        f'<a class="chip" href="{root}tags/index.html#{t["anchor"]}">#{esc(t["name"])}</a>'
        for t in doc.tag_links
    )
    return (
        '<article class="card-panel post-card">'
        '<div class="post-card-body">'
        f'<h2 class="post-card-title"><a href="{root}{doc.url}">{esc(doc.title)}</a></h2>'
        f'<div class="post-badges">{"".join(badges)}</div>'
        f'<p class="post-excerpt">{esc(doc.summary)}</p>'
        f'<div class="post-chips">{chips}</div>'
        "</div>"
        f"{thumb}"
        "</article>"
    )


def render_post_list(posts: list[Doc], root: str) -> str:
    return "".join(render_post_card(doc, root) for doc in posts)


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

        if chunk:
            posts_html = render_post_list(chunk, root)
        else:
            posts_html = '<p class="card-panel empty">还没有文章，去 <code>posts/</code> 里写下第一篇吧。</p>'

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

        # 标签栏只放在首页第一页，翻页后不再重复
        tag_bar = render_tag_bar(posts, root) if page_no == 1 else ""
        body = fill(
            template("index.html"),
            {"tag_bar": tag_bar, "posts": posts_html, "pager": pager},
        )

        if page_no == 1:
            banner = render_banner(root, CONFIG["title"], CONFIG["subtitle"], social=True)
        else:
            banner = render_banner(root, CONFIG["title"], f"第 {page_no} 页", short=True)

        render_page(
            out_path=out_path,
            page_title=CONFIG["title"] if page_no == 1 else f"第 {page_no} 页",
            body=body,
            description=CONFIG["description"],
            nav_active="index.html",
            body_class="page-index",
            banner=banner,
            left=render_sidebar_left(root),
            right=render_stats_card(posts) + render_recent_card(posts, root),
        )


def build_posts(posts: list[Doc], pages: list[Doc]) -> None:
    for index, doc in enumerate(posts):
        out_path = Path(doc.url)
        root = root_prefix(out_path)
        cover = ""
        if doc.cover:
            cover = (
                f'<figure class="post-cover"><img src="{asset_url(doc.cover, root)}" '
                f'alt="{esc_attr(doc.title)}" loading="lazy" decoding="async"></figure>'
            )
        body = fill(
            template("post.html"),
            {
                "title": esc(doc.title),
                "meta": post_meta_html(doc, root),
                "tags": tags_html(doc, root),
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
            banner=render_banner(root, CONFIG["title"], CONFIG["subtitle"], short=True),
            left=render_sidebar_left(root),
            right=render_toc_card(doc.toc, root) + render_stats_card(posts),
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
            banner=render_banner(root, CONFIG["title"], CONFIG["subtitle"], short=True),
            left=render_sidebar_left(root),
            right=render_stats_card(posts) + render_recent_card(posts, root),
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
        banner=render_banner(root, CONFIG["title"], CONFIG["subtitle"], short=True),
        left=render_sidebar_left(root),
        right=render_stats_card(posts) + render_recent_card(posts, root),
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


def build_404(posts: list[Doc]) -> None:
    body = fill(template("404.html"), {"root": ""})
    render_page(
        out_path=Path("404.html"),
        page_title="页面走丢了",
        body=body,
        description="找不到这个页面",
        body_class="page-404",
        banner=render_banner("", CONFIG["title"], CONFIG["subtitle"], short=True),
        left=render_sidebar_left(""),
        right=render_recent_card(posts, ""),
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
    build_404(posts)

    total_files = sum(1 for p in OUT_DIR.rglob("*") if p.is_file())
    print(f"完成: {total_files} 个文件 → {OUT_DIR.relative_to(ROOT)}/")
    if WARNINGS:
        print(f"有 {len(WARNINGS)} 条警告，请检查上面的输出。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
