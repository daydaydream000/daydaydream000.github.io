"""
Day 5 概念图 1：Knockback 时序对照
- 上半：玩家正常时 FixedUpdate 每帧响应 WASD
- 下半：被击退时 0.5s 内 isKnockback = true，WASD 被忽略
- 协程结束后恢复控制

概念图 2：Anim 事件触发点
- 挥剑动画时间轴（0% → 100%）
- 三个事件点：Attack 启动（0%）、DealDamage（30%）、FinishAttacking（100%）
"""
import os
import subprocess

# === 图 1: Knockback 时序对照 ===
SVG1 = r"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 400" width="1200" height="400">
  <defs>
    <linearGradient id="bg1" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0" stop-color="#eef5ee"/>
      <stop offset="1" stop-color="#d8e8d8"/>
    </linearGradient>
  </defs>

  <rect x="0" y="0" width="1200" height="400" fill="url(#bg1)"/>

  <!-- 标题 -->
  <text x="600" y="40" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="22" font-weight="700" fill="#1a3d28">Knockback 时序对照：协程 0.5s 期间控制权转移</text>
  <text x="600" y="62" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="13" fill="#3a4a3a">if (isKnockback == false) 守门是关键，WASD 在眩晕期被忽略</text>

  <!-- 时间轴 -->
  <line x1="120" y1="200" x2="1080" y2="200" stroke="#1a3d28" stroke-width="2"/>
  <polygon points="1080,200 1066,194 1066,206" fill="#1a3d28"/>
  <text x="600" y="226" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="11" fill="#3a4a3a" font-style="italic">时间</text>

  <!-- 关键时刻 -->
  <line x1="240" y1="100" x2="240" y2="320" stroke="#c43131" stroke-width="1" stroke-dasharray="3 3"/>
  <text x="240" y="92" text-anchor="middle" font-family="ui-monospace, monospace" font-size="11" font-weight="700" fill="#c43131">敌人打中</text>
  <text x="240" y="108" text-anchor="middle" font-family="ui-monospace, monospace" font-size="9" fill="#c43131">Knockback() 被调用</text>

  <line x1="540" y1="100" x2="540" y2="320" stroke="#1a7a3a" stroke-width="1" stroke-dasharray="3 3"/>
  <text x="540" y="92" text-anchor="middle" font-family="ui-monospace, monospace" font-size="11" font-weight="700" fill="#1a7a3a">0.5s 后</text>
  <text x="540" y="108" text-anchor="middle" font-family="ui-monospace, monospace" font-size="9" fill="#1a7a3a">协程结束</text>

  <!-- 上半：正常状态 -->
  <g>
    <rect x="100" y="130" width="980" height="40" fill="#a8d49a" rx="4"/>
    <text x="120" y="156" font-family="ui-sans-serif, sans-serif" font-size="13" font-weight="700" fill="#1a3d28">正常：isKnockback = false</text>
    <text x="320" y="156" font-family="ui-monospace, monospace" font-size="11" fill="#1a3d28">FixedUpdate 每帧响应 WASD → rb.velocity = input * speed</text>
  </g>

  <!-- 下半：被击退状态 -->
  <g>
    <rect x="100" y="260" width="180" height="40" fill="#f0b090" rx="4"/>
    <text x="115" y="286" font-family="ui-sans-serif, sans-serif" font-size="13" font-weight="700" fill="#5a2a20">被击退中</text>

    <rect x="280" y="260" width="300" height="40" fill="#e09080" rx="4"/>
    <text x="295" y="286" font-family="ui-monospace, monospace" font-size="11" fill="#5a2a20">isKnockback = true</text>
    <text x="295" y="302" font-family="ui-monospace, monospace" font-size="9" fill="#5a2a20">WASD 被忽略，rb.velocity 由击退方向*force 驱动</text>

    <rect x="580" y="260" width="500" height="40" fill="#a8d49a" rx="4"/>
    <text x="600" y="286" font-family="ui-sans-serif, sans-serif" font-size="13" font-weight="700" fill="#1a3d28">恢复：isKnockback = false</text>
    <text x="800" y="286" font-family="ui-monospace, monospace" font-size="11" fill="#1a3d28">WASD 重新生效</text>
  </g>

  <!-- 底部小注 -->
  <text x="600" y="350" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="12" fill="#3a4a3a" font-style="italic">KnockbackCounter(stunTime) 协程：</text>
  <text x="600" y="368" text-anchor="middle" font-family="ui-monospace, monospace" font-size="11" fill="#1a3d28">yield return new WaitForSeconds(stunTime);  rb.velocity = Vector2.zero;  isKnockback = false;</text>
  <text x="600" y="386" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="10" fill="#3a4a3a" opacity="0.7">注意：先置零速度，再解锁状态——顺序反了玩家会瞬间冲到旧方向</text>
</svg>
"""

# === 图 2: Anim 事件时间轴 ===
SVG2 = r"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 400" width="1200" height="400">
  <defs>
    <linearGradient id="bg2" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0" stop-color="#fff8e8"/>
      <stop offset="1" stop-color="#f4e6c0"/>
    </linearGradient>
    <linearGradient id="animbar" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0" stop-color="#f0a868"/>
      <stop offset="0.3" stop-color="#e23a3a"/>
      <stop offset="0.6" stop-color="#e23a3a"/>
      <stop offset="1" stop-color="#7a8a3a"/>
    </linearGradient>
  </defs>

  <rect x="0" y="0" width="1200" height="400" fill="url(#bg2)"/>

  <text x="600" y="40" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="22" font-weight="700" fill="#5a3a20">Animator 事件：动画峰值触发 DealDamage</text>
  <text x="600" y="62" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="13" fill="#3a2a20">Attack() 启动动画 → 中间帧触发伤害判定 → 末帧结束动画</text>

  <!-- 时间轴主条 -->
  <rect x="100" y="160" width="1000" height="40" fill="url(#animbar)" rx="4"/>
  <line x1="100" y1="160" x2="1100" y2="160" stroke="#5a3a20" stroke-width="1"/>
  <line x1="100" y1="200" x2="1100" y2="200" stroke="#5a3a20" stroke-width="1"/>

  <!-- 0% -->
  <line x1="100" y1="140" x2="100" y2="220" stroke="#5a3a20" stroke-width="2"/>
  <text x="100" y="240" text-anchor="middle" font-family="ui-monospace, monospace" font-size="12" font-weight="700" fill="#5a3a20">0%</text>
  <text x="100" y="258" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="11" fill="#5a3a20">Attack()</text>

  <!-- 30% 触发 DealDamage -->
  <line x1="400" y1="140" x2="400" y2="220" stroke="#c43131" stroke-width="2"/>
  <circle cx="400" cy="180" r="8" fill="#c43131"/>
  <text x="400" y="240" text-anchor="middle" font-family="ui-monospace, monospace" font-size="12" font-weight="700" fill="#c43131">~30%</text>
  <text x="400" y="258" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="11" fill="#c43131">DealDamage()</text>
  <text x="400" y="276" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="10" fill="#3a2a20">剑挥到目标位置</text>

  <!-- 60% 还在判定 -->
  <line x1="700" y1="140" x2="700" y2="220" stroke="#c43131" stroke-width="1" stroke-dasharray="2 2"/>
  <text x="700" y="240" text-anchor="middle" font-family="ui-monospace, monospace" font-size="12" fill="#c43131" opacity="0.7">~60%</text>

  <!-- 100% -->
  <line x1="1100" y1="140" x2="1100" y2="220" stroke="#1a7a3a" stroke-width="2"/>
  <circle cx="1100" cy="180" r="8" fill="#1a7a3a"/>
  <text x="1100" y="240" text-anchor="middle" font-family="ui-monospace, monospace" font-size="12" font-weight="700" fill="#1a7a3a">100%</text>
  <text x="1100" y="258" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="11" fill="#1a7a3a">FinishAttacking()</text>
  <text x="1100" y="276" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="10" fill="#3a2a20">收招，bool 复位</text>

  <!-- 阶段标 -->
  <text x="250" y="320" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="12" fill="#5a3a20" font-weight="600">前摇（举剑）</text>
  <text x="550" y="320" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="12" fill="#c43131" font-weight="600">挥砍（剑在目标位置）</text>
  <text x="900" y="320" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="12" fill="#1a7a3a" font-weight="600">收招（剑放下）</text>

  <!-- 底部：冷却 2 秒独立计时 -->
  <g transform="translate(0, 350)">
    <text x="600" y="14" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="12" fill="#3a2a20" font-weight="600">冷却 2 秒独立计时（不在动画时间轴上）</text>
    <text x="600" y="32" text-anchor="middle" font-family="ui-monospace, monospace" font-size="11" fill="#5a3a20">timer -= Time.deltaTime  每帧在 Update 倒数；timer &lt;= 0 才能再次 Attack()</text>
  </g>
</svg>
"""

for name, svg in [('arpg-day5-knockback', SVG1), ('arpg-day5-anim-events', SVG2)]:
    out = f'D:\\1\\mypro\\daydaydream000.github.io\\images\\{name}.svg'
    with open(out, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f'Written: {out}')

# 截图
ch = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
for name in ['arpg-day5-knockback', 'arpg-day5-anim-events']:
    out = f'D:\\1\\mypro\\daydaydream000.github.io\\images\\{name}.svg'
    png = f'C:\\Users\\lishen\\AppData\\Local\\Temp\\ddopt\\{name}.png'
    subprocess.run([ch, '--headless', '--disable-gpu', '--hide-scrollbars',
                    f'--screenshot={png}', '--window-size=1200,400',
                    f'file:///{out.replace(chr(92), "/")}'],
                   capture_output=True)
    print(f'Screenshot: {png}')
