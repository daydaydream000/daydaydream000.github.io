---
title: ARPG 学习日志 Day 3：虚拟相机与敌人的初级 AI
date: 2026-10-13 23:59:00
tags: Unity, ARPG, 游戏开发, Cinemachine, 状态机, 源码分析
summary: 拆解 ARPGbegin 的 Cinemachine 虚拟相机系统（Follow + Confiner + DeadZone），以及 Enemy_Movement 实现的 Idle/Chasing 状态机，两个代码里的 bug 也在文末。
cover: images/arpg-day3-cover.svg
pinned: false
draft: false
slug: arpg-day3-camera-enemy
---

## 一句话说清这天的内容

用 Cinemachine 让相机平滑跟随玩家移动、加一个边界限制；写一个 Torch 敌人的巡逻/追击状态机，进来就追、走了就停。

---

## 场景里的相机结构

之前 Day 2 讲 Tilemap 时跳过了相机部分。这次从场景文件里还原出完整的相机层级：

```
==CAMERAS==                    （空物体，仅作目录）
└── Main Camera                 fileID 519420028
    └── CinemachineBrain
        m_DefaultBlend: Style=1(EaseInOut)  Time=2s
└── Virtual Camera              fileID 6637214
    ├── Virtual Camera Core
    │   m_Follow: Player (fileID 391093246)
    │   m_Lens: OrthographicSize=3.5
    │   m_Transitions: m_DefaultBlend=EaseInOut 2s
    └── cm                           fileID 1190508284
        ├── CinemachineFramingTransposer
        │   m_ScreenX=0.5  m_ScreenY=0.5   （居中）
        │   m_DeadZoneWidth=0.8  m_DeadZoneHeight=0.8
        │   m_DampingX=0.5  m_DampingY=0.5
        ├── CinemachineConfiner2D
        │   m_ConfineMode=0
        │   m_BoundingShape2D: PolygonCollider2D (fileID 137846008)
        └── CinemachineTransposer
            （第二层 Transposer，绑定在 cm 上）
```

Main Camera 本身 orthographic size 也是 3.5，保证了两层相机的一致。虚拟相机 Priority=10，高于默认值，所以 CinemachineBrain 会把输出权交给它。

---

## Cinemachine 虚拟相机的三个组成部分

### 1. 跟随目标（Follow）

```
m_Follow: Player
```

虚拟相机告诉 Cinemachine：「我要跟谁」。设置了 Follow 之后，Transposer 组件才有用武之地——它负责「跟随目标移动后，相机要放在哪里」。

### 2. 阻尼（Damping）

```
m_DampingX=0.5   m_DampingY=0.5
```

没有阻尼的话，相机和玩家是完全同步的——玩家停，相机立刻停。有阻尼的情况下，相机像连着一根橡皮筋，会「追」着玩家移动，追的过程中平滑减速。0.5 这个值偏大，实际效果是相机会稍微慢半拍，对于俯视角 RPG 来说手感还算舒适，但对于快速横版游戏可能需要调低。

### 3. 边界限制（Confiner）

```csharp
// m_BoundingShape2D 引用了一个 PolygonCollider2D
PolygonCollider2D fileID 137846008
```

`CinemachineConfiner2D` 把一个 2D 多边形碰撞体作为边界——玩家移动到边界附近时，相机不会再往外推。实际场景里这个 PolygonCollider 大概覆盖了地图的可视区域，防止玩家走到瓦片边缘时看到空白。

**问题**：PolygonCollider 是静态的（Scene 文件里的固定值），如果地图有动态边界（比如门打开后玩家可以走到新区域），这套 Confiner 就需要配合 `m_ConfineMode` 的动态切换，或者在运行时替换 BoundingShape2D。

---

## 敌人的初级 AI：Idle / Chasing 状态机

### 场景里的敌人实体

```
Enemy_Torch  position (-0.16, 3.48)
├── Enemy_Movement     speed=5
├── Enemy_Combat       damage=0    ← 注意是 0！
├── Animator           Enemy.controller
├── Rigidbody2D        Dynamic  gravity=0  constraints=Rz
├── CapsuleCollider2D   （物理碰撞体）
└── CircleCollider2D   IsTrigger=true  radius=1.44  ← 追击检测区
```

CircleCollider2D 是关键——它是一个触发器，半径 1.44 单位，包裹着敌人。当玩家走进这个圆的范围，触发器产生 `OnTriggerEnter2D`，敌人进入 Chasing 状态；玩家走出范围，产生 `OnTriggerExit2D`，敌人回到 Idle。

### 状态枚举与切换

```csharp
public enum EnemyState { Idle, Chasing }

private void OnTriggerEnter2D(Collider2D collision) {
    if (collision.gameObject.tag == "Player") {
        if (player == null) {
            player = collision.gameObject.transform;
        }
        ChangeState(EnemyState.Chasing);
    }
}

private void OnTriggerExit2D(Collider2D collision) {
    if (collision.gameObject.tag == "Player") {
        rb.velocity = Vector2.zero;     // 停下
        ChangeState(EnemyState.Idle);
    }
}
```

**一个细节**：`if (player == null)` 这个判断只出现在 `OnTriggerEnter2D` 里，`OnTriggerExit2D` 里没有。这意味着一旦 `player` 被赋值过一次，它就永远不会变成 null——即使玩家后来被销毁（HP 归零后 `SetActive(false)`），敌人依然记得最后看到的位置。这个设计对「追到目标消失的地方然后发呆」的行为来说恰好是对的，但如果以后要做「玩家死亡→重生」机制，这里需要加 null 检查。

### 追击逻辑（Update）

```csharp
void Update() {
    if (enemyState == EnemyState.Chasing) {
        if (player.position.x > transform.position.x && facingDirection == -1 ||
            player.position.x < transform.position.x && facingDirection == 1) {
            Flip();
        }
        Vector2 direction = (player.position - transform.position).normalized;
        rb.velocity = direction;     // ← 未乘 speed！
    }
}
```

**这里有个 bug**：`rb.velocity = direction` 没有乘以 `speed`！`direction` 是单位向量（长度 1），所以敌人的实际移动速度是 1 单位/秒，而 Inspector 里填的 `speed=5` 永远不会被用上。

正确写法应该是：
```csharp
rb.velocity = direction * speed;
```

或者把 `direction` 改名叫 `normalizedVelocity`，让 bug 更容易被发现。

### 翻转逻辑

```csharp
void Flip() {
    facingDirection *= -1;
    transform.localScale = new Vector3(
        transform.localScale.x * -1,
        transform.localScale.y,
        transform.localScale.z
    );
}
```

和 Day 1 玩家脚本里的 `Flip()` 结构几乎一模一样，唯一的区别是初始朝向：`PlayerMovement` 的 `facingDirection` 初始是 `1`（朝右），`Enemy_Movement` 初始是 `-1`（朝左）。

### ChangeState 方法

```csharp
void ChangeState(EnemyState newState) {
    // 先关闭上一个状态的动画
    if (enemyState == EnemyState.Idle) {
        anim.SetBool("isIdle", false);
    } else if (enemyState == EnemyState.Chasing) {
        anim.SetBool("isChasing", false);
    }

    enemyState = newState;

    // 再开启新状态的动画
    if (enemyState == EnemyState.Chasing) {
        anim.SetBool("isChasing", true);
    } else if (enemyState == EnemyState.Idle) {
        anim.SetBool("isIdle", true);
    }
}
```

这段代码的逻辑是正确的，但写法有优化空间：先判断旧状态关闭动画，再统一设置新状态——这个模式容易在新增状态时漏掉一边的关闭逻辑。如果改成枚举驱动的字典映射，会更易维护：

```csharp
anim.SetBool("isIdle",   newState == EnemyState.Idle);
anim.SetBool("isChasing", newState == EnemyState.Chasing);
```

两条赋值，无论状态如何变化都不会漏。

---

## Enemy.controller 动画状态机

```
              Entry
                │
                ▼  (isChasing=true)
         ┌──────────────┐
         │   Sub SM     │
         │  ┌───────┐   │
         │  │ Idle  │───┼── isIdle=false ──► Exit
         │  └───────┘   │
         │      ▲       │
         │ isChasing=true│
         └──────┼───────┘
                │  (isChasing=true)
                ▼
         ┌──────────────┐
         │     Run      │──── isChasing=false ──► Exit ─► Sub SM ──► Idle
         └──────────────┘
```

状态机有两个层级：
- 外层：`Sub State Machine`（子状态机）包含了 Idle 状态
- 内层：`Run` 状态

Entry Transition（从 AnyState 到 Run）条件是 `isChasing=true`，没有 Exit Time，切换立即发生。Idle → Exit 的条件是 `isIdle=false`（即 `isIdle` 从 true 变成 false）。

还有一个多余的 `Original` 状态（fileID -5673407816275442753），美术动画文件存在，但没有被任何 Transition 引用——可能是调试时留下的，忘记删掉。

---

## Enemy_Combat：碰撞扣血

```csharp
public class Enemy_Combat : MonoBehaviour {
    public int damage = 1;     // Inspector 里实际填的是 0！

    private void OnCollisionEnter2D(Collision2D collision) {
        if (collision.gameObject.tag == "Player") {
            collision.gameObject.GetComponent<PlayerHealth>().ChangeHealth(-damage);
        }
    }
}
```

用 `OnCollisionEnter2D` 而不是 `OnTriggerEnter2D`，意味着碰撞体必须是**实心的**（IsTrigger=false）。场景里 Enemy_Torch 的 CapsuleCollider2D 没有设置 IsTrigger，所以这是正确的。

**注意**：`damage` 在 Inspector 里填的是 `0`——敌人现在实际上不会对玩家造成任何伤害。这可能是调试阶段故意设成 0，也可能是忘记改成 1。

---

## PlayerHealth：HP 显示与扣血

```csharp
public class PlayerHealth : MonoBehaviour {
    public int currentHealth;
    public int maxHealth;
    public TMP_Text healthText;
    public Animator healthTextAnim;

    private void Start() {
        healthText.text = "HP: " + currentHealth + '/' + maxHealth;
    }

    public void ChangeHealth(int amount) {
        currentHealth += amount;
        healthTextAnim.Play("TextUpdate");       // 播放抖动动画
        healthText.text = "HP: " + currentHealth + '/' + maxHealth;
        if (currentHealth <= 0) {
            gameObject.SetActive(false);          // 玩家消失（不是死亡动画）
        }
    }
}
```

`TextUpdate` 动画定义在 `HP Text.controller` 里，是一个从任意状态（无 Exit Time 限制）进入的过渡到 Idle 的动画，大概是文字缩放或抖动的效果，用来提示 HP 发生了变化。

`currentHealth` 和 `maxHealth` 是 public 字段，没有 `[SerializeField]`，这意味着它们会暴露在 Inspector 里。如果两个值都填 0，或者 `currentHealth > maxHealth` 初始值不合理，`Start()` 里的文本显示就会是负数或逻辑错误。

---

## 待改进的地方

### 会影响玩法的

1. **Enemy_Movement 追击速度 bug**：`rb.velocity = direction` 没有乘 `speed`，敌人永远以 1 单位/秒移动
2. **Enemy_Combat.damage = 0**：Inspector 里填了 0，玩家现在不会被扣血
3. **HP 初始值不校验**：`currentHealth` 和 `maxHealth` 没有任何范围检查

### 结构性问题

4. **`player` 字段永不重置**：玩家 `SetActive(false)` 后 `player` 依然非 null，后续需要加 null 检查
5. **ChangeState 写法扩展性差**：新增状态时容易漏掉旧状态的「关闭」逻辑
6. **Enemy.controller 有多余状态**：`Original` 状态从未被触发，美术文件浪费
7. **`Unity.VisualScripting` using 被 PlayerMovement 引入**（Day 1 记录过），但 Enemy 系列脚本已修正——只引入了必要的 `using`

---

## 小结

这天的核心是两个子系统的组合：

**相机**由 Cinemachine 管理，用了虚拟相机 + Transposer（跟随 + 阻尼）+ Confiner（边界限制）三层。开发者不需要写一行相机代码，只要配置参数就能得到平滑跟随的效果。三个组件各司其职：Follow 告诉相机跟谁，Transposer 决定相机相对目标的位置，Confiner 限制相机的移动范围。

**敌人 AI**是一个简单的状态机，两个状态（Idle / Chasing）、一个检测区（CircleCollider2D 触发器）。代码行数少（88+16+25），但已经覆盖了「感知→决策→移动→动画」的基本流程。最大的问题是追击速度 bug 和 damage=0，两个都是 Inspector 填数值的疏忽，比逻辑错误更难发现。
