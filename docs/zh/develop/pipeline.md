---
title: "Pipeline 编写指南"
order: 2
icon: "ri:git-branch-fill"
---

# Pipeline 编写指南

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

| 类型          | 适用场景     | 说明                                                             |
| ------------- | ------------ | ---------------------------------------------------------------- |
| TemplateMatch | 静态 UI 元素 | OpenCV 模板匹配，图片放 `image/` 目录，threshold 默认 0.7        |
| OCR           | 动态文本     | PaddleOCR v5，`expected` 支持正则，`roi` 指定文字区域            |
| DirectHit     | 路由分发     | 始终匹配成功，用于 `next` 分支控制                               |
| Custom        | 复杂逻辑     | Python 自定义识别，通过 `@AgentServer.custom_recognition()` 注册 |
| ColorMatch    | 颜色过滤     | 配合 OCR 的 `color_filter` 字段使用，过滤背景干扰                |

## 动作类型

| 类型      | 说明                                                              |
| --------- | ----------------------------------------------------------------- |
| Click     | 点击识别位置。`target: true` 点中心，`target: [x,y,w,h]` 偏移坐标 |
| DoNothing | 仅做识别路由，不执行操作                                          |
| Swipe     | 滑动。`param.begin` / `param.end` / `param.duration`              |
| Custom    | Python 自定义动作，通过 `@AgentServer.custom_action()` 注册       |

## 常用字段

| 字段                       | 说明                                               |
| -------------------------- | -------------------------------------------------- |
| `pre_delay` / `post_delay` | 动作前/后等待（毫秒），导航点击后建议 1000-2000ms  |
| `post_wait_freezes`        | 等待画面静止不动（替代固定延迟，更智能）           |
| `max_hit`                  | 最大命中次数，超过后节点被跳过。用于循环出现的元素 |
| `timeout`                  | 识别超时（ms），默认 20000                         |
| `only_rec`                 | 仅识别不动作（用于 TemplateMatch 时需注意 schema） |
| `focus`                    | 命中/失败时显示日志通知                            |
| `color_filter`             | OCR 预处理颜色过滤，值为 ColorMatch 节点名         |

## 节点命名约定

- 节点名称用**点分隔层级**，如 `FarmResources.Start`、`ClaimRewards.CheckDaily`
- 前缀用功能模块英文名：`PVP.`、`BattlePass.`、`Common.`
- JumpBack 节点不加 `next` 字段

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

当节点的识别失败属于正常流程分支时（如"没找到每日徽章 → 检查每周徽章"），把兜底节点放在 `next` 列表末尾，利用 MaaFW 的 OR 语义自动触达：

```json
"CheckDaily": {
    "recognition": "TemplateMatch",
    "template": "claim_rewards/daily_badge.png",
    "next": [
        "ClaimDailyButton",                // 识别成功 → 领奖
        "[JumpBack]CheckWeekly"            // 识别失败 → 跳到下周检查
    ]
}
```

若当前节点识别成功，走 `next` 列表的首个匹配节点；若识别失败，则依次尝试 `next` 列表中后续节点的识别。把兜底放在末尾，自然在"前面都识别失败"时生效。

**注意**：`next` 列表只在识别**成功**时触发——"否定检查"模式（识别成功=停止、识别失败=继续）无法用纯 next 实现，需走 `on_error` 兜底（见下文）。

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

### 特殊情况：否定检查模式

对于"识别到 X 就停止，没识别到就继续"的节点（如"检查关卡是否锁住"），MaaFW 没有 `on_failure` 路由，只能用 `on_error` 实现流程兜底：

```json
"CheckLocked": {
    "recognition": "TemplateMatch",
    "template": "lock_icon.png",
    "on_error": ["ProceedNode"],  // 没找到锁 → 继续
    "focus": {
        "Node.Recognition.Succeeded": "已锁，停止",
        "Node.Recognition.Failed": "未锁，继续"
    }
}
```

这种节点在 `desc` 中注明"否定检查"以辅助理解。

## 注意事项

1. **等待时间要充足** — 导航点击后至少 1000ms，复杂界面建议 2000ms
2. **OCR expected 是正则表达式** — `".*"` 匹配任意，`"^text$"` 精确匹配
3. **ROI 以 1280x720 为基准** — 坐标 `[x, y, w, h]`
4. **兜底策略** — 流程兜底（正常可预期的走不通）放 `next` 末尾；真错误兜底（异常状态）保留 `on_error` 并加 `[错误兜底]` 标记。详见上方"兜底策略"一节
5. **`next` 顺序重要** — 优先匹配的放在前面，减少等待时间
6. **截图不全时加 roi** — 缩小识别范围提升速度和准确率
7. **`post_wait_freezes`** — 适合动画结束后再操作，比固定 `post_delay` 更可靠
8. **清体力模式使用 RepeatCount** — 通过 Custom Action 动态减少战斗次数
