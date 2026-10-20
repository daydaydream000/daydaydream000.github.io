---
title: ARPG 功能复盘 Day 1：42 行代码，让骑士走起来
date: 2026-10-11 21:50:00
updated: 2026-10-20 12:00:00
tags: Unity, ARPG, 游戏开发, 复盘, 移动
summary: 从空 2D 模板到「按方向键能走、朝向正确、动画同步」，第一天的交付物是一个 42 行的 PlayerMovement。这篇复盘拆开它的四段结构（输入 → 物理 → 动画 → 翻面），并交代三个当时看不见、后面陆续发作的伏笔。
cover: images/arpg-review-day1-cover.svg
pinned: false
draft: false
slug: arpg-review-day1
---

## 背景与目标

`ARPGbegin` 从一个空 2D 模板起步：场景里一个 Sprite、一个 `Rigidbody2D`，人物站着不动。第一天只解决一件事——**按方向键能走，松手能停，朝向和动画跟着变**。

目标拆成三条验收标准：

- 八方向移动，斜向速度不失真
- 朝左走时人物翻面，而不是「倒着滑」
- 站立 / 行走两套动画由移动状态驱动，不靠代码硬切

移动是后面所有系统的地基。追击、击退、攻击位移最终都复用同一套「往刚体写速度」的方式，所以第一天把这条路径固定下来，比把功能做全更重要。

## 实现要点

### 实现思路

输入、物理、表现三件事分开处理：

1. `Input.GetAxis` 读出 `horizontal` / `vertical`，得到一个方向向量
2. 在 `FixedUpdate` 里写 `rb.velocity`
3. 把方向喂给 `Animator` 参数，由状态机决定播哪个动画

核心只有四行（下面是 Day 9 的现状，第一天 `speed` 还是脚本上的 `public` 字段，Day 6 才收进 `StatsManger`）：

```csharp
float horizontal = Input.GetAxis("Horizontal");
float vertical = Input.GetAxis("Vertical");
anim.SetFloat("horizontal", Mathf.Abs(horizontal));
anim.SetFloat("vertical", Mathf.Abs(vertical));
rb.velocity = new Vector2(horizontal, vertical) * StatsManger.Instance.speed;
```

### 关键技术点

- **写 `velocity` 必须放在 `FixedUpdate`**：刚体速度属于物理步，`Update` 里写会和物理求解抢同一帧的结果，帧率一波动就开始抖。
- **`Mathf.Abs` 是给动画用的**：动画参数只表达「这个轴动没动、动多大」，朝哪边由翻面解决。不取绝对值，状态机就得铺左右两套参数。
- **翻面用 `localScale.x *= -1`**：没有准备左右两份美术资源，直接镜像整棵子物体，资源量减半。
- **`facingDirection` 与 `localScale` 同步取反**：翻面不能只看输入方向，要判断「当前朝向是否与输入冲突」，否则每帧都在翻。

### 遇到的问题与解决

**1. 按住方向键时人物高频抖动**

最初的写法是 `if (horizontal > 0) Flip();`，结果每帧翻一次，人物原地抽搐。改成「符号冲突才翻」：

```csharp
if (horizontal > 0 && transform.localScale.x < 0 ||
    horizontal < 0 && transform.localScale.x > 0)
{
    Flip();
}
```

这个判据有个隐含前提：`localScale.x` 必须是 ±1。后来若给角色加父级缩放，判断会失效——当时没遇到，属于欠下的债。

**2. 被镜像的不只是角色**

`localScale` 翻转会把所有子物体一起镜像。玩家这边「攻击点跟着脸走」正好是想要的效果；但 Day 3 把这套写法复制到敌人身上时，检测点也跟着左右横跳，检测圈中心随朝向偏移。

**3. 移动脚本顺手管了攻击**

`Update` 里写了攻击输入：

```csharp
if (Input.GetButtonDown("Slash"))
    player_Combat.Attack();
```

当时只有 42 行，看着合理。到 Day 5 之后，输入散落在 `PlayerMovement`（攻击）、`StatsUI`（暂停）、`ExpManager`（调试加经验）三处，想统一改键位得翻三个文件。

## 小结

第一天交付的是 `PlayerMovement` 的初版：输入 → 物理 → 动画 → 翻面，四段各管一件事。42 行解决了「能走」，同时留下三个伏笔：`localScale` 作为朝向的唯一真相、子物体随翻面镜像、输入散落在功能脚本里。

这三个伏笔在后面几天陆续被踩到，也都各自付了修复成本。**功能跑起来和结构立住是两件事，第一天通常只能拿到第一件。**

---

下一篇：[Day 2：七层瓦片与「钻山洞」的碰撞开关](arpg-review-day2.html)
