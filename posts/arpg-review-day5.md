---
title: ARPG 功能复盘 Day 5：挥剑、掉血与击退眩晕
date: 2026-10-15 22:00:00
updated: 2026-10-20 12:00:00
tags: Unity, ARPG, 游戏开发, 复盘, 战斗, 协程
summary: 玩家第一次能主动出手。伤害结算挂在动画事件上，命中后同时改血量、给反方向速度、进眩晕协程；玩家自己挨打也走同一套。这篇复盘拆开「动画事件 + 协程 + 单标志门控」这套最小战斗骨架，以及它只结算第一个目标、协程可重入这两个洞。
cover: images/arpg-review-day5-cover.svg
pinned: false
draft: false
slug: arpg-review-day5
---

## 背景与目标

到 Day 4 为止，战斗是单向的：敌人能打你，你只能跑。第五天补齐另一半——玩家挥剑能打到敌人，敌人被打会掉血、后退、短暂眩晕。

三条验收标准：

- 按攻击键播放挥剑动画，动画播到「剑挥出」的那一帧才结算伤害
- 被打的敌人血量减少，并朝反方向弹开
- 击退期间双方都不受操作干扰

## 实现要点

### 实现思路

四个脚本分工，是一条单向链路：

```
输入 → Player_Combat（判定 + 冷却）
         ├─→ Enemy_Health（扣血、死亡销毁）
         └─→ Enemy_Knockback（位移 + 眩晕）
```

被打的一方同样要动：`PlayerHealth` 扣血刷 UI，`PlayerMovement.Knockback` 负责玩家自己的击退与硬直。

### 关键技术点

**1. 伤害结算挂在动画事件上**

`Attack()` 只负责开门：播动画、把冷却重置。真正的判定在动画事件回调里：

```csharp
public void Attack()
{
    if (timer <= 0)
    {
        anim.SetBool("isAttacking", true);
        timer = cooldown;   // 2 秒
    }
}

public void DealDamage()   // 动画事件
{
    Collider2D[] enemies = Physics2D.OverlapCircleAll(
        attackPoint.position, StatsManger.Instance.weaponRange, enemyLayer);

    if (enemies.Length > 0)
    {
        enemies[0].GetComponent<Enemy_Health>()
            .ChangeHealth(-StatsManger.Instance.damage);
        enemies[0].GetComponent<Enemy_Knockback>().Knockback(
            transform,
            StatsManger.Instance.knockbackForce,
            StatsManger.Instance.knockbackTime,
            StatsManger.Instance.stunTime);
    }
}

public void FinishAttacking()   // 动画事件
{
    anim.SetBool("isAttacking", false);
}
```

好处很直接：手感由动画决定，代码不需要知道「第 0.2 秒」。改动画不改代码。

**2. 击退 = 反向速度 + 协程计时**

```csharp
public void Knockback(Transform enemy, float force, float stunTime)
{
    isKnockack = true;
    Vector2 direction = (transform.position - enemy.position).normalized;
    rb.velocity = direction * force;
    StartCoroutine(KnockbackCounter(stunTime));
}
```

`direction` 用「自己减攻击者」而不是「攻击者减自己」，一个减号决定往哪边弹。敌人侧是同一套，只是多了 `ChangeState(EnemyState.knockback)`。

**3. `isKnockack` 单标志门控**

`FixedUpdate` 里先判断这个标志：

```csharp
if (isKnockack == false)
{
    // 正常读输入、写速度
}
```

没有它，玩家被击退的同一帧松开方向键，`rb.velocity` 会立刻被输入覆盖成 0，击退就「看不见」了。

**4. 眩晕用两段协程**

敌人侧把位移和硬直拆成两段：`knockbackTime` 后速度清零，再等 `stunTime` 才恢复状态。玩家侧则是单一时长。

**5. 攻击范围可视化**

`OnDrawGizmosSelected` 画红圈，和 `attackPoint` 一起调，避免「看着打到了其实没打到」。

### 遇到的问题与解决

**1. 范围里有三个敌人，只掉一个**

`enemies[0]` 只处理数组第一个。想要「一刀多杀」或「至少打最近的」，必须遍历并逐个结算。这是当天最明显的一处偷懒。

**2. 击退协程可以叠加**

`Enemy_Knockback.Knockback()` 没有重入保护。连续挨两刀会启动两个 `StunTimer`，先结束的那个把速度清零，后一个还在等——表现为「第二刀的击退半路消失」。

**3. 眩晕结束直接回 Idle**

`StunTimer` 最后一行是 `ChangeState(EnemyState.Idle)`，不回「被击退之前」的状态。敌人本来在追你，挨一下之后就站着不动了，得等下一次检测才重新进入 Chasing。

**4. `PlayerMovement` 从 42 行长到 65 行**

移动、翻转、击退、协程、以及攻击输入全挤在一个类里。类名叫 Movement，做的事已经超出 Movement。

## 小结

最小可用的战斗骨架由三样东西组成：**动画事件决定「什么时候结算」，协程决定「持续多久」，单标志决定「这期间听不听输入」**。三者都不依赖具体数值，调手感只要改 Inspector。

代价在边界情况：只结算第一个目标、协程可重入、状态复位粗暴。这三条在单敌场景下几乎无感，一旦同屏出现两个敌人就会立刻暴露——这也是第 9 天把它们列进优化清单的原因。

---

上一篇：[Day 4：从「碰到才打」到「看见就追」](arpg-review-day4.html) ｜ 下一篇：[Day 6：把数值收进单例，把面板做成时停](arpg-review-day6.html)
