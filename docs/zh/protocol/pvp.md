---
order: 5
icon: ri:sword-line
---

# 玩家对战（PVP）协议

## 任务入口

| 项     | 值                                |
| ------ | --------------------------------- |
| 任务名 | 见 `tasks/pvp.json`               |
| entry  | `PVP.EnsureHome`（恒命中门节点）  |
| 流程   | `resource/base/pipeline/pvp.json` |

## 任务前置条件

任务以 `PVP.EnsureHome` 为入口（恒命中门节点）：开始前通常应处于游戏主界面。未确认到主页时，由通用回主页枢纽 `Common.EnsureHome` 接管——依次尝试关闭「获得物品」弹窗、点击顶部主页按钮、点击通用返回按钮，最后发送系统返回键；回到主页后自动重试原流程，因此任务入口本身不会因为「不在主页」而失败。枢纽最多尝试 10 轮，仍无法回到主页时任务才会失败。

## 选项

战斗次数由任务选项控制（1–6 次，其中第 6 次用于高级账号首次失败保护），通过 Custom（如 `InitPVPBattleCount` / `CheckPVPBattleCount`）维护计数。

## 典型流程

```text
CheckHomePage → Entry → CheckBattleInterface
  → SelectOpponent（Custom 识别三个对手等级，选最低点击）
  → InitBattleCount
       → CheckChallengeLimit（今日次数用尽则回主页）
       → StartBattle
       → BeginCombat（可重试直至进入战斗）
       → CheckInBattle
            → [JumpBack]Speed2x（命中即点 2 倍速，随后回跳本列表）
            → [JumpBack]BeginCombat（战斗未真正开始时再点一次）
            → BattleLoop（恒命中收敛，保证进入战斗循环）
       → CheckBattleEnd（OCR「跳过」）
       → WaitSettlement → ReadResult（Custom 读分/排名）
       → ExitResult → BackToBattleInterface（ResetCount 重置倍速命中计数）
       → CheckBattleCount
            → 未满：SelectOpponent
            → 已满：ReturnMain
```

## 关键约定

- **SelectOpponent**：`SelectPVPOpponent` 自定义识别，对 3 个对手区域分别 OCR 提取等级，选择等级最低的对手点击。ROI 和点击位置在 pipeline 的 `custom_recognition_param` 中配置
- **BeginCombat**：一次点击可能无响应；`next` / `on_error` 应允许重试，直到 `CheckInBattle` 成功
- **Speed2x**：`[JumpBack]` 叶子节点（不带 `next`），命中后点击 2 倍速并回跳 `CheckInBattle` 重新评估其 `next`。为了**每场恰好点一次**、且不依赖「点击后按钮外观会不会变」，用 `max_hit: 1` 挡住回跳后的重复命中（否则会连点，甚至把倍速来回切），再由每场战斗结束后必经的 `PVP.BackToBattleInterface`（动作改为 `ResetCount`）清空 `PVP.Speed2x` 的命中计数——`max_hit` 是任务内累计计数、不按场重置，不清理的话第 2 场起就点不到了。`CheckInBattle.next` 末位的 `BattleLoop`（DirectHit）是收敛出口——**即使倍速按钮没有识别到或已达 `max_hit` 被跳过，也一定会进入战斗循环**，不会像以前那样在 20s 超时后直接判任务失败
- **BattleLoop**：长超时等待结算；失败可兜底 `ReadResult`
- **ReadResult**：`ReadPVPResult` 自定义识别，ROI 在 pipeline 的 `custom_recognition_param` 中
- **高账失败保护判定**：仅以「分数是否变化」为准——分数变化区域 OCR 为空即判定为高级账号首次失败保护（本场不扣分）。实机存在「分数不变但排名仍下降」的情况，因此不能要求排名也无变化，否则这类正常战斗会被误判为保护
- **挑战上限**：`challenge_limit` 模板命中则 toast/日志提示并退出

## 图片目录

`resource/base/image/pvp/`（入口、对战界面、开始、作战中、倍速、退出结果等）。

## 验收清单

改动本任务后按以下顺序验证：

1. 对手选择：三个对手等级 OCR 正确，选最低等级点击
2. 单场战斗端到端：主页 → 进对战 → 开战 → 结算 → 回对战界面
3. 任意进度重启（战斗中 / 结算中 / 结果界面）都能继续或正确退出
4. 今日挑战次数用尽时正确提示并回主页
5. 战斗失败 / 断线等异常结算有兜底路径
6. 全量回归：与其它任务（启动、领取奖励、刷取）组合跑一遍无冲突
7. 倍速：每场战斗恰好一次 `PVP.Speed2x` 命中，点击后紧接 `BattleLoop`，同一场不出现第二次（回到对战界面时会看到 `PVP.BackToBattleInterface` 执行 `ResetCount`，把计数清零供下一场使用）；把 `PVP.Speed2x` 临时置为 `enabled: false` 时仍能进入战斗循环，而不是直接判任务失败

## 说明

自动化只负责操作流程，不保证胜负。
