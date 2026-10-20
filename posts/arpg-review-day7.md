---
title: ARPG 功能复盘 Day 7：用一个静态事件接住「敌人死了」
date: 2026-10-18 22:00:00
updated: 2026-10-20 12:00:00
tags: Unity, ARPG, 游戏开发, 复盘, 事件, 经验系统
summary: 击杀给经验看着简单，难点在「谁该知道敌人死了」。这一天没有让 Player_Combat 顺手加经验，而是在 Enemy_Health 上挂了一个静态事件，让经验系统自己去订阅。收益是发送方不认识接收方，代价是生命周期要自己管。
cover: images/arpg-review-day7-cover.svg
pinned: false
draft: false
slug: arpg-review-day7
---

## 背景与目标

到 Day 6，玩家的数值已经集中，但等级还只是一个不存在的概念。第七天要让「打怪」有长期回报：

- 敌人死亡时给出经验值
- 经验攒够就升级，升级曲线逐级变陡
- HUD 上有一条经验条和一个等级数字

关键约束不在功能，而在**依赖方向**：结算伤害的是玩家，销毁对象的是敌人，涨经验的是另一个系统。三者如果互相引用，会立刻缠成一团。

## 实现要点

### 实现思路

把「敌人死了」做成一次广播，而不是一次调用。

`Enemy_Health` 里加一个静态事件：

```csharp
public int expReward = 3;

public delegate void MonsterDefeated(int amount);
public static event MonsterDefeated OnMonsterDefeated;

public void ChangeHealth(int amount)
{
    currentHealth += amount;
    if (currentHealth > maxHealth) currentHealth = maxHealth;

    if (currentHealth <= 0)
    {
        OnMonsterDefeated(expReward);   // 先广播
        Destroy(gameObject);            // 再销毁
    }
}
```

`ExpManager` 只管订阅和消费：

```csharp
private void OnEnable()  => Enemy_Health.OnMonsterDefeated += GainExperience;
private void OnDisable() => Enemy_Health.OnMonsterDefeated -= GainExperience;

public void GainExperience(int amount)
{
    currentExp += amount;
    if (currentExp >= expToLevel) LevelUp();
    UpdateUI();
}

private void LevelUp()
{
    level++;
    currentExp -= expToLevel;
    expToLevel = Mathf.RoundToInt(expToLevel * expGrowthMultiplier);  // 1.2
}
```

顺序很重要：先广播再 `Destroy`。反过来的话，订阅者在回调里访问一个已销毁的对象。

### 关键技术点

- **静态事件 = 全局广播**：`Enemy_Health` 不需要知道 `ExpManager` 存在，新增一个「成就系统」也只要自己订阅。
- **订阅放在 `OnEnable` / `OnDisable`**：物体禁用或销毁时自动退订，避免「订阅者已经没了，事件还在调」。
- **成长曲线用乘数而不是加数**：`expToLevel` 从 10 开始按 1.2 倍递增，取整后是 **10 → 12 → 14 → 17**。乘数让后期需求指数级上涨，加数只会线性变难。
- **`Slider` 直接当进度条**：`maxValue` 设成 `expToLevel`、`value` 设成 `currentExp`，不需要自己算百分比。
- **`currentExp -= expToLevel` 而不是清零**：溢出部分带进下一级，体感更连续。

### 遇到的问题与解决

**1. 一次只升一级**

`LevelUp()` 用的是 `if`，不是 `while`。三只怪同时死亡、一次性给 9 点经验，如果一次跨两级，多出来的经验会被白白吞掉。正确写法是循环到 `currentExp < expToLevel` 为止。

**2. 静态事件的生命周期没人管**

`ExpManager` 自己用 `OnEnable` / `OnDisable` 做了订阅与退订，这一层是安全的。但静态事件本身是进程级的：编辑器关闭「Enter Play Mode 时重载域」后，上一次运行的订阅可能还挂在委托链上，表现就是「一杀怪加了两倍经验」。

**3. 调试键混进了正式输入**

`Update` 里留着一个 `KeyCode.Return` 加 2 点经验的测试入口。调试期很有用，上线前必须删——它和真正的输入映射混在同一个方法里，很容易忘。

**4. 升级了，但什么都没变**

`LevelUp()` 只改了 `level` 和 `expToLevel`，属性一个没动。等级目前是个纯展示数字，技能点什么的全是空的。这正是 Day 8 要去搭技能面板的原因。

## 小结

Day 7 是这套工程第一次用事件解耦。它解决的问题很具体：**发送方不该知道接收方是谁**。代价同样具体：静态事件是全局的，谁订阅、谁退订、什么时候退，全靠自觉。

一个经验系统的最小闭环其实只有四行：累加、判断、升级、刷 UI。真正花时间的是「谁通知谁」这件事——想清楚之后，代码量反而比预想的少。

---

上一篇：[Day 6：把数值收进单例，把面板做成时停](arpg-review-day6.html) ｜ 下一篇：[Day 8：0 行脚本的一天，搭出技能面板骨架](arpg-review-day8.html)
