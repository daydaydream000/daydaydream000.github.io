"""
再次回滚 + 重新生成 inline img：
- 不解码 alt，直接用 raw bytes
- alt 写为占位符（让 build.py 自己从原 markdown 的图片位置取 alt）

但 markdown 里 alt 已经在 ![alt](src) 里了——删掉 markdown 的图片，改用 inline HTML，
但 alt 直接传 GBK 字节（也就是 str 在 build.py 看来是乱码）。

最简单方案：让 build.py 不读 alt 字段，改为留空。修：
"""
import re

THUMB_FILES = {
    'warrior-idle.png', 'warrior-walk.png',
    'torch-red-idle.png', 'torch-red-walk.png',
    'skull.png',
}

# 把 alt 改为空字符串（这样 build.py 不会把乱码当作 caption）
for path in [
    r'D:\1\mypro\daydaydream000.github.io\posts\arpg-day1-player.md',
    r'D:\1\mypro\daydaydream000.github.io\posts\arpg-day3-camera-enemy.md',
    r'D:\1\mypro\daydaydream000.github.io\posts\arpg-day4-enemy-attack.md',
]:
    with open(path, 'rb') as f:
        raw = f.read()
    before = raw
    for fname in THUMB_FILES:
        # 找 inline img: <img src="images/arpg/<fname>" alt="..." class="arpg-thumb" ...>
        # 把 alt 改为空
        # src 后面是 alt="xxx"，xxx 包含 GBK 字节——需要正则匹配到下一个 "
        pattern = re.compile(
            rb'(<img\s+src="images/arpg/' + fname.encode('utf-8') + rb'"\s+alt=")[^"]*("\s+class="arpg-thumb")'
        )
        raw = pattern.sub(rb'\1\2', raw)
    if raw != before:
        with open(path, 'wb') as f:
            f.write(raw)
        print(f'Cleaned alt: {path}')
    else:
        print(f'No change: {path}')
