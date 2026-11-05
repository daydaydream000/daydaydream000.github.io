# -*- coding: utf-8 -*-
"""粗略版面体检：文字溢出方框 / 文字互相压盖 / 连线穿过节点方框。
不是渲染器，只按字符宽度估算（CJK 1.03em、西文 0.55em），够发现明显问题。"""
import re, sys, os

import sys
FILES = [(f, 0, 0) for f in sys.argv[1:]] or []


def tw(s, size):
    w = 0.0
    for ch in s:
        w += size * 1.03 if ord(ch) > 127 else size * 0.55
    return w


def unesc(s):
    return s.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def parse(path):
    src = open(path, encoding="utf-8").read()
    rects = []
    for m in re.finditer(r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" '
                         r'height="([-\d.]+)"[^>]*rx="([-\d.]+)"', src):
        x, y, w, h, rx = map(float, m.groups())
        rects.append((x, y, w, h, rx))
    texts = []
    src_norot = re.sub(r'<text x="0" y="0" transform="[^"]*"', '', src)
    for m in re.finditer(r'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*font-size="([\d.]+)"'
                         r'[^>]*text-anchor="(\w+)"[^>]*>(.*?)</text>', src_norot):
        x, y, fs, anchor, raw = m.group(1), m.group(2), float(m.group(3)), m.group(4), m.group(5)
        texts.append((float(x), float(y), fs, anchor, unesc(raw)))
    body = re.sub(r"<defs>.*?</defs>", "", src, flags=re.S)
    paths = []
    for m in re.finditer(r'<path d="M([^"]+)"', body):
        raw = m.group(1).strip().rstrip("z").strip()
        try:
            pts = [tuple(map(float, p.split(","))) for p in raw.split(" L")]
        except ValueError:
            continue
        if len(pts) >= 2:
            paths.append(pts)
    return rects, texts, paths


def tbox(x, y, fs, anchor, txt):
    w = tw(txt, fs)
    if anchor == "middle":
        x0 = x - w / 2
    elif anchor == "end":
        x0 = x - w
    else:
        x0 = x
    return (x0, y - fs * 0.86, x0 + w, y + fs * 0.26)


problems = 0
for name, W, H in FILES:
    path = name if os.path.isabs(name) else os.path.join(os.getcwd(), name)
    rects, texts, paths = parse(path)
    nodes = [r for r in rects if r[4] >= 6 and r[2] > 60 and 40 < r[3] < 500]
    labels = [r for r in rects if r[4] < 6]

    print("=" * 70)
    print(name, "| nodes:", len(nodes), "texts:", len(texts), "paths:", len(paths))

    # 1) 文字溢出所属方框
    for (x, y, fs, anchor, t) in texts:
        b = tbox(x, y, fs, anchor, t)
        for (rx, ry, rw, rh, _) in nodes:
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                if b[0] < rx + 4 or b[2] > rx + rw - 6:
                    if t.strip():
                        print(f"  [溢出] '{t[:38]}' 文本 {b[0]:.0f}..{b[2]:.0f} 框 {rx:.0f}..{rx+rw:.0f}")
                        problems += 1
                break

    # 2) 文字互相压盖（同一方框内相邻行的轻微接触放过）
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            a = tbox(*texts[i][:4], texts[i][4])
            b = tbox(*texts[j][:4], texts[j][4])
            ox = min(a[2], b[2]) - max(a[0], b[0])
            oy = min(a[3], b[3]) - max(a[1], b[1])
            if ox > 6 and oy > 3:
                print(f"  [重叠] '{texts[i][4][:28]}' ×× '{texts[j][4][:28]}' 重叠 {ox:.0f}×{oy:.0f}")
                problems += 1

    # 3) 连线穿过节点方框（采样）
    for pts in paths:
        hits = set()
        for k in range(len(pts) - 1):
            (x1, y1), (x2, y2) = pts[k], pts[k + 1]
            steps = max(2, int(max(abs(x2 - x1), abs(y2 - y1)) / 4))
            for s in range(steps + 1):
                px = x1 + (x2 - x1) * s / steps
                py = y1 + (y2 - y1) * s / steps
                for idx, (rx, ry, rw, rh, rrx) in enumerate(rects):
                    if rrx < 6 or rh > 500:
                        continue
                    if 0 < idx and rx + 3 < px < rx + rw - 3 and ry + 3 < py < ry + rh - 3:
                        hits.add((round(rx), round(ry), round(rw), round(rh)))
        for h in hits:
            print(f"  [穿框] 连线经过方框 x={h[0]} y={h[1]} w={h[2]} h={h[3]}")
            problems += 1

print("=" * 70)
print("problems:", problems)
