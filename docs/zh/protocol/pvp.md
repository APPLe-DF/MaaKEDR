---
order: 5
icon: ri:sword-line
---

# 玩家对战（PVP）协议

## 任务入口

| 项     | 值                                         |
| ------ | ------------------------------------------ |
| 任务名 | 见 `tasks/pvp.json`                        |
| entry  | 以该文件中定义为准（通常自检主页后进对战） |
| 流程   | `resource/base/pipeline/pvp.json`          |

## 任务前置条件

任务以 `PVP.CheckHomePage` 为入口：开始前通常应处于游戏主界面。若主页识别失败，Pipeline 会通过 `PVP.ReturnToHome` 尝试识别并点击返回按钮，再回到主页重新检查；如果仍无法确认主页，任务才会失败。

## 选项

战斗次数由任务选项控制（如 1–5 次），通过 Custom（如 `InitPVPBattleCount` / `CheckPVPBattleCount`）维护计数。

## 典型流程

```text
CheckHomePage → Entry → CheckBattleInterface
  → SelectOpponent（Custom 识别三个对手等级，选最低点击）
  → InitBattleCount
       → CheckChallengeLimit（今日次数用尽则回主页）
       → StartBattle
       → BeginCombat（可重试直至进入战斗）
       → CheckInBattle → Speed2x
       → BattleLoop → CheckBattleEnd（OCR「跳过」）
       → WaitSettlement → ReadResult（Custom 读分/排名）
       → ExitResult → BackToBattleInterface
       → CheckBattleCount
            → 未满：SelectOpponent
            → 已满：ReturnMain
```

## 关键约定

- **SelectOpponent**：`SelectPVPOpponent` 自定义识别，对 3 个对手区域分别 OCR 提取等级，选择等级最低的对手点击。ROI 和点击位置在 pipeline 的 `custom_recognition_param` 中配置
- **BeginCombat**：一次点击可能无响应；`next` / `on_error` 应允许重试，直到 `CheckInBattle` 成功
- **BattleLoop**：长超时等待结算；失败可兜底 `ReadResult`
- **ReadResult**：`ReadPVPResult` 自定义识别，ROI 在 pipeline 的 `custom_recognition_param` 中
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

## 说明

自动化只负责操作流程，不保证胜负。
