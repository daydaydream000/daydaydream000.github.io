"""Day 6 配图：封面 + 3 张内文概念图（属性系统重构 + 暂停式属性面板）"""
import shutil
import subprocess
from pathlib import Path

ROOT = Path(r'D:\1\mypro\daydaydream000.github.io')
IMG = ROOT / 'images'
DOCS_IMG = ROOT / 'docs' / 'assets' / 'images'
TMP = Path(r'C:\Users\lishen\AppData\Local\Temp\ddopt')
TMP.mkdir(parents=True, exist_ok=True)
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

SANS = 'ui-sans-serif, sans-serif'
MONO = 'ui-monospace, monospace'

COVER = r"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 400" width="1200" height="400">
  <defs>
    <linearGradient id="sky6" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0" stop-color="#cfe6f7"/>
      <stop offset="1" stop-color="#eef6fb"/>
    </linearGradient>
    <linearGradient id="grass6" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0" stop-color="#9edb6c"/>
      <stop offset="1" stop-color="#5fa841"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="1200" height="400" fill="url(#sky6)"/>
  <path d="M0,302 L1200,302 L1200,400 L0,400 Z" fill="url(#grass6)" opacity="0.45"/>
  <path d="M0,302 L210,206 L420,266 L640,196 L860,260 L1050,200 L1200,272 L1200,302 Z" fill="#7bb661" opacity="0.35"/>

  <text x="600" y="44" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="24" font-weight="700" fill="#1a3d28">ARPG 学习日志 Day 6：属性系统重构与暂停式属性面板</text>
  <text x="600" y="70" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="13" fill="#3a4a3a">StatsManger 单例 · StatsUI 开关 · StatsSlot 预制体</text>

  <!-- 左：重构前 -->
  <g transform="translate(36, 92)">
    <text x="0" y="12" font-family="ui-sans-serif, sans-serif" font-size="12.5" font-weight="700" fill="#5a2a20">重构前：数字散在各脚本的 Inspector 里</text>
    <g>
      <rect x="0" y="26" width="252" height="32" rx="3" fill="#ffffff" stroke="#1a3d28" stroke-opacity="0.35"/>
      <text x="10" y="46" font-family="ui-monospace, monospace" font-size="11.5" fill="#1a3d28">PlayerMovement</text>
      <text x="242" y="46" text-anchor="end" font-family="ui-monospace, monospace" font-size="11.5" fill="#c43131">speed = 5</text>
    </g>
    <g>
      <rect x="0" y="64" width="252" height="32" rx="3" fill="#ffffff" stroke="#1a3d28" stroke-opacity="0.35"/>
      <text x="10" y="84" font-family="ui-monospace, monospace" font-size="11.5" fill="#1a3d28">PlayerHealth</text>
      <text x="242" y="84" text-anchor="end" font-family="ui-monospace, monospace" font-size="11.5" fill="#c43131">maxHealth = 20</text>
    </g>
    <g>
      <rect x="0" y="102" width="252" height="32" rx="3" fill="#ffffff" stroke="#1a3d28" stroke-opacity="0.35"/>
      <text x="10" y="122" font-family="ui-monospace, monospace" font-size="11.5" fill="#1a3d28">Player_Combat</text>
      <text x="242" y="122" text-anchor="end" font-family="ui-monospace, monospace" font-size="11.5" fill="#c43131">damage = 1</text>
    </g>
    <g>
      <rect x="0" y="140" width="252" height="32" rx="3" fill="#ffffff" stroke="#1a3d28" stroke-opacity="0.35"/>
      <text x="10" y="160" font-family="ui-monospace, monospace" font-size="11.5" fill="#1a3d28">Player_Combat</text>
      <text x="242" y="160" text-anchor="end" font-family="ui-monospace, monospace" font-size="11.5" fill="#c43131">range = 0.7</text>
    </g>
  </g>

  <!-- 箭头 1 -->
  <g stroke="#1a3d28" stroke-width="2" fill="none">
    <path d="M294,182 L326,182" stroke-dasharray="5 4"/>
    <path d="M326,182 L317,177 M326,182 L317,187" stroke-linecap="round"/>
  </g>
  <text x="310" y="170" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="10" fill="#1a3d28">收拢</text>

  <!-- 中：StatsManger -->
  <g transform="translate(334, 92)">
    <text x="172" y="12" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="12.5" font-weight="700" fill="#5a3a20">StatsManger（单例）</text>
    <rect x="0" y="26" width="344" height="150" rx="4" fill="#fff8e8" stroke="#b48a2a"/>
    <text x="12" y="46" font-family="ui-monospace, monospace" font-size="11" font-weight="700" fill="#8a5a20">[Header("Combat Stats")]</text>
    <text x="12" y="63" font-family="ui-monospace, monospace" font-size="10.5" fill="#5a3a20">damage · weaponRange · knockbackForce</text>
    <text x="12" y="78" font-family="ui-monospace, monospace" font-size="10.5" fill="#5a3a20">knockbackTime · stunTime</text>
    <text x="12" y="100" font-family="ui-monospace, monospace" font-size="11" font-weight="700" fill="#8a5a20">[Header("Movement Stats")]</text>
    <text x="12" y="117" font-family="ui-monospace, monospace" font-size="10.5" fill="#5a3a20">speed</text>
    <text x="12" y="139" font-family="ui-monospace, monospace" font-size="11" font-weight="700" fill="#8a5a20">[Header("Health Stats")]</text>
    <text x="12" y="156" font-family="ui-monospace, monospace" font-size="10.5" fill="#5a3a20">maxHealth · currentHealth</text>
  </g>

  <!-- 箭头 2 -->
  <g stroke="#1a3d28" stroke-width="2" fill="none">
    <path d="M684,182 L838,182" stroke-dasharray="5 4"/>
    <path d="M838,182 L829,177 M838,182 L829,187" stroke-linecap="round"/>
  </g>
  <text x="761" y="170" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="10" fill="#1a3d28">读取</text>

  <!-- 右：属性面板 -->
  <g transform="translate(846, 92)">
    <text x="159" y="12" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="12.5" font-weight="700" fill="#1a3d28">Esc 打开的属性面板</text>
    <rect x="0" y="26" width="318" height="150" rx="4" fill="#1e2a22"/>
    <rect x="16" y="44" width="286" height="30" rx="3" fill="#2c3b30"/>
    <text x="28" y="64" font-family="ui-monospace, monospace" font-size="12" fill="#e8f0e8">Damage: 1</text>
    <rect x="16" y="82" width="286" height="30" rx="3" fill="#2c3b30"/>
    <text x="28" y="102" font-family="ui-monospace, monospace" font-size="12" fill="#e8f0e8">Speed: 5</text>
    <rect x="16" y="124" width="62" height="30" rx="3" fill="#fff8e8" stroke="#b48a2a"/>
    <text x="47" y="144" text-anchor="middle" font-family="ui-monospace, monospace" font-size="12" font-weight="700" fill="#5a3a20">Esc</text>
    <text x="90" y="144" font-family="ui-sans-serif, sans-serif" font-size="11" fill="#9fb8a4">Time.timeScale = 0</text>
    <text x="28" y="170" font-family="ui-sans-serif, sans-serif" font-size="10" fill="#7f9b86">StatsSlot ×2 由 GridLayoutGroup 排列</text>
  </g>

  <!-- 底部 -->
  <g transform="translate(0, 330)">
    <rect x="60" y="0" width="1080" height="42" rx="4" fill="#1a3d28" opacity="0.06"/>
    <text x="600" y="19" text-anchor="middle" font-family="ui-monospace, monospace" font-size="11" fill="#1a3d28">各脚本的 Inspector 字段 → StatsManger.Instance 单点读取 → Esc 冻结时间 + CanvasGroup 淡入</text>
    <text x="600" y="35" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="10" fill="#3a4a3a" opacity="0.7">数值有了唯一出处，UI 才能只问 StatsManger 一个对象</text>
  </g>
</svg>
"""

FLOW = r"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 400" width="1200" height="400">
  <defs>
    <linearGradient id="bgf" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0" stop-color="#eef5ee"/>
      <stop offset="1" stop-color="#dcebdc"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="1200" height="400" fill="url(#bgf)"/>

  <text x="600" y="38" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="22" font-weight="700" fill="#1a3d28">数值的读取方式：从多份副本到单一数据源</text>
  <text x="600" y="60" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="13" fill="#3a4a3a">重构只做了一件事——把 public 字段的读取换成 StatsManger.Instance.xxx，调用点一行都没挪</text>

  <!-- 重构前 -->
  <g transform="translate(48, 84)">
    <rect x="0" y="0" width="520" height="130" rx="5" fill="#ffffff" stroke="#c43131" stroke-opacity="0.5"/>
    <text x="14" y="24" font-family="ui-sans-serif, sans-serif" font-size="13" font-weight="700" fill="#8a2a20">重构前：每个脚本自带一份</text>
    <text x="14" y="50" font-family="ui-monospace, monospace" font-size="11.5" fill="#1a3d28">PlayerMovement</text>
    <text x="506" y="50" text-anchor="end" font-family="ui-monospace, monospace" font-size="11.5" fill="#c43131">* speed</text>
    <text x="14" y="76" font-family="ui-monospace, monospace" font-size="11.5" fill="#1a3d28">PlayerHealth</text>
    <text x="506" y="76" text-anchor="end" font-family="ui-monospace, monospace" font-size="11.5" fill="#c43131">currentHealth</text>
    <text x="14" y="102" font-family="ui-monospace, monospace" font-size="11.5" fill="#1a3d28">Player_Combat</text>
    <text x="506" y="102" text-anchor="end" font-family="ui-monospace, monospace" font-size="11.5" fill="#c43131">damage / weaponRange</text>
    <text x="14" y="122" font-family="ui-sans-serif, sans-serif" font-size="10.5" fill="#8a2a20">3 份副本，改一处要记得同步另外几处</text>
  </g>

  <g stroke="#1a3d28" stroke-width="2" fill="none">
    <path d="M572,150 L624,150" stroke-dasharray="5 4"/>
    <path d="M624,150 L615,145 M624,150 L615,155" stroke-linecap="round"/>
  </g>

  <!-- 重构后 -->
  <g transform="translate(632, 84)">
    <rect x="0" y="0" width="520" height="130" rx="5" fill="#ffffff" stroke="#1a7a3a" stroke-opacity="0.55"/>
    <text x="14" y="24" font-family="ui-sans-serif, sans-serif" font-size="13" font-weight="700" fill="#1a5a30">重构后：全部读同一个单例</text>
    <text x="14" y="50" font-family="ui-monospace, monospace" font-size="11.5" fill="#1a3d28">PlayerMovement</text>
    <text x="506" y="50" text-anchor="end" font-family="ui-monospace, monospace" font-size="11" fill="#1a7a3a">StatsManger.Instance.speed</text>
    <text x="14" y="76" font-family="ui-monospace, monospace" font-size="11.5" fill="#1a3d28">PlayerHealth</text>
    <text x="506" y="76" text-anchor="end" font-family="ui-monospace, monospace" font-size="11" fill="#1a7a3a">StatsManger.Instance.currentHealth</text>
    <text x="14" y="102" font-family="ui-monospace, monospace" font-size="11.5" fill="#1a3d28">Player_Combat</text>
    <text x="506" y="102" text-anchor="end" font-family="ui-monospace, monospace" font-size="11" fill="#1a7a3a">StatsManger.Instance.damage</text>
    <text x="14" y="122" font-family="ui-sans-serif, sans-serif" font-size="10.5" fill="#1a5a30">1 个数据源，UI 与战斗逻辑看到的是同一组数</text>
  </g>

  <!-- 对比小结 -->
  <g transform="translate(48, 232)">
    <rect x="0" y="0" width="12" height="12" rx="2" fill="#c43131"/>
    <text x="20" y="11" font-family="ui-sans-serif, sans-serif" font-size="12" fill="#5a2a20">改一个数值：要在 3 个 Inspector 之间来回找，漏掉一个就「表里不一」</text>
  </g>
  <g transform="translate(632, 232)">
    <rect x="0" y="0" width="12" height="12" rx="2" fill="#1a7a3a"/>
    <text x="20" y="11" font-family="ui-sans-serif, sans-serif" font-size="12" fill="#1a5a30">改一个数值：只动 StatsManger 一处，所有引用自动生效</text>
  </g>

  <!-- 代码前后对照 -->
  <g transform="translate(48, 262)">
    <rect x="0" y="0" width="1104" height="118" rx="5" fill="#1e2a22"/>
    <text x="16" y="24" font-family="ui-monospace, monospace" font-size="11.5" fill="#e8a0a0">// 重构前（PlayerMovement.cs）</text>
    <text x="16" y="46" font-family="ui-monospace, monospace" font-size="12.5" fill="#e8f0e8">rb.velocity = new Vector2(horizontal, vertical) * speed;</text>
    <text x="16" y="74" font-family="ui-monospace, monospace" font-size="11.5" fill="#9fd8a8">// 重构后（同一个调用点，只是取值来源变了）</text>
    <text x="16" y="96" font-family="ui-monospace, monospace" font-size="12.5" fill="#e8f0e8">rb.velocity = new Vector2(horizontal, vertical) * StatsManger.Instance.speed;</text>
    <text x="1088" y="24" text-anchor="end" font-family="ui-sans-serif, sans-serif" font-size="10.5" fill="#7f9b86">变量名一个没改，只换了「去哪儿拿数」</text>
  </g>
</svg>
"""

TOGGLE = r"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 400" width="1200" height="400">
  <defs>
    <linearGradient id="bgt" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0" stop-color="#fff8e8"/>
      <stop offset="1" stop-color="#f2e4c4"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="1200" height="400" fill="url(#bgt)"/>

  <text x="600" y="40" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="22" font-weight="700" fill="#5a3a20">Esc 开关：一个 bool 同时翻转三个东西</text>
  <text x="600" y="62" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="13" fill="#3a2a20">statsOpen 决定 Time.timeScale 与 CanvasGroup.alpha，三者必须一起变</text>

  <!-- 关闭态 -->
  <g transform="translate(72, 92)">
    <rect x="0" y="0" width="470" height="190" rx="5" fill="#ffffff" stroke="#1a3d28" stroke-opacity="0.35"/>
    <text x="16" y="28" font-family="ui-sans-serif, sans-serif" font-size="14" font-weight="700" fill="#1a3d28">关闭态（游戏进行中）</text>
    <line x1="16" y1="42" x2="454" y2="42" stroke="#1a3d28" stroke-opacity="0.2"/>
    <text x="16" y="68" font-family="ui-monospace, monospace" font-size="12.5" fill="#1a3d28">statsOpen</text>
    <text x="454" y="68" text-anchor="end" font-family="ui-monospace, monospace" font-size="12.5" fill="#8a5a20">false</text>
    <text x="16" y="106" font-family="ui-monospace, monospace" font-size="12.5" fill="#1a3d28">Time.timeScale</text>
    <text x="454" y="106" text-anchor="end" font-family="ui-monospace, monospace" font-size="12.5" fill="#1a7a3a">1.0f</text>
    <text x="16" y="144" font-family="ui-monospace, monospace" font-size="12.5" fill="#1a3d28">statsCanvas.alpha</text>
    <text x="454" y="144" text-anchor="end" font-family="ui-monospace, monospace" font-size="12.5" fill="#c43131">0</text>
    <text x="16" y="176" font-family="ui-sans-serif, sans-serif" font-size="11" fill="#3a4a3a">Update / FixedUpdate 都在跑，游戏照常进行</text>
  </g>

  <!-- 双向箭头 -->
  <g stroke="#5a3a20" stroke-width="2" fill="none">
    <path d="M548,150 L640,150" stroke-dasharray="5 4"/>
    <path d="M640,150 L631,145 M640,150 L631,155" stroke-linecap="round"/>
    <path d="M640,214 L548,214" stroke-dasharray="5 4"/>
    <path d="M548,214 L557,209 M548,214 L557,219" stroke-linecap="round"/>
  </g>
  <text x="594" y="138" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="11" fill="#5a3a20" font-weight="600">Esc 按下</text>
  <text x="594" y="234" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="11" fill="#5a3a20" font-weight="600">再按一次</text>

  <!-- 打开态 -->
  <g transform="translate(658, 92)">
    <rect x="0" y="0" width="470" height="190" rx="5" fill="#1e2a22" stroke="#b48a2a"/>
    <text x="16" y="28" font-family="ui-sans-serif, sans-serif" font-size="14" font-weight="700" fill="#f0e0b8">打开态（面板显示）</text>
    <line x1="16" y1="42" x2="454" y2="42" stroke="#f0e0b8" stroke-opacity="0.25"/>
    <text x="16" y="68" font-family="ui-monospace, monospace" font-size="12.5" fill="#e8f0e8">statsOpen</text>
    <text x="454" y="68" text-anchor="end" font-family="ui-monospace, monospace" font-size="12.5" fill="#e8c870">true</text>
    <text x="16" y="106" font-family="ui-monospace, monospace" font-size="12.5" fill="#e8f0e8">Time.timeScale</text>
    <text x="454" y="106" text-anchor="end" font-family="ui-monospace, monospace" font-size="12.5" fill="#e8a0a0">0</text>
    <text x="16" y="144" font-family="ui-monospace, monospace" font-size="12.5" fill="#e8f0e8">statsCanvas.alpha</text>
    <text x="454" y="144" text-anchor="end" font-family="ui-monospace, monospace" font-size="12.5" fill="#9fd8a8">1</text>
    <text x="16" y="176" font-family="ui-sans-serif, sans-serif" font-size="11" fill="#9fb8a4">世界冻结，但 Update 照跑——所以 Esc 还能被读到</text>
  </g>

  <!-- 底部坑 -->
  <g transform="translate(0, 306)">
    <rect x="72" y="0" width="1056" height="76" rx="5" fill="#ffffff" stroke="#b48a2a" stroke-opacity="0.7"/>
    <text x="88" y="24" font-family="ui-sans-serif, sans-serif" font-size="12.5" font-weight="700" fill="#8a5a20">💡 timeScale = 0 冻结的是「时间」，不是「输入」</text>
    <text x="88" y="46" font-family="ui-monospace, monospace" font-size="11.5" fill="#5a3a20">FixedUpdate 不再被调用；WaitForSeconds 被冻住，WaitForSecondsRealtime 不受影响；Update 仍每帧执行</text>
    <text x="88" y="66" font-family="ui-sans-serif, sans-serif" font-size="11" fill="#3a2a20">所以：玩家会停在原地（移动在 FixedUpdate），被击退的协程也会被冻住——打开面板等于直接暂停</text>
  </g>
</svg>
"""

SLOTS = r"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 400" width="1200" height="400">
  <defs>
    <linearGradient id="bgs" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0" stop-color="#eef2f5"/>
      <stop offset="1" stop-color="#dbe4ea"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="1200" height="400" fill="url(#bgs)"/>

  <text x="600" y="40" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="22" font-weight="700" fill="#1a2a33">StatsSlot：一个可复用的面板槽</text>
  <text x="600" y="62" text-anchor="middle" font-family="ui-sans-serif, sans-serif" font-size="13" fill="#2a3a44">预制体 = 九宫格底图 + 铺满父级的 TMP 子物体；面板用 GridLayoutGroup 来排它</text>

  <!-- 左：层级树 -->
  <g transform="translate(48, 92)">
    <rect x="0" y="0" width="600" height="188" rx="5" fill="#ffffff" stroke="#1a3d28" stroke-opacity="0.3"/>
    <text x="16" y="26" font-family="ui-sans-serif, sans-serif" font-size="13" font-weight="700" fill="#1a3d28">场景层级（SampleScene）</text>

    <text x="24" y="52" font-family="ui-monospace, monospace" font-size="12" fill="#1a3d28">StatsCanvas</text>
    <text x="150" y="52" font-family="ui-monospace, monospace" font-size="10.5" fill="#5a3a20">Canvas · CanvasScaler(1920×1080) · GraphicRaycaster · CanvasGroup α=0</text>

    <path d="M32,58 L32,72 L40,72" fill="none" stroke="#1a3d28" stroke-width="1.2"/>
    <text x="48" y="76" font-family="ui-monospace, monospace" font-size="12" fill="#1a3d28">StatsPanel</text>
    <text x="150" y="76" font-family="ui-monospace, monospace" font-size="10.5" fill="#c43131">← StatsUI 脚本挂在这里</text>

    <path d="M56,82 L56,98 L64,98" fill="none" stroke="#1a3d28" stroke-width="1.2"/>
    <text x="72" y="102" font-family="ui-monospace, monospace" font-size="12" fill="#1a3d28">Banner</text>
    <text x="150" y="102" font-family="ui-monospace, monospace" font-size="10.5" fill="#5a3a20">标题底图（Image）</text>

    <path d="M56,108 L56,124 L64,124" fill="none" stroke="#1a3d28" stroke-width="1.2"/>
    <text x="72" y="128" font-family="ui-monospace, monospace" font-size="12" fill="#1a3d28">TextPanel</text>
    <text x="170" y="128" font-family="ui-monospace, monospace" font-size="10.5" fill="#1a7a3a">GridLayoutGroup · cell 300×100</text>

    <path d="M80,134 L80,150 L88,150" fill="none" stroke="#1a3d28" stroke-width="1.2"/>
    <text x="96" y="154" font-family="ui-monospace, monospace" font-size="12" fill="#1a3d28">StatsSlot</text>
    <text x="200" y="154" font-family="ui-monospace, monospace" font-size="10.5" fill="#5a3a20">预制体实例 · statsSlots[0]</text>

    <text x="120" y="176" font-family="ui-monospace, monospace" font-size="11" fill="#5a3a20">├ Image（sliced 九宫格）　└ StarText（TMP，锚点拉伸铺满父级）</text>
  </g>

  <!-- 右：槽的外观 + 说明 -->
  <g transform="translate(676, 92)">
    <rect x="0" y="0" width="476" height="188" rx="5" fill="#1e2a22"/>
    <text x="20" y="26" font-family="ui-sans-serif, sans-serif" font-size="13" font-weight="700" fill="#f0e0b8">运行时长这样</text>

    <rect x="40" y="48" width="180" height="46" rx="4" fill="#3a5a44" stroke="#7fbf8f" stroke-dasharray="4 3"/>
    <text x="130" y="77" text-anchor="middle" font-family="ui-monospace, monospace" font-size="14" fill="#ffffff">Damage: 1</text>

    <rect x="256" y="48" width="180" height="46" rx="4" fill="#3a5a44" stroke="#7fbf8f" stroke-dasharray="4 3"/>
    <text x="346" y="77" text-anchor="middle" font-family="ui-monospace, monospace" font-size="14" fill="#ffffff">Speed: 5</text>

    <text x="40" y="118" font-family="ui-monospace, monospace" font-size="10.5" fill="#9fb8a4">底图 Image 用九宫格（Type=Sliced）</text>
    <text x="40" y="136" font-family="ui-monospace, monospace" font-size="10.5" fill="#9fb8a4">文字由子物体 StarText 提供，脚本只改它的 text</text>
    <text x="40" y="160" font-family="ui-monospace, monospace" font-size="10.5" fill="#e8c870">占位文案 'Strenth: 00'（拼写错了，Start 后立刻被覆盖）</text>
    <text x="40" y="178" font-family="ui-monospace, monospace" font-size="10.5" fill="#e8a0a0">GetComponentInChildren&lt;TMP_Text&gt;() 取的就是这个子物体</text>
  </g>

  <!-- 底部坑 -->
  <g transform="translate(0, 296)">
    <rect x="48" y="0" width="1104" height="88" rx="5" fill="#ffffff" stroke="#c43131" stroke-opacity="0.6"/>
    <text x="64" y="24" font-family="ui-sans-serif, sans-serif" font-size="12.5" font-weight="700" fill="#8a2a20">💡 预制体里的 RectTransform 会被 LayoutGroup 覆写</text>
    <text x="64" y="46" font-family="ui-monospace, monospace" font-size="11.5" fill="#5a2a20">StatsSlot.prefab 存的是 AnchoredPosition(-72.83, 87.89) / SizeDelta(145.66, 37.889)</text>
    <text x="64" y="66" font-family="ui-monospace, monospace" font-size="11.5" fill="#1a5a30">场景里这两个值被 GridLayoutGroup 改成了 0 —— 位置和尺寸由布局组算，不由预制体说了算</text>
    <text x="64" y="84" font-family="ui-sans-serif, sans-serif" font-size="10.5" fill="#3a2a20">所以「在预制体里把槽对齐好」是徒劳的，对齐要交给 TextPanel 的 GridLayoutGroup</text>
  </g>
</svg>
"""

IMAGES = [
    ('arpg-day6-cover', COVER),
    ('arpg-day6-stats-flow', FLOW),
    ('arpg-day6-panel-toggle', TOGGLE),
    ('arpg-day6-slot-hierarchy', SLOTS),
]

for name, svg in IMAGES:
    out = IMG / f'{name}.svg'
    out.write_text(svg, encoding='utf-8')
    shutil.copy(out, DOCS_IMG / f'{name}.svg')
    print(f'Written: {out}')
    png = TMP / f'{name}.png'
    subprocess.run([EDGE, '--headless', '--disable-gpu', '--hide-scrollbars',
                    f'--screenshot={png}', '--window-size=1200,400',
                    f'file:///{str(out).replace(chr(92), "/")}'],
                   capture_output=True)
    print(f'Screenshot: {png}')
