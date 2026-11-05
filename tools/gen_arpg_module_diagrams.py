#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARPG 模块系列配图生成器

来源工程：ARPGbegin（Unity 2022.3.62f3）
事实来源：Assets/Scripe/ 下 31 个 C# 脚本 + SampleScene.unity 的 37 条序列化引用
          + ProjectSettings/InputManager.asset 按键映射 + 6 组静态事件

布局原则（避免连线穿框）：
  纵向链式流程图 —— 所有卡片排成一列，连线只出现在卡片之间的「间隙带」里；
  旁注固定在右侧留白区，用短横虚线对接，不跨任何卡片。
  于是「线穿框」在结构上就不可能发生。

输出到 images/：
  arpg-mod-1-map.svg      模块全景（三层）
  arpg-mod-2-matrix.svg   耦合矩阵 7x7
  arpg-mod-3-player.svg   玩家与武器
  arpg-mod-4-enemy.svg    敌人 AI
  arpg-mod-5-growth.svg   成长与技能
  arpg-mod-6-items.svg    物品与商店
  arpg-mod-c1..c4.svg     四篇专文封面

运行：python tools/gen_arpg_module_diagrams.py
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "images")

SANS = "ui-sans-serif, sans-serif"
MONO = "ui-monospace, monospace"

C = {
    "ink":    "#1d2a24",
    "sub":    "#5c6b62",
    "bg":     "#f5f7f3",
    "line":   "#dfe5df",
    "in":     "#8a6a1f",
    "player": "#2f6f4f",
    "enemy":  "#a8412c",
    "data":   "#3c6e8f",
    "growth": "#0f6d86",
    "item":   "#7a4a9e",
    "ui":     "#5b4a9e",
    "world":  "#6a7f2a",
    "bad":    "#b3261e",
    "gray":   "#8a8a8a",
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tw(s, size):
    w = 0.0
    for ch in s:
        w += size * 1.04 if ord(ch) > 127 else size * 0.55
    return w


def T(x, y, s, size=12, fill=None, anchor="start", weight="400", mono=False, op=1.0):
    fam = MONO if mono else SANS
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" '
            f'fill="{fill or C["ink"]}" text-anchor="{anchor}" font-weight="{weight}" '
            f'opacity="{op}">{esc(s)}</text>')


def chip(x, y, s, size=10.5, color=None, anchor="middle"):
    """带底色的短标签，用于压在连线上。"""
    color = color or C["sub"]
    w = tw(s, size) + 12
    x0 = x - w / 2 if anchor == "middle" else x
    return (f'<rect x="{x0:.1f}" y="{y - size * 1.05:.1f}" width="{w:.1f}" '
            f'height="{size * 1.6:.1f}" rx="4" fill="#ffffff" fill-opacity="0.97"/>'
            + T(x, y, s, size, color, anchor, "500"))


def svg_head(w, h, bg=None):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}">'
            f'<rect width="{w}" height="{h}" fill="{bg or C["bg"]}"/>')


def svg_tail(keys):
    d = "<defs>"
    for k in keys:
        d += (f'<marker id="a-{k}" viewBox="0 0 12 12" refX="10.2" refY="6" '
              f'markerWidth="7.5" markerHeight="7.5" orient="auto-start-reverse">'
              f'<path d="M0,0 L12,6 L0,12 z" fill="{C.get(k, k)}"/></marker>')
    d += "</defs>"
    return d + "</svg>"


def vline(x, y1, y2, key, dash=None, w=2.2, arrow=True):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#a-{key})"' if arrow else ""
    return (f'<path d="M{x},{y1} L{x},{y2}" stroke="{C.get(key,key)}" stroke-width="{w}" '
            f'stroke-linecap="round"{da}{m}/>')


def hline(x1, x2, y, key, dash=None, w=1.6, arrow=False):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#a-{key})"' if arrow else ""
    return (f'<path d="M{x1},{y} L{x2},{y}" stroke="{C.get(key,key)}" stroke-width="{w}" '
            f'stroke-linecap="round"{da}{m}/>')


def path(pts, key, dash=None, w=2.2, arrow=True):
    d = "M" + " L".join(f"{p[0]},{p[1]}" for p in pts)
    da = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#a-{key})"' if arrow else ""
    return (f'<path d="{d}" fill="none" stroke="{C.get(key,key)}" stroke-width="{w}" '
            f'stroke-linecap="round" stroke-linejoin="round"{da}{m}/>')


def card(x, y, w, h, title, lines, color, note=None, ts=13.5, ls=11.4, sub=None):
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="#ffffff" '
         f'stroke="{color}" stroke-opacity="0.30" stroke-width="1.4"/>',
         f'<rect x="{x}" y="{y}" width="5.5" height="{h}" rx="2.7" fill="{color}" fill-opacity="0.85"/>',
         T(x + 20, y + 27, title, ts, color, weight="700")]
    yy = y + 51
    if sub:
        o.append(T(x + 20, yy, sub, 10.6, C["sub"]))
        yy += 19
    for ln in lines:
        o.append(T(x + 20, yy, ln, ls, C["ink"], mono=True))
        yy += 18.6
    if note:
        o.append(T(x + 20, yy + 2, note, 10.6, C["bad"]))
    return "".join(o)


def ghost(x, y, w, h, title, lines, color=None, fs=10.8):
    color = color or C["gray"]
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="#ffffff" '
         f'fill-opacity="0.62" stroke="{color}" stroke-opacity="0.5" stroke-dasharray="6 4"/>',
         T(x + 20, y + 26, title, 12.6, color, weight="700")]
    yy = y + 49
    for ln in lines:
        o.append(T(x + 20, yy, ln, fs, C["sub"]))
        yy += 17.4
    return "".join(o)


def diamond(cx, cy, hw, hh, text, color):
    o = [f'<polygon points="{cx},{cy-hh} {cx+hw},{cy} {cx},{cy+hh} {cx-hw},{cy}" '
         f'fill="#ffffff" stroke="{color}" stroke-opacity="0.62" stroke-width="1.5"/>']
    rows = text.split("\n")
    for i, s in enumerate(rows):
        o.append(T(cx, cy - (len(rows) - 1) * 9 + i * 18 + 4, s, 11, color, "middle", "700", mono=True))
    return "".join(o)


def head(w, main, sub):
    return T(46, 47, main, 23, C["ink"], weight="700") + T(46, 75, sub, 13.2, C["sub"])


def legend(x, y, items):
    o, xx = [], x
    for key, dash, lab in items:
        da = f' stroke-dasharray="{dash}"' if dash else ""
        o.append(f'<path d="M{xx},{y-4.5} L{xx+30},{y-4.5}" stroke="{C.get(key,key)}" '
                 f'stroke-width="2.4"{da} stroke-linecap="round"/>')
        o.append(T(xx + 38, y, lab, 11.2, C["sub"]))
        xx += 38 + tw(lab, 11.2) + 24
    return "".join(o)


# ============================================================ 链式布局引擎
class Flow:
    """纵向链：卡片单列排布，连线只出现在卡片之间的间隙带里。"""

    def __init__(self, x, w, y, gap=46, side_x=None, side_w=None):
        self.x, self.w, self.y, self.gap = x, w, y, gap
        self.side_x, = (side_x,)
        self.side_w = side_w
        self.steps = []
        self.o = []
        self.side_o = []

    # ---- 添加步骤 ----------------------------------------------------
    def one(self, title, lines, color, note=None, sub=None, h=None, side=None):
        hh = h or (54 + 18.6 * len(lines) + (19 if sub else 0) + (18 if note else 0) + 12)
        self.steps.append({"kind": "one", "title": title, "lines": lines, "color": color,
                           "note": note, "sub": sub, "h": hh, "side": side})
        return self

    def split(self, a, b, gapx=26, sides=None):
        """a/b 为 (title, lines, color, note) 四元组，并排两卡。"""
        ha = 54 + 18.6 * len(a[1]) + (18 if a[3] else 0) + 12
        hb = 54 + 18.6 * len(b[1]) + (18 if b[3] else 0) + 12
        self.steps.append({"kind": "split", "a": a, "b": b, "gapx": gapx,
                           "h": max(ha, hb), "sides": sides or (None, None),
                           "ha": ha, "hb": hb})
        return self

    def label(self, text, color=None, at="mid"):
        self.steps.append({"kind": "label", "text": text, "color": color or C["sub"],
                           "h": 30, "at": at})
        return self

    # ---- 绘制 --------------------------------------------------------
    def boxes(self):
        """返回 [(step_index, [(x,y,w,h,color)])]，供外部做旁注定位。"""
        out = []
        for i, s in enumerate(self.steps):
            if s["kind"] == "one":
                out.append((i, [(self.x, 0, self.w, s["h"], s["color"])]))
            elif s["kind"] == "split":
                gw = s["gapx"]
                w = (self.w - gw) / 2
                out.append((i, [(self.x, 0, w, s["ha"], s["a"][2]),
                                (self.x + w + gw, 0, w, s["hb"], s["b"][2])]))
            else:
                out.append((i, []))
        return out

    def build(self):
        # 1) 先算每个步骤的 y 与中心
        y = self.y
        meta = []
        for s in self.steps:
            meta.append({"y": y, "h": s["h"]})
            y += s["h"] + self.gap
        total = y - self.gap
        self.meta = meta

        # 2) 画卡片
        for i, s in enumerate(self.steps):
            top = meta[i]["y"]
            if s["kind"] == "one":
                self.o.append(card(self.x, top, self.w, s["h"], s["title"], s["lines"],
                                   s["color"], s["note"], sub=s["sub"]))
                if s["side"] and self.side_x:
                    self.o.append(hline(self.x + self.w, self.side_x, top + s["h"] / 2,
                                        "gray", dash="4 4", w=1.2))
                    self.o.append(ghost(self.side_x, top, self.side_w, s["h"],
                                        s["side"][0], s["side"][1],
                                        C.get("bad") if s["side"][2] == "bad" else C["gray"]))
            elif s["kind"] == "split":
                gw = s["gapx"]
                w = (self.w - gw) / 2
                a, b = s["a"], s["b"]
                self.o.append(card(self.x, top, w, s["ha"], a[0], a[1], a[2], a[3]))
                self.o.append(card(self.x + w + gw, top, w, s["hb"], b[0], b[1], b[2], b[3]))
                for k, sd in enumerate(s["sides"]):
                    if sd and self.side_x and k == 1:   # 只有右卡能挂旁注，否则虚线会穿过左卡
                        bx = self.x if k == 0 else self.x + w + gw
                        bh = s["ha"] if k == 0 else s["hb"]
                        self.o.append(hline(bx + w, self.side_x, top + bh / 2,
                                            "gray", dash="4 4", w=1.2))
                        self.o.append(ghost(self.side_x, top, self.side_w, bh, sd[0], sd[1],
                                            C["bad"] if sd[2] == "bad" else C["gray"]))
            else:
                self.o.append(T(self.x + 6, top + 20, s["text"], 11.2, s["color"],
                                weight="700"))

        # 3) 画连接（只在间隙带内）
        def child_x(i):
            s = self.steps[i]
            if s["kind"] == "one":
                return [self.x + self.w / 2]
            if s["kind"] == "split":
                gw, w = s["gapx"], (self.w - s["gapx"]) / 2
                return [self.x + w / 2, self.x + w + gw + w / 2]
            return None

        for i in range(len(self.steps) - 1):
            cur, nxt = self.steps[i], self.steps[i + 1]
            if cur["kind"] == "label" or nxt["kind"] == "label":
                continue
            y1 = meta[i]["y"] + meta[i]["h"]
            y2 = meta[i + 1]["y"]
            if y2 <= y1:
                continue
            mid = (y1 + y2) / 2
            key = cur["color"] if cur["kind"] != "split" else cur["a"][2]
            key = nxt["color"] if nxt["kind"] == "one" else nxt["a"][2]
            xs, xd = child_x(i), child_x(i + 1)
            if len(xs) == 1 and len(xd) == 1:
                self.o.append(vline(xs[0], y1, y2 - 1, key))
            elif len(xs) == 1 and len(xd) == 2:
                self.o.append(path([(xs[0], y1), (xs[0], mid), (xd[0], mid), (xd[0], y2 - 1)], key))
                self.o.append(path([(xs[0], mid), (xd[1], mid), (xd[1], y2 - 1)], key))
            elif len(xs) == 2 and len(xd) == 1:
                self.o.append(path([(xs[0], y1), (xs[0], mid), (xd[0], mid), (xd[0], y2 - 1)], key))
                self.o.append(path([(xs[1], y1), (xs[1], mid), (xd[0], mid)], key, arrow=False))
            else:
                self.o.append(path([(xs[0], y1), (xs[0], mid), (xd[0], mid), (xd[0], y2 - 1)], key))
                self.o.append(path([(xs[1], y1), (xs[1], mid), (xd[1], mid), (xd[1], y2 - 1)], key))

        return "".join(self.o), total

    # ---- 连接标签（压在间隙带中央）-----------------------------------
    def connect_label(self, after_index, text, color=None, dx=26):
        """在 after_index 步骤之后的间隙里放一个标签。"""
        return None  # 由外部用 chip 手工放，避免二次计算


def finish(items, w, keys, bg=None):
    """按内容实际范围决定画布高度，避免裁切。"""
    body = "".join(items)
    ys = [float(m) for m in re.findall(r'<text[^>]*\by="([-\d.]+)"', body)]
    rects = re.findall(r'<rect x="[-\d.]+" y="([-\d.]+)" width="[-\d.]+" height="([-\d.]+)"', body)
    rmax = max((float(a) + float(b) for a, b in rects), default=0.0)
    h = int(max(max(ys) + 28 if ys else 0, rmax) + 48)
    return svg_head(w, h, bg) + body + svg_tail(keys)


def _gap_y(flow, i):
    y = flow.y
    for k in range(i):
        y += flow.steps[k]["h"] + flow.gap
    return y + flow.steps[i]["h"] + flow.gap / 2


def _cx(flow):
    return flow.x + flow.w / 2


def gapchip(flow, i, text, color=None, dx=24):
    return chip(_cx(flow) + dx, _gap_y(flow, i), text, 10.2, color or C["sub"], anchor="start")


def section(y, text, color, note=None, W=1200):
    o = [f'<rect x="44" y="{y}" width="5" height="20" rx="2.5" fill="{color}"/>',
         T(60, y + 16, text, 16, color, weight="700")]
    if note:
        o.append(T(60 + tw(text, 16) + 24, y + 16, note, 11.2, C["sub"]))
    return "".join(o)


# ============================================================ 图 3 玩家与武器
def build_player():
    W = 1200
    s = []
    s.append(head(W, "玩家模块：两条武器链、一个开关、一个受击入口",
                  "PlayerMovement / Player_Combat / Player_Bow / Arrow / PlayerHealth 的真实接线"))
    s.append(legend(44, 104, [
        ("in", None, "输入"), ("player", None, "同步调用"),
        ("enemy", None, "打到敌人"), ("gray", "4 4", "旁注：坑"),
    ]))

    # ---------- 上段：近战 ----------
    y0 = 150
    s.append(section(y0, "① 近战输出链：K 键 → 挥刀 → 只打第一只", C["player"],
                     "整条链的判定点只有一处 OverlapCircleAll"))

    f = Flow(44, 560, y0 + 42, gap=48, side_x=628, side_w=528)
    f.one("输入：Slash（K）",
          ["Input.GetButtonDown(\"Slash\")", "且 player_Combat.enabled == true"], C["in"])
    f.one("PlayerMovement.Update()",
          ["player_Combat.Attack()"], C["player"])
    f.one("Player_Combat.Attack()",
          ["if (timer > 0) return      ← 2 秒冷却",
           "anim.SetBool(\"isAttacking\", true)",
           "timer = cooldown"], C["player"])
    f.one("动画事件：Slash.anim",
          ["t = 0.27  → DealDamage()",
           "t = 0.42  → FinishAttacking()"], C["player"],
          side=("为什么伤害不写在 Attack() 里",
                ["Attack() 只负责「播动画 + 上锁」；",
                 "真正的判定挂在动画帧事件上，",
                 "所以伤害时刻由美术的动画长度决定，",
                 "代码里找不到任何一秒的硬编码。"], "gray"))
    f.one("DealDamage()",
          ["OverlapCircleAll(attackPoint,",
           "  weaponRange 0.7, enemyLayer)",
           "if (hits.Length > 0)",
           "  hits[0].ChangeHealth(-1)",
           "  hits[0].Knockback(10, 0.15, 0.2)"], C["player"],
          side=("hits[0]：只结算第一个",
                ["enemies[0] 是 OverlapCircleAll 返回数组的第 0 个，",
                 "不是「离我最近的那个」，而是碰撞体缓存顺序。",
                 "两只怪叠在一起时，永远只有一只掉血；",
                 "另一只连击退都没有。"], "bad"))
    f.one("Enemy_Health.ChangeHealth(-1)",
          ["currentHealth -= 1", "if (<= 0) → 死亡广播"], C["enemy"])
    f.one("Enemy_Knockback.Knockback(...)",
          ["ChangeState(knockback)", "velocity = 反方向 × 10",
           "StunTimer：0.15s 停 → 0.2s 后回 Idle"], C["enemy"])
    frag, endy = f.build()
    s.append(frag)
    s.append(gapchip(f, 2, "冷却没到就直接 return", C["player"], 24))
    s.append(gapchip(f, 3, "动画事件回调（不是 Update）", C["player"], 24))
    s.append(gapchip(f, 4, "同步调用", C["enemy"], 24))

    # ---------- 中段：远程 ----------
    y1 = endy + 76
    s.append(section(y1, "② 远程输出链：J 键 → 挡位瞄准 → 出箭 → 物理碰撞", C["player"],
                     "这条链不用 OverlapCircleAll，交给 Rigidbody2D 自己撞"))
    f2 = Flow(44, 560, y1 + 42, gap=48, side_x=628, side_w=528)
    f2.one("输入：Shoot（J）",
           ["Input.GetButtonDown(\"Shoot\")", "且 shootTimer <= 0（0.5 秒）"], C["in"])
    f2.one("Player_Bow.Update()",
           ["playerMovement.isShooting = true",
            "anim.SetBool(\"isShooting\", true)",
            "HandleAiming() 每帧读 GetAxisRaw",
            "  → aimDirection + anim(aimX, aimY)"], C["player"],
           side=("isShooting 是谁清的",
                 ["由 Shoot() 清 —— 而 Shoot() 是动画事件。",
                  "所以「抬手」到「出箭」之间玩家不能动，",
                  "一旦动画被打断/没播完，",
                  "isShooting 会永远停在 true，",
                  "骑士永久钉在原地（不报错）。"], "bad"))
    f2.one("动画事件：Archer_Shoot_*.anim",
           ["5 个方向各一个剪辑，都挂 Shoot()",
            "t = 出箭帧 → Shoot()"], C["player"])
    f2.one("Player_Bow.Shoot()",
           ["Instantiate(arrowPrefab, launchPoint)",
            "arrow.direction = aimDirection",
            "shootTimer = 0.5",
            "isShooting = false → 交还控制权"], C["player"])
    f2.one("Arrow.Start()",
           ["velocity = direction × 8",
            "rotation = Atan2(dir.y, dir.x)",
            "Destroy(gameObject, 2s)"], C["player"])
    f2.one("Arrow.OnCollisionEnter2D",
           ["enemyLayer 命中 → -2 血 + 击退",
            "obstacleLayer → 贴到物体上（插墙）"], C["player"],
           side=("为什么不打自己脸",
                 ["Arrow 用 LayerMask 位运算判断目标层：",
                  "  (enemyLayer.value & (1 << layer)) > 0",
                  "和第 3 篇里敌人判定玩家用的是同一套写法。",
                  "好处是不依赖 tag；坏处是层配错就静默失效。"], "gray"))
    frag2, endy2 = f2.build()
    s.append(frag2)
    s.append(gapchip(f2, 1, "出手瞬间锁住移动", C["player"], 24))
    s.append(gapchip(f2, 2, "动画事件回调", C["player"], 24))
    s.append(gapchip(f2, 3, "物理碰撞（不用射线）", C["player"], 24))

    # ---------- 下段：切换 ----------
    y2 = endy2 + 76
    s.append(section(y2, "③ 武器开关：Q 键只是翻两个 enabled", C["in"],
                     "没有状态对象、没有事件、没有 UI 同步"))
    f3 = Flow(44, 560, y2 + 42, gap=48, side_x=628, side_w=528)
    f3.one("输入：ChangeEquipment（Q）", ["Input.GetButtonDown(\"ChangeEquipment\")"], C["in"])
    f3.one("Player_ChangeEqiupment.Update()",
           ["combat.enabled = !combat.enabled",
            "bow.enabled   = !bow.enabled"], C["in"])
    f3.one("两侧各自的 OnEnable / OnDisable",
           ["Player_Bow.OnEnable  → layer 0 权重 0 / layer 1 权重 1",
            "Player_Bow.OnDisable → 反过来",
            "Player_Combat 没有 OnEnable（只靠 enabled 拦 Update）"], C["player"],
           side=("用 enabled 当状态位的代价",
                 ["enabled = false 只是让 Unity 不再调 Update，",
                  "  组件本身还在、协程还在跑、对外方法照样能被调用。",
                  "所以在别处仍然可以 player_Combat.Attack()，",
                  "冷却计时（Update 里的 timer-=）却停了 —— 会卡住。",
                  "Feat：第 11 篇把 Attack() 也加了 enabled 守卫。"], "bad"))
    frag3, endy3 = f3.build()
    s.append(frag3)
    s.append(gapchip(f3, 0, "翻开关", C["in"], 24))

    # 底部说明
    yb = endy3 + 54
    s.append(ghost(44, yb, 1112, 118, "三条链的共同终点：StatsManger 与「谁判命中」",
                   ["近战：动画事件 → OverlapCircleAll → hits[0].ChangeHealth(-1)（伤害 1，判定 0.7）",
                    "远程：动画事件 → Instantiate → Rigidbody2D 碰撞 → ChangeHealth(-2)（伤害 2，速度 8）",
                    "受击：Enemy_Combat.Attack() → PlayerHealth.ChangeHealth(-damage) + PlayerMovement.Knockback(...)",
                    "三条路最后都落到 StatsManger.Instance.currentHealth 这一个 int 上。"], C["gray"]))
    return finish(s, W, ["in", "player", "enemy", "gray", "bad", "data"])



# ============================================================ 图 4 敌人 AI
def build_enemy():
    W = 1200
    s = []
    s.append(head(W, "敌人模块：一个状态机、三个动画事件、两条判定",
                  "Enemy_Movement 140 行是全场最长的脚本；Enemy_Health 是全场唯一的事件发布者"))
    s.append(legend(44, 104, [
        ("enemy", None, "敌人内部"), ("player", None, "打到玩家"),
        ("growth", "7 5", "静态事件"), ("gray", "4 4", "旁注"),
    ]))

    # ---------- ① 状态机 ----------
    y0 = 150
    s.append(section(y0, "① 状态机：4 个状态、1 个出口 ChangeState()", C["enemy"],
                     "Update 里先 CheckForPlayer() 再按状态分派"))
    f = Flow(150, 450, y0 + 46, gap=52, side_x=628, side_w=528)
    f.one("Idle", ["velocity = 0", "anim.isIdle = true"], C["enemy"], h=96)
    f.one("Chasing", ["朝玩家方向 velocity = 2", "翻转 localScale.x 换朝向",
                      "anim.isChasing = true"], C["enemy"], h=104)
    f.one("Attacking", ["velocity = 0（停下挨打）", "动画 Attack_Right 开始播",
                        "anim.isAttacking = true"], C["enemy"], h=104,
          side=("进门与出门不是同一个函数",
                ["进 Attacking：CheckForPlayer() 直接调 ChangeState()。",
                 "出 Attacking：靠动画事件 t=0.59 调 ChangeState(0)，",
                 "  参数是 int 0 —— 也就是 Idle。",
                 "所以「打完回 Idle」这一步写在 .anim 文件里，不在 C# 里。"], "gray"))
    f.one("knockback", ["Update 整个跳过（不再感知）", "velocity = 反方向 × 10",
                        "状态由协程兜底"], C["enemy"], h=104,
          side=("击退会把状态机按在地上",
                ["Enemy_Knockback.Knockback() 先 ChangeState(knockback)，",
                 "然后协程：0.15s 后 velocity=0，再过 0.2s 回 Idle。",
                 "而 Update 里 if (state != knockback) 才跑感知，",
                 "所以这 0.35 秒敌人是「聋哑」的 —— 这是有意的。"], "gray"))
    frag, endy = f.build()
    s.append(frag)
    s.append(gapchip(f, 0, "距离 ≤ 2 且冷却好", C["enemy"], -22))
    s.append(gapchip(f, 1, "距离 > 2", C["enemy"], -22))
    s.append(gapchip(f, 2, "被打中 → Knockback()", C["player"], -22))

    last = f.meta[3]
    first = f.meta[0]
    lx = 118
    s.append(path([(150, last["y"] + last["h"]), (lx, last["y"] + last["h"]),
                   (lx, first["y"]), (150, first["y"])], "enemy", dash="6 4", w=1.8))
    s.append(chip(lx + 8, (last["y"] + last["h"] + first["y"]) / 2,
                  "0.35s 后回 Idle", 10, C["player"], anchor="start"))

    # ---------- ② 攻击玩家链 ----------
    y1 = endy + 82
    s.append(section(y1, "② 攻击玩家链：每帧感知 → 状态切换 → 动画事件才真正扣血", C["enemy"],
                     "Enemy_Movement.Attack() 自己只打一行 Debug.Log，真正的伤害在动画文件里"))
    f2 = Flow(44, 560, y1 + 44, gap=50, side_x=628, side_w=528)
    f2.one("Enemy_Movement.CheckForPlayer()",
           ["每帧调用（state != knockback）",
            "OverlapCircleAll(detectionPoint,",
            "  playerDetectRange 4.14, playerLayer)"], C["enemy"])
    f2.one("决策三分支",
           ["hits.Length == 0  → Idle",
            "距离 ≤ 2 且冷却 <= 0 → Attacking",
            "距离 > 2 且非 Attacking → Chasing",
            "命中后 attackCooldownTimer = 2"], C["enemy"])
    f2.one("ChangeState(Attacking)",
           ["anim.SetBool(\"isAttacking\", true)",
            "Animator 播 Attack_Right",
            "ChangeState 是唯一出口：先关旧 bool 再开新 bool"], C["enemy"])
    f2.one("动画事件 t = 0.30 → Attack()",
           ["Attack_Right.anim 里挂的函数名是 Attack",
            "广播给同物体上所有组件的同名方法：",
            "  Enemy_Movement.Attack() → 只有 Debug.Log",
            "  Enemy_Combat.Attack()   → 真正判定"], C["enemy"],
           side=("为什么两个同名方法都会收到",
                 ["动画事件按「函数名 + 参数签名」广播给该 GameObject",
                  "上的所有组件，不指定接收者。",
                  "于是两个 Attack() 同时被调用 —— 一个空转，一个干活。",
                  "看起来像写错了，实际是有意留的占位。"], "bad"))
    f2.one("Enemy_Combat.Attack()",
           ["OverlapCircleAll(attackPoint,",
            "  weaponRange 0.8, playerLayer)",
            "if (hits.Length > 0)",
            "  hits[0].ChangeHealth(-1)",
            "  hits[0].Knockback(10, 0.2)"], C["enemy"])
    f2.one("玩家侧：两件事同时发生",
           ["PlayerHealth.ChangeHealth(-1)",
            "  StatsManger.currentHealth -= 1",
            "  HP 文本播 TextUpdate",
            "  <= 0 则 SetActive(false)",
            "PlayerMovement.Knockback(10, 0.2)",
            "  isKnockback 锁 0.2 秒不读输入"], C["player"],
           side=("只取 hits[0] 的第二处",
                 ["Enemy_Combat 和 Player_Combat 一模一样地只处理 hits[0]。",
                  "两处都是「多目标只结算第一个」。",
                  "玩家被两只怪同时围住时，每帧只有一只真的打到人。"], "bad"))
    frag2, endy2 = f2.build()
    s.append(frag2)
    s.append(gapchip(f2, 1, "状态切换", C["enemy"], 24))
    s.append(gapchip(f2, 2, "动画开始", C["enemy"], 24))
    s.append(gapchip(f2, 3, "动画事件回调", C["enemy"], 24))
    s.append(gapchip(f2, 4, "同步调用", C["player"], 24))

    # ---------- ③ 敌人死亡链 ----------
    y2 = endy2 + 78
    s.append(section(y2, "③ 敌人死亡链：全场唯一的事件发布点", C["growth"],
                     "expReward 写在敌人身上：数量由敌人配，怎么用由 ExpManager 决定"))
    f3 = Flow(44, 560, y2 + 44, gap=50, side_x=628, side_w=528)
    f3.one("玩家打过来",
           ["hits[0].ChangeHealth(-1)   近战，伤害 1",
            "Arrow.OnCollisionEnter2D  远程，伤害 2"], C["player"])
    f3.one("Enemy_Health.ChangeHealth(int)",
           ["currentHealth += amount",
            "if (currentHealth > maxHealth) 夹回上限",
            "if (currentHealth <= 0)"], C["enemy"])
    f3.one("死亡广播",
           ["OnMonsterDefeated(expReward)   裸调用",
            "Destroy(gameObject)"], C["enemy"],
           side=("为什么必须先广播再销毁",
                 ["Destroy 是帧末才真的移除对象，顺序反了当帧也不会崩；",
                  "但「发奖励」在语义上必须早于「我不存在了」，",
                  "不能靠「销毁是延迟的」这个实现细节兜底。"], "gray"))
    f3.one("ExpManager.GainExperience(10)",
           ["currentExp += 10", "够门槛就 LevelUp()", "UpdateUI() 刷经验条"], C["growth"],
           side=("没有 ?.Invoke 的代价",
                 ["OnMonsterDefeated 是裸调用。若这一刻没有订阅者",
                  "（比如挂着 ExpManager 的 ExpCanvas 被 SetActive(false)），",
                  "就会抛 NullReferenceException，Destroy 永不执行。",
                  "结果：血量已 ≤ 0 的敌人还站着、还追人、还打人。"], "bad"))
    frag3, endy3 = f3.build()
    s.append(frag3)
    s.append(gapchip(f3, 1, "血量归零", C["enemy"], 24))
    s.append(gapchip(f3, 2, "静态事件", C["growth"], 24))

    yb = endy3 + 56
    s.append(ghost(44, yb, 1112, 100, "一句话分清四个脚本的职责",
                   ["Enemy_Movement   决定「什么时候打」 —— 感知 + 状态机 + 冷却",
                    "Enemy_Combat     决定「打到谁」    —— OverlapCircleAll + 扣血 + 击退",
                    "Enemy_Health     决定「死了给什么」—— expReward + 广播 + 销毁",
                    "Enemy_Knockback  决定「被打飞多远」—— 状态锁 + 协程"], C["enemy"]))
    return finish(s, W, ["enemy", "player", "growth", "gray", "bad", "in"])


# ============================================================ 图 5 成长链
def build_growth():
    W = 1200
    s = []
    s.append(head(W, "成长链：从一个 int 走到一条真能改属性的路",
                  "击杀 → 经验 → 升级 → 能力点 → 花点 → 技能效果 → 属性。六段里五段靠事件，只有最后一段直达单例。"))
    s.append(legend(44, 104, [
        ("growth", None, "经验/技能"), ("player", None, "直接调用"),
        ("data", None, "写单例属性"), ("gray", "4 4", "旁注"),
    ]))

    y0 = 150
    s.append(section(y0, "① 主链：三段发布、三段订阅", C["growth"],
                     "每一层都只发「发生了什么」，不指定谁来听"))
    f = Flow(44, 560, y0 + 46, gap=50, side_x=628, side_w=528)
    f.one("发布①：敌人死了",
           ["Enemy_Health.ChangeHealth(-1)",
            "currentHealth <= 0",
            "OnMonsterDefeated(expReward)   expReward = 10"], C["enemy"])
    f.one("订阅①：ExpManager.GainExperience(10)",
           ["currentExp += 10",
            "if (currentExp >= expToLevel) LevelUp()",
            "UpdateUI()"], C["growth"],
           side=("这里用的是 if，不是 while",
                 ["一次只结算一级。若将来出现 +100 的经验卷轴：",
                  "  0 + 100 → 升 1 级扣 10 → currentExp 停在 90，",
                  "  而新门槛只有 12。于是条满、等级不动，",
                  "  多出来的 7 级全压在口袋里。",
                  "现在没炸，只因一只怪只给 10 点、门槛起步也是 10。"], "bad"))
    f.one("发布②：升级了",
           ["level++",
            "currentExp -= expToLevel",
            "expToLevel = RoundToInt(expToLevel × 1.2)",
            "OnLevelUp?.Invoke(1)"], C["growth"],
           side=("先减、再乘，两步都用旧门槛",
                 ["顺序写成「先乘再减」的话，第一次升级会扣 12 而不是 10，",
                  "玩家凭空少 2 点经验，而且每次升级都吞一点。",
                  "门槛序列：10 → 12 → 14 → 17 → 20 → 24 → 29 → 35"], "gray"))
    f.one("订阅②：SkillTreeManager.UpdateAbilityPoints(1)",
           ["availablePoints += 1",
            "pointsText = \"Points: \" + n",
            "场景初始 availablePoints = 5"], C["growth"])
    f.one("玩家点技能按钮",
           ["Button.onClick → CheckAvailablePoints(slot)",
            "if (availablePoints > 0) slot.TryUpgradeSkill()",
            "  currentLevel++",
            "  发布③ OnAbilityPointSpent(this)",
            "  if 满级 → OnSkillMaxed(this)"], C["growth"],
           side=("点数只认「有没有」，不认「几个」",
                 ["HandleAbilityPointSpent 只判断 availablePoints > 0 就扣 1。",
                  "一个 5 级的 Max Health Boost 和 1 级的 Sword Slash",
                  "都只扣 1 点 —— 技能等级越高越划算（白送）。",
                  "而 availablePoints 本身是 Inspector 硬编码的 5，不是存档。"], "bad"))
    f.one("订阅③：三个订阅者同时收到 OnAbilityPointSpent",
           ["SkillTreeManager  点数 -1",
            "SkillManager      按 skillName 分支",
            "  \"Max Health Boost\" → UpdateMaxHealth(1)",
            "  \"Sword Slash\"      → combat.enabled = true",
            "  default             → LogWarning(\"Error\" + name)"], C["growth"])
    f.one("StatsManger.UpdateMaxHealth(1)",
           ["maxHealth += 1",
            "healthText 立刻刷新",
            "（全项目唯一「等级真的影响数值」的地方）"], C["data"],
           side=("24 个格子里只有 4 份 SkillSO",
                 ["MaxHealthBoost × 15    2Boost × 4",
                  "3Boost × 4             Combat(Sword Slash) × 1",
                  "2Boost / 3Boost 的名字不在 SkillManager 的 switch 里，",
                  "点满 4 × 5 级只会打 20 行 LogWarning，什么也不发生。"], "bad"))
    frag, endy = f.build()
    s.append(frag)
    s.append(gapchip(f, 0, "静态事件", C["growth"], 24))
    s.append(gapchip(f, 1, "静态事件 OnLevelUp", C["growth"], 24))
    s.append(gapchip(f, 3, "静态事件 OnAbilityPointSpent", C["growth"], 24))
    s.append(gapchip(f, 4, "同步调用", C["data"], 24))

    # ---------- ② 断掉的那条边 ----------
    y1 = endy + 78
    s.append(section(y1, "② 这里少一条边：升级 → 属性", C["bad"],
                     "LevelUp() 只动自己的三个字段，从不调用 StatsManger"))
    f2 = Flow(44, 560, y1 + 46, gap=50, side_x=628, side_w=528)
    f2.one("LevelUp() 实际做了什么",
           ["level++                    ← 只是个计数器",
            "currentExp -= expToLevel",
            "expToLevel = RoundToInt(×1.2)",
            "OnLevelUp?.Invoke(1)       ← 只发「涨了 1 点」",
            "没有任何一行碰到 StatsManger"], C["bad"])
    f2.one("结果：10 级和 1 级手感完全一样",
           ["damage 仍然 1（打小怪三刀）",
            "speed 仍然 5",
            "maxHealth 仍然 20",
            "升级的全部意义 = 经验条归零 + 数字 +1"], C["bad"],
           side=("为什么这不完全是 bug",
                 ["那一天的验收目标就是「经验能流动」，不是数值平衡，",
                  "所以先让链路通、数值后调是合理的取舍。",
                  "但要知道：现在等级是「解锁点数用的计数器」，",
                  "不是成长曲线。想补的话别在 LevelUp() 里直接改字段，",
                  "而是走 StatsManger 的方法 + StatsUI 订阅刷新。"], "gray"))
    f2.one("真正在改数值的只有技能",
           ["MaxHealthBoost → UpdateMaxHealth(1)  （每级 +1，最多 5 级）",
            "Sword Slash   → combat.enabled = true",
            "其余 22 个格子 → 没有对应的 switch 分支"], C["data"])
    frag2, endy2 = f2.build()
    s.append(frag2)
    s.append(gapchip(f2, 0, "该有却没有的调用", C["bad"], 24))

    # ---------- ③ 面板为什么不同步 ----------
    y2 = endy2 + 74
    s.append(section(y2, "③ 属性面板是启动快照", C["ui"],
                     "StatsUI.UpdateAllStats() 只在 Start() 里调一次"))
    f3 = Flow(44, 560, y2 + 46, gap=48, side_x=628, side_w=528)
    f3.one("StatsUI.Start()",
           ["UpdateAllStats() → UpdateDamage() + UpdateSpeed()",
            "把 StatsManger 的值写进 8 个 statsSlots 的文本"], C["ui"])
    f3.one("之后再也不刷新",
           ["UpdateSpeed() 会顺手调 statsUI.UpdateAllStats()",
            "所以吃加速道具后面板会变；",
            "但 UpdateMaxHealth / UpdateHealth 不调它",
            "→ 加血、掉血后面板都是旧数字"], C["ui"],
           side=("同一个类里两种命运",
                 ["UpdateSpeed 里有 statsUI.UpdateAllStats()，",
                  "UpdateMaxHealth 与 UpdateHealth 里没有。",
                  "这不是设计，是三个方法分别手写的结果 ——",
                  "典型的「忘了在入口处统一刷新」。"], "bad"))
    frag3, endy3 = f3.build()
    s.append(frag3)

    yb = endy3 + 54
    s.append(ghost(44, yb, 1112, 104, "这条链最值得抄的一点：三层发布者都不认识订阅者",
                   ["Enemy_Health 只发「死了，值 10 点」—— 不认识 ExpManager，也不认识技能树。",
                    "ExpManager 只发「升级了」—— 不认识 SkillTreeManager，也不认识 UI。",
                    "SkillSlot 只发「有人花点了」—— 不认识 SkillManager 的 switch。",
                    "任何一层换实现，其余两层都不用改。这就是 6 组事件里最有价值的那 3 组。"], C["growth"]))
    return finish(s, W, ["enemy", "growth", "player", "data", "ui", "gray", "bad"])


# ============================================================ 图 6 物品与商店
def build_items():
    W = 1200
    s = []
    s.append(head(W, "物品与商店：从地上捡到口袋里，再从口袋里换成钱",
                  "Loot → InventoryManager → InventorySlot → UseItem / ShopManager。物品是数据，面板只是它的投影。"))
    s.append(legend(44, 104, [
        ("item", None, "物品链路"), ("growth", "7 5", "静态事件"),
        ("data", None, "写单例属性"), ("gray", "4 4", "旁注"),
    ]))

    # ---------- ① 拾取与背包 ----------
    y0 = 150
    s.append(section(y0, "① 拾取与背包：地上 → 格子里", C["item"],
                     "整条链只有两个数据结构：ItemSo 和 InventorySlot"))
    f = Flow(44, 560, y0 + 46, gap=50, side_x=628, side_w=528)
    f.one("ItemSo（ScriptableObject）",
           ["itemName · itemDescription · icon",
            "isGold · stackSize（默认 3）",
            "currentHealth · maxHealth · speed · damage",
            "duration（临时效果的时长）"], C["item"],
           side=("四份资产，两种用途",
                 ["Gold       isGold = 1，只走金币计数，不占格子",
                  "Steak      全 0，纯道具（没有效果）",
                  "Mushroom   全 0",
                  "Pumpkin    +1 血 +1 上限 +1 速度，持续 5 秒",
                  "→ 只有 Pumpkin 同时踩到了「属性」和「临时」两条路"], "gray"))
    f.one("Loot.OnTriggerEnter2D",
           ["if (CompareTag(\"Player\") && canBePickUp)",
            "  anim.Play(\"LootPickup\")",
            "  OnItemLooted?.Invoke(itemSo, quantity)",
            "  Destroy(gameObject, 0.5f)",
            "Initialize() 先置 canBePickUp = false"], C["item"])
    f.one("订阅：InventoryManager.AddItem(itemSo, qty)",
           ["if (itemSo.isGold)",
            "  gold += qty → 只刷 goldText → return",
            "先找同类且未满的格，补满",
            "再找空网格，放进去",
            "仍然放不下 → DropLoot(溢出部分)"], C["item"],
           side=("金币和物品是两条完全不同的路",
                 ["isGold 一进来就分流：金币只加数字，不占格子、不堆叠、",
                  "也不参与 DropLoot。",
                  "于是任何一处忘了刷 goldText，就会出现",
                  "「钱在涨但数字不动」或「数字变了但钱没变」。"], "bad"))
    f.split(("格子：左键", ["activeShop != null → 卖出",
                            "否则 → inventoryManager.UseItem(this)",
                            "（加血类道具满血时直接 return）"], C["item"], None),
            ("格子：右键", ["inventoryManager.DropItem(this)",
                            "→ DropLoot(slot.itemSo, 1)",
                            "→ quantity-- → UpdateUI()"], C["item"], None))
    f.one("InventoryManager.UseItem(slot)",
           ["useItem.ApplyItemEffects(slot.itemSo)",
            "slot.quantity--",
            "if (quantity <= 0) itemSo = null",
            "slot.UpdateUI()"], C["item"])
    f.one("UseItem.ApplyItemEffects(itemSo)",
           ["currentHealth > 0 → StatsManger.UpdateHealth(+n)",
            "maxHealth > 0  → UpdateMaxHealth(+n)",
            "speed > 0      → UpdateSpeed(+n)",
            "duration > 0   → 启动协程，到期把三项反向扣回"], C["data"])
    f.one("StatsManger",
           ["currentHealth / maxHealth / speed 改变",
            "healthText 立即刷新",
            "UpdateSpeed 会顺手调 statsUI.UpdateAllStats()"], C["data"])
    frag, endy = f.build()
    s.append(frag)
    s.append(gapchip(f, 0, "静态事件 OnItemLooted", C["growth"], 24))
    s.append(gapchip(f, 2, "溢出回到地上", C["item"], 24))
    s.append(gapchip(f, 4, "同步调用", C["data"], 24))

    # ---------- ② 商店 ----------
    y1 = endy + 78
    s.append(section(y1, "② 商店：一个人、一台副相机、三档货", C["item"],
                     "开店 = 暂停 + 填格 + 亮面板；事件所有权在 ShopKeeper 手上"))
    f2 = Flow(44, 560, y1 + 46, gap=50, side_x=628, side_w=528)
    f2.one("ShopKeeper.OnTriggerEnter2D",
           ["CompareTag(\"Player\") → playerInRange = true",
            "同时 anim.SetBool(\"playerInRange\", true)"], C["item"])
    f2.one("Update()：Interact（K）",
           ["Time.timeScale = 0",
            "currentShopKeeper = this",
            "OnShopStateChanged(shopManager, true)",
            "面板 α=1 / 挡射线 / 可点",
            "副相机移到店主位置并 SetActive(true)",
            "OpenItemShop()"], C["item"],
           side=("K 绑了两次",
                 ["Slash    → PlayerMovement.Update",
                  "Interact → ShopKeeper.Update",
                  "两者都是 K。走进触发圈按 K：一边挥刀、一边开店。",
                  "这不是「偶发」，是 100% 复现的输入冲突。"], "bad"))
    f2.one("ShopManager.PopulateShopItems(list)",
           ["逐格 ShopSlot.Initialize(itemSo, price)",
            "  填图标、名字、价格",
            "多出来的格子 SetActive(false)",
            "三档表：shopItems / shopWeapons / shopArmour"], C["item"])
    f2.one("ShopSlot.OnBuyBottonClicked()",
           ["shopManager.TryBuyItem(itemSo, price)",
            "  if (gold >= price && HasSpaceForItem)",
            "    gold -= price → AddItem(itemSo, 1)"], C["item"],
           side=("HasSpaceForItem 只查「有没有空」",
                 ["它遍历背包：找到同类未满格、或任一空格就返回 true。",
                  "于是「金币够 + 有一格空」就允许买。",
                  "看起来没问题 —— 直到你把金币和物品当成两类东西。"], "gray"))
    f2.split(("关店：Cancel（Esc）", ["Time.timeScale = 1",
                                      "OnShopStateChanged(shopManager, false)",
                                      "面板 α=0 / 不挡射线",
                                      "副相机 SetActive(false)"], C["item"], None),
             ("卖出：InventorySlot 左键", ["activeShop.SellItem(itemSo)",
                                          "  在 shopSlots 里找同款",
                                          "  找到 → gold += slot.price",
                                          "  找不到 → 直接 return",
                                          "然后才 quantity--"], C["item"], None),
             sides=(None, ("这里会吞物品",
                           ["InventorySlot 先调 SellItem，然后无条件 quantity--。",
                            "而 SellItem 找不到同款时什么都不做就 return。",
                            "于是「卖一个这家店不收的东西」= 物品凭空少一个、钱不变。"], "bad")))
    frag2, endy2 = f2.build()
    s.append(frag2)
    s.append(gapchip(f2, 0, "静态事件 OnShopStateChanged", C["growth"], 24))
    s.append(gapchip(f2, 2, "点买", C["item"], 24))

    # ---------- ③ 断链 ----------
    y2 = endy2 + 74
    s.append(section(y2, "③ 三处「看起来接上了、其实没接上」", C["bad"], None))
    f3 = Flow(44, 560, y2 + 40, gap=48, side_x=628, side_w=528)
    f3.one("① 敌人击杀不掉物品",
           ["Enemy_Health 死亡只发 OnMonsterDefeated(expReward)",
            "全项目没有任何一处「敌人死了 → 生成 Loot」",
            "地上会出现的东西只有三种来源：",
            "  · 背包满时 AddItem 的 DropLoot 溢出",
            "  · 右键 DropItem",
            "  · 场景里手工摆的 5 个 LootPrefab"], C["bad"],
           side=("为什么这一条最要命",
                 ["经验链是通的：击杀 → 经验 → 升级 → 点数 → 技能 → 属性。",
                  "物品链也是通的：地上 → 背包 → 使用 / 卖出。",
                  "但两条链之间没有接头 ——",
                  "所以「打怪变强」和「打怪有 loot」是两套世界。",
                  "加一行掉落表就能接上，这是最划算的下一个改动。"], "bad"))
    f3.one("② 背包没有开关",
           ["InventoryCanvas 上没有 Toggle 组件",
            "sortingOrder = −1，常驻在场景最底层",
            "不在 UIManager 下，也不受 Time.timeScale 影响"], C["bad"])
    f3.one("③ 面板互斥靠同一个 timeScale",
           ["StatsUI 开面板 → timeScale = 0",
            "ToggleSkillTree 开面板 → timeScale = 0",
            "ShopKeeper 开店 → timeScale = 0",
            "三处各自记一个 bool，谁也不看谁",
            "→ 先开属性面板再按 K：两个面板同时亮着"], C["bad"])
    frag3, endy3 = f3.build()
    s.append(frag3)

    yb = endy3 + 54
    s.append(ghost(44, yb, 1112, 104, "结构上最漂亮的一处",
                   ["ItemSo 只是数据，InventorySlot 只是它的投影。",
                    "同一个 ItemSo 能躺在背包里、挂在商店格上、也能躺在地上 ——",
                    "三处都只是持有同一个 SO 引用，谁改了数据全体立刻一致（因为是同一个对象）。",
                    "这也是为什么商店卖完不会「生成副本」：从头到尾只有一个。"], C["item"]))
    return finish(s, W, ["item", "growth", "data", "gray", "bad"])


# ============================================================ 图 1 模块全景
def build_map():
    W = 1200
    s = []
    s.append(head(W, "ARPG 工程的 7 个模块：三层、五类接线",
                  "31 个脚本 / 1435 行 / 1 个场景。箭头颜色代表依赖性质；同层横向关系在底部用摘要条说明。"))
    s.append(legend(44, 108, [
        ("player", None, "直接引用"),
        ("data", "3 3", "单例读取"),
        ("growth", "7 5", "静态事件"),
        ("bad", "5 4", "该有却没有"),
    ]))

    # ---------- Band A ----------
    ax, ay, aw, ah = 44, 148, 1112, 104
    s.append(f'<rect x="{ax}" y="{ay}" width="{aw}" height="{ah}" rx="9" fill="#ffffff" '
             f'stroke="{C["in"]}" stroke-opacity="0.30"/>')
    s.append(f'<rect x="{ax}" y="{ay}" width="5.5" height="{ah}" rx="2.7" fill="{C["in"]}" fill-opacity="0.85"/>')
    s.append(T(ax + 20, ay + 26, "① 输入层 · 7 个轴（InputManager.asset）", 13.2, C["in"], weight="700"))
    cols = [
        ["Slash             K", "Shoot             J"],
        ["Interact          K   ← 与 Slash 同键", "ChangeEquipment   Q"],
        ["ToggleStats       1", "ToggleSkillTree   2"],
        ["Cancel         Escape", "Horizontal / Vertical   方向键 + WASD"],
    ]
    for ci, col in enumerate(cols):
        for ri, ln in enumerate(col):
            s.append(T(ax + 24 + ci * 276, ay + 54 + ri * 20, ln, 10.8, C["ink"], mono=True))

    # ---------- Band B ----------
    bw, bgap = 254, 32
    by, bh = 322, 196
    bx = [44 + i * (bw + bgap) for i in range(4)]
    bands = [
        ("② 玩家与武器", ["PlayerMovement    65 行", "Player_Combat     62 行",
                        "Player_Bow       71 行", "Arrow             56 行",
                        "PlayerHealth      24 行", "Player_ChangeEqiupment"], C["player"]),
        ("③ 敌人", ["Enemy_Movement   140 行", "Enemy_Combat      37 行",
                   "Enemy_Health      30 行", "Enemy_Knockback    30 行",
                   "", "场景里只有 1 只 Enemy_Torch"], C["enemy"]),
        ("④ 成长与技能", ["ExpManager        60 行", "SkillTreeManager  63 行",
                        "SkillManager      32 行", "SkillSlot         81 行 ×24",
                        "SkillSO           13 行 ×4", "6 组静态事件里的 3 组"], C["growth"]),
        ("⑤ 物品与商店", ["ItemSo            23 行", "Loot              51 行",
                        "InventoryManager  98 行", "InventorySlot     79 行",
                        "ShopKeeper        92 行", "ShopManager       75 行"], C["item"]),
    ]
    for i, (t, lines, col) in enumerate(bands):
        s.append(card(bx[i], by, bw, bh, t, lines, col, ts=12.8, ls=10.2))

    # ---------- Band C ----------
    cy, ch = 612, 148
    s.append(card(44, cy, 550, ch, "⑥ 数据层 · StatsManger（单例）",
                  ["static Instance（Awake 里赋值，重复则销毁自己）",
                   "damage 1 · weaponRange 0.7 · speed 5",
                   "knockbackForce 20 · knockbackTime 0.15 · stunTime 0.2",
                   "maxHealth 20 · currentHealth 20",
                   "全项目 20 处 StatsManger.Instance"], C["data"], ts=12.8, ls=10.2))
    s.append(card(614, cy, 542, ch, "⑦ 表现层 · 5 张 Canvas + 关卡触发器",
                  ["ExpCanvas       经验条 / 等级文本",
                   "StatsPanel       Esc 属性面板（8 个格）",
                   "SkillCanvass     2 键技能树（24 个格）",
                   "ShopCanvas       商店 + 悬停信息框",
                   "InventoryCanvas  背包（常驻，没有开关）",
                   "Elevation_Entry / Exit   改 sortingOrder 15 / 10"], C["ui"], ts=12.8, ls=10.2))

    # ---------- A → B 竖直连线（间隙 252..322）----------
    g1a, g1b = ay + ah, by
    m1 = (g1a + g1b) / 2
    s.append(vline(bx[0] + bw / 2, g1a, g1b - 1, "in"))
    s.append(vline(bx[3] + bw / 2, g1a, g1b - 1, "in"))
    s.append(chip(bx[0] + bw / 2 + 14, m1, "Slash / Shoot / Q / 1 / 2 / Esc", 9.8, C["in"], "start"))
    s.append(chip(bx[3] + bw / 2 + 14, m1, "Interact（K，和 Slash 同键）", 9.8, C["in"], "start"))

    # ---------- B → C 竖直总线（间隙 518..612，90px）----------
    g2a, g2b = by + bh, cy
    m2 = (g2a + g2b) / 2
    # 玩家 → 数据
    s.append(vline(bx[0] + bw / 2, g2a, g2b - 1, "data"))
    s.append(chip(bx[0] + bw / 2 + 14, m2, "读 damage / speed / 击退三件套", 9.8, C["data"], "start"))
    # 成长 → 数据（折线，走 y = g2a+30）
    s.append(path([(bx[2] + bw / 2 - 26, g2a), (bx[2] + bw / 2 - 26, g2a + 30),
                   (516, g2a + 30), (516, g2b - 1)], "data", dash="3 3"))
    # 物品 → 数据（折线，走 y = g2a+56）
    s.append(path([(bx[3] + bw / 2 - 26, g2a), (bx[3] + bw / 2 - 26, g2a + 56),
                   (556, g2a + 56), (556, g2b - 1)], "data", dash="3 3"))
    # 成长 → 表现（竖直）
    s.append(vline(bx[2] + bw / 2 + 40, g2a, g2b - 1, "growth"))
    # 物品 → 表现（竖直）
    s.append(vline(bx[3] + bw / 2 + 40, g2a, g2b - 1, "item"))
    s.append(chip(566, g2a + 22, "UpdateMaxHealth(1)（技能改属性）", 9.8, C["data"], "start"))
    s.append(chip(566, g2a + 48, "UpdateHealth / MaxHealth / Speed（吃道具）", 9.8, C["data"], "start"))
    s.append(chip(bx[2] + bw / 2 + 54, m2 + 18, "expSlider / pointsText", 9.8, C["growth"], "start"))
    s.append(chip(bx[3] + bw / 2 + 54, m2 + 18, "goldText / 格子 / 面板", 9.8, C["item"], "start"))

    # ---------- 同层关系摘要条 ----------
    yh = cy + ch + 52
    s.append(T(44, yh, "同层之间的四条关系（为避免连线穿卡，这里改用文字表述）", 15, C["ink"], weight="700"))
    rows = [
        ("敌人 → 玩家", "player", "Enemy_Combat.Attack() → hits[0].ChangeHealth(-1) + PlayerMovement.Knockback(10, 0.2)"),
        ("玩家 → 敌人", "player", "Player_Combat.DealDamage() / Arrow.OnCollisionEnter2D → Enemy_Health.ChangeHealth + Enemy_Knockback.Knockback"),
        ("敌人 → 成长", "growth", "Enemy_Health 死亡时 OnMonsterDefeated(expReward = 10) → ExpManager.GainExperience（唯一的击杀→成长入口）"),
        ("成长 → 物品", "bad", "✗ 不存在：敌人只广播经验，全场没有「死了生成 Loot」的掉落表；地上的东西全来自背包溢出或手工摆放"),
    ]
    yy = yh + 30
    for left, col, right in rows:
        s.append(f'<rect x="44" y="{yy - 14}" width="6" height="20" rx="3" fill="{C[col]}" fill-opacity="0.8"/>')
        s.append(T(60, yy, left, 11.4, C[col], weight="700"))
        s.append(T(196, yy, right, 10.8, C["sub"]))
        yy += 30

    # ---------- 五类接线 ----------
    yb = yy + 30
    s.append(T(44, yb, "五类接线，各自解决一个问题", 16, C["ink"], weight="700"))
    kinds = [
        ("拖 Inspector 引用", C["player"],
         ["双方都知道对方的类型", "最快、最硬、最难换", "例：Player_Bow.playerMovement"]),
        ("单例读取", C["data"],
         ["不用拖，随处可取", "全局可变、难测试", "例：StatsManger.Instance"]),
        ("静态事件", C["growth"],
         ["发布方不认识订阅者", "忘了退订就静默失效", "例：OnMonsterDefeated"]),
        ("enabled 当开关", C["in"],
         ["一行切功能", "拦不住别人直接调方法", "例：Q 切 combat / bow"]),
        ("动画事件", C["ui"],
         ["时机由动画决定", "函数名写错不报错", "例：DealDamage / Attack / Shoot"]),
    ]
    kw = (1112 - 4 * 18) / 5
    for i, (t, col, lines) in enumerate(kinds):
        x = 44 + i * (kw + 18)
        s.append(f'<rect x="{x:.1f}" y="{yb + 16}" width="{kw:.1f}" height="128" rx="8" '
                 f'fill="#ffffff" stroke="{col}" stroke-opacity="0.32"/>')
        s.append(f'<rect x="{x:.1f}" y="{yb + 16}" width="{kw:.1f}" height="4" rx="2" '
                 f'fill="{col}" fill-opacity="0.8"/>')
        s.append(T(x + 14, yb + 42, t, 11.6, col, weight="700"))
        for k, ln in enumerate(lines):
            s.append(T(x + 14, yb + 66 + k * 18, ln, 10, C["sub"]))
    return finish(s, W, ["in", "player", "enemy", "data", "growth", "item", "ui", "bad", "gray"])


# ============================================================ 图 2 耦合矩阵
MODULES = [
    ("输入", "Input", C["in"], "7 个轴，直接喂 5 个 Update"),
    ("玩家", "Player", C["player"], "5 脚本互拖，2 处外部消费者"),
    ("敌人", "Enemy", C["enemy"], "既发事件也直接打玩家"),
    ("数据", "Stats", C["data"], "被 4 个模块读写，自己零依赖"),
    ("成长", "Growth", C["growth"], "订阅升级并回写属性"),
    ("物品", "Item", C["item"], "最长的一条链"),
    ("表现", "UI", C["ui"], "只被写，不读任何模块"),
]

EDGES = [
    (0, 1, "in",     "GetButtonDown(Slash / Shoot / Q / 1 / 2 / Esc)"),
    (0, 5, "in",     "Interact（K）—— 与 Slash 同键"),
    (1, 3, "data",   "读 damage / weaponRange / speed / 击退参数（共 20 处）"),
    (1, 2, "player", "ChangeHealth(-1) + Knockback(10, 0.15, 0.2)"),
    (2, 1, "player", "ChangeHealth(-1) + Knockback(10, 0.2)"),
    (2, 4, "evt",    "OnMonsterDefeated(expReward = 10)"),
    (2, 5, "bad",    "✗ 击杀 → 掉落物：这条边不存在"),
    (4, 3, "data",   "UpdateMaxHealth(1)（技能真的改属性）"),
    (4, 1, "player", "SkillManager：Sword Slash → combat.enabled = true"),
    (5, 3, "data",   "UpdateHealth / UpdateMaxHealth / UpdateSpeed"),
    (5, 1, "player", "InventoryManager.player（掉落点）"),
    (5, 5, "self",   "InventoryManager ↔ InventorySlot ↔ UseItem"),
    (5, 6, "player", "goldText / slot.UpdateUI / 各面板开关"),
    (4, 6, "player", "expSlider / pointsText"),
    (6, 0, "self",   "按钮 onClick → ShopKeeper.OpenXxxShop()"),
]

KIND = {
    "in":     ("←", 20, "#8a6a1f", "输入驱动"),
    "player": ("●", 15, "#2f6f4f", "直接引用"),
    "data":   ("○", 15, "#3c6e8f", "单例读取"),
    "evt":    ("⇢", 18, "#0f6d86", "静态事件"),
    "self":   ("↔", 15, "#6a7f2a", "模块内部"),
    "bad":    ("✗", 15, "#b3261e", "缺失的边"),
}


def build_matrix():
    W = 1200
    n = len(MODULES)
    X0, CW, RH, Y0 = 226, 100, 54, 272
    GW = n * CW
    s = []
    s.append(head(W, "模块耦合矩阵：7 个模块谁离不开谁",
                  "行 = 主动方，列 = 被动方。符号即依赖性质；底部把每条边展开成人话。"))
    s.append(legend(44, 108, [
        ("player", None, "● 直接引用"), ("data", None, "○ 单例读取"),
        ("growth", None, "⇢ 静态事件"), ("world", None, "↔ 模块内部"),
        ("bad", "5 4", "✗ 缺失"),
    ]))

    # 列头
    for j, (cn, en, col, _) in enumerate(MODULES):
        cx = X0 + j * CW
        s.append(f'<rect x="{cx}" y="{Y0 - 56}" width="{CW}" height="56" fill="{col}" fill-opacity="0.09"/>')
        s.append(T(cx + CW / 2, Y0 - 34, cn, 12, col, "middle", "700"))
        s.append(T(cx + CW / 2, Y0 - 16, en, 9.6, C["sub"], "middle"))

    # 行条 + 标签
    for i, (cn, en, col, note) in enumerate(MODULES):
        ry = Y0 + i * RH
        s.append(f'<rect x="40" y="{ry}" width="{X0 + GW - 40}" height="{RH}" '
                 f'fill="{"#ffffff" if i % 2 == 0 else "#fafbfa"}"/>')
        s.append(f'<rect x="40" y="{ry}" width="5" height="{RH}" fill="{col}" fill-opacity="0.85"/>')
        s.append(T(58, ry + 22, cn, 11.8, col, weight="700"))
        s.append(T(58, ry + 39, note, 9.2, C["sub"]))

    # 网格
    for j in range(n + 1):
        s.append(f'<line x1="{X0 + j * CW}" y1="{Y0}" x2="{X0 + j * CW}" y2="{Y0 + n * RH}" '
                 f'stroke="{C["line"]}"/>')
    for i in range(n + 1):
        s.append(f'<line x1="40" y1="{Y0 + i * RH}" x2="{X0 + GW}" y2="{Y0 + i * RH}" '
                 f'stroke="{C["line"]}"/>')
    for i in range(n):
        s.append(f'<rect x="{X0 + i * CW}" y="{Y0 + i * RH}" width="{CW}" height="{RH}" fill="#f1f3f0"/>')

    # 符号
    for a, b, kind, _ in EDGES:
        cx = X0 + b * CW + CW / 2
        cy = Y0 + a * RH + RH / 2
        ch, fs, hexcol, _ = KIND[kind]
        if kind == "bad":
            s.append(f'<rect x="{cx - 18}" y="{cy - 16}" width="36" height="32" rx="7" '
                     f'fill="#fdecea" stroke="{hexcol}" stroke-opacity="0.55" stroke-dasharray="4 3"/>')
        s.append(T(cx, cy + fs * 0.36, ch, fs, hexcol, "middle", "700"))

    # 计数
    yc = Y0 + n * RH
    s.append(T(X0 + GW + 14, yc - 22, "被依赖", 9.8, C["sub"], weight="700"))
    for j in range(n):
        c = sum(1 for a, b, k, _ in EDGES if b == j and k != "bad")
        if c:
            s.append(T(X0 + j * CW + CW / 2, yc + 24, str(c), 12, C["sub"], "middle", "700"))
    s.append(T(58, yc + 24, "依赖别人 →", 9.8, C["sub"], weight="700"))
    for i in range(n):
        c = sum(1 for a, b, k, _ in EDGES if a == i and k != "bad")
        if c:
            s.append(T(X0 - 16, Y0 + i * RH + RH / 2 + 5, str(c), 11, C["sub"], "end", "700"))

    # 边清单
    ye = yc + 62
    s.append(T(44, ye, "十五条边逐一展开", 15, C["ink"], weight="700"))
    s.append(T(196, ye, "（其中 14 条真接线 + 1 条该有却没有的）", 10.6, C["sub"]))
    yy = ye + 28
    for a, b, kind, desc in EDGES:
        ch, fs, hexcol, lab = KIND[kind]
        s.append(T(52, yy, ch, fs, hexcol, weight="700"))
        s.append(T(76, yy, f"{MODULES[a][0]} → {MODULES[b][0]}", 10.8, C["ink"]))
        s.append(T(148, yy, lab, 10, hexcol))
        s.append(T(238, yy, desc, 10.6, C["sub"]))
        yy += 21

    # 结论
    yk = yy + 24
    concl = [
        ("被依赖最多的是数据层", C["data"],
         "4 个模块读写 StatsManger，而它自己零依赖 —— 这是单例最典型的形状：全项目最稳也最难改的一点。"),
        ("唯一解耦成功的边", C["growth"],
         "敌人 → 成长走静态事件：Enemy_Health 不认识 ExpManager，新增伤害源零改动。"),
        ("两个模块之间没有任何边", C["bad"],
         "敌人 → 物品是空的：打怪只给经验，不掉东西。补一张掉落表就能把两条链接上。"),
    ]
    for i, (t, col, body) in enumerate(concl):
        y = yk + i * 62
        s.append(f'<rect x="44" y="{y - 16}" width="6" height="44" rx="3" fill="{col}" fill-opacity="0.8"/>')
        s.append(T(64, y, t, 12, col, weight="700"))
        s.append(T(64, y + 20, body, 10.6, C["sub"]))
    return finish(s, W, ["in", "player", "enemy", "data", "growth", "item", "ui", "world", "bad", "gray"])


# ============================================================ 文章封面
def cover(name, title, subtitle, facts, c1, c2, accent):
    W, H = 1200, 400
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
         f'<defs><linearGradient id="g{name}" x1="0" x2="0" y1="0" y2="1">',
         f'<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/>',
         f'</linearGradient></defs>',
         f'<rect width="{W}" height="{H}" fill="url(#g{name})"/>']
    # 装饰：右侧同心圆弧
    for k in range(3):
        r = 150 + k * 78
        o.append(f'<circle cx="1090" cy="392" r="{r}" fill="none" stroke="{accent}" '
                 f'stroke-opacity="{0.16 - k * 0.04:.2f}" stroke-width="1.6"/>')
    # 顶部细线
    o.append(f'<rect x="0" y="0" width="{W}" height="4" fill="{accent}" fill-opacity="0.55"/>')

    o.append(T(600, 56, title, 25, accent, "middle", "700"))
    o.append(T(600, 84, subtitle, 13, "#3f4f47", "middle"))

    bw = (1000 - 2 * 24) / 3
    for i, (head, body) in enumerate(facts):
        x = 100 + i * (bw + 24)
        o.append(f'<rect x="{x:.1f}" y="130" width="{bw:.1f}" height="196" rx="10" '
                 f'fill="#ffffff" fill-opacity="0.55" stroke="{accent}" stroke-opacity="0.30"/>')
        o.append(f'<rect x="{x:.1f}" y="130" width="{bw:.1f}" height="4" rx="2" fill="{accent}" fill-opacity="0.65"/>')
        o.append(T(x + 18, 162, head, 13.2, accent, weight="700"))
        yy = 192
        for ln in body:
            o.append(T(x + 18, yy, ln, 11, "#2b3a33"))
            yy += 19
    o.append(T(600, 372, "ARPG 学习日志 · 模块专文", 10.8, "#5c6b62", "middle"))
    o.append("</svg>")
    return "".join(o)


COVERS = [
    ("arpg-mod-c1.svg",
     "ARPG 模块全景：7 个模块、五类接线",
     "31 个脚本 / 1435 行 / 1 个场景 / 6 组静态事件 / 2 个单例",
     [("① 三层结构", ["输入层：7 个轴", "逻辑层：玩家·敌人·成长·物品", "底层：数据单例 + 5 张 Canvas"]),
      ("② 7×7 耦合矩阵", ["● 直接引用 14 条", "○ 单例读取 4 条", "⇢ 静态事件 1 条 · ✗ 缺口 1 条"]),
      ("③ 一条缺失的边", ["敌人 → 物品 不存在", "打怪只给经验", "地上没有掉落表"])],
     "#eef5ee", "#dbe9df", "#1a3d28"),
    ("arpg-mod-c2.svg",
     "玩家与敌人：两条武器链、一个状态机",
     "近战靠动画事件的 OverlapCircleAll，远程靠物理碰撞，敌人靠 4 态状态机",
     [("近战链", ["K → Attack() → 播动画", "动画事件 DealDamage()", "OverlapCircleAll → hits[0]"]),
      ("远程链", ["J → 瞄准 → 播动画", "动画事件 Shoot()", "Instantiate → Rigidbody2D 碰撞"]),
      ("敌人 AI", ["Idle / Chasing / Attacking / knockback", "攻击也由动画事件驱动", "两个 Attack() 同名共存"])],
     "#eef2fb", "#dde5f7", "#26426e"),
    ("arpg-mod-c3.svg",
     "成长链：一个 int 走完五段",
     "击杀 → 经验 → 升级 → 能力点 → 技能 → 属性，五段靠事件、一段直达单例",
     [("三段发布", ["敌人死了 → OnMonsterDefeated", "升级了 → OnLevelUp", "花点了 → OnAbilityPointSpent"]),
      ("三段订阅", ["ExpManager 累加经验", "SkillTreeManager 发点数", "SkillManager 改属性"]),
      ("一个缺口", ["LevelUp() 不碰 StatsManger", "10 级和 1 级手感一样", "改数值的只有技能"])],
     "#e9f4f6", "#d5eaee", "#0f5f74"),
    ("arpg-mod-c4.svg",
     "物品与商店：从地上捡到换成钱",
     "Loot → InventoryManager → InventorySlot → UseItem / ShopManager",
     [("拾取与背包", ["Loot 触发器 + 静态事件", "堆叠 3 / 空格 / 溢出回地上", "金币 isGold 直接分流"]),
      ("商店", ["ShopKeeper 触发圈 + K 开店", "三档货：Items/Weapons/Armour", "TryBuy 查钱查格 · Sell 找同款"]),
      ("三处断链", ["卖出不校验 → 物品蒸发", "击杀不掉物品", "背包没有开关常驻"])],
     "#f5effa", "#e7daf3", "#54306e"),
]


def build_covers():
    out = {}
    for name, title, sub, facts, c1, c2, accent in COVERS:
        out["images/" + name] = cover(name.replace("-", "").replace(".svg", ""),
                                      title, sub, facts, c1, c2, accent)
    return out


BUILDERS = [
    ("arpg-mod-1-map.svg", build_map),
    ("arpg-mod-2-matrix.svg", build_matrix),
    ("arpg-mod-3-player.svg", build_player),
    ("arpg-mod-4-enemy.svg", build_enemy),
    ("arpg-mod-5-growth.svg", build_growth),
    ("arpg-mod-6-items.svg", build_items),
]


def main():
    want = set(os.sys.argv[1:])
    for name, fn in BUILDERS:
        if want and name not in want:
            continue
        data = fn()
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            fh.write(data)
        print(f"  {name:28s} {len(data):7d} bytes")
    if not want:
        for name, data in build_covers().items():
            with open(os.path.join(ROOT, name), "w", encoding="utf-8") as fh:
                fh.write(data)
            print(f"  {name:28s} {len(data):7d} bytes")


if __name__ == "__main__":
    main()
