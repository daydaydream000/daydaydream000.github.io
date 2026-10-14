"""
为 7 张角色单图加 arpg-thumb class（用 bytes 处理 GBK 编码）
"""
THUMB_FILES = [
    'warrior-idle.png', 'warrior-walk.png',
    'torch-red-idle.png', 'torch-red-walk.png',
    'skull.png',
]

for path in [
    r'D:\1\mypro\daydaydream000.github.io\posts\arpg-day1-player.md',
    r'D:\1\mypro\daydaydream000.github.io\posts\arpg-day3-camera-enemy.md',
    r'D:\1\mypro\daydaydream000.github.io\posts\arpg-day4-enemy-attack.md',
]:
    with open(path, 'rb') as f:
        raw = f.read()
    orig = raw
    for fname in THUMB_FILES:
        # 找: ![alt](images/arpg/<fname>) 然后在 ) 前插入 {.arpg-thumb}
        marker = f'](images/arpg/{fname})'.encode('utf-8')
        replacement = f'](images/arpg/{fname}){{.arpg-thumb}}'.encode('utf-8')
        if marker in raw:
            raw = raw.replace(marker, replacement, 1)
    if raw != orig:
        with open(path, 'wb') as f:
            f.write(raw)
        print(f'Patched: {path}')
    else:
        print(f'No change: {path}')
