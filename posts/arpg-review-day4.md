---
title: ARPG 功能复盘 Day 4：从「碰到才打」到「看见就追」
date: 2026-10-14 22:00:00
updated: 2026-10-20 12:00:00
tags: Unity, ARPG, 游戏开发, 复盘, AI, 状态机, 物理检测
summary: 用 OverlapCircleAll 把敌人的感知从「碰撞被动触发」换成「每帧主动查询」，再加攻击距离、冷却计时和第四个状态。这篇复盘讲清检测半径与攻击半径如何分工，也记下三个至今仍在的问题：每帧分配、hits[0] 不确定、以及场景里被改成 0 的攻击力。
cover: images/arpg-review-day4-cover.svg
pinned: false
draft: false
slug: arpg-review-day4
---

## 背景与目标

Day 3 的敌人只有一种伤害方式：撞上来。这带来两个体验问题——玩家站在攻击范围外可以无限安全，敌人也不会「注意到」你。

第四天的目标是把被动改主动，具体指标写进 Inspector：

| 参数 | 值 | 含义 |
|---|---|---|
| `playerDetectRange` | 5 | 5 格内算「发现玩家」 |
| `attackRange` | 2 | 2 格内可以出手 |
| `attackCooldown` | 2 | 两次攻击间隔 2 秒 |

## 实现要点

### 实现思路

在敌人身上挂一个 `DetectionPoint` 子物体作为感知中心，每帧做一次圆形查询：

```csharp
Collider2D[] hits = Physics2D.OverlapCircleAll(
    detectionPoint.position, playerDetectRange, playerLayer);

if (hits.Length > 0)
{
    player = hits[0].transform;
    // 在攻击距离内且冷却结束 → Attacking
    // 在攻击距离外且不在攻击中 → Chasing
}
else
{
    rb.velocity = Vector2.zero;
    ChangeState(EnemyState.Idle);
}
```

冷却独立于状态机：`attackCooldownTimer` 在 `Update` 里递减，进入攻击时重置。这样即使攻击被打断，计时也不会停。

伤害结算从碰撞搬到攻击点——`Enemy_Combat.Attack()` 用 `OverlapCircleAll(attackPoint.position, weaponRange, playerLayer)` 找玩家，和玩家的 `Player_Combat.DealDamage()` 是同一套写法。

### 关键技术点

- **LayerMask 优于 tag**：`playerLayer` 在查询阶段就把地面、装饰全部排除，不需要先取回再过滤。
- **攻击期间锁速度**：`if (enemyState == EnemyState.Attacking) rb.velocity = Vector3.zero;`，避免「边追边打」的滑步感。
- **冷却放在状态外**：状态是「此刻在做什么」，冷却是「多久没出手」，两个维度不该耦合。
- **`OnDrawGizmosSelected` 画黄圈**：把 5 格的检测范围可视化，调数值时不用盲猜。
- **伤害挂在动画事件上**：`Enemy_Combat.Attack()` 由攻击动画的关键帧调用，判定发生在挥击的那一帧，而不是进入状态的那一帧。

### 遇到的问题与解决

**1. 每帧分配数组**

`OverlapCircleAll` 每次调用都会返回一个新数组，5 个敌人 × 60 帧就是每秒 300 次分配，全靠 GC 兜底。正确写法是 `OverlapCircleNonAlloc` 配一个复用的缓冲区。这个问题当天没暴露——场景里只有 1 个敌人。

**2. `hits[0]` 不等于「最近的那个」**

玩家和别的东西同时进入检测圈时，谁排第一由物理引擎返回顺序决定，跟距离无关。追击目标应该是「最近的玩家」，或者至少做一次显式排序。

**3. 攻击力在场景里被改成了 0**

`Enemy_Combat.damage` 脚本默认值是 `1`，但场景里这个实例序列化成了 `damage: 0`。后果是：敌人会走到你面前、会播放攻击动画、`PlayerHealth.ChangeHealth(0)` 也会被调用——唯独血量不掉，`PlayerHealth` 里 `currentHealth <= 0` 的死亡分支从来没有被执行过。

这是 Day 8 做整体复盘时才翻出来的一条，属于「Inspector 覆盖脚本默认值」的典型陷阱：代码读起来完全正确，问题只存在于场景文件里。

**4. 两个 `Attack()` 并存**

`Enemy_Movement.Attack()` 至今还是个 `Debug.Log("Attack")` 的空壳，真正结算伤害的是 `Enemy_Combat.Attack()`。同名方法分属两个脚本，看代码的人很容易改错地方。

## 小结

主动感知的本质是把「物理事件」换成「主动查询」：从「碰撞引擎通知我」变成「我每帧问一次」。代价是每帧成本，收益是可控——可以随时知道目标在不在、有多远、能不能打。

冷却与状态的分离是这一天最值得留下的设计：**状态回答「在做什么」，计时回答「什么时候能做下一次」**，两者混在一起后，任何一次打断都会让节奏乱掉。

---

上一篇：[Day 3：虚拟相机与敌人的第一套状态机](arpg-review-day3.html) ｜ 下一篇：[Day 5：挥剑、掉血与击退眩晕](arpg-review-day5.html)
