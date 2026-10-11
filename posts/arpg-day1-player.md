---
title: "ARPG 学习日志 Day 1：让一个骑士动起来"
date: 2026-10-11 20:30:00
tags: [Unity, 游戏开发, ARPG, 学习日志]
summary: "开新坑了——从零做一个 2D ARPG。第一天只解决一件事：让 Tiny Swords 里的蓝衣骑士能听键盘的话。42 行代码、藕合动画状态机，顺便记下我踩到的第一个坑。"
cover: images/arpg-day1-cover.svg
pinned: false
draft: false
---

## 为什么开这个坑

之前拆过两个 Unity 小项目（[楼梯](stairs-unity.html) 和 [小恐龙](dino-unity.html)），都是「读别人的代码写分析」。这次换个方向：**自己动手，从零搭一个 ARPG**，全程记录学习进度。

工程名很朴素，叫 `ARPGbegin`，用的美术素材是 [Tiny Swords](https://pixelfrog-assets.itch.io/tiny-swords)——一套很完整的像素风素材，有骑士、哥布林、地形、UI，够折腾很久。

> [!NOTE]
> 文章里的代码和数值都直接来自工程里正在跑的文件（`SampleScene.unity` + `PlayerMovement.cs`），不是伪代码。

---

## 今天的目标：人物能走

只做一件事：**让骑士响应 WASD / 方向键移动**，并且走路时播放走路动画、停下来播放待机动画。

听起来简单，但这里面藏着 2D 角色控制的三个核心问题：

1. 速度怎么给——直接改位置，还是用物理？
2. 朝哪个方向——左右翻转怎么做才不连物理一起翻？
3. 什么时候换动画——动画参数怎么算？

---

## 第一步：搭一个不会掉下去的骑士

我先在场景里创建角色，然后挂上这几个组件：

| 组件 | 作用 | 关键设置 |
|------|------|----------|
| **SpriteRenderer** | 显示像素图 | Sorting Order = **10**（要压在地面上） |
| **Rigidbody2D** | 参与物理 | Body Type = Dynamic，**Gravity Scale = 0**，Constraints = Freeze Rotation |
| **CapsuleCollider2D** | 碰撞体 | Size ≈ 0.40 × 0.53，Direction = Horizontal |
| **Animator** | 播放动画 | Controller = Player.controller |
| **PlayerMovement** | 我写的脚本 | — |

两个设置特别关键，一开始我没想明白为什么要这样：

**为什么 `GravityScale = 0`？**
ARPG 是俯视角（Top-Down），世界没有「下」的概念。如果留着重力，骑士会一直往下掉。所以干脆关掉重力，让角色的位置完全由代码控制——这也是俯视角和平台跳跃最本质的区别。

**为什么 `Constraints = Freeze Rotation`？**
俯视角角色移动时如果要转身，物理引擎可能会让刚体轻微旋转，看起来就歪了。锁定 Z 轴旋转是标准做法。

> [!TIP]
> 碰撞体我用了 **Capsule（胶囊）** 而不是 Box（矩形）。原因是俯视角角色在贴墙走的时候，胶囊的圆角不容易卡在瓦片缝隙里。这是个很小的选择，但手感差别很明显。

---

## 第二步：42 行代码搞定移动

完整脚本 `Assets/Scripe/PlayerMovement.cs`：

```csharp
using UnityEngine;

public class PlayerMovement : MonoBehaviour
{
    public float speed = 5f;
    public int facingDirection = 1;
    public Rigidbody2D rb;
    public Animator anim;

    void Start()
    {
        rb = GetComponent<Rigidbody2D>();
        anim = GetComponent<Animator>();
    }

    void FixedUpdate()
    {
        float horizontal = Input.GetAxis("Horizontal");
        float vertical = Input.GetAxis("Vertical");

        // 朝向与当前缩放不一致时翻转
        if (horizontal > 0 && transform.localScale.x < 0 ||
            horizontal < 0 && transform.localScale.x > 0)
        {
            Flip();
        }

        // 用绝对值喂动画：只关心「有没有在动」，不关心往哪动
        anim.SetFloat("horizontal", Mathf.Abs(horizontal));
        anim.SetFloat("vertical", Mathf.Abs(vertical));

        rb.velocity = new Vector2(horizontal, vertical) * speed;
    }

    void Flip()
    {
        facingDirection *= -1;
        transform.localScale = new Vector3(
            facingDirection, transform.localScale.y, transform.localScale.z);
    }
}
```

代码不长，但每一行都有讲究。

### 为什么物理写在 `FixedUpdate`？

`Update` 跟帧率走，`FixedUpdate` 跟固定时间步长（默认 0.02 秒）走。**所有跟 Rigidbody 打交道的代码都应该放 `FixedUpdate`**，否则在不同帧率的机器上，角色速度会不一样。

这也是我在[楼梯那篇](stairs-unity.html)里挑出的毛病（那个项目的 `CameraManager` 在 `FixedUpdate` 里用了 `Time.deltaTime`），所以这次一开始就写对了。

### 为什么用 `velocity` 而不是 `AddForce`？

```csharp
rb.velocity = new Vector2(horizontal, vertical) * speed;
```

这行是**直接赋值**速度，不是施加力。区别很大：

- `AddForce` 是「推」——速度会累积，松手后还有惯性，角色会滑一段
- `velocity =` 是「设定」——按下去就是 5 单位/秒，松开立刻为 0

对像素风 ARPG 来说，**要的就是这种干脆的手感**。老式 RPG 里角色都是说走就走、说停就停的。

### `Input.GetAxis` 帮我做了三件事

`Input.GetAxis("Horizontal")` 返回的是 `-1` 到 `1` 之间的浮点数，它自动处理了：

1. **多键映射**——A/左方向键都行
2. **平滑过渡**——检测到键盘输入时会有个短暂的加速曲线
3. **对角线归一化**——不会出现「斜着走比直着走快 1.41 倍」

第 3 点很重要。如果自己算 `Vector2(1, 1)`，长度是 1.414，斜着走就会比直走快。`GetAxis` 输出的已经是处理过的值。

> [!WARNING]
> `GetAxis` 的平滑其实对像素游戏**有点过于柔和**。如果想要更硬朗的复古手感，可以换成 `Input.GetAxisRaw("Horizontal")`——它直接返回 -1/0/1，没有过渡。我暂时保留 `GetAxis`，等后面加冲刺再一起调。

---

## 第三步：翻转的两个坑

### 坑一：翻转要翻 `transform`，不是 SpriteRenderer

```csharp
transform.localScale = new Vector3(facingDirection, y, z);
```

我一开始想的是 `spriteRenderer.flipX = true`。两种都能让图片左右镜像，但**翻转整个 `transform` 会连碰撞体一起翻**——这是好事，因为碰撞体跟着角色走才对称。

但这里有个隐患，后面会讲到。

### 坑二：不要每帧都翻转

```csharp
if (horizontal > 0 && transform.localScale.x < 0 ||
    horizontal < 0 && transform.localScale.x > 0)
{
    Flip();
}
```

这个判断的意思是：**「想往右走，但现在朝左」或者「想往左走，但现在朝右」**——只有这两种情况才翻转。

如果直接写成 `if (horizontal != 0) Flip();`，角色就会疯狂抽搐：每一帧都翻一次，`facingDirection` 在 1 和 -1 之间来回跳。

---

## 第四步：动画状态机

Animator Controller 里我建了两个状态：`idle` 和 `walk`，两个 float 参数：`horizontal` 和 `vertical`。

脚本喂参数时用了 `Mathf.Abs()`：

```csharp
anim.SetFloat("horizontal", Mathf.Abs(horizontal));
anim.SetFloat("vertical", Mathf.Abs(vertical));
```

**为什么取绝对值？** 因为动画只需要知道「有没有在动」——往左走和往右走都是走路动画，方向由 `localScale` 翻转解决。如果不取绝对值，参数会是负数，而状态机的条件写的是 `Greater 0.1`，负数值就永远触发不了。

状态机里的过渡条件大致是这样：

| 从 | 到 | 条件 |
|----|----|------|
| idle | walk | `horizontal > 0.1` |
| idle | walk | `vertical > 0.1` |
| walk | idle | `horizontal < 0.1` 且 `vertical < 0.1` |

> [!NOTE]
> `0.1` 这个阈值叫**死区**。因为 `GetAxis` 有平滑曲线，松开按键后数值不会立刻归零，而是缓慢衰减。如果没有死区，角色停下后动画还会断断续续播一会儿，看起来像在抽搐。

动画剪辑都是 60 采样率（`m_SampleRate: 60`），也就是按 60 FPS 逐帧绘制的手绘动画。

---

## 今天踩到的第一个坑

写完跑起来，角色能动能转向，看起来一切正常。但我盯着代码看了几秒，发现一个**现在没报错、以后一定出事**的地方：

```csharp
void Start()
{
    rb = GetComponent<Rigidbody2D>();
    anim = GetComponent<Animator>();
}
```

`rb` 和 `anim` 明明是 `public` 字段——**Inspector 里可以手动拖引用**。但这里又在 `Start()` 里用 `GetComponent` 覆盖了一遍。

这意味着：如果哪天我在 Inspector 里拖了个别的对象（比如把某个特效的 Animator 拖进来），`Start()` 一执行就被覆盖成自己的了，**Inspector 的设置形同虚设**。

正确做法二选一：

```csharp
// 方案 A：既然是 public，就信任 Inspector，别覆盖
void Start() { }   // 或者干脆删掉 rb/anim，改用私有字段

// 方案 B：既然是代码拿，就别 public（更推荐，避免误操作）
[SerializeField] private Rigidbody2D rb;
[SerializeField] private Animator anim;
```

我倾向方案 B——用 `[SerializeField] private` 既能在 Inspector 看到（方便调试），又不会被外部脚本乱改。

> [!TIP]
> 这个坑还有个更隐蔽的版本：`GetComponent` 写在 `Start()` 而不是 `Awake()`。如果别的脚本在 `Awake()` 里访问 `playerMovement.rb`，拿到的就是 `null`。**依赖注入的初始化要放 `Awake()`**。

---

## 另一个已经埋下的隐患

翻转用的是 `transform.localScale.x = -1`。这在现在没问题，但等后面加上**攻击、受伤、阴影**时会出事：

- 子物体（比如武器、影子）会跟着一起镜像，可能跑到角色另一边
- `localScale` 为负时，某些情况下碰撞检测的方向会反
- 动画里如果有位移曲线，负缩放会让位移方向反转

更稳的做法是**只翻 `SpriteRenderer.flipX`**，物理碰撞体保持不动（前提是碰撞体本身左右对称）。我暂时留着现在的写法，等遇到问题再改——正好可以记录「什么时候它真的会坏」。

---

## 今天的成果

- ✅ 场景里有了一个不掉、不歪、能响应键盘的骑士
- ✅ 走 / 停切换有动画，朝向能正确翻转
- ✅ 42 行代码，理解了 `FixedUpdate`、`velocity` 赋值、`GetAxis` 的平滑与归一化
- ✅ 记下 2 个待改点：`public` + `Start()` 覆盖引用的矛盾、`localScale` 翻转的隐患

**明天计划**：地图瓦片。这个工程的地形分了 7 层 Tilemap（`Ground` / `Collision-Low` / `Collision-High` / `Non-Collision-Low` / `Non-Collision-High` / `Rocks` / `MountainBoundary`），还有一套 「走进山体自动改变遮挡关系」的脚本——那部分很有意思，明天专门写。

---

## 数值速查

| 参数 | 值 | 位置 |
|------|-----|------|
| 移动速度 | `5` | PlayerMovement.speed |
| 初始朝向 | `1`（右） | PlayerMovement.facingDirection |
| 重力 | `0` | Rigidbody2D.gravityScale |
| 旋转约束 | Freeze Rotation | Rigidbody2D.constraints |
| 碰撞检测 | Continuous | Rigidbody2D.collisionDetection |
| 碰撞体尺寸 | 0.40 × 0.53 | CapsuleCollider2D.size |
| 角色 Sorting Order | `10` | SpriteRenderer |
| 相机 | 正交，Size `5` | Main Camera |
| 像素密度 | 100 PPU | Warrior_Blue.png 导入设置 |