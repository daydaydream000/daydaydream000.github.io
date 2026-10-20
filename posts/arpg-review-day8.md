---
title: ARPG 功能复盘 Day 8：0 行脚本的一天，搭出技能面板骨架
date: 2026-10-19 22:00:00
updated: 2026-10-20 12:00:00
tags: Unity, ARPG, 游戏开发, 复盘, UI, Canvas, 技能树
summary: 这一天没有写一行脚本：新建 UIManager 把散在根级的 Canvas 收拢，再挂一张 SkillCanvass 把技能面板的空间先摆出来——1200 的九宫格面板、两棵 300×480 的树、每棵 12 个 85×85 的空格子。这篇复盘讲清 UI 的四个开关（层级 / 排序 / 可见 / 可点），以及搬层级搬丢的一个值。
cover: images/arpg-review-day8-cover.svg
pinned: false
draft: false
slug: arpg-review-day8
---

## 背景与目标

Day 7 结束时，`level` 只是一个数字：升级了、经验条归零了、属性一点没变。下一个自然动作是「升级给技能点，点数拿去点技能树」——而技能树是这套工程里第一次出现「点哪儿」的界面。

第八天故意不写代码，只做两件事：

- **收拢**：把散在场景根级的 UI 收进一个 `UIManager` 空物体下
- **摆位**：新建一张 `SkillCanvass`，把技能面板的骨架搭到能看

理由很实际：脚本判断不了「这个格子离标题条是不是太近」「两棵树的间距合不合适」。先让界面可见，再谈它背后的数据。

## 实现要点

### 实现思路

结构上分三层：

```
UIManager（空物体）
├── StatsCanvas      （Day 6 的属性面板）
├── ExpCanvas        （Day 7 的经验条 HUD）
└── SkillCanvass     （今天新建，sortingOrder = 1）
    └── SkillPanel   1200 × 1200 九宫格
        ├── TextPanel      1200 × 250 标题条
        ├── CombatTree     300 × 480，12 个 85 × 85 空槽
        └── MagicTree      300 × 480，12 个 85 × 85 空槽
```

格子数量不是数出来的，是算出来的：`85 × 85` 的单格 + `5` 的间距，在 Flexible 布局下正好 3 列 × 4 行，12 个占位。

### 关键技术点

**1. 两个 Overlay Canvas 谁盖住谁，只看 `sortingOrder`**

同在 Screen Space - Overlay 模式下，`SkillCanvass` 的 `sortingOrder = 1`、`StatsCanvas` 默认 0，所以技能面板永远压在上面——**和 Hierarchy 里的顺序无关**。这一点和「嵌套 Canvas」是两套规则，混着记最容易翻车。

**2. `CanvasGroup` 的三个开关，管三件不同的事**

| 属性 | 管什么 | 设为 0 的效果 |
|---|---|---|
| `alpha` | 看不看得见 | 透明，但仍然参与布局 |
| `interactable` | 点不点得到 | 按钮不响应 |
| `blocksRaycasts` | 挡不挡后面的 UI | 鼠标穿透到下层 |

技能面板当天是 `alpha 1 / interactable 0 / blocksRaycasts 0`——**看得见，点不到，也不挡鼠标**。这是在「还没有交互逻辑」的阶段让骨架可见的最小代价方案。

**3. 布局用 Flexible 而不是手摆坐标**

格子放进 Grid Layout Group，锚点与间距交给布局系统，改格子尺寸不用重摆 24 个 RectTransform。

### 遇到的问题与解决

**1. 搬层级把 `alpha` 搬丢了**

Day 6 把属性面板的 `CanvasGroup.alpha` 设成 0（开局隐藏），移进 `UIManager` 之后变回了 1。结果是属性面板从第一帧就盖在屏幕上。

原因是移动父节点时，如果做过「Revert / Reset」或者重新添加 `CanvasGroup` 组件，序列化值会被重置成默认的 1。**层级搬动不是无副作用操作，搬完要回头核一遍关键开关。**

**2. 整个技能面板落在 Layer 0**

Canvas 子物体没有改 Layer，全部是 Default。如果后续给 UI 加了相机或射线，Layer 会决定谁被照到、谁被点到。

**3. 1200 高的面板超出 1080 参考**

面板高度 1200，参考分辨率 1080，上下各溢出 60。当前因为 `blocksRaycasts = 0` 没有实际影响，但一旦开启交互，边缘的内容会点不到。

**4. 两棵树下面都有一个叫 `CombatPanel` 的容器**

复制粘贴时没改名。`MagicTree` 里的那个网格容器至今还叫 `CombatPanel`，`SkillSTile` 也是那时的拼写。

**5. 面板没有任何开关**

`SkillCanvass` 没有 `CanvasGroup` 控制器，也没有按键绑定。它现在只能靠 Inspector 手动关。

**6. `ExpCanvas` 没搬进来**

UIManager 号称收拢了所有 UI，实际只收了两个。经验条仍在根级，属于「收了一半」。

## 小结

这一天的产出是零行代码，但把 UI 的四件事彻底分开了：**谁管层级（UIManager）、谁管排序（sortingOrder）、谁管可见（alpha）、谁管可点（interactable / blocksRaycasts）**。

四件事分不清，后面每加一个面板都会重踩一遍。而这一天真正的教训是另一条：**动层级和动组件是两种改动，前者会悄悄覆盖后者留下的值**。Day 6 设的 `alpha = 0` 就是这么丢的。

---

上一篇：[Day 7：用一个静态事件接住「敌人死了」](arpg-review-day7.html) ｜ 下一篇：[Day 9：八天功能复盘](arpg-day9-review.html)
