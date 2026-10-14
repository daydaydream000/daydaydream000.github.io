"""
直接用 bytes 替换 _image 函数，绕开中文注释
"""
p = r'D:\1\mypro\daydaydream000.github.io\build.py'
with open(p, 'rb') as f:
    raw = f.read()

# 用 bytes 找位置：从 def _image 开头到函数结束（return + 换行）
start_marker = b'def _image(match: re.Match, ctx: RenderContext) -> str:\n'
i = raw.index(start_marker)
# 函数结束：从 start 找到下一个 'def _' 开头（_image_figure）就是函数结束
end_marker = b'\ndef _image_figure'
eidx = raw.index(end_marker, i)

# 构造新函数
new_func = b'''def _image(match: re.Match, ctx: RenderContext) -> str:
    alt, src, title = html.unescape(match.group(1)), html.unescape(match.group(2)), html.unescape(match.group(3))
    # kramdown-style class: ![alt](src "title"){.class}
    css_class = ''
    cls_match = re.search(br'\\{([^}]+)\\}\\s*$', (title or '').encode('utf-8'))
    if cls_match:
        css_class = cls_match.group(1).decode('utf-8').strip()
        title = (title or '')[: cls_match.start()].rstrip()
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

new_raw = raw[:i] + new_func + raw[eidx+1:]  # +1 to skip the leading \n
with open(p, 'wb') as f:
    f.write(new_raw)
print(f'OK: replaced {eidx - i} bytes with {len(new_func)} bytes')
