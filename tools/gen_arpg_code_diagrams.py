#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARPG 代码级分析系列配图（复用模块系列的绘图引擎）

数据来源：对 Assets/Scripe 下 31 个 .cs 的静态扫描
  编码探测 / public 字段 / GetComponent / Debug.Log / 静态事件 /
  拼写可疑标识符 / 注释掉的代码 / 目录汇总

输出：
  arpg-code-1-audit.svg     体检：5 个总指标 + 目录指标表 + P0/P1/P2 分级
  arpg-code-2-naming.svg    命名：拼写清单 + 不一致对照 + 改名影响面
  arpg-code-3-patterns.svg  八个反模式 × 出现位置
  arpg-code-4-refactor.svg  重构：目录树前后对照 + 迁移五步
  arpg-code-c7..c10.svg     四篇封面

运行：python tools/gen_arpg_code_diagrams.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_arpg_module_diagrams import (  # noqa: E402
    C, T, chip, card, ghost, table, section, head, legend, finish,
    svg_head, svg_tail, Flow, gapchip, tw, ROOT, OUT,
)


# ============================================================ 图 1 体检报告
def build_audit():
    W = 1200
    s = []
    s.append(head(W, "代码体检：31 个文件，1565 行，一次静态扫描",
                  "扫的是 Assets/Scripe 下全部 .cs：编码、public 字段、GetComponent、事件、拼写、注释掉的代码"))

    # ---- 五个总指标 ----
    y0 = 118
    stats = [
        ("31", "个脚本", "7 个目录", C["ui"]),
        ("1565", "行代码", "含注释与空行", C["player"]),
        ("113", "个 public 字段", "全靠 Inspector 拖", C["bad"]),
        ("5", "个文件是 GBK", "其余 26 个带 BOM", C["bad"]),
        ("11", "个文件有拼写问题", "共 6 类", C["item"]),
    ]
    cw = (1112 - 4 * 18) / 5
    for i, (big, unit, note, col) in enumerate(stats):
        x = 44 + i * (cw + 18)
        s.append(f'<rect x="{x:.1f}" y="{y0}" width="{cw:.1f}" height="104" rx="9" '
                 f'fill="#ffffff" stroke="{col}" stroke-opacity="0.30"/>')
        s.append(f'<rect x="{x:.1f}" y="{y0}" width="{cw:.1f}" height="4" rx="2" '
                 f'fill="{col}" fill-opacity="0.75"/>')
        s.append(T(x + 16, y0 + 46, big, 26, col, weight="700"))
        s.append(T(x + 16 + tw(big, 26) + 6, y0 + 46, unit, 10.4, C["sub"]))
        s.append(T(x + 16, y0 + 70, note, 9.8, C["sub"]))

    # ---- 目录指标表 ----
    y1 = y0 + 130
    s.append(section(y1, "① 按目录摊开：谁的 public 字段最多", C["ui"],
                     "public 字段 = 需要人去 Inspector 里拖一次的接口，数量越多，模块越难整体搬走"))
    body, h = table(44, y1 + 34,
                    ["目录", "文件", "行数", "public", "GetComponent", "Debug.Log", "静态事件"],
                    [["Player", "9", "462", "45", "9", "2", "1"],
                     ["Inventory&Shop/Shop", "5", "303", "14", "1", "0", "1"],
                     ["Inventory&Shop", "5", "282", "24", "2", "0", "1"],
                     ["Enemy", "4", "237", "15", "7", "2", "1"],
                     ["SkillTree", "5", "220", "15", "0", "1", "2"],
                     ["Tile Scripe", "2", "54", "0", "2", "0", "0"],
                     ["Arrow", "1", "7", "0", "0", "0", "0"],
                     ["合计", "31", "1565", "113", "21", "5", "6"]],
                    [214, 76, 86, 96, 150, 132, 110], accent=C["ui"], mono_cols=(0,))
    s.append(body)
    y2 = y1 + 34 + h + 22
    s.append(T(44, y2, "Player 一个目录占了 45 个 public 字段（全项目的 40%）——"
                       "这也是为什么「玩家」最难拆成独立模块。", 10.8, C["bad"]))

    # ---- 严重度分级 ----
    y3 = y2 + 30
    s.append(section(y3, "② 严重度分级：先修会崩的，再谈优雅", C["bad"],
                     "P0 = 会崩或逻辑错；P1 = 能跑但会咬人；P2 = 看着难受"))
    cols = [
        ("P0 · 7 条", C["bad"], [
            "OnMonsterDefeated 裸调用 → 敌人不死",
            "AddItem 写入 quantity → 超堆叠",
            "SellItem 不返回结果 → 物品蒸发",
            "ItemSo.damage 从不生效 → 承诺落空",
            "Arrow 命中非敌人层 → 空引用",
            "OnValidate 未判空 → 编辑器报错",
            "Return 调试键进了发布版",
        ]),
        ("P1 · 9 条", C["in"], [
            "113 个 public 字段靠人拖",
            "StatsManger ↔ StatsUI 双向引用",
            "静态事件订阅绑在 UI 生命周期上",
            "enabled 当状态位（Q 切武器）",
            "动画事件承载判定时序",
            "skillName 字符串 switch",
            "三份面板开关各自改 timeScale",
            "hits[0] 只结算第一个",
            "8 个 statsSlots 只填 2 个",
        ]),
        ("P2 · 6 条", C["sub"], [
            "5 个 GBK 文件混在 UTF-8 里",
            "6 类拼写（Manger/Eqiupment/…）",
            "12 行注释掉的旧代码",
            "未使用的 using（VisualScripting）",
            "5 处 Debug.Log 留在正式代码",
            "ArrowPool 是个空类",
        ]),
    ]
    cw2 = (1112 - 2 * 20) / 3
    for i, (t, col, lines) in enumerate(cols):
        x = 44 + i * (cw2 + 20)
        hh = 46 + len(lines) * 20
        s.append(f'<rect x="{x:.1f}" y="{y3 + 24}" width="{cw2:.1f}" height="{hh}" rx="9" '
                 f'fill="#ffffff" stroke="{col}" stroke-opacity="0.30"/>')
        s.append(T(x + 16, y3 + 48, t, 12.4, col, weight="700"))
        yy = y3 + 72
        for ln in lines:
            s.append(T(x + 16, yy, "· " + ln, 9.9, C["ink"]))
            yy += 20
    return finish(s, W, ["ui", "player", "bad", "item", "in", "sub"])




# ============================================================ 图 2 命名
def build_naming():
    W = 1200
    s = []
    s.append(head(W, "命名与拼写：6 类拼写、6 处不一致",
                  "这些名字不会让游戏崩，但它们会让人在搜索框里搜不到东西 —— 这是最便宜也最容易被跳过的一部分"))

    y0 = 118
    s.append(section(y0, "① 拼写清单", C["item"],
                     "按「错误出现在多少个文件里」排序，前两个是系统性污染"))
    body, h = table(44, y0 + 34,
                    ["现在的写法", "应该是", "出现在", "波及"],
                    [["StatsManger", "StatsManager", "Player/StatsManger.cs", "11 个文件 + 20 处引用"],
                     ["Player_ChangeEqiupment", "Player_ChangeEquipment", "Player/", "3 处（类名 + 字段 + 场景）"],
                     ["shootColldown", "shootCooldown", "Player_Bow", "3 处"],
                     ["isKnockack", "isKnockback", "PlayerMovement", "2 处"],
                     ["OnBuyBottonClicked", "OnBuyButtonClicked", "ShopSlot", "2 处（含按钮绑定）"],
                     ["Scripe（目录）", "Script / Scripts", "Assets/Scripe", "整个目录"],
                     ["ShopKeeperRennderTexture", "ShopKeeperRenderTexture", "RenderTexture 资产", "1 处"]],
                    [326, 300, 262, 200], accent=C["item"], mono_cols=(0, 1, 2))
    s.append(body)
    y1 = y0 + 34 + h + 22
    s.append(T(44, y1, "最贵的是 StatsManger：11 个文件都在写这个名字，"
                       "而 Unity 里改 MonoBehaviour 类名必须同步改文件名 —— 改名不是「查找替换」那么简单。", 10.8, C["bad"]))

    y2 = y1 + 30
    s.append(section(y2, "② 命名不一致：同一件事，三种叫法", C["in"],
                     "这类问题不影响运行，只影响「这个字段到底是干什么的」"))
    body2, h2 = table(44, y2 + 34,
                      ["位置", "写法", "问题"],
                      [["两个 SO 基类", "ItemSo / SkillSO", "后缀大小写不一致（So / SO）"],
                       ["敌人模块", "Enemy_Health.OnMonsterDefeated", "同一个模块里 Enemy 与 Monster 混用"],
                       ["ToggleSkillTree", "字段名 statsCanvas", "实际指向的是技能面板的 CanvasGroup"],
                       ["Player_Bow", "shootTimer / shootColldown", "一个计时器、一个间隔，后缀还不一样"],
                       ["全项目 private 字段", "isKnockack / facingDirection", "有没有 _ 前缀完全随机"],
                       ["InventoryManager", "itemSlots / lootPrefab / player", "三个字段指向三种东西，命名无规律"]],
                      [280, 330, 460], accent=C["in"], mono_cols=(1,))
    s.append(body2)

    # ---- ③ 改一个类名要走几步 ----
    y3 = y2 + 34 + h2 + 40
    s.append(section(y3, "③ 把 StatsManger 改名，要走四步", C["bad"],
                     "Unity 的 MonoBehaviour 类名必须与文件名一致，所以这不是一次查找替换"))
    f = Flow(44, 520, y3 + 44, gap=44, side_x=596, side_w=560)
    f.one("① 改文件名", ["StatsManger.cs → StatsManager.cs", "（.meta 跟着改名，GUID 不变）"], C["item"])
    f.one("② 改类名", ["public class StatsManger → StatsManager", "此时若文件名与类名不一致，", "Unity 会报「脚本类找不到」"], C["item"],
          side=("为什么必须成对改",
                ["MonoBehaviour 的序列化靠「GUID + fileID」认脚本，",
                 "但 Unity 编辑器还要求类名 == 文件名，",
                 "否则场景里的组件会显示为 Missing (Mono Script)。",
                 "所以这两步必须一起做、一次做完。"], "gray"))
    f.one("③ 改 11 个文件里的引用", ["PlayerMovement / Player_Combat / PlayerHealth", "StatsUI / Player_Bow / Arrow / UseItem",
                                    "InventorySlot / SkillManager / Enemy_* …", "共 20 处 StatsManger.Instance"], C["item"])
    f.one("④ 回归测试", ["确认场景里 6 个组件没变成 Missing", "确认 20 处 .Instance 都不为空", "确认 Inspector 里的数值还在"], C["bad"])
    frag, endy = f.build()
    s.append(frag)
    s.append(gapchip(f, 2, "最容易漏的一步", C["bad"], 22))

    y4 = endy + 40
    s.append(ghost(44, y4, 1112, 76, "为什么不建议现在改名",
                   ["改名收益是「以后好搜」，成本是「动一次全项目最大的单例 + 6 个场景组件 + 20 处调用」。",
                    "更划算的顺序：先补掉落表、先修 P0 的逻辑错，等这些代码真的要被重用时再改名。",
                    "如果要改，就用 IDE 的 Rename 一次做完，不要分两次提交。"], C["gray"]))
    return finish(s, W, ["item", "in", "bad", "gray", "ui"])




# ============================================================ 图 3 八个反模式
def build_patterns():
    W = 1200
    s = []
    s.append(head(W, "八个反模式：全项目扫出来的重复病灶",
                  "每一种都在多处出现。数字是「这个写法在代码里出现了多少次」，不是「有几个 bug」。"))

    # ---- 出现次数横条 ----
    y0 = 118
    s.append(section(y0, "① 出现次数", C["bad"], "越靠上越是结构性的，越难靠局部修补解决"))
    bars = [
        ("public 字段当接口", 113, C["bad"], "45 个在 Player 一个目录"),
        ("anim.SetXxx 魔法字符串", 20, C["item"], "9 个不同参数名，写错不报错"),
        ("Input 轮询散在 6 个 Update", 12, C["in"], "没有统一输入层"),
        ("静态事件", 6, C["growth"], "解耦的关键，也是断链的源头"),
        ("动画事件", 6, C["ui"], "判定时序写在 .anim 里"),
        ("hits[0] / enemies[0] 只取第一个", 5, C["player"], "多目标只结算一个"),
        ("Time.timeScale 当面板开关", 6, C["bad"], "3 个文件各改各的"),
        ("Debug.Log 留在正式代码", 5, C["sub"], "含 gizmo 里的调试输出"),
    ]
    maxv = max(b[1] for b in bars)
    bx, bw = 244, 520
    yy = y0 + 34
    for name, v, col, note in bars:
        s.append(T(44, yy + 15, name, 10.6, C["ink"]))
        s.append(f'<rect x="{bx}" y="{yy + 4}" width="{bw}" height="14" rx="7" fill="{col}" fill-opacity="0.10"/>')
        s.append(f'<rect x="{bx}" y="{yy + 4}" width="{bw * v / maxv:.1f}" height="14" rx="7" '
                 f'fill="{col}" fill-opacity="0.62"/>')
        s.append(T(bx + bw + 12, yy + 15, str(v), 10.8, col, weight="700"))
        s.append(T(bx + bw + 56, yy + 15, note, 9.8, C["sub"]))
        yy += 26

    # ---- 八条清单 ----
    y1 = yy + 22
    s.append(section(y1, "② 每条的危险点与修法", C["bad"], None))
    body, h = table(44, y1 + 34,
                    ["反模式", "为什么危险", "修法"],
                    [["public 字段当依赖注入", "换场景/换预制体就得重新拖一遍，错了只在运行时空引用", "改成 Awake 里 GetComponent 或显式 Initialize()"],
                     ["单例 + 双向引用", "StatsManger 持有 statsUI，数据层反过来依赖表现层", "让 UI 订阅事件，不提供服务给数据层"],
                     ["静态事件绑在 UI 生命周期", "关掉 HUD 就退订，逻辑随之失效", "把 ExpManager 移到常驻物体上"],
                     ["enabled 当状态位", "拦得住 Update，拦不住别人直接调方法", "用状态机或接口，不用 enabled 当锁"],
                     ["动画事件承载逻辑", "函数名写错/改名 → 不报错、静默失效", "动画事件只转发到明确的入口方法"],
                     ["skillName 字符串 switch", "加一份 SO 就要改代码，名字打错落进 default", "给 SkillSO 加枚举或 Effect 策略"],
                     ["魔法数字", "15/10、2、0.5、3、1.2 散落各处，改一处漏一处", "抽到 SO 或 static readonly 常量"],
                     ["复制粘贴", "三份面板开关、两处 hits[0]，改一处就不同步", "抽公共基类或工具方法"]],
                    [300, 470, 340], accent=C["bad"], mono_cols=(0,))
    s.append(body)

    y2 = y1 + 34 + h + 22
    s.append(ghost(44, y2, 1112, 76, "这八个里有三个是「Unity 特有」的，也是最容易被教程带进来的",
                   ["enabled 当开关、动画事件承载逻辑、public 字段拖引用 —— 它们在几十行的小 demo 里都没问题，",
                    "问题出在「项目长到上千行之后，这三样会同时变成隐式契约」，而隐式契约没法被编译器检查。",
                    "其余五个（单例双向、静态事件、字符串 switch、魔法数字、复制粘贴）是通用工程问题。"], C["gray"]))
    return finish(s, W, ["bad", "item", "in", "growth", "ui", "player", "sub", "gray"])




# ============================================================ 图 4 重构方案
def build_refactor():
    W = 1200
    s = []
    s.append(head(W, "如果重写：目录重组与六步迁移",
                  "原则：先做「纯新增」的改动，再做「替换实现」，最后才做「改名」。风险从零往上走。"))

    # ---- ① 目录树前后 ----
    y0 = 118
    s.append(section(y0, "① 目录：从「按天建」到「按层建」", C["ui"], None))
    before = [
        "Assets/Scripe/            ← 名字拼错",
        "├ Player/        9 文件 462 行",
        "├ Enemy/         4 文件 237 行",
        "├ Inventory&Shop/10 文件 585 行",
        "│  └ Shop/       5 文件 303 行",
        "├ SkillTree/     5 文件 220 行",
        "├ Tile Scripe/   2 文件  54 行",
        "└ Arrow/         1 文件   7 行（空类）",
    ]
    after = [
        "Assets/Scripts/",
        "├ Core/         GameEvents / IPanel / IDamageable",
        "├ Player/       Movement Combat Bow Arrow Health",
        "├ Enemy/        Movement Combat Health Knockback",
        "├ Items/        ItemSO Inventory Shop",
        "├ Skills/       SkillSO Slot TreeManager Effects",
        "├ World/        Elevation Entry/Exit",
        "└ UI/           PanelManager + 各面板",
    ]
    for k, (title, lines, col) in enumerate([
            ("现在：一层按「主题」，一层按「子系统」", before, C["sub"]),
            ("之后：先按职责分层，再按子系统分目录", after, C["ui"])]):
        x = 44 + k * 566
        s.append(f'<rect x="{x}" y="{y0 + 30}" width="546" height="216" rx="9" fill="#ffffff" '
                 f'stroke="{col}" stroke-opacity="0.30"/>')
        s.append(T(x + 18, y0 + 56, title, 11.6, col, weight="700"))
        for j, ln in enumerate(lines):
            s.append(T(x + 18, y0 + 82 + j * 19, ln, 10.2, C["ink"], mono=True))
    y1 = y0 + 30 + 216 + 22
    s.append(T(44, y1, "关键差别：现在「Inventory&Shop 里有一半是 UI」，"
                       "之后 UI 全部收进 UI/，数据与流程留在 Items/。", 10.8, C["sub"]))

    # ---- ② 六步迁移 ----
    y2 = y1 + 30
    s.append(section(y2, "② 六步迁移：每一步都能单独发布", C["growth"],
                     "前两步是纯新增，中间两步换实现，最后两步才是打通链路与改名"))
    f = Flow(44, 540, y2 + 44, gap=44, side_x=612, side_w=544)
    f.one("第 1 步 · 抽 GameEvents", ["6 组静态事件集中到一个静态类", "现有发布/订阅点各改一行",
                                     "不改任何生命周期、不新增行为"], C["growth"],
          side=("为什么从这一步开始",
                ["纯搬迁：事件签名不变、订阅时机不变、行为不变。",
                 "但从此「谁在发、谁在听」有了唯一入口，",
                 "后面每一步都能靠它解耦。",
                 "风险：接近零（只改 using 和事件前缀）。"], "gray"))
    f.one("第 2 步 · 抽 PanelManager", ["栈管理 + 引用计数",
                                     "Time.timeScale 只由它决定", "替掉 StatsUI / ToggleSkillTree / ShopKeeper 三份复制"],
          C["ui"],
          side=("这一步解决什么",
                ["三个面板不再各记一个 bool。",
                 "打开 push、关闭 pop，栈空才 timeScale = 1。",
                 "顺带把 interactable 的设值统一。"], "gray"))
    f.one("第 3 步 · ExpManager 搬离 Canvas", ["挂到 Player 或空 GameManager 上",
                                            "UI 引用改为 Inspector 注入",
                                            "关 HUD 不再退订"], C["player"],
          side=("为什么这一步必须早于「加掉落表」",
                ["掉落表会让「击杀」承担更多职责；",
                 "如果那时 ExpManager 还挂在 Canvas 上，",
                 "就是在一根随时会断的线上再加负载。"], "bad"))
    f.one("第 4 步 · SkillSO 加效果策略", ["去掉 switch(skillName)",
                                       "改为 SkillEffect 基类 / 枚举 + 表",
                                       "加一份 SO 不用改代码"], C["growth"])
    f.one("第 5 步 · 打通升级 → 属性", ["StatsManger 暴露 AddDamage / AddMaxHealth",
                                   "LevelUp() 调它，不再只 +1 个计数",
                                   "StatsUI 改为订阅刷新"], C["data"])
    f.one("第 6 步 · 最后才改名", ["StatsManger → StatsManager",
                               "Player_ChangeEqiupment → …Equipment",
                               "Scripe/ → Scripts/"], C["item"],
          side=("为什么放最后",
                ["改名会同时动：文件名、类名、11 个文件的引用、",
                 "  6 个场景组件、以及所有文档截图。",
                 "它不改变任何行为 —— 所以收益最低、噪音最大。",
                 "等前面五步做完，代码结构稳定了再改，一次到位。"], "gray"))
    frag, endy = f.build()
    s.append(frag)

    # ---- ③ 收益表 ----
    y3 = endy + 46
    s.append(section(y3, "③ 每一步的代价与收益", C["ui"], None))
    body, h = table(44, y3 + 34,
                    ["步骤", "改动量", "风险", "换来了什么"],
                    [["1 抽 GameEvents", "1 个新文件 + 6 处引用", "极低", "事件的唯一入口"],
                     ["2 抽 PanelManager", "1 个新类 + 3 处替换", "低", "面板能叠加、timeScale 有主"],
                     ["3 ExpManager 搬家", "1 处挂载 + 2 个引用", "低", "关 HUD 不再断链"],
                     ["4 SkillSO 策略化", "1 个基类 + 4 份 SO", "中", "加技能不用改代码"],
                     ["5 升级 → 属性", "1 个方法 + 1 处调用", "中", "等级第一次真的有意义"],
                     ["6 改名", "全项目 + 场景", "中（易漏）", "只影响可读性"]],
                    [246, 300, 130, 348], accent=C["growth"], mono_cols=(0,))
    s.append(body)
    return finish(s, W, ["ui", "growth", "player", "data", "item", "sub", "bad", "gray"])


# ============================================================ 封面
from gen_arpg_module_diagrams import cover as _cover  # noqa: E402

COVERS = [
    ("arpg-code-c7.svg",
     "代码体检：31 个文件的一次静态扫描",
     "1565 行 · 113 个 public 字段 · 5 个 GBK 文件 · 11 个文件有拼写问题",
     [("五个总指标", ["31 个脚本 / 1565 行", "113 个 public 字段", "5 个 GBK + 26 个 BOM"]),
      ("按目录摊开", ["Player 45 个 public 字段", "Enemy 7 处 GetComponent", "SkillTree 2 组事件"]),
      ("严重度分级", ["P0 七条：会崩 / 逻辑错", "P1 九条：能跑但咬人", "P2 六条：看着难受"])],
     "#f6f3ee", "#ece5da", "#4a3d28"),
    ("arpg-code-c8.svg",
     "命名与拼写：6 类错误、6 处不一致",
     "StatsManger / Eqiupment / Colldown / Knockack / Botton / Scripe",
     [("六类拼写", ["StatsManger → StatsManager", "11 个文件 + 20 处引用", "改名要连文件名一起动"]),
      ("六处不一致", ["ItemSo vs SkillSO", "OnMonsterDefeated 在 Enemy 模块", "statsCanvas 其实是技能面板"]),
      ("改名四步", ["改文件名 → 改类名", "改 11 个文件引用", "回归场景 6 个组件"])],
     "#f7f2f6", "#eee2ec", "#5c2f52"),
    ("arpg-code-c9.svg",
     "八个反模式：全项目扫出来的重复病灶",
     "public 字段 113 次 · 魔法字符串 20 次 · 静态事件 6 组 · 动画事件 6 个",
     [("结构性最强的", ["public 字段当接口（113）", "anim.SetXxx 魔法字符串（20）", "Input 轮询散在 6 个 Update"]),
      ("Unity 特有的三个", ["enabled 当状态位", "动画事件承载逻辑", "public 字段拖引用"]),
      ("每条的修法", ["抽 GameEvents / PanelManager", "SkillSO 加效果策略", "把魔法数字搬进 SO"])],
     "#eef3f7", "#dde7f1", "#2a4763"),
    ("arpg-code-c10.svg",
     "如果重写：目录重组与六步迁移",
     "先做纯新增，再替换实现，最后才改名",
     [("目录重组", ["Scripe/ → Scripts/", "Core / Player / Enemy", "Items / Skills / World / UI"]),
      ("六步迁移", ["1 抽 GameEvents（零风险）", "2 抽 PanelManager", "3 ExpManager 搬离 Canvas"]),
      ("最后两步", ["5 打通升级 → 属性", "6 最后才改名", "改名收益最低、噪音最大"])],
     "#eef6ee", "#dcead9", "#25452a"),
]


def build_covers():
    out = {}
    for name, title, sub, facts, c1, c2, accent in COVERS:
        out["images/" + name] = _cover(name.replace("-", "").replace(".svg", ""),
                                       title, sub, facts, c1, c2, accent)
    return out


BUILDERS = [
    ("arpg-code-1-audit.svg", build_audit),
    ("arpg-code-2-naming.svg", build_naming),
    ("arpg-code-3-patterns.svg", build_patterns),
    ("arpg-code-4-refactor.svg", build_refactor),
]


def main():
    want = set(os.sys.argv[1:])
    for name, fn in BUILDERS:
        if want and name not in want:
            continue
        data = fn()
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            fh.write(data)
        print(f"  {name:30s} {len(data):7d} bytes")
    if not want:
        for name, data in build_covers().items():
            with open(os.path.join(ROOT, name), "w", encoding="utf-8") as fh:
                fh.write(data)
            print(f"  {name:30s} {len(data):7d} bytes")


if __name__ == "__main__":
    main()
