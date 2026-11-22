---
order: 5
icon: ri:sword-line
---

# 玩家对战（PVP）协议

「玩家对战」在主页进对战界面后循环打满设定场次：每场选等级最低的对手、开战、点 2 倍速、
读结算积分与排名，场次用尽后回主页。赛季重置当天会先走一段编队引导。

## 任务入口

| 项     | 值                                                  |
| ------ | --------------------------------------------------- |
| 任务名 | 玩家对战（`tasks/pvp.json`，`default_check: true`） |
| entry  | `PVP.EnsureHome`（恒命中门节点）                    |
| 流程   | `resource/base/pipeline/pvp.json`                   |
| 选项   | `pvp_battle_count`                                  |

## 数据链路

```text
tasks/pvp.json
  └─ option pvp_battle_count（select，6 个 case）
       → 覆盖 PVP.InitBattleCount.custom_action_param.target_count（1–6）
  → resource/base/pipeline/pvp.json
  → agent/custom/action/pvp.py（InitPVPBattleCount、CheckPVPBattleCount）
     agent/custom/action/general.py（ResetCount）
     agent/custom/recognition/pvp.py（SelectPVPOpponent、ReadPVPResult）
```

## 任务前置条件

任务以 `PVP.EnsureHome` 为入口（恒命中门节点，`max_hit: 6`）：开始前通常应处于游戏主界面。未确认到主页时，由通用回主页枢纽 `Common.EnsureHome` 接管——依次尝试关闭「获得物品」弹窗、点击顶部主页按钮、点击通用返回按钮；回到主页后自动重试原流程，因此任务入口本身不会因为「不在主页」而失败。枢纽最多尝试 10 轮，仍无法回到主页时任务才会失败。

## 选项

| 选项               | 控件   | 默认 | 覆盖的节点                                             | 说明                                                |
| ------------------ | ------ | ---- | ------------------------------------------------------ | --------------------------------------------------- |
| `pvp_battle_count` | select | 1次  | `PVP.InitBattleCount.custom_action_param.target_count` | `1`–`6`；每天 5 次机会，第 6 次用于高账首次失败保护 |

选项只改计数器的初始值，不碰流程节点：`PVP.InitBattleCount` 是 Custom 动作节点，`target_count` 由 `agent` 进程内的模块级变量保存，`PVP.CheckBattleCount` 每场命中后减 1。

## 典型流程

```text
PVP.EnsureHome（门节点）→ PVP.CheckHomePage
  → PVP.Entry（对战入口）
       → 并列候选：PVP.SeasonReset.ClickContinue（赛季重置弹窗；未命中回落 CheckBattleInterface）
  → PVP.CheckBattleInterface
  → PVP.InitBattleCount（Custom：初始化剩余场次）
  → PVP.SelectOpponent（Custom：三个对手等级 OCR，点最低的那个）
       → PVP.CheckChallengeLimit（今日次数用尽 → PVP.ReturnMain）
       → PVP.StartBattle
            → PVP.BeginCombat（可重试直至进入战斗）
            → PVP.CheckInBattle
                 ├─ [JumpBack]PVP.Speed2x（每场只点一次 2 倍速）
                 ├─ [JumpBack]PVP.BeginCombat（战斗未真正开始时再点一次）
                 └─ PVP.BattleLoop（恒命中收敛，保证进入战斗循环）
            → PVP.CheckBattleEnd（OCR「跳过」）
            → PVP.WaitSettlement → PVP.ReadResult（Custom 读积分/排名）
            → PVP.ExitResult → PVP.BackToBattleInterface（ResetCount 重置倍速命中计数）
            → PVP.CheckBattleCount（Custom：场次 -1）
                 ├─ 未满 → PVP.SelectOpponent
                 └─ 已满 → PVP.ReturnMain
```

## 赛季重置适配

`PVP.Entry.next` 的第一项是赛季重置链的入口：平时识别不到，命中时才依次推进；每个节点的 `next` 首位都指向
**自己**，即「没点到就再点一次」，最后一项回到 `PVP.CheckBattleInterface`。

| 节点                                  | OCR `expected`   | 动作      |
| ------------------------------------- | ---------------- | --------- |
| `PVP.SeasonReset.ClickContinue`       | `点击任意处继续` | Click     |
| `PVP.SeasonReset.CheckEnterFormation` | `进入布阵`       | DoNothing |
| `PVP.SeasonReset.ClickEdit`           | `编辑`           | Click     |
| `PVP.SeasonReset.ClickQuickFormation` | `快速编队`       | Click     |
| `PVP.SeasonReset.CheckFormationCount` | `\d`             | DoNothing |
| `PVP.SeasonReset.ClickSave`           | `保存`           | Click     |
| `PVP.SeasonReset.ClickEnterFormation` | `进入布阵`       | Click     |
| `PVP.SeasonReset.ClickSavePosition`   | `保存`           | Click     |

换季后若引导文案变化，只需改上表节点的 `expected`，不用动流程结构。

## 关键约定

- **SelectOpponent**：`SelectPVPOpponent` 自定义识别，对 3 个对手区域分别 OCR 提取等级，选择等级最低的对手点击。`custom_recognition_param` 里的 `rois`（3 个等级数字 ROI）与 `click_positions`（3 个对手卡片点击位）一一对应，长度必须都是 3；某个对手 OCR 不到等级时跳过该对手，其余仍可比较
- **InitBattleCount / CheckBattleCount**：两个 Custom 动作共用一个模块级计数（`agent/custom/action/pvp.py` 的 `_remaining`）；`CheckBattleCount` 每命中一次减 1，减到 0 时用 `context.override_pipeline()` 把 `PVP.CheckBattleCount.next` 改成 `[PVP.ReturnMain]`，强制本场结束后收尾
- **BeginCombat**：一次点击可能无响应；`next` / `on_error` 应允许重试，直到 `CheckInBattle` 成功；`timeout: 30000` 用于覆盖长加载（loading 画面持续动画，无法用 `post_wait_freezes`）
- **Speed2x**：`[JumpBack]` 叶子节点（不带 `next`），命中后点击 2 倍速并回跳 `CheckInBattle` 重新评估其 `next`。为了**每场恰好点一次**、且不依赖「点击后按钮外观会不会变」，用 `max_hit: 1` 挡住回跳后的重复命中（否则会连点，甚至把倍速来回切），再由每场战斗结束后必经的 `PVP.BackToBattleInterface`（动作改为 `ResetCount`，参数 `nodes: ["PVP.Speed2x"]`）清空命中计数——`max_hit` 是任务内累计计数、不按场重置，不清理的话第 2 场起就点不到了。`CheckInBattle.next` 末位的 `BattleLoop`（DirectHit）是收敛出口——**即使倍速按钮没有识别到或已达 `max_hit` 被跳过，也一定会进入战斗循环**，不会在 20s 超时后直接判任务失败
- **BattleLoop**：长超时等待结算（`timeout: 300000`）；`on_error` 兜底到 `PVP.ReadResult`
- **ReadResult**：`ReadPVPResult` 自定义识别，`custom_recognition_param` 给 4 个 ROI（`result_roi`、`current_score_roi`、`score_change_roi`、`current_rank_roi`、`rank_change_roi`），每次 OCR 都带 `color_filter="PVP.TextFilter"`
- **PVP.TextFilter**：不是流程节点，是一个 `ColorMatch` 节点（`method: 4`、两组 `lower`/`upper`、`count: 1000`），供上面 4 处 OCR 当颜色过滤器用，压掉背景色提高数字识别率
- **高账失败保护判定**：`分数变化区域 OCR 为空` **且** `结算文案含「败」` 两个条件同时满足才判定为保护（本场不扣分）。只判「分数没变化」不够——OCR 漏检也会读空；实机还存在「分数不变但排名仍下降」的正常战斗，因此不能要求排名也无变化
- **挑战上限**：`pvp/challenge_limit.png` 命中则直接 `PVP.ReturnMain`，回主页结束本次任务

## 改动这类流程要动哪些文件

1. **改场次选项**：`tasks/pvp.json` 的 `pvp_battle_count.cases[].pipeline_override.PVP.InitBattleCount.custom_action_param.target_count`
2. **改对手选择**：`resource/base/pipeline/pvp.json` 的 `PVP.SelectOpponent.custom_recognition_param.rois` / `click_positions`（必须同时改，长度都是 3）
3. **改结算读取**：`PVP.ReadResult.custom_recognition_param` 的 5 个 ROI；数字识别不稳时先调 `PVP.TextFilter` 的颜色区间
4. **换季文案变化**：改 `PVP.SeasonReset.*` 各节点的 `expected`
5. **改计数逻辑**：`agent/custom/action/pvp.py`（`InitPVPBattleCount`、`CheckPVPBattleCount`）
6. **校验**：`pnpm exec maa-tools check`、`pnpm check`；改过 agent 代码再跑 `pnpm check:py`

## 图片目录

`resource/base/image/pvp/`：`entry.png`（对战入口）、`battle_interface.png`（对战界面）、`start_battle.png`（开始战斗）、`begin_combat.png`（作战开始）、`in_battle.png`（战斗中）、`speed_2x.png`（2 倍速）、`exit_result.png`（结算退出）、`challenge_limit.png`（次数用尽）。

## 验收清单

改动本任务后按以下顺序验证：

1. 对手选择：三个对手等级 OCR 正确，选最低等级点击
2. 单场战斗端到端：主页 → 进对战 → 开战 → 结算 → 回对战界面
3. 任意进度重启（战斗中 / 结算中 / 结果界面）都能继续或正确退出
4. 今日挑战次数用尽时正确提示并回主页
5. 战斗失败 / 断线等异常结算有兜底路径
6. 赛季重置：重置当天首次运行能走完编队引导并进入对战界面
7. 全量回归：与其它任务（启动、领取奖励、刷取）组合跑一遍无冲突
8. 倍速：每场战斗恰好一次 `PVP.Speed2x` 命中，点击后紧接 `BattleLoop`，同一场不出现第二次（回到对战界面时会看到 `PVP.BackToBattleInterface` 执行 `ResetCount`，把计数清零供下一场使用）；把 `PVP.Speed2x` 临时置为 `enabled: false` 时仍能进入战斗循环，而不是直接判任务失败

## 说明

自动化只负责操作流程，不保证胜负。
