---
title: "Pipeline 编写指南"
order: 2
icon: "ri:git-branch-fill"
---

# Pipeline 编写指南

## 什么是 Pipeline？

Pipeline（任务流水线）是 MaaFramework 的核心概念：用 JSON 描述自动化任务的执行流程。每个 Pipeline 由若干**节点（Node）**组成，每个节点定义三件事：

- **识别算法**（recognition）：如何识别屏幕上的目标
- **执行动作**（action）：识别成功后要执行的操作
- **后继节点**（next）：完成当前节点后要尝试的下一步

本项目采用三层架构：`tasks/*.json` 定义 GUI 中可见的任务入口，`resource/base/pipeline/*.json` 用节点图描述流程（绝大部分逻辑落在这一层），`agent/custom/` 用 Python 处理复杂逻辑。三层职责划分见[项目结构说明](./structure.md)。

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

它与官方文档中 v2 协议的嵌套写法（`recognition: {"type": ..., "param": {...}}`）结构等价。运行渠道为 MaaFramework **stable**（见 `maa-project.json` 的 `maafw` 字段，版本随渠道自动更新；发布包复用客户端那份原生库，故 `runtimes/` 与 `pyproject.toml` 里 pin 的 `maafw` 版本须保持一致），字段合法性以 `tools/schema/` 的 schema 与 `pnpm check:schema` 为准；通用协议细节可对照 [MaaFramework Pipeline 协议](https://maafw.com/docs/3.1-PipelineProtocol)。

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

节点字段的全集与默认值以 `tools/schema/pipeline.schema.json` 为准（如 `threshold` 默认 0.7、`timeout` 默认 20000、`rate_limit` 默认 1000），本页只列常用部分。

## 基本结构与执行流程

### 节点执行顺序

Pipeline 的运行可以概括为一个循环。schema 中 `timeout` 字段给出的定义就是 `while (!timeout) { foreach(next); sleep_until(rate_limit); }`，展开后是：

1. 从入口节点开始（入口由 `tasks/*.json` 的 task 或 `interface.json` 指定）
2. 依次检测当前节点 `next` 列表里的每个候选节点
3. 第一个识别成功的候选节点执行其动作，并成为新的当前节点
4. 重复第 2 步，直到 `next` 为空或超过 `timeout`（默认 20000ms，`-1` 表示永不超时）
5. 每轮识别至少消耗 `rate_limit`（默认 1000ms），不足的时间会 sleep 等待

单个节点内部的执行顺序（`repeat` > 1 时）：

```text
pre_wait_freezes → pre_delay → action → [repeat_wait_freezes → repeat_delay → action] × (repeat-1) → post_wait_freezes → post_delay
```

**识别失败时的两种去向**必须分清：

- 节点**自身**识别失败 → 走该节点的 `on_error`（如有），否则停止
- 节点作为父节点 `next` 里的**候选**识别失败 → 只表示"该候选未命中"，框架继续尝试下一个候选，**不会**触发候选自己的 `on_error`

这个区别是[兜底策略](#兜底策略)一节的基础。

### 节点连接机制

节点通过 `next` 连接。`next` 的元素除节点名外还可以带属性前缀（schema：`节点名称，可带前缀如 [JumpBack]NodeName`）：

```json
{
    "StartTask": {
        "next": [
            "CheckStatus",
            "[JumpBack]HandleError"
        ]
    }
}
```

| 属性         | 作用                                                                       | 本项目用法                                                              |
| ------------ | -------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `[JumpBack]` | 命中节点执行完动作后**跳回父节点**重新尝试 `next` 列表，而不是继续向下推进 | 异常处理、弹窗关闭、可复用工具节点的标准写法，项目内已大量使用（73 处） |
| `[Anchor]`   | 引用某个锚点最后绑定的节点；节点用 `anchor` 字段把锚点名指向自己           | 暂未使用（`resource/base/pipeline/` 中没有 `anchor`），需要时再引入     |

`[Anchor]` 除了写在 `next` / `on_error` 里，也可以写在 `roi` / `target` 里（`[Anchor]锚点名`），直接复用该节点最近一次识别到的位置。

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

| 字段                       | 说明                                                                                                                                                               |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `pre_delay` / `post_delay` | 动作前/后等待（毫秒）；**应避免使用**，优先用 `pre_wait_freezes` / `post_wait_freezes` 或中间识别节点替代                                                          |
| `pre_wait_freezes`         | 识别到目标后、执行动作前等待画面静止（替代固定延迟）                                                                                                               |
| `post_wait_freezes`        | 等待画面静止不动（替代固定延迟，更智能）。项目内主流写法是整数简写（如 `"post_wait_freezes": 500`），也可写 `{"time": 500, "target": [x, y, w, h]}` 只关注局部区域 |
| `repeat` / `repeat_delay`  | 动作重复次数与每次间隔（如 `ClickHomePage` 连点 5 次、间隔 500ms）；`repeat_wait_freezes` 可在每次重复前等画面静止                                                 |
| `max_hit`                  | 最大命中次数，超过后节点被跳过。用于循环出现的元素                                                                                                                 |
| `timeout`                  | 识别超时（ms），默认 20000；`-1` 表示永不超时                                                                                                                      |
| `rate_limit`               | 每轮识别的最低耗时（ms，默认 1000），给高频节点降速用；项目内仅在少数节点显式设置                                                                                  |
| `enabled`                  | 是否启用；为 `false` 时其他节点 `next` 里会跳过它（Custom Action `DisableNode` 就是把它 override 成 `false`）                                                      |
| `inverse`                  | 反转识别结果；**慎用**，见[编写最佳实践](#编写最佳实践)                                                                                                            |
| `only_rec`                 | 仅识别不动作（用于 TemplateMatch 时需注意 schema）                                                                                                                 |
| `focus`                    | 命中/失败时显示日志通知                                                                                                                                            |
| `color_filter`             | OCR 预处理颜色过滤，值为 ColorMatch 节点名                                                                                                                         |
| `replace`                  | OCR 结果替换（`[["错字", "正字"]]`），用于修正模型反复识别错的文本                                                                                                 |
| `desc` / `doc`             | 节点说明，见[注释与占位字段](#注释与占位字段)                                                                                                                      |

## 节点命名约定

- 节点名称用**点分隔层级**，如 `FarmResources.Start`、`ClaimRewards.CheckDaily`
- 前缀用功能模块英文名：`PVP.`、`BattlePass.`、`Common.`
- JumpBack 节点不加 `next` 字段

## 模板图片与资源命名

模板图片统一放在 `resource/base/image/` 下：

- **目录组织**：按 pipeline 模块分子目录（如 `image/event_stage/`、`image/farm_resources/`）；多模块共用的公共图直接放在 `image/` 根目录
- **文件命名**：小写 `snake_case`，如 `flare_title.png`、`no_stamina.png`、`more.png`
- **区服差异**：`resource/bilibili/`、`resource/taptap/` 是叠在官服之上的增量目录（加载顺序见 `interface.json` 的 `resource` 字段）；目前两处都只覆盖了 `pipeline/startup.json`，需要区服专属模板图时同样按 `image/` 子目录组织
- **制作规范**：以 1280×720 截图裁剪，尺寸适中（约 50×50 到 200×200），过大容易误匹配；ROI 与分辨率基线见 [项目与资源约定](../protocol/overview.md)
- **路径写法**：Pipeline JSON 中 `template` 写相对 `image/` 目录的路径，统一使用**正斜杠**（如 `event_stage/flare_title.png`）

## 编写最佳实践

:::tip 节点连接原则

- **`next` 放出口节点**：`next` 表示"当前阶段做完了，接下来可能到哪"，不是"顺序执行的下一条"
- **`[JumpBack]` 放临时打断**：弹窗关闭、返回上一级、回主页这类逻辑都挂 `[JumpBack]`，执行完自动回跳，不污染主流程
- **降低耦合**：复用性高的节点（`Common.BackButton`、`Common.EnsureHome`）做成 `[JumpBack]` 叶子节点，供多处 `next` 引用
- **自循环**：操作可能不生效时，把节点自身放进自己的 `next`（如 `FarmResources.ExitStageConfirm` 点掉关卡退出 ✕ 后重新判定，✕ 仍在就再点一次，靠 `max_hit` 收敛）
- **页面切换**：点击进入新界面后加 `post_wait_freezes`，等画面静止再继续识别
- **滑动操作**：滑动后补一次识别或点击确认，避免画面还在惯性滚动就开始判断

:::

:::warning 注意事项

- **慎用 `inverse`**：反转识别结果会让流程难以推演；确实要用时配合 `post_wait_freezes` 锁定状态
- **避免无条件匹配**：`DirectHit` 没有任何判断条件，在 `next` 里滥用会导致非预期循环（项目里它主要用在枢纽/路由节点和少数无条件动作节点上）
- **优先级顺序**：`next` 按"必须先排除的"从高到低排，避免优先级倒挂
- **匹配频率**：同优先级下把识别更快的节点放前面，提高命中效率

:::

**优先级排序示例**（弹窗 vs 主界面）：

```text
场景：Node B 判断小弹窗（优先级高、出现频率低），Node A 判断主界面（优先级低、出现频率高）。

若弹窗出现时 A 依然能匹配上，就必须把 B 排在前面：
  "next": ["B", "A"]   ✓ B 先判断，弹窗被及时处理
  "next": ["A", "B"]   ✗ A 先命中，流程卡在弹窗上
```

## 注释与占位字段

Pipeline 节点支持两类注释/占位字段（schema 已支持，不会报错）：

1. `doc` / `*_doc` / `desc` / `*_desc`：节点功能说明，schema 模式为 `.*_doc$|^doc$|.*_desc$|^desc$`
2. `*_code` / `code`：**必填字段占位**，用于"模板路径统一在 `interface.json` 配置、不硬编码进 pipeline"的场景，schema 模式为 `.*_code$|^code$`

**本项目统一用 `desc`**：`resource/base/pipeline/` 里现有 250 处 `desc`、0 处 `doc`，新写节点请跟 `desc` 保持一致。

```json
"EnterBattle": {
    "desc": "进入作战界面",
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
        "type": "StartApp",
        "param": { "package": "com.phxh.official.nld" }
    },
    "timeout": 60000,
    "next": ["WaitGameLoading", "ClickToStart", "CheckHomePage"]
},
"WaitGameLoading": {
    "desc": "等待游戏加载完成",
    "recognition": "TemplateMatch",
    "roi": [595, 653, 146, 64],
    "template": "game_loading.png",
    "threshold": 0.8,
    "post_wait_freezes": 500,
    "next": ["ClickToStart"]
},
"ClickToStart": {
    "recognition": "TemplateMatch",
    "template": "startgame1.png",
    "threshold": 0.8,
    "action": { "type": "Click", "param": { "target_offset": [120, 0, 0, 0] } },
    "repeat": 3,
    "next": ["DailyLoginReward", "CheckHomePage"]
}
```

`LaunchGame` 用 `DirectHit` 起手，`next` 三个候选覆盖"加载中 / 登录页 / 已在主页"三种开局状态，因此同一条链路可以应付冷启动和热启动。以上为节选，源文件里 `WaitGameLoading` / `ClickToStart` 还带着 `post_delay` 等固定延迟（早期写法）；新增节点应优先用 `post_wait_freezes` 收敛。

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

**JumpBack 叶子节点不要带 `next` 字段**——执行完即回跳，路由由父节点的 `next` 控制。若该节点确实需要子链（例如枢纽节点本身），其 `next` 会被正常展开，整条子链执行完毕后才会回跳；命中节点「动作失败」时走 `on_error` 且不回跳（详见[官方协议](https://maafw.com/docs/3.1-PipelineProtocol#jump-back-jumpback)）。

本项目在此基础上提供了跨任务复用的**通用回主页枢纽**（`Common.EnsureHome`）：把已知界面的处理节点放进枢纽的 `next`，调用方在 `next` 末位挂 `[JumpBack]Common.EnsureHome`，即可获得「卡在任何界面都能回主页再继续」的能力。枢纽定义、四条约束与已接入的任务见[通用节点与回主页枢纽](./common.md)。

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

最多命中 5 次后跳过，适合循环出现的领取按钮。命中计数在**任务执行期间累计**，不因界面切换或单场战斗结束而清零；需要中途清零时用 Custom Action `ResetCount`（内部调用 `context.clear_hit_count`），项目里 `PVP.Speed2x` 就是靠它实现「每场恰好点一次」，详见[玩家对战协议](../protocol/pvp.md)。

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
    "desc": "从主页进入作战界面 [错误兜底: FarmResources.EnsureHome]",
    "recognition": "TemplateMatch",
    "template": "farm_resources/battle_entry.png",
    "on_error": ["FarmResources.EnsureHome"]
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

## 实战示例

以下示例全部取自本仓库 `resource/base/pipeline/` 的真实节点，可直接对照源文件阅读。为便于阅读，示例省略了 `pre_delay` / `post_delay` 等与说明无关的字段。

### 示例 1：线性推进与多候选 next

启动游戏链路（`startup.json`）：

```json
"LaunchGame": {
    "recognition": "DirectHit",
    "action": {
        "type": "StartApp",
        "param": { "package": "com.phxh.official.nld" }
    },
    "timeout": 60000,
    "next": ["WaitGameLoading", "ClickToStart", "CheckHomePage"]
},
"ClickToStart": {
    "recognition": "TemplateMatch",
    "template": "startgame1.png",
    "threshold": 0.8,
    "action": { "type": "Click", "param": { "target_offset": [120, 0, 0, 0] } },
    "repeat": 3,
    "next": ["DailyLoginReward", "CheckHomePage"]
}
```

**分析**：

- `LaunchGame` 用 `DirectHit` 无条件起手，`next` 的三个候选分别对应"还在加载 / 登录页 / 已在主页"，冷启动和热启动共用一条链路
- `ClickToStart` 用 `repeat: 3` + `target_offset` 连点，规避首屏点击不生效
- `next` 两个候选对应"弹了每日登录奖励 / 已进主页"，把弹窗处理并进主流程而不是单独加延迟

### 示例 2：页面切换与等待

活动关卡入口（`event_stage.json`）：

```json
"EventStage.ClickJourney": {
    "desc": "点击踏上征途进入关卡选择（固定点击 event7 右下角按钮中心，并用 OCR 确认按钮存在）",
    "max_hit": 3,
    "recognition": "OCR",
    "roi": [920, 570, 320, 100],
    "expected": "踏上征途",
    "only_rec": true,
    "threshold": 0.5,
    "action": { "type": "Click", "param": { "target": [1025, 607, 1, 1] } },
    "next": ["EventStage.WaitStageMapStable"]
},
"EventStage.WaitStageMapStable": {
    "desc": "确认已进入 EX 关卡地图：底部 EP 标签页可见后再继续；未切换成功则重试踏上征途",
    "recognition": "OCR",
    "roi": [80, 590, 560, 130],
    "expected": "EP\\.?[1-4]",
    "threshold": 0.7,
    "action": { "type": "DoNothing" },
    "post_wait_freezes": 1000,
    "next": ["EventStage.ClickEP2"],
    "on_error": ["EventStage.ClickJourney"]
}
```

**分析**：

- 按钮位置固定、文字可能变化时，用 OCR + `only_rec: true` 只做"存在性确认"，点击落点交给 `target` 固定坐标
- `WaitStageMapStable` 是"真的进去了吗"的确认节点：`post_wait_freezes: 1000` 等地图加载稳定，再继续下一步
- 没切换成功走 `on_error` 回到点击节点重试，比固定延迟更可靠

### 示例 3：JumpBack 战斗循环与异常回主页

战斗循环（`farm_resources.json`）：

```json
"FarmResources.BattleStage": {
    "desc": "战斗循环父节点：循环检测胜利画面/物品对话框/快速战斗按钮",
    "recognition": "DirectHit",
    "action": { "type": "DoNothing" },
    "next": [
        "[JumpBack]FarmResources.ClickVictory",
        "[JumpBack]FarmResources.ClickItemDialog",
        "FarmResources.QuickBattle",
        "FarmResources.ExitStageConfirm",
        "FarmResources.PrepareBattle"
    ]
},
"FarmResources.ClickVictory": {
    "desc": "检测并点击战斗胜利画面",
    "recognition": "TemplateMatch",
    "roi": [14, 6, 270, 119],
    "template": "farm_resources/battle_victory.png",
    "threshold": 0.8,
    "action": { "type": "Click" }
}
```

**分析**：

- 前两个 `[JumpBack]` 候选处理"战斗中随时可能弹出的胜利画面 / 物品对话框"，点掉后自动跳回 `FarmResources.BattleStage` 继续轮询
- 后三个普通候选是"这一场打完才走"的出口（快速战斗 / 退出确认 / 准备下一场），谁先命中谁退出循环
- `FarmResources.ClickVictory` 不写 `next`：它只负责点掉弹窗，路由完全由父节点控制，因此可以被多处复用
- 回主页兜底不放在这个循环里，而是挂在调用方 `next` 末位的 `[JumpBack]Common.EnsureHome`，见[通用节点与回主页枢纽](./common.md)

## 注意事项

1. **优先用 `wait_freezes` 而非固定延迟** — 导航点击后画面可能仍在过渡，用 `post_wait_freezes` 等待画面静止比固定 `post_delay` 更可靠；仅在加载动画无法冻结时才用固定延迟
2. **OCR expected 是正则表达式** — `".*"` 匹配任意，`"^text$"` 精确匹配
3. **ROI 以 1280x720 为基准** — 坐标 `[x, y, w, h]`
4. **兜底策略** — 流程兜底（正常可预期的走不通）放 `next` 末尾；真错误兜底（异常状态）保留 `on_error` 并加 `[错误兜底]` 标记。详见上方"兜底策略"一节
5. **`next` 顺序重要 — 按"必须先判断的"优先** — `next` 按优先级从高到低排列：先放**需要优先排除的界面**（如弹窗、错误提示），再放常规分支。反例：若主界面节点（识别频率高）排在弹窗节点前面，弹窗出现时主界面节点先命中，流程会卡死在错误界面。同优先级时按匹配频率排序，匹配快的放前面
6. **截图不全时加 roi** — 缩小识别范围提升速度和准确率
7. **清体力模式使用 `ReduceBattleCount`** — 通过 Custom Action `ReduceBattleCount` 动态减少战斗次数
8. **写 `desc` 而不是 `doc`** — 本仓库现有节点统一用 `desc` 做说明字段，两种都合法但别混着写

## 参考资源

- [MaaFramework Pipeline 协议](https://maafw.com/docs/3.1-PipelineProtocol)：字段语义、默认值，`[JumpBack]` / `[Anchor]` 等节点属性的权威定义
- [MaaFramework 项目接口协议](https://maafw.com/docs/3.3-ProjectInterfaceV2)：`interface.json` 与 `pipeline_override` 的写法
- 本仓库 `tools/schema/pipeline.schema.json`：本项目实际使用的 schema（由 `pnpm sync:schema` 从上游同步），字段合法性以它为准，`pnpm check:schema` 负责校验
- 相关文档：[项目结构说明](./structure.md)、[通用节点与回主页枢纽](./common.md)、[Custom 编写指南](./custom.md)、[环境搭建](./setup.md)
