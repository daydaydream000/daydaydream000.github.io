p = r'D:\1\mypro\daydaydream000.github.io\build.py'
with open(p, 'rb') as f:
    raw = f.read()

start = raw.find(b'def _image(match')
end = raw.find(b'\ndef _image_figure', start)
old = raw[start:end]
print('current length:', len(old))

new = b'''def _image(match: re.Match, ctx: RenderContext) -> str:
    raw_alt, raw_src, raw_title = match.group(1), match.group(2), match.group(3)
    alt = html.unescape(raw_alt)
    src = html.unescape(raw_src)
    title = html.unescape(raw_title) if raw_title else ""
    # kramdown-style class: ![alt](src "title"){.class}
    css_class = ""
    cls_match = re.search(rb"\\{([^}]+)\\}\\s*$", title.encode("utf-8"))
    if cls_match:
        css_class = cls_match.group(1).decode("utf-8").strip()
        title = title[: cls_match.start()].rstrip()
    resolved = ctx.resolve_image(src)
    attrs = [
        f'src="{esc_attr(resolved)}"',
        f'alt="{esc_attr(alt)}"',
        'loading="lazy"',
        'decoding="async"',
    ]
    if title:
        attrs.append(f'title="{esc_attr(title)}"')
    if css_class:
        attrs.append(f'class="{esc_attr(css_class)}"')
    return f"<img {' '.join(attrs)}>"
'''

new_raw = raw[:start] + new + raw[end+1:]
with open(p, 'wb') as f:
    f.write(new_raw)
print(f'OK: replaced {len(old)} bytes with {len(new)} bytes')
