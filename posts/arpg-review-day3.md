---
title: ARPG 功能复盘 Day 3：虚拟相机与敌人的第一套状态机
date: 2026-10-13 22:00:00
updated: 2026-10-20 12:00:00
tags: Unity, ARPG, 游戏开发, 复盘, Cinemachine, 状态机
summary: 这一天两个系统同时上线：Cinemachine 虚拟相机让镜头跟手又不越界，Enemy_Movement 用枚举 + Animator Bool 搭出第一套状态机。这也是敌人第一次真的能造成伤害——用的是被后来废弃的碰撞扣血。
cover: images/arpg-review-day3-cover.svg
pinned: false
draft: false
slug: arpg-review-day3
---

## 背景与目标

前两天人物能走、地图有层次，但镜头是死的：走出屏幕就看不见人。同时敌人还只是个会站着的 Sprite。第三天的目标有两块：

- **镜头**：跟随玩家、平滑、不露出地图外的空白
- **敌人**：从完全静止，变成会朝玩家移动

顺带把「敌人碰到玩家会掉血」这条链路接通，让战斗有一个起点。

## 实现要点

### 实现思路

相机侧不写代码，交给 Cinemachine：

- `Main Camera` 挂 `CinemachineBrain`，负责把虚拟相机的计算结果应用到真实相机
- `Virtual Camera` 用一个 `Follow` 目标（玩家）+ 一个 `Confiner`（限定相机可达范围）+ 一个死区（目标小幅移动时不推镜头）

敌人侧写状态机：

- 定义枚举 `EnemyState { Idle, Chasing, Attacking, knockback }`，当天只实现前两态，后两个先占位
- `ChangeState(newState)` 里负责把旧的 Animator Bool 关掉、新的打开
- `Update` 里根据当前状态决定要不要追击

伤害侧走物理碰撞：`Enemy_Combat` 里用 `OnCollisionEnter2D`，撞到玩家就调 `PlayerHealth.ChangeHealth(-damage)`。

### 关键技术点

- **分离「相机逻辑」与「相机表现」**：`CinemachineBrain` 在真实相机上，跟随策略全在虚拟相机上配。换跟法不用改代码，也不用担心手写 `Lerp` 跟不上的问题。
- **Confiner 用碰撞体圈出取景范围**：相机中心被限制在这个形状内，靠近地图边缘时不会拍到空白。这比手写边界钳制少写几十行。
- **死区（Dead Zone）**：玩家在中心小范围移动时镜头不动，避免「人一动画面就跟着晃」的晕眩感。
- **状态用枚举而不是一堆 bool**：`ChangeState` 内部把旧态关掉、新态打开，调用方只说「我要去哪」，不用记上一帧是什么。
- **HP 文本用动画而不是代码补间**：`PlayerHealth` 24 行，改文本的同时 `healthTextAnim.Play("TextUpdate")`，数字跳动交给 Animator。

### 遇到的问题与解决

**1. 碰撞扣血只能贴身**

`OnCollisionEnter2D` 要求两个碰撞体真的碰上。于是敌人必须贴到玩家身上才能造成伤害，没有任何「挥击前的距离判断」。这不是 bug，是设计边界——它直接催生了 Day 4 的主动感知。

那段代码至今还以注释形式留在 `Enemy_Combat.cs` 第 14–20 行，成了这次迭代的化石：

```csharp
//private void OnCollisionEnter2D(Collision2D collision)
//{
//    if (collision.gameObject.tag == "Player")
//    {
//        collision.gameObject.GetComponent<PlayerHealth>().ChangeHealth(-damage);
//    }
//}
```

**2. 追击进得去出不来**

当天只有 Idle / Chasing 两态，且没有「失去目标」的判断。玩家一旦离开视野，敌人仍然朝最后位置走。这个洞在 Day 4 用检测半径补上了。

**3. `ChangeState` 是一条手写 if 链**

每加一个状态都要改四处：关旧态、赋新值、开新态、以及在 `Update` 里加分支。漏一处不会报错，只会表现为「动画卡在上一帧」。

**4. 碰撞完全静默失败**

`OnCollisionEnter2D` 依赖 Layer 碰撞矩阵。玩家和敌人只要有一边的 Layer 没勾选，代码一行不报错、伤害一点不掉。排查只能靠打印。

## 小结

这一天的两条线走的是相反路线：相机交给了现成组件，配置代替代码；敌人 AI 则是纯手写，一个枚举加一个 `ChangeState`。

手写状态机的收益是可控——你清楚每一帧在判断什么；代价是扩展时容易漏分支。后来 Day 4 加 Attacking、Day 5 加 knockback，`ChangeState` 的 if 链越来越长，这段逻辑最终成为第 9 天优化清单里的一项。

---

上一篇：[Day 2：七层瓦片与「钻山洞」的碰撞开关](arpg-review-day2.html) ｜ 下一篇：[Day 4：从「碰到才打」到「看见就追」](arpg-review-day4.html)
