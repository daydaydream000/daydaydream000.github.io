---
title: ARPG 技能树系统详解：从 ScriptableObject 到真正改游戏的完整链路
date: 2026-10-24 19:19:00
tags: Unity, ARPG, 游戏开发, 技能树, ScriptableObject, 事件, 架构, 系统设计
summary: 一篇单独拆给技能树的文章——不写新功能，把 SkillSO / SkillSlot / SkillTreeManager / SkillManager / ToggleSkillTree 五个脚本的关系、一个格子从点击到生效的完整链路、三条数据流，以及当前还差什么（含对 Day10「升级没真给点数」的更正）一次讲透。
cover: images/arpg-skilltree-cover.svg
pinned: false
draft: false
slug: arpg-skilltree-deep-dive
---

## 一句话说清这篇在讲什么

前面 Day 8–11 断断续续碰过技能树，但都是夹在「当天功能」里顺手写的。这篇把它单独拎出来，把 **5 个脚本怎么分工、一个格子从「点击」到「真正改游戏」走完哪几步、三条数据流怎么走**，以及**当前还差什么**一次讲透。所有代码都来自 `Assets/Scripe/SkillTree/` 和 `ExpManager.cs` 的当前真实版本。

## 先说结论

当前技能树 = **「一个数据资产（SkillSO）+ 24 个格子（SkillSlot）+ 一个总调度（SkillTreeManager）+ 一个生效器（SkillManager）+ 一个面板开关（ToggleSkillTree）」**，靠 **两个静态事件（`OnAbilityPointSpent` / `OnSkillMaxed`）+ 一个单例（`StatsManger.Instance`）** 串起来。

它的好：技能是**数据资产**，加技能 = 新建 SO + 拖进格子，不用改代码；格子和「生效逻辑」**互不知道对方**，靠事件解耦。它的弱：这棵「树」目前是**扁平 24 格**——前置关系（`prerequisiteSkillSlots`）还是空的，所以「树」还没长出来；外加几个已知的脆点（满级卡 4/5、`combat` 漏拖、命名误导、点数硬编码）。

## 一、五个脚本怎么分工

| 脚本 | 角色 | 关键成员 | 一句话 |
|---|---|---|---|
| `SkillSO` | 数据资产 | `skillName` / `maxLevel` / `skillIcon` | 描述「一个技能是什么」，纯数据 |
| `SkillSlot` | 格子 | `skillSO` / `currentLevel` / `isUnlocked` / 两个静态事件 | 一个格子的一生：升级、解锁、刷新 UI |
| `SkillTreeManager` | 总调度 | `skillSlots[24]` / `availablePoints` | 把按钮点击接到升级、扣点、连锁解锁、接收升级加点 |
| `SkillManager` | 生效器 | `combat` | 订阅事件，把「点了技能」翻译成「改数值 / 开战斗」 |
| `ToggleSkillTree` | 面板开关 | `statsCanvas`(实际是技能面板) | 开关面板 + `timeScale` 暂停 |

<figure class="post-figure"><img src="images/arpg-skilltree-cover.svg" alt="技能树五个脚本分工" loading="lazy" decoding="async"><figcaption>五个脚本各管一摊：数据 / 格子 / 调度 / 生效 / 面板</figcaption></figure>

## 二、SkillSO：技能是「数据资产」，不是代码

```csharp
[CreateAssetMenu(fileName = "NewSkill", menuName = "SkillTree/Skill")]
public class SkillSO : ScriptableObject
{
    public string skillName;
    public int maxLevel;
    public Sprite skillIcon;
}
```

就三个字段，干净。值得注意两点：

1. **前置关系不在 SO 里**。`SkillSO` 只描述技能自己；「谁是谁的前置」写在场景里 `SkillSlot` 的 `prerequisiteSkillSlots` 列表上。也就是说，这棵「树」目前是**场景里拼出来的**，不是数据驱动的——这直接导致下面会说到的「树还没长出来」问题。
2. **加技能零代码**：右键 `SkillTree/Skill` 新建一个 SO、填名字 / 满级 / 图标，再拖进某个格子即可。这是 SO 与逻辑分离带来的最大便利。

## 三、SkillSlot：一个格子的完整一生

```csharp
public class SkillSlot : MonoBehaviour
{
    public List<SkillSlot> prerequisiteSkillSlots;   // 前置格子（当前为空）
    public SkillSO skillSO;
    public int currentLevel;
    public bool isUnlocked;
    public Image skillIcon;
    public TMP_Text skillLevelText;
    public Button skillButton;

    public static event Action<SkillSlot> OnAbilityPointSpent;
    public static event Action<SkillSlot> OnSkillMaxed;

    public void TryUpgradeSkill()
    {
        if (isUnlocked && currentLevel < skillSO.maxLevel)
        {
            currentLevel++;
            OnAbilityPointSpent?.Invoke(this);          // ① 广播：扣点 + 生效
            if (currentLevel >= skillSO.maxLevel)
            {
                OnSkillMaxed?.Invoke(this);             // ② 若满级，广播连锁解锁
            }
            UpdateUI();                                 // ③ 最后才刷新自己
        }
    }

    public bool CanUnlockSkill()
    {
        foreach (SkillSlot slot in prerequisiteSkillSlots)
            if (!slot.isUnlocked || slot.currentLevel < slot.skillSO.maxLevel)
                return false;
        return true;
    }

    public void Unlock() { isUnlocked = true; UpdateUI(); }

    private void UpdateUI()
    {
        skillIcon.sprite = skillSO.skillIcon;           // ← 空格子（skillSO==null）这里会 NRE
        if (isUnlocked) { /* 按钮可点、显示 x/max、图标白 */ }
        else           { /* 按钮不可点、显示 Locked、图标灰 */ }
    }
}
```

**一个格子从点击到刷新，顺序是关键**：`currentLevel++` → `OnAbilityPointSpent`（扣点 + 让技能生效）→ 若满级 `OnSkillMaxed`（连锁解锁别的格子）→ **最后才 `UpdateUI()`**。

> [!WARNING]
> `UpdateUI()` 排在所有事件广播**之后**。这意味着：只要①或②里任何一个订阅者抛异常，`UpdateUI()` 就不会执行——你刚点的格子 UI 停在旧状态。这正是 Day 9 那个「满级卡 4/5」的根因：满级时 `OnSkillMaxed` 触发 `HandleSkillMaxed` 遍历 24 格，撞上 `skillSO==null` 的空格子，`UpdateUI()` 里的 `skillIcon.sprite = skillSO.skillIcon` 抛 NRE，异常冒泡把当前格子本该执行的最后一步 `UpdateUI()` 一起吞了。

## 四、SkillTreeManager：把点击接到升级的总指挥

```csharp
public class SkillTreeManager : MonoBehaviour
{
    public SkillSlot[] skillSlots;          // 24 格
    public TMP_Text pointsText;
    public int availablePoints;             // 初始值在 Inspector 硬编码

    private void OnEnable()
    {
        SkillSlot.OnAbilityPointSpent += HandleAbilityPointsSpent;
        SkillSlot.OnSkillMaxed       += HandleSkillMaxed;
        ExpManager.OnLevelUp         += UpdateAbilityPoints;   // 升级事件 → 加点
    }
    private void OnDisable()
    {
        SkillSlot.OnAbilityPointSpent -= HandleAbilityPointsSpent;
        SkillSlot.OnSkillMaxed       -= HandleSkillMaxed;
        ExpManager.OnLevelUp         -= UpdateAbilityPoints;   // 成对退订 ✓
    }

    private void Start()
    {
        foreach (SkillSlot slot in skillSlots)
            slot.skillButton.onClick.AddListener(() => CheckAvailablePoints(slot));
        UpdateAbilityPoints(0);             // 刷新点数文本
    }

    private void CheckAvailablePoints(SkillSlot slot)
    {
        if (availablePoints > 0) slot.TryUpgradeSkill();      // 真正的「有没有点」闸门
    }

    private void HandleAbilityPointsSpent(SkillSlot _)
    {
        if (availablePoints > 0) UpdateAbilityPoints(-1);     // 扣 1 点
    }

    private void HandleSkillMaxed(SkillSlot _)
    {
        foreach (SkillSlot slot in skillSlots)
            if (!slot.isUnlocked && slot.CanUnlockSkill())
                slot.Unlock();                                // 连锁解锁满足条件的格子
    }

    public void UpdateAbilityPoints(int amount)
    {
        availablePoints += amount;
        pointsText.text = "Points: " + availablePoints;
    }
}
```

几个要点：

- **闸门在 `CheckAvailablePoints`**：点击按钮先查 `availablePoints>0` 才允许升级，扣点则在事件 `HandleAbilityPointsSpent` 里做——升级动作和扣点是**解耦**的（格子不知道点数，调度器负责记账）。
- **连锁解锁**：满级时遍历全部 24 格，对「未解锁且前置满足」的格子调用 `Unlock()`。但如第三节所说，这个遍历对 `skillSO==null` 的格子会 NRE（因为 `CanUnlockSkill` 对空前置列表直接返回 `true`，锁不住）。
- **事件订阅成对**：`OnEnable` 加、`OnDisable` 减，三对都在——这是 Day 8 踩过 `OnDisable` 写成 `+=` 之后修回来的纪律，要守住。

## 五、SkillManager：让技能「真正生效」

格子只管「升级 + 广播」，至于「升级后游戏里发生什么」，交给 `SkillManager` 这个订阅者：

```csharp
public class SkillManager : MonoBehaviour
{
    public Player_Combat combat;            // Day 11 已改为 private + 自动取

    private void OnEnable()  { SkillSlot.OnAbilityPointSpent += HandleAbilityPointSpent; }
    private void OnDisable() { SkillSlot.OnAbilityPointSpent -= HandleAbilityPointSpent; }

    private void HandleAbilityPointSpent(SkillSlot slot)
    {
        string skillName = slot.skillSO.skillName;
        switch (skillName)
        {
            case "Max Health Boost":
                StatsManger.Instance.UpdateMaxHealth(1);   // 改单例数值
                break;
            case "Sword Slash":
                combat.enabled = true;                     // 开战斗
                break;
            default:
                Debug.LogWarning("Error" + skillName);
        }
    }
}
```

这里就是「事件解耦」的价值：格子完全不知道 `StatsManger` 和 `combat` 的存在，它只喊一声「我花了点 / 我满了」，谁爱听谁听。`SkillManager` 按 `skillName` 把抽象事件翻译成具体游戏效果。当前只接了两种技能，扩技能 = 在 `switch` 里加 `case`。

## 六、ToggleSkillTree：开关面板 + 暂停

```csharp
public class ToggleSkillTree : MonoBehaviour
{
    public CanvasGroup statsCanvas;     // 命名误导：实际控的是「技能面板」
    private bool skillTreeOpen = false;

    void Update()
    {
        if (Input.GetButtonDown("ToggleSkillTree"))
        {
            if (skillTreeOpen) { Time.timeScale = 1;  statsCanvas.alpha = 0; statsCanvas.blocksRaycasts = false; }
            else               { Time.timeScale = 0;  statsCanvas.alpha = 1; statsCanvas.blocksRaycasts = true;  }
            skillTreeOpen = !skillTreeOpen;
        }
    }
}
```

开门时 `Time.timeScale = 0` 冻结世界、用 `CanvasGroup` 淡入面板并开启射线；关门相反。一个值得改的小问题：变量叫 `statsCanvas` 却控技能面板，纯命名误导（Day 10 已记）。

## 七、三条数据流全景

<figure class="post-figure"><img src="images/arpg-skilltree-flow.svg" alt="技能树三条数据流" loading="lazy" decoding="async"><figcaption>流 A 升级给点（事件）· 流 B 点格升级→扣点→生效→连锁（事件+点击）· 流 C 面板开关</figcaption></figure>

- **流 A · 升级给点（事件驱动）**：敌人死亡 `OnMonsterDefeated` → `ExpManager.GainExperience` → `LevelUp` → `OnLevelUp(1)` → `SkillTreeManager.UpdateAbilityPoints(+1)` → `availablePoints` +1。
- **流 B · 点格升级→扣点→生效→连锁**：点击 `skillButton` → `CheckAvailablePoints`（有點才放行）→ `TryUpgradeSkill`（`currentLevel++` → `OnAbilityPointSpent` 扣点 + `SkillManager` 改游戏 → 满级则 `OnSkillMaxed` 连锁解锁 → 最后 `UpdateUI`）。
- **流 C · 面板开关**：`ToggleSkillTree` 输入 → `timeScale` 0/1 + `CanvasGroup` 显隐。

> [!NOTE]
> **更正 Day 10 的一个误记**：Day 10 把「升级没真给点数」列进了脆弱点，但顺着当前真实代码看，`SkillTreeManager` 在 `OnEnable` 里订阅了 `ExpManager.OnLevelUp += UpdateAbilityPoints`，而 `LevelUp()` 会 `OnLevelUp?.Invoke(1)` → `availablePoints += 1`。**升级确实会给点（每级 +1），事件链是接通的**。真正剩下的不是「没给」，而是：初始 `availablePoints` 在 Inspector 硬编码、且每级只 +1 偏慢。

## 八、当前还差什么（让扁平 24 格长成真正的「树」）

| 问题 | 现状 | 怎么补 |
|---|---|---|
| 满级卡 4/5 | `UpdateUI()` 排最后，上游异常被吞；`HandleSkillMaxed` 撞 `skillSO==null` 空格子 NRE | `UpdateUI` 对 `skillSO` 判空；`HandleSkillMaxed`/`CanUnlockSkill` 跳过 null 格子；或把 `UpdateUI()` 移到事件广播**之前** |
| `combat` 漏拖 | `SkillManager.combat` 靠 Inspector | Day 11 已用 `RequireComponent` + `Awake` 自取焊死 |
| 前置关系没配 | `prerequisiteSkillSlots` 全空 → 24 格同时可解锁，「树」没长出来 | 在场景里给每个格子配前置；或把前置搬进 `SkillSO` 做成数据驱动 |
| 命名误导 | `ToggleSkillTree.statsCanvas` 实际控技能面板 | 改名为 `skillTreeCanvas` |
| 点数硬编码 | 初始 `availablePoints` 写死、每级只 +1 | 改为「每级给 N 点」的配置项，初始 0 靠升级攒 |

**设计可取之处（值得延续）**：① SO 与逻辑分离，加技能零代码；② 格子与生效逻辑靠静态事件解耦，互不认识；③ `StatsManger.Instance` 作统一数值真相源；④ 事件订阅成对退订的纪律已建立。

## 一句话总结

技能树由 `SkillSO`（数据资产）/ `SkillSlot`（24 个格子，含 `OnAbilityPointSpent`、`OnSkillMaxed` 两个静态事件）/ `SkillTreeManager`（总调度：接线、扣点、连锁解锁、接收升级加点）/ `SkillManager`（按 `skillName` 把事件翻译成改数值或开战斗）/ `ToggleSkillTree`（开关 + `timeScale` 暂停）五个脚本组成，靠事件 + 单例串成「点击→升级→广播→生效→连锁」的完整链路；它好在 SO 与逻辑分离、事件解耦、数值单例化，弱在仍是扁平 24 格——前置关系没配、「树」没长出来，外加满级卡 4/5、`combat` 漏拖、命名误导、点数硬编码几个脆点（其中「升级给点」实际已通过 `OnLevelUp→UpdateAbilityPoints(+1)` 接通，Day10 的「没给点数」是误记）；下一步是把前置关系数据化、让 `availablePoints` 配置化，并焊死 `HandleSkillMaxed` 的 null 判断。
