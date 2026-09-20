---
title: "通用节点与回主页枢纽"
order: 3
icon: "ri:home-4-fill"
---

# 通用节点与回主页枢纽

`resource/base/pipeline/common.json` 存放跨任务复用的通用节点。MaaFramework 会把 `pipeline/` 目录下所有 JSON 合并进同一命名空间，因此各任务文件直接按节点名引用即可，无需任何导入声明。

## 节点清单

| 节点                       | 类型          | 作用                                                                                                                      |
| -------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `Common.EnsureHome`        | DirectHit     | 回主页枢纽：依次处理已知浮层/子页，直到命中全局主页标记                                                                   |
| `Common.CheckHomePage`     | TemplateMatch | 全局主页标记（`main_option.png`，阈值 0.75）。叶子节点，是枢纽的收敛出口                                                  |
| `Common.ClickHomeButton`   | TemplateMatch | 点击顶部主页按钮（`return_main.png`）                                                                                     |
| `Common.PressBackToHome`   | DirectHit     | **有意保留的 DirectHit 回退例外**：排在 `Common.CheckHomePage` 之后、枢纽 `next` 末位；嵌套 `next` 每次按键后重新判定主页 |
| `Common.CheckItemObtained` | TemplateMatch | 全屏「获得物品」弹窗（定义在 `claim_rewards.json`，按名跨文件引用）                                                       |
| `Common.BackButton`        | TemplateMatch | 通用返回箭头（同上，定义在 `claim_rewards.json`）                                                                         |

## 枢纽定义

```json
"Common.EnsureHome": {
    "max_hit": 10,
    "recognition": "DirectHit",
    "action": { "type": "DoNothing" },
    "timeout": 30000,
    "next": [
        "[JumpBack]Common.CheckItemObtained",
        "[JumpBack]Common.ClickHomeButton",
        "[JumpBack]Common.BackButton",
        "Common.CheckHomePage",
        "Common.PressBackToHome"
    ]
}
```

## 调用方写法

每个任务在开头放一个恒命中的**门节点**，`next` 先列本任务主路径、末位挂枢纽：

```json
"FarmResources.EnsureHome": {
    "max_hit": 6,
    "recognition": "DirectHit",
    "action": { "type": "DoNothing" },
    "next": ["FarmResources.CheckHomePage", "[JumpBack]Common.EnsureHome"]
}
```

任务入口识别失败（不在主页）时不再直接判任务失败：枢纽会依次尝试关闭「获得物品」弹窗、点击主页按钮、点击通用返回、最后发送系统返回键；回到主页后**自动跳回调用方**重试原列表，从而进入正常流程。

## 四条约束

1. **必须带 `[JumpBack]`**：枢纽出口 `Common.CheckHomePage` 是叶子，靠回跳把控制权交回调用方；不带 `[JumpBack]` 时枢纽跑完会命中流程终止条件，任务「成功但什么都没做」。
2. **必须放在 `next` 末位**：枢纽是 `DirectHit`，放在前面会压制其后所有候选。
3. **枢纽内的 `[JumpBack]` 处理节点必须是叶子且非 `DirectHit`**，否则会把收敛判定饿死。唯一的刻意例外是背键兜底 `Common.PressBackToHome`：它**有意**采用 `DirectHit`，且**不是** `[JumpBack]` 处理节点；它必须排在 `Common.CheckHomePage` **之后**、作为枢纽 `next` 的最后一项，并由自身的嵌套 `next`（`Common.CheckHomePage` → `Common.ClickHomeButton` → 自身）在每次按键后重新判定主页，使重试链有界（`max_hit: 5`）。把它移到收敛判定之前、或改成 `[JumpBack]` 子节点，都会破坏枢纽。
4. **列表顺序**：`[JumpBack]` 处理项在前、非 JumpBack 的收敛判定在后、恒命中兜底垫底；同一节点的 `next` 与 `on_error` 合并计算，不能重复指向同一目标（`pnpm check:maa` 会报 `duplicate-next`）。

## on_error 使用约定

`on_error` 只用于真正的失败兜底，例如「关卡退出键连点多次仍无效」「自定义识别等待超时后放弃」。**正常路径不要用 `on_error`**——每次都会写一条节点失败与 error-handling 日志，长期运行会明显放大日志体积，也让真正的失败难以辨认。

## 已接入的任务

| 任务                    | 入口                                        | 说明                                                                 |
| ----------------------- | ------------------------------------------- | -------------------------------------------------------------------- |
| 资源刷取 / 剩余体力刷取 | `FarmResources.EnsureHome`                  | 流程中段的 `FarmResources.Start` 失败时也回到该门重试                |
| 领取奖励                | `ClaimRewards`（入口本身即 DirectHit 列表） | 枢纽挂在列表末位                                                     |
| 玩家对战                | `PVP.EnsureHome`                            | —                                                                    |
| 体力信息                | `StaminaInfo.EnsureHome`                    | 自定义识别放弃后由枢纽接管，不再直接判任务失败                       |
| 活动关卡 / 活动商店     | `EventStage.EnsureHome` / `EnsureHomeShop`  | 由 `CheckEventHub` 的 `other_next` 路由进入，任务入口仍为 `EventHub` |
| 启动游戏                | 不接入                                      | 启动阶段游戏可能尚未进入游戏内，按返回键有退出游戏的风险             |

## 新增界面时

往枢纽 `next` 里加一条 `[JumpBack]` 处理节点即可（模板匹配或自定义识别均可），调用方无需改动；若新界面相对主页有独立的判定基准（例如活动页的 `flare_home.png`），则按同样结构新增一个作用域门节点，而不是修改共享枢纽。
