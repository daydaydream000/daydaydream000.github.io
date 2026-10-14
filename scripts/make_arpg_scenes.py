"""
为 Day 2/4 文章生成三张内文配图：
- arpg-day2-elevation-scene.svg
- arpg-day4-detection.svg
- arpg-day4-attack.svg
"""
import os

DST = r"D:\1\mypro\daydaydream000.github.io\images"

# === 1. Day 2 钻山洞内文配图 ===
# 比 cover 更简单：左侧山脚骑士 + 山体剖面 + 右侧山体内的骑士
day2_svg = '''<svg viewBox="0 0 1200 380" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="d2s-sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#CFE5F4"/>
      <stop offset="100%" stop-color="#E8F1DC"/>
    </linearGradient>
    <linearGradient id="d2s-grass" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#8FCB5E"/>
      <stop offset="100%" stop-color="#5A9C35"/>
    </linearGradient>
    <linearGradient id="d2s-cliff" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#A8763F"/>
      <stop offset="100%" stop-color="#7A5228"/>
    </linearGradient>
    <radialGradient id="d2s-glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#FFE9A8" stop-opacity="0.85"/>
      <stop offset="100%" stop-color="#FFE9A8" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect width="1200" height="380" fill="url(#d2s-sky)"/>

  <!-- 远处山 -->
  <path d="M0,240 L130,150 L260,240 L390,130 L520,240 L660,170 L800,240 L940,140 L1080,240 L1200,180 L1200,380 L0,380 Z"
        fill="#B5DDA0" opacity="0.45"/>

  <!-- 草地 -->
  <rect x="0" y="300" width="1200" height="80" fill="url(#d2s-grass)"/>
  <g stroke="#4E8C2F" stroke-opacity="0.25" stroke-width="2">
    <line x1="100" y1="300" x2="100" y2="380"/>
    <line x1="200" y1="300" x2="200" y2="380"/>
    <line x1="300" y1="300" x2="300" y2="380"/>
    <line x1="400" y1="300" x2="400" y2="380"/>
    <line x1="500" y1="300" x2="500" y2="380"/>
    <line x1="600" y1="300" x2="600" y2="380"/>
    <line x1="700" y1="300" x2="700" y2="380"/>
    <line x1="800" y1="300" x2="800" y2="380"/>
    <line x1="900" y1="300" x2="900" y2="380"/>
    <line x1="1000" y1="300" x2="1000" y2="380"/>
    <line x1="1100" y1="300" x2="1100" y2="380"/>
  </g>

  <!-- 山体剖面（中央偏右） -->
  <g>
    <path d="M540,300 L540,140 Q660,100 780,140 L780,300 Z" fill="url(#d2s-cliff)"/>
    <!-- 崖壁纹理 -->
    <g stroke="#5E3D1C" stroke-opacity="0.35" stroke-width="2" fill="none">
      <path d="M575,170 q40,8 80,0"/>
      <path d="M595,210 q50,10 100,0"/>
      <path d="M565,250 q60,10 120,0"/>
    </g>
    <!-- 洞口 -->
    <ellipse cx="660" cy="265" rx="42" ry="48" fill="#2A1A0C"/>
    <ellipse cx="660" cy="265" rx="36" ry="42" fill="url(#d2s-glow)" opacity="0.45"/>
  </g>

  <!-- 左侧：山脚外的骑士（蓝衣） -->
  <ellipse cx="260" cy="338" rx="36" ry="9" fill="#2A4A1A" opacity="0.3"/>
  <g transform="translate(260, 250) scale(0.78)">
    <rect x="-15" y="48" width="13" height="28" rx="3" fill="#2E5A8C"/>
    <rect x="3" y="48" width="13" height="28" rx="3" fill="#2E5A8C"/>
    <rect x="-13" y="72" width="16" height="10" rx="3" fill="#4A3A2A"/>
    <rect x="2" y="72" width="16" height="10" rx="3" fill="#4A3A2A"/>
    <rect x="-22" y="5" width="44" height="48" rx="10" fill="#4A8FD4"/>
    <ellipse cx="-25" cy="15" rx="13" ry="11" fill="#5EA0DC"/>
    <ellipse cx="25" cy="15" rx="13" ry="11" fill="#5EA0DC"/>
    <rect x="-34" y="20" width="11" height="28" rx="5" fill="#3B7CC0"/>
    <rect x="23" y="20" width="11" height="28" rx="5" fill="#3B7CC0"/>
    <rect x="-17" y="-25" width="34" height="34" rx="10" fill="#6FB0E8"/>
    <rect x="-13" y="-10" width="26" height="5" rx="2" fill="#22364A"/>
    <path d="M0,-27 q-14,-22 5,-29 q-2,15 9,22 Z" fill="#E8552F"/>
  </g>
  <text x="260" y="358" font-family="ui-sans-serif, system-ui, sans-serif" font-size="16"
        font-weight="700" fill="#2F5A1E" text-anchor="middle">山脚外</text>

  <!-- 右侧：山体内部的骑士（变小半透明） -->
  <g transform="translate(870, 250) scale(0.55)" opacity="0.78">
    <rect x="-15" y="48" width="13" height="28" rx="3" fill="#2E5A8C"/>
    <rect x="3" y="48" width="13" height="28" rx="3" fill="#2E5A8C"/>
    <rect x="-22" y="5" width="44" height="48" rx="10" fill="#4A8FD4"/>
    <ellipse cx="-25" cy="15" rx="13" ry="11" fill="#5EA0DC"/>
    <ellipse cx="25" cy="15" rx="13" ry="11" fill="#5EA0DC"/>
    <rect x="-17" y="-25" width="34" height="34" rx="10" fill="#6FB0E8"/>
    <rect x="-13" y="-10" width="26" height="5" rx="2" fill="#22364A"/>
    <path d="M0,-27 q-14,-22 5,-29 q-2,15 9,22 Z" fill="#E8552F"/>
  </g>
  <text x="870" y="358" font-family="ui-sans-serif, system-ui, sans-serif" font-size="16"
        font-weight="700" fill="#2F5A1E" text-anchor="middle">山体内部</text>

  <!-- 标注线：Entry/Exit 触发器 -->
  <g stroke="#7A5228" stroke-width="2" stroke-dasharray="5 4" fill="none">
    <path d="M480,300 L480,338"/>
    <path d="M840,300 L840,338"/>
  </g>
  <g font-family="ui-sans-serif, system-ui, sans-serif" font-size="13" font-weight="700" fill="#7A5228" text-anchor="middle">
    <rect x="430" y="340" width="100" height="24" rx="6" fill="#FFF6E0" stroke="#D8B878" stroke-width="1.5"/>
    <text x="480" y="357">Entry 触发</text>
    <rect x="790" y="340" width="100" height="24" rx="6" fill="#FFF6E0" stroke="#D8B878" stroke-width="1.5"/>
    <text x="840" y="357">Exit 触发</text>
  </g>

  <!-- 顶部说明 -->
  <text x="600" y="50" font-family="ui-sans-serif, system-ui, sans-serif" font-size="18"
        font-weight="700" fill="#2F5A1E" text-anchor="middle">Elevation_Entry 触发 → 山体碰撞关闭、角色 SortingOrder 改为 15</text>
</svg>'''

with open(os.path.join(DST, "arpg-day2-elevation-scene.svg"), "w", encoding="utf-8") as f:
    f.write(day2_svg)
print("-> arpg-day2-elevation-scene.svg")

# === 2. Day 4 OverlapCircleAll 主动检测 ===
day4_det_svg = '''<svg viewBox="0 0 1200 380" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="d4d-sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#CFE5F4"/>
      <stop offset="100%" stop-color="#E8F1DC"/>
    </linearGradient>
    <linearGradient id="d4d-grass" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#8FCB5E"/>
      <stop offset="100%" stop-color="#5A9C35"/>
    </linearGradient>
    <radialGradient id="d4d-radar" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#FFD45A" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="#FFD45A" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect width="1200" height="380" fill="url(#d4d-sky)"/>
  <rect x="0" y="300" width="1200" height="80" fill="url(#d4d-grass)"/>
  <g stroke="#4E8C2F" stroke-opacity="0.25" stroke-width="2">
    <line x1="100" y1="300" x2="100" y2="380"/>
    <line x1="220" y1="300" x2="220" y2="380"/>
    <line x1="340" y1="300" x2="340" y2="380"/>
    <line x1="460" y1="300" x2="460" y2="380"/>
    <line x1="580" y1="300" x2="580" y2="380"/>
    <line x1="700" y1="300" x2="700" y2="380"/>
    <line x1="820" y1="300" x2="820" y2="380"/>
    <line x1="940" y1="300" x2="940" y2="380"/>
    <line x1="1060" y1="300" x2="1060" y2="380"/>
  </g>

  <!-- 中央：火把哥布林（敌人） -->
  <g transform="translate(600, 250)">
    <ellipse cx="0" cy="88" rx="42" ry="11" fill="#2A4A1A" opacity="0.3"/>
    <g transform="scale(0.85)">
      <!-- 火把火焰 -->
      <path d="M-35,-65 q-12,-22 5,-32 q-2,15 9,22 Z" fill="#FFC850"/>
      <path d="M-37,-70 q-10,-18 4,-26 q-1,12 7,18 Z" fill="#FF9430"/>
      <!-- 哥布林本体 -->
      <rect x="-15" y="48" width="13" height="28" rx="3" fill="#7A2E40"/>
      <rect x="3" y="48" width="13" height="28" rx="3" fill="#7A2E40"/>
      <rect x="-22" y="5" width="44" height="48" rx="10" fill="#A04050"/>
      <ellipse cx="-25" cy="15" rx="13" ry="11" fill="#C25060"/>
      <ellipse cx="25" cy="15" rx="13" ry="11" fill="#C25060"/>
      <rect x="-18" y="-25" width="36" height="36" rx="10" fill="#B85060"/>
      <ellipse cx="-8" cy="-15" rx="3" ry="4" fill="#1A1A1A"/>
      <ellipse cx="8" cy="-15" rx="3" ry="4" fill="#1A1A1A"/>
      <rect x="-34" y="20" width="11" height="28" rx="5" fill="#8A3848"/>
      <rect x="23" y="20" width="11" height="28" rx="5" fill="#8A3848"/>
      <!-- 火把杆 -->
      <rect x="-44" y="-25" width="4" height="40" rx="1" fill="#3A1F0F"/>
    </g>
  </g>

  <!-- 黄色检测圆（detectionPoint, radius=5） -->
  <circle cx="600" cy="250" r="220" fill="url(#d4d-radar)"/>
  <circle cx="600" cy="250" r="220" fill="none" stroke="#E8A830" stroke-width="3" stroke-dasharray="8 6" opacity="0.9"/>
  <circle cx="600" cy="250" r="160" fill="none" stroke="#E8A830" stroke-width="1.5" stroke-dasharray="4 4" opacity="0.4"/>
  <circle cx="600" cy="250" r="80" fill="none" stroke="#E8A830" stroke-width="1.5" stroke-dasharray="4 4" opacity="0.4"/>

  <!-- 左侧：玩家（蓝衣骑士，已经走进检测范围） -->
  <ellipse cx="320" cy="338" rx="36" ry="9" fill="#2A4A1A" opacity="0.3"/>
  <g transform="translate(320, 250) scale(0.78)">
    <rect x="-15" y="48" width="13" height="28" rx="3" fill="#2E5A8C"/>
    <rect x="3" y="48" width="13" height="28" rx="3" fill="#2E5A8C"/>
    <rect x="-13" y="72" width="16" height="10" rx="3" fill="#4A3A2A"/>
    <rect x="2" y="72" width="16" height="10" rx="3" fill="#4A3A2A"/>
    <rect x="-22" y="5" width="44" height="48" rx="10" fill="#4A8FD4"/>
    <ellipse cx="-25" cy="15" rx="13" ry="11" fill="#5EA0DC"/>
    <ellipse cx="25" cy="15" rx="13" ry="11" fill="#5EA0DC"/>
    <rect x="-17" y="-25" width="34" height="34" rx="10" fill="#6FB0E8"/>
    <rect x="-13" y="-10" width="26" height="5" rx="2" fill="#22364A"/>
    <path d="M0,-27 q-14,-22 5,-29 q-2,15 9,22 Z" fill="#E8552F"/>
  </g>
  <text x="320" y="358" font-family="ui-sans-serif, system-ui, sans-serif" font-size="14"
        font-weight="700" fill="#1A4070" text-anchor="middle">玩家（被检测到）</text>

  <!-- 右侧：玩家（未进入检测范围） -->
  <ellipse cx="980" cy="338" rx="30" ry="8" fill="#2A4A1A" opacity="0.3"/>
  <g transform="translate(980, 260) scale(0.6)" opacity="0.55">
    <rect x="-22" y="5" width="44" height="48" rx="10" fill="#4A8FD4"/>
    <rect x="-17" y="-25" width="34" height="34" rx="10" fill="#6FB0E8"/>
    <path d="M0,-27 q-14,-22 5,-29 q-2,15 9,22 Z" fill="#E8552F"/>
  </g>
  <text x="980" y="358" font-family="ui-sans-serif, system-ui, sans-serif" font-size="14"
        font-weight="700" fill="#666" text-anchor="middle">范围外</text>

  <!-- 顶部说明 -->
  <text x="600" y="50" font-family="ui-sans-serif, system-ui, sans-serif" font-size="18"
        font-weight="700" fill="#2F5A1E" text-anchor="middle">每帧 OverlapCircleAll(detectionPoint, 5, playerLayer) 主动扫描</text>
  <text x="600" y="76" font-family="ui-sans-serif, system-ui, sans-serif" font-size="14"
        fill="#666" text-anchor="middle">敌人不再傻站着等玩家撞进来 —— 玩家进圈就被锁定，状态 → Chasing</text>
</svg>'''

with open(os.path.join(DST, "arpg-day4-detection.svg"), "w", encoding="utf-8") as f:
    f.write(day4_det_svg)
print("-> arpg-day4-detection.svg")

# === 3. Day 4 攻击判定 ===
day4_atk_svg = '''<svg viewBox="0 0 1200 380" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="d4a-sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#F2DCD0"/>
      <stop offset="100%" stop-color="#E8C8B8"/>
    </linearGradient>
    <linearGradient id="d4a-grass" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#8FCB5E"/>
      <stop offset="100%" stop-color="#5A9C35"/>
    </linearGradient>
    <radialGradient id="d4a-attack" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#FF5050" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#FF5050" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect width="1200" height="380" fill="url(#d4a-sky)"/>
  <rect x="0" y="300" width="1200" height="80" fill="url(#d4a-grass)"/>

  <!-- 左侧：哥布林敌人 -->
  <g transform="translate(380, 250)">
    <ellipse cx="0" cy="88" rx="42" ry="11" fill="#2A4A1A" opacity="0.3"/>
    <g transform="scale(0.85)">
      <rect x="-15" y="48" width="13" height="28" rx="3" fill="#7A2E40"/>
      <rect x="3" y="48" width="13" height="28" rx="3" fill="#7A2E40"/>
      <rect x="-22" y="5" width="44" height="48" rx="10" fill="#A04050"/>
      <ellipse cx="-25" cy="15" rx="13" ry="11" fill="#C25060"/>
      <ellipse cx="25" cy="15" rx="13" ry="11" fill="#C25060"/>
      <rect x="-18" y="-25" width="36" height="36" rx="10" fill="#B85060"/>
      <ellipse cx="-8" cy="-15" rx="3" ry="4" fill="#1A1A1A"/>
      <ellipse cx="8" cy="-15" rx="3" ry="4" fill="#1A1A1A"/>
      <rect x="22" y="20" width="11" height="28" rx="5" fill="#8A3848"/>
      <!-- 武器（朝右挥出） -->
      <rect x="38" y="-15" width="50" height="6" rx="2" fill="#3A1F0F" transform="rotate(20 38 -12)"/>
      <path d="M86,-7 l30,12 l-10,15 l-30,-12 z" fill="#D8D0C0" transform="rotate(20 86 0)"/>
    </g>
  </g>

  <!-- 武器前端的攻击判定圆（红色，attackPoint + weaponRange） -->
  <circle cx="540" cy="230" r="90" fill="url(#d4a-attack)"/>
  <circle cx="540" cy="230" r="90" fill="none" stroke="#D04040" stroke-width="3" stroke-dasharray="6 4" opacity="0.85"/>
  <circle cx="540" cy="230" r="6" fill="#D04040"/>
  <circle cx="540" cy="230" r="6" fill="none" stroke="#FFFFFF" stroke-width="1.5"/>

  <!-- 右侧：被击中的玩家 -->
  <g transform="translate(720, 250)">
    <ellipse cx="0" cy="88" rx="36" ry="9" fill="#2A4A1A" opacity="0.3"/>
    <g transform="scale(0.78)">
      <rect x="-15" y="48" width="13" height="28" rx="3" fill="#2E5A8C"/>
      <rect x="3" y="48" width="13" height="28" rx="3" fill="#2E5A8C"/>
      <rect x="-13" y="72" width="16" height="10" rx="3" fill="#4A3A2A"/>
      <rect x="2" y="72" width="16" height="10" rx="3" fill="#4A3A2A"/>
      <rect x="-22" y="5" width="44" height="48" rx="10" fill="#4A8FD4"/>
      <ellipse cx="-25" cy="15" rx="13" ry="11" fill="#5EA0DC"/>
      <ellipse cx="25" cy="15" rx="13" ry="11" fill="#5EA0DC"/>
      <rect x="-17" y="-25" width="34" height="34" rx="10" fill="#6FB0E8"/>
      <rect x="-13" y="-10" width="26" height="5" rx="2" fill="#22364A"/>
      <path d="M0,-27 q-14,-22 5,-29 q-2,15 9,22 Z" fill="#E8552F"/>
    </g>
  </g>
  <!-- 击中星 -->
  <g transform="translate(630, 200)">
    <path d="M0,-30 L8,-8 L30,0 L8,8 L0,30 L-8,8 L-30,0 L-8,-8 Z" fill="#FFE848" stroke="#D08000" stroke-width="2"/>
  </g>
  <text x="720" y="358" font-family="ui-sans-serif, system-ui, sans-serif" font-size="16"
        font-weight="700" fill="#A02020" text-anchor="middle">hits[0] 扣血</text>

  <!-- 顶部说明 -->
  <text x="600" y="50" font-family="ui-sans-serif, system-ui, sans-serif" font-size="18"
        font-weight="700" fill="#A02020" text-anchor="middle">Attack() 在 attackPoint 周围 OverlapCircleAll，命中即扣血</text>
  <text x="600" y="76" font-family="ui-sans-serif, system-ui, sans-serif" font-size="14"
        fill="#666" text-anchor="middle">冷却 2 秒，Trigger 框 + 攻击范围都由代码控制</text>
</svg>'''

with open(os.path.join(DST, "arpg-day4-attack.svg"), "w", encoding="utf-8") as f:
    f.write(day4_atk_svg)
print("-> arpg-day4-attack.svg")

print("\n3 张内文配图生成完毕")
