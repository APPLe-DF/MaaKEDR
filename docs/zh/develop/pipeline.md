---
title: "Pipeline 编写指南"
order: 2
icon: "ri:git-branch-fill"
---

# Pipeline 编写指南

## 协议版本

本项目由 create-maa-project 的 pipeline 模板生成，Pipeline 使用**经典写法**：`recognition` / `action` 为字符串、参数平铺在节点顶层：

```json
{
    "NodeName": {
        "recognition": "TemplateMatch",
        "template": "button.png",
        "threshold": 0.8,
        "action": {"type": "Click"}
    }
}
```

它与官方文档中 v2 协议的嵌套写法（`recognition: {"type": ..., "param": {...}}`）结构等价。运行渠道为 MaaFramework **stable**（见 `maa-project.json` 的 `maafw` 字段，版本随渠道自动更新，以发布包内置运行时为准），字段合法性以 `tools/schema/` 的 schema 与 `pnpm check:schema` 为准；通用协议细节可对照 [MaaFramework Pipeline 协议](https://maafw.com/docs/3.1-PipelineProtocol)。

## 节点结构

Pipeline 节点用 JSON 定义，每个节点描述一个识别 → 动作 → 跳转的完整步骤：

```json
{
    "NodeName": {
        "recognition": "TemplateMatch",
        "roi": [
            100,
            200,
            80,
            50
        ],
        "template": "button.png",
        "threshold": 0.8,
        "action": {"type": "Click"},
        "next": [
            "NextNode",
            "FallbackNode"
        ]
    }
}
```

## 识别类型

| 类型          | 适用场景     | 说明                                                                                                                                    |
| ------------- | ------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| TemplateMatch | 静态 UI 元素 | OpenCV 模板匹配，图片放 `image/` 目录，threshold 默认 0.7；`template` 支持数组（多模板任一命中即可，适合入口图存在多种样式/状态时兜底） |
| OCR           | 动态文本     | PaddleOCR v5，`expected` 支持正则，`roi` 指定文字区域                                                                                   |
| DirectHit     | 路由分发     | 始终匹配成功，用于 `next` 分支控制                                                                                                      |
| Custom        | 复杂逻辑     | Python 自定义识别，通过 `@AgentServer.custom_recognition()` 注册                                                                        |
| ColorMatch    | 颜色过滤     | 配合 OCR 的 `color_filter` 字段使用，过滤背景干扰                                                                                       |

## 动作类型

| 类型      | 说明                                                              |
| --------- | ----------------------------------------------------------------- |
| Click     | 点击识别位置。`target: true` 点中心，`target: [x,y,w,h]` 偏移坐标 |
| DoNothing | 仅做识别路由，不执行操作                                          |
| Swipe     | 滑动。`param.begin` / `param.end` / `param.duration`              |
| Custom    | Python 自定义动作，通过 `@AgentServer.custom_action()` 注册       |

## 常用字段

| 字段                       | 说明                                                                                                      |
| -------------------------- | --------------------------------------------------------------------------------------------------------- |
| `pre_delay` / `post_delay` | 动作前/后等待（毫秒）；**应避免使用**，优先用 `pre_wait_freezes` / `post_wait_freezes` 或中间识别节点替代 |
| `post_wait_freezes`        | 等待画面静止不动（替代固定延迟，更智能）                                                                  |
| `max_hit`                  | 最大命中次数，超过后节点被跳过。用于循环出现的元素                                                        |
| `timeout`                  | 识别超时（ms），默认 20000                                                                                |
| `only_rec`                 | 仅识别不动作（用于 TemplateMatch 时需注意 schema）                                                        |
| `focus`                    | 命中/失败时显示日志通知                                                                                   |
| `color_filter`             | OCR 预处理颜色过滤，值为 ColorMatch 节点名                                                                |

## 节点命名约定

- 节点名称用**点分隔层级**，如 `FarmResources.Start`、`ClaimRewards.CheckDaily`
- 前缀用功能模块英文名：`PVP.`、`BattlePass.`、`Common.`
- JumpBack 节点不加 `next` 字段

## 模板图片与资源命名

模板图片统一放在 `resource/base/image/` 下：

- **目录组织**：按 pipeline 模块分子目录（如 `image/event_stage/`、`image/farm_resources/`）；多模块共用的公共图直接放在 `image/` 根目录
- **文件命名**：小写 `snake_case`，如 `flare_title.png`、`no_stamina.png`、`main_option.png`
- **区服差异图**：放 `resource/bilibili/image/`、`resource/taptap/image/` 对应目录（加载顺序见 `interface.json` 的 `resource` 字段）
- **制作规范**：以 1280×720 截图裁剪，尺寸适中（约 50×50 到 200×200），过大容易误匹配；ROI 与分辨率基线见 [项目与资源约定](../protocol/overview.md)
- **路径写法**：Pipeline JSON 中 `template` 写相对 `image/` 目录的路径，统一使用**正斜杠**（如 `event_stage/flare_title.png`）

## 注释与占位字段

Pipeline 节点支持两类注释/占位字段（schema 已支持，不会报错）：

1. `doc` / `*_doc`：节点功能说明
2. `*_code` / `code`：**必填字段占位**，用于"模板路径统一在 `interface.json` 配置、不硬编码进 pipeline"的场景

```json
"EnterBattle": {
    "doc": "进入作战界面",
    "template_code": "在 interface.json 的 pipeline_override 中配置 template",
    "recognition": "TemplateMatch",
    "roi": [885, 123, 340, 183],
    "action": { "type": "Click" },
    "next": ["CheckBattleInterface"]
}
```

:::tip 为什么需要 `*_code` 占位？

`TemplateMatch` 的 `template` 字段是必填项，但若模板路径由 `interface.json` 的 `pipeline_override` 统一注入（换分辨率/换区服时只改一处），pipeline 文件中就没有可填的值。此时用 `template_code` 占位，既过 schema 校验，又提示开发者"模板在别处配置"。

:::

## 设计模式

### 线性流程

适合有明确先后顺序的操作（如启动游戏）：

```json
"LaunchGame": {
    "recognition": "DirectHit",
    "action": {
        "type": "DoNothing",
        "param": { "package": "com.phxh.official.nld" }
    },
    "next": ["ClickToStart"]
},
"ClickToStart": {
    "recognition": "TemplateMatch",
    "template": "click_to_start.png",
    "action": { "type": "Click" },
    "post_delay": 2000,
    "next": ["DailyLoginReward", "CheckHomePage"]
}
```

### DirectHit 路由枢纽

```json
"HubNode": {
    "recognition": "DirectHit",
    "action": { "type": "DoNothing" },
    "next": ["BranchA", "BranchB"]
}
```

`next` 是 OR 逻辑：从上到下依次尝试，第一个识别成功的节点被执行。

### [JumpBack] 中心枢纽

适合需要反复进入子模块的场景（如领取奖励循环）：

```json
"ClaimRewards.MainHub": {
    "recognition": "DirectHit",
    "action": { "type": "DoNothing" },
    "next": [
        "[JumpBack]DispatchClaim.Start",
        "[JumpBack]ClaimRewards.Start",
        "[JumpBack]BattlePass.Start",
        "[JumpBack]Mailbox.Start"
    ]
}
```

`[JumpBack]` 节点命中后执行动作，然后**跳回父节点**重新尝试 next 列表。只有非 JumpBack 节点能退出循环。

**JumpBack 节点不能有 `next` 字段**——路由由父节点的 `next` 控制。

### 战斗循环

```json
"BattleStage": {
    "recognition": "DirectHit",
    "action": { "type": "DoNothing" },
    "next": [
        "[JumpBack]ClickVictory",
        "[JumpBack]ClickItemDialog",
        "QuickBattle"
    ]
}
```

战斗胜利 → 点击 → 跳回检测 → 再次战斗 → 体力不足时退出。

### 任务选项覆盖

`tasks/*.json` 中用 `pipeline_override` 在运行时修改节点行为：

```json
"pipeline_override": {
    "FarmResources.Start": {
        "next": ["FarmResources.ResourceCollect"]
    },
    "FarmResources.ClickStage": {
        "custom_recognition_param": "{\"stage_name\": \"1-1\", \"stage_index\": 1, \"resource_type\": \"特别军费行动\"}"
    }
}
```

可以修改 `next`、`roi`、`threshold`、`custom_action_param` 等任意字段。

### max_hit 防循环

```json
"ClaimButton": {
    "max_hit": 5,
    "recognition": "TemplateMatch",
    ...
}
```

最多命中 5 次后跳过，适合循环出现的领取按钮。`max_hit` 跨会话计数。

### color_filter OCR 预处理

对于颜色鲜明的文本，可以用 ColorMatch 预先过滤背景，提升 OCR 准确率：

```json
"GoldTextFilter": {
    "recognition": "ColorMatch",
    "method": 4,
    "lower": [[38, 31, 30]],
    "upper": [[50, 44, 44]],
    "count": 1000,
    "connected": true
}
```

在 OCR 节点中引用：

```python
JOCR(roi=(x, y, w, h), color_filter="GoldTextFilter")
```

## 兜底策略

分为两种兜底，按节点语义区分，**禁止混用**：

### 流程兜底（推荐用 next 列表）

当节点的识别失败属于正常流程分支时（如"没找到每日徽章 → 检查每周徽章"），把兜底节点放在父节点的 `next` 列表中当前节点之后，利用 MaaFW 的**顺序 OR** 语义自动触达。

在 MaaFW 中，父节点识别成功后，会依次尝试 `next` 列表中的每个子节点，直到有一个子节点的识别成功为止。若前面的子节点识别失败，框架自动回落到下一个子节点继续尝试。因此，将兜底节点放在 `next` 列表末尾，即可在"前面所有正常分支都识别失败"时自然触达。

```json
"ConfirmInterface": {
    "next": [
        "CheckDaily",        // 先尝试检查每日徽章
        "CheckWeekly",       // CheckDaily 识别失败时，自动回落到每周徽章
        "CheckMilitary"      // 两者都失败时，再检查军旅徽章
    ]
}
```

**注意**：上述"识别失败继续尝试后续节点"的行为发生在**父节点的 `next` 列表层面**。对于单个节点自身而言，其 `next` 字段仅在"该节点识别成功"后才会被进入；若该节点自身识别失败，则直接进入其 `on_error`（如有）或停止。因此，"否定检查"模式（识别成功=停止、识别失败=继续）无法通过单个节点的 `next` 实现，需保留 `on_error`（见下文）。

### 真错误兜底（保留 on_error，加 `[错误兜底]` 标记）

当兜底路径仅在异常/意外状态触发时（如关卡 UI 无法识别、快战按钮消失），保留 `on_error` 并加标记：

```json
"FarmResources.Start": {
    "desc": "从主页进入作战界面 [错误兜底: ReturnMain]",
    "recognition": "TemplateMatch",
    "template": "battle_entry.png",
    "on_error": ["ReturnMain"]
}
```

这类节点触发时说明遇到了预期外的 UI 状态，`on_error` 截图对调试有价值，应保留。

### 特殊情况：否定检查模式（并列候选）

对于"识别到 X 就停止，没识别到就继续"的节点（如"检查关卡是否锁住"），**不要依赖候选自身的 `on_error` 兜底**：当该节点是父节点 `next` 列表中的候选时，识别失败只表示"候选未命中"，**不会触发节点自身的 `on_error`**，列表若无后续候选会整列表失败并重试，造成死循环超时（实机验证：`FarmResources.SelectSkillStage` 曾因此循环 21 次 × 20s 后任务失败）。

正确写法是**并列候选模式**——把"继续"节点放在 `next` 列表中、检查节点之后，让它自然回落：

```json
"SelectStage": {
    "recognition": "DirectHit",
    "next": [
        "CheckLocked",   // 命中=锁定停止；未命中→回落下一候选
        "ClickStage"     // 未命中时的继续分支（实际点击进入）
    ]
},
"CheckLocked": {
    "recognition": "TemplateMatch",
    "template": "lock_icon.png",
    // 不设 on_error（候选位置不生效，保留反而误导）
    "focus": {
        "Node.Recognition.Succeeded": "已锁，停止",
        "Node.Recognition.Failed": "未锁，继续"
    }
}
```

注意：`CheckLocked` 作为候选时会先评估一次，失败后自动尝试下一个候选（`ClickStage`），两者都失败才整列表失败。这种节点在 `desc` 中注明"否定检查（并列候选）"以辅助理解。

## 注意事项

1. **优先用 `wait_freezes` 而非固定延迟** — 导航点击后画面可能仍在过渡，用 `post_wait_freezes` 等待画面静止比固定 `post_delay` 更可靠；仅在加载动画无法冻结时才用固定延迟
2. **OCR expected 是正则表达式** — `".*"` 匹配任意，`"^text$"` 精确匹配
3. **ROI 以 1280x720 为基准** — 坐标 `[x, y, w, h]`
4. **兜底策略** — 流程兜底（正常可预期的走不通）放 `next` 末尾；真错误兜底（异常状态）保留 `on_error` 并加 `[错误兜底]` 标记。详见上方"兜底策略"一节
5. **`next` 顺序重要 — 按"必须先判断的"优先** — `next` 按优先级从高到低排列：先放**需要优先排除的界面**（如弹窗、错误提示），再放常规分支。反例：若主界面节点（识别频率高）排在弹窗节点前面，弹窗出现时主界面节点先命中，流程会卡死在错误界面。同优先级时按匹配频率排序，匹配快的放前面
6. **截图不全时加 roi** — 缩小识别范围提升速度和准确率
7. **清体力模式使用 `ReduceBattleCount`** — 通过 Custom Action `ReduceBattleCount` 动态减少战斗次数
