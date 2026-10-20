---
title: ARPG 功能复盘 Day 6：把数值收进单例，把面板做成时停
date: 2026-10-16 22:00:00
updated: 2026-10-20 12:00:00
tags: Unity, ARPG, 游戏开发, 复盘, 架构, 单例, UI
summary: 伤害、范围、击退力、速度、血量原本散在四个脚本的 public 字段里，改一个数要翻四个文件。这一天用 StatsManger 单例把它们收成一个来源，再接一按 Esc 就 timeScale = 0 的属性面板。收益是改数值只改一处，代价是全局状态与时停语义。
cover: images/arpg-review-day6-cover.svg
pinned: false
draft: false
slug: arpg-review-day6
---

## 背景与目标

到 Day 5，同一个「攻击力」被三个地方各存了一份：`Player_Combat` 里有 `cooldown`，`Enemy_Combat` 里有 `damage`，玩家挥剑时读的又是一组独立字段。想调一次平衡，得先在 Hierarchy 里找到对应物体，再逐个改 Inspector。

第六天的目标是把这件事收敛：

- **单一数据源**：玩家相关的数值只存在一个地方
- **只依赖一个引用**：用到数值的脚本不必各自持有 `public` 字段
- **能看**：按 Esc 弹出属性面板，面板打开时游戏暂停

## 实现要点

### 实现思路

`StatsManger` 用 32 行做两件事：持有数值、保证全局唯一。字段按用途分三组：

```csharp
[Header("Combat Stats")]
public int damage;
public float weaponRange;
public float knockbackForce;
public float knockbackTime;
public float stunTime;

[Header("Movement Stats")]
public float speed;

[Header("Health Stats")]
public int maxHealth;
public int currentHealth;

private void Awake()
{
    if (Instance == null) Instance = this;
    else Destroy(gameObject);      // 场景里拖了第二个就自杀
}
```

随后把已有脚本里的 11 处硬引用改成 `StatsManger.Instance.xxx`，`Player_Combat`、`Enemy_Combat`、`PlayerMovement`、`PlayerHealth` 都不再各自保存伤害或速度。

面板侧 `StatsUI` 46 行：轮询 `ToggleStats` 输入，用一个 `statsOpen` 布尔决定开还是关。

### 关键技术点

- **单例在 `Awake` 里自毁**：重复实例直接 `Destroy`，避免两个 `StatsManager` 同时改同一份数据。
- **`Time.timeScale = 0` 冻结物理**：`FixedUpdate` 和物理步全停，但 `Update` 照常执行——这正是「暂停面板还能响应按键」的原因。
- **用 `CanvasGroup.alpha` 而不是 `SetActive`**：隐藏时不用重建 UI 层级，也不会触发一次布局重算。
- **面板内容用槽位数组**：`statsSlots[]` 里每个槽通过 `GetComponentInChildren<TMP_Text>()` 找文本，加一行属性就多拖一个槽。

### 遇到的问题与解决

**1. 只切了 `alpha`，没切交互**

面板隐藏后 `alpha = 0`，但 `CanvasGroup.interactable` 和 `blocksRaycasts` 仍然是 `true`。这块面板虽然看不见，却依然会拦住鼠标事件。Day 8 在整理 UI 时才把「三个开关管三件事」讲清楚：

| 属性 | 管什么 |
|---|---|
| `alpha` | 看不看得见 |
| `interactable` | 点不点得到 |
| `blocksRaycasts` | 会不会挡住别的 UI |

**2. `timeScale = 0` 是全局的**

暂停手感很好，但它是「整个游戏一起停」。以后想做子弹时间、或者让 UI 动画在暂停时继续播，这套方案就得换——`timeScale` 一改，所有依赖它的协程和动画都会跟着变。

**3. 槽位用下标硬编码**

`statsSlots[0]` 是伤害、`statsSlots[1]` 是速度。新增一条属性要重排数组，顺序错了不会报错，只会显示错。这类「用位置表达语义」的写法，在数据变多后一定要换成字典或显式引用。

**4. 初始化顺序靠运气**

`StatsUI.Start()` 里立刻 `UpdateAllStats()`，而它依赖 `StatsManger.Instance` 已经赋值。`Awake` 通常早于 `Start`，所以能跑通——但这是执行顺序的巧合，不是保证。

## 小结

这一天的价值不在面板，而在**把「数值」从「使用数值的脚本」里剥出来**。剥出来之后，调平衡从「翻四个 Inspector」变成「看一个组件」，也给后面的等级、技能点留了口子——加属性只需要往 `StatsManger` 里加字段。

单例的代价同样明确：它是全局状态，任何脚本都能改。工程规模一旦超过「一个人一个场景」，这个模式就会开始反噬。所以第 9 天把它列进「知道债在哪」的清单，而不是「必须马上改」的清单。

---

上一篇：[Day 5：挥剑、掉血与击退眩晕](arpg-review-day5.html) ｜ 下一篇：[Day 7：用一个静态事件接住「敌人死了」](arpg-review-day7.html)
