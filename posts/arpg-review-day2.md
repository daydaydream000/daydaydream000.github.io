---
title: ARPG 功能复盘 Day 2：七层瓦片与「钻山洞」的碰撞开关
date: 2026-10-11 22:20:00
updated: 2026-10-20 12:00:00
tags: Unity, ARPG, 游戏开发, 复盘, Tilemap
summary: 单层 Tilemap 无法同时表达遮挡与碰撞，于是把地图拆成七层，再给山洞入口/出口各挂一个 Trigger，进入时批量关掉山体碰撞、抬高玩家排序。这篇复盘讲清「渲染顺序」和「物理阻挡」为什么要当成两个维度处理，以及七层结构带来的引用维护成本。
cover: images/arpg-review-day2-cover.svg
pinned: false
draft: false
slug: arpg-review-day2
---

## 背景与目标

一张 Tilemap 只能承载一种排序。地面、水面、可穿过的草丛、挡住去路的岩壁、盖在人物前面的树冠——它们需要不同的渲染顺序和不同的碰撞行为，塞在一层里只能二选一。

第二天要解决两件事：

- **分层**：让「画在哪一层」和「能不能走过去」互相独立
- **钻山洞**：进入山洞时，遮蔽视线的山体碰撞需要被临时关掉，但它的贴图必须还在

## 实现要点

### 实现思路

按「高度 × 是否碰撞」两个维度拆分，最终得到七层（另有一层纯背景板，不参与玩法）：

| 层 | 职责 |
|---|---|
| `Ground` | 地面底色 |
| `Water` | 水面贴图 |
| `Rocks` | 岩石装饰 |
| `Collision-Low` | 低处挡路层，只碰不画 |
| `Collision-High` | 高处挡路层，只碰不画 |
| `Non-Collision-Low` | 低处纯表现层，只画不碰 |
| `Non-Collision-High` | 高处纯表现层，只画不碰 |

钻山洞用两个 Trigger 实现：`Elevation_Entry` 放在洞口，`Elevation_Exit` 放在洞的另一端，两者结构完全对称。

### 关键技术点

- **用 `OnTriggerEnter2D` 而不是碰撞**：玩家是「穿过一个区域」，不该有物理反应，Trigger 正好只报事件不产生推力。
- **批量开关碰撞体数组**：两个脚本各 27 行，核心就是遍历 Inspector 上拖好的 `mountainColliders` 与 `boundaryColliders`，一组 `enabled = false`、另一组 `enabled = true`：

```csharp
private void OnTriggerEnter2D(Collider2D collision)
{
    if (collision.gameObject.tag == "Player")
    {
        foreach (var mountain in mountainColliders) mountain.enabled = false;
        foreach (var boundary in boundaryColliders) boundary.enabled = true;
        collision.gameObject.GetComponent<SpriteRenderer>().sortingOrder = 15;
    }
}
```

- **改 `sortingOrder` 而不是 z 轴**：正交相机下 z 虽然参与排序，但它是浮点数、和地图层的编号没有对应关系。`sortingOrder` 是显式整数，谁高谁在上，排查时一眼能看出来。
- **边界碰撞与山体碰撞分组**：进洞要「去掉遮挡 + 补上洞的边界」，这是两组相反的操作，所以分成两个数组而不是一个。

### 遇到的问题与解决

**1. 进洞后能穿墙，或者出洞被空气墙挡住**

本质是数组没连全，或 Entry 与 Exit 的数组顺序不一致。四个数组全靠 Inspector 手拖、十四个引用手工对应，漏一个不会报错，只会表现为「某段墙时有时无」。这类问题只能靠走完整圈地图来验证，没有编译期保护。

**2. 七层里只有三层真的带碰撞**

场景里 7 个 Tilemap，`TilemapCollider2D` 只有 3 个，`CompositeCollider2D` 是 0 个。这意味着碰撞是逐 tile 生成的，沿砖缝走动时会被接缝轻微绊住。正确做法是给碰撞层加 `CompositeCollider2D` 并勾选 `Used By Composite`，把上千个 tile 合并成一个多边形。

**3. 排序值硬编码**

进洞 `sortingOrder = 15`，出洞回 `10`。两个数字散在两个文件里，不对称，也没有和地图层的编号建立约定。后来加新场景时这个值没有依据，只能试着调。

**4. Trigger 只认「进入」**

`OnTriggerEnter2D` 只在跨入那一刻触发。如果玩家在洞内死亡或重生，碰撞体状态不会复位，出来时世界是错的。

## 小结

七层瓦片的价值不在「层多」，而在于把**渲染顺序**和**物理阻挡**显式拆成两个可以独立调整的维度：想加一层前景装饰，只需新建一个 Non-Collision 层，不用动任何碰撞。

代价是引用密集。这套结构天然需要「配置即代码」——用脚本按名字批量绑定碰撞体，比 Inspector 手拖可靠得多。这条债一直到 Day 8 复盘时才被明确记下来。

---

上一篇：[Day 1：42 行代码，让骑士走起来](arpg-review-day1.html) ｜ 下一篇：[Day 3：虚拟相机与敌人的第一套状态机](arpg-review-day3.html)
