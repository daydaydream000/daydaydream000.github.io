"""
回滚：清掉之前的 {.arpg-thumb} 痕迹
然后用更可靠的方式：直接修改 markdown 源文件，把每个 ![](src) 改成包含 class 的图片
"""
import re

THUMB_FILES = {
    'warrior-idle.png', 'warrior-walk.png',
    'torch-red-idle.png', 'torch-red-walk.png',
    'skull.png',
}

# 1) 清理旧痕迹：把 "{.arpg-thumb}" 文本去掉（但保留在 src 之前的 class 属性）
# 实际渲染里出现 "]{.arpg-thumb}" 后面还有 "{.arpg-thumb}" 重复
# 回滚：把 "{.arpg-thumb})" -> ")" 同时 "){.arpg-thumb}" 也清掉
for path in [
    r'D:\1\mypro\daydaydream000.github.io\posts\arpg-day1-player.md',
    r'D:\1\mypro\daydaydream000.github.io\posts\arpg-day3-camera-enemy.md',
    r'D:\1\mypro\daydaydream000.github.io\posts\arpg-day4-enemy-attack.md',
]:
    with open(path, 'rb') as f:
        raw = f.read()
    before = raw
    # 去掉游离的 {.arpg-thumb} 文字（紧跟 ) 的或者前导 .arpg-thumb})
    # 1) ".arpg-thumb}" 后面跟 ) 的: ...images/arpg/xxx.png){.arpg-thumb}
    raw = re.sub(rb'\)\{\.arpg-thumb\}', b')', raw)
    # 2) 重复的 {.arpg-thumb}) 之类
    raw = re.sub(rb'\{\.arpg-thumb\}', b'', raw)
    if raw != before:
        with open(path, 'wb') as f:
            f.write(raw)
        print(f'Cleaned: {path}')
    else:
        print(f'No need: {path}')

# 2) 重新打 class——这次改 HTML inline <img> 写法更直接
# 找到 markdown 里所有 ![alt](images/arpg/warrior-idle.png) 这种，替换为 inline HTML
# 这样 build.py 里的 inline <img> 后处理会拿到 class 属性
for path in [
    r'D:\1\mypro\daydaydream000.github.io\posts\arpg-day1-player.md',
    r'D:\1\mypro\daydaydream000.github.io\posts\arpg-day3-camera-enemy.md',
    r'D:\1\mypro\daydaydream000.github.io\posts\arpg-day4-enemy-attack.md',
]:
    with open(path, 'rb') as f:
        raw = f.read()
    before = raw
    for fname in THUMB_FILES:
        # 匹配: ![...](images/arpg/<fname>)
        # 提取 alt 文本（中文）然后构造 <img src="..." alt="..." class="arpg-thumb">
        pattern = re.compile(
            rb'!\[([^\]]*)\]\((images/arpg/' + fname.encode('utf-8') + rb')\)'
        )
        def _repl(m):
            alt = m.group(1).decode('gbk', errors='replace')
            src = m.group(2).decode('utf-8')
            return f'<img src="{src}" alt="{alt}" class="arpg-thumb" loading="lazy" decoding="async">'.encode('utf-8')
        raw = pattern.sub(_repl, raw)
    if raw != before:
        with open(path, 'wb') as f:
            f.write(raw)
        print(f'Re-patched: {path}')
    else:
        print(f'No change: {path}')
