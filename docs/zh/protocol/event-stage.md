---
order: 6
icon: ri:fire-line
---

# 活动关卡与活动商店协议

本页记录耀斑活动的两个每日任务：活动关卡刷取与活动商店兑换。任务定义位于 `tasks/event_stage.json`，入口分别为
`EventStage.EventHub`（关卡）与 `EventStage.EventHubShop`（商店）——两者都先检查活动主页，再检查游戏主页；
两个任务结束后都必须返回游戏主页。

## 任务入口与选项

| 任务         | entry                     | 默认勾选 | 选项                               |
| ------------ | ------------------------- | -------- | ---------------------------------- |
| 活动关卡刷取 | `EventStage.EventHub`     | 否       | `event_stage`、`event_sweep_count` |
| 活动商店兑换 | `EventStage.EventHubShop` | 否       | 无额外选项，自动处理定额保障商品   |

活动关卡当前支持 `EX2-1`、`EX2-2`、`EX3-1`、`EX4-1`；活动关卡每日扫荡上限为 3 次，且不消耗普通体力，
前置条件是先通关耀斑活动的全部关卡（含 EX 关）。

选项与覆盖：

| 选项                | 控件   | 默认  | 覆盖的节点                                                                                                                                                           |
| ------------------- | ------ | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `event_stage`       | select | EX2-1 | `EventStage.FindTargetStage.custom_recognition_param`（`stage_name` / `stage_roi`）、`EventStage.ClickEP2.expected`；EX3-1 另改 `EventStage.WaitStageMapStable.next` |
| `event_sweep_count` | select | 3次   | `EventStage.SetBattleCount.custom_action_param.target_count`（`1` / `2` / `3` / `"max"`）                                                                            |

目标关卡 → EP 标签的当前映射（由 `event_stage` 选项决定）：

| 选项    | `ClickEP2.expected` | 额外覆盖                                                         |
| ------- | ------------------- | ---------------------------------------------------------------- |
| `EX2-1` | `EP\.?2`            | —                                                                |
| `EX2-2` | `EP\.?3`            | —                                                                |
| `EX3-1` | `EP\.?4`            | `WaitStageMapStable.next = [ClickEP1, ClickEP2]`（先切离再切回） |
| `EX4-1` | `EP\.?4`            | —                                                                |

`ClickEP1` 的存在原因是：进入地图时若已停在最右章节，直接点 EP.4 标签可能无响应，需先点 EP.1 切走再点回。

## 数据链路

```text
tasks/event_stage.json
  ├─ 活动关卡刷取：option [event_stage, event_sweep_count]
  │    + 任务级 pipeline_override：EventStage.EventHub 的 custom_recognition_param / next（固定关卡任务的入口路由）
  └─ 活动商店兑换：无选项，直接走 EventStage.EventHubShop
  → resource/base/pipeline/event_stage.json
  → agent/custom/recognition/event_stage.py（CheckEventHub、CheckEventStage、CheckAllSoldOut、
     CheckShopItemSoldOut、CheckShopRefreshAfterPurchase）
     agent/custom/action/farm_resources.py（SetBattleCount，与资源刷取共用）
```

入口是三态路由：`EventStage.EventHub` / `EventStage.EventHubShop` 用自定义识别 `CheckEventHub` 判断当前在
**活动首页**（`flare_home.png`）、**游戏主页**（`main_option.png`，ROI `[1199,6,77,83]`）还是**其他页面**，
再用 `context.override_next()` 分别路由到活动流程入口 / `EventStage.Start` / 门节点 `EventStage.EnsureHome`
（商店任务为 `EventStage.EnsureHomeShop`）；门节点把控制权交给通用回主页枢纽 `Common.EnsureHome`，
回主页后重试。

## 活动关卡刷取流程

```text
EventStage.EventHub（三态路由）
  → EventStage.ClickJourney（OCR「踏上征途」）
  → EventStage.WaitStageMapStable（OCR EP 标签出现）
  → EventStage.ClickEP2（OCR EP 标签并点击；EX3-1 先经 ClickEP1）
  → EventStage.FindTargetStage（Custom CheckEventStage：定位并点击目标关卡）
  → EventStage.StagePrepare（DirectHit 分流）
       → EventStage.CheckQuickBattleState（OCR「打开」→ 点开关）
       → EventStage.CheckQuickBattleEnabled（OCR「关闭」→ 已开启，直接进次数设置）
  → EventStage.SetBattleCount（Custom SetBattleCount）
  → EventStage.PrepareBattle（OCR「准备(快速)战斗」）→ EventStage.StartBattle
  → EventStage.BattleStage（战斗循环父节点）
       → [JumpBack]ClickVictory / [JumpBack]ClickItemDialog
       → CheckQuickBattleState（再来一轮）
       → ExitStageConfirm / CheckBackOnMap（回到地图）
  → EventStage.ReturnMainFromStage → EventStage.CheckReturnedHome（主页，任务成功出口）

主页分支：EventHub 未命中 → EventStage.CheckHomePage → EventStage.Start（点「耀斑」艺术字）
其他页面：EventHub / CheckHomePage 均未命中 → EventStage.EnsureHome → Common.EnsureHome → 回主页后重试
```

关键约定：

- `EventStage.FindTargetStage` 用 `CheckEventStage` 在 `stage_roi`（默认全屏 `[0,0,1280,640]`）内 OCR 目标关卡名，
  命中即点击，并由识别器内部用 `override_next` 决定下一步：
    - 目标不在当前视野 → `EventStage.DragFindStage`（向左拖动地图，`max_hit: 8`，滑完回到 `FindTargetStage`）
    - 关卡卡片锁定 → `EventStage.StageLocked`
    - 卡片上方徽标 OCR 到 `0/3`（次数耗尽）→ `EventStage.ReturnMainFromStage`
    - 正常找到 → `EventStage.StagePrepare`
- `EventStage.WaitStageMapStable` 的 `on_error` 回到 `ClickJourney`，即地图没加载出来就再点一次「踏上征途」；
  `ClickEP2` 的 `on_error` 回到 `WaitStageMapStable`。
- `EventStage.BattleStage` 处理胜利画面、获得物品弹窗、下一轮快速战与退出；`EventStage.CheckBackOnMap`
  用 OCR 确认已回到活动地图，再经 `ReturnMainFromStage` 统一回主页。
- `EventStage.CheckBattlePage`（OCR EP 标签、`max_hit: 3`）用于退出确认后确认「确实回到了地图」，未命中则重试自身。
- 出口统一是 `EventStage.CheckReturnedHome`（识别 `main_option.png`，叶子节点）；未识别到主页时
  `on_error` → `EventStage.ReturnMain` 再点一次 HOME 键。

> [!NOTE]
> `EventStage.ClickEX2_1` ~ `ClickEX4_1`、`EventStage.CheckStageEntryResult`、`EventStage.ReturnToStageSelect`、
> `EventStage.EventHubRetry` 是早期按「每个 EX 关卡一个点击节点」写的遗留节点，当前主流程已改由
> `CheckEventStage` 统一识别，**没有节点引用它们**。改流程时不必同步这几处。

## 活动商店清空

活动商店任务的入口为 `EventStage.EventHubShop`，由它路由到 `EventStage.ClickBattleReport`，进入活动商店的「定额保障」页：

```text
EventHubShop（三态路由）→ ClickBattleReport（OCR「战果上报」）
  → SelectFixedGuarantee（OCR「定额保障」）
  → CheckAllSoldOut（Custom CheckAllSoldOut：roi [0,180,1280,540]、total_items 10）
       ├─ 全部售罄 → EventStage.ShopAllSoldOut → ReturnMainFromShop
       └─ 未全售罄 → CheckSoldOut1 … CheckSoldOut10
  → BuyItemN（DirectHit 点商品卡）→ SetPurchaseMaxN（点「最大」）→ ConfirmPurchaseN
       → WaitPurchaseClosedN → CheckShopRefreshAfterPurchaseN
            ├─ 已刷新 → 下一件 CheckSoldOut(N+1)
            └─ 未刷新 → RefreshShopAfterPurchaseN（补点一次）→ 下一件
  → 商品 10 结束 → ReturnMainFromShop → CheckReturnedHome
```

- `CheckAllSoldOut` 在商店区域 OCR「已售罄」；达到快捷判断阈值时提示全部售罄并返回主页，否则进入逐件检查。
- `CheckSoldOut1` ~ `CheckSoldOut10` 由 `CheckShopItemSoldOut` 按商品卡片 ROI 判断：`sold_out_next` / `buy_next`
  两个参数显式给出「跳过」与「购买」分支，路由不写在 pipeline 的 `next` 里。
- `BuyItemN` 点击商品卡片 → `SetPurchaseMaxN` 点「最大」→ `ConfirmPurchaseN` 识别并点击确认；
  确认按钮不在时 `on_error` → `SkipConfirmPurchaseN`，继续检查下一件。
- 购买完成后 `CheckShopRefreshAfterPurchaseN` 判断商店是否已刷新；未刷新时 `RefreshShopAfterPurchaseN`
  只补点一次，避免重复购买。
- 商品 10 的购买或跳过路径都进入 `EventStage.ReturnMainFromShop`（`max_hit: 3`），再经 `CheckReturnedHome` 确认回到主页。
- `CheckEventHub`、`CheckEventStage`、`CheckAllSoldOut`、`CheckShopItemSoldOut`、`CheckShopRefreshAfterPurchase`
  在已读取界面但需要选择分支时，返回占位 `AnalyzeResult`（`box=(0,0,1,1)` 一类）并调用 `context.override_next()`；
  真正的识别失败才返回 `None`。

## 代码位置

| 内容                      | 路径                                                                      |
| ------------------------- | ------------------------------------------------------------------------- |
| 任务与选项                | `tasks/event_stage.json`                                                  |
| 活动 Pipeline             | `resource/base/pipeline/event_stage.json`                                 |
| Custom Recognition        | `agent/custom/recognition/event_stage.py`                                 |
| Custom Action（共用）     | `agent/custom/action/farm_resources.py`                                   |
| Recognition / Action 注册 | `agent/custom/recognition/__init__.py`、`agent/custom/action/__init__.py` |
| Interface import          | `interface.json`                                                          |
| 活动图片                  | `resource/base/image/event_stage/`、`resource/base/image/flare_home.png`  |

## 改动这类流程要动哪些文件

1. **换期改关卡名 / 位置**：`tasks/event_stage.json` 的 `event_stage.cases` 加/改一项，
   同时改 `EventStage.FindTargetStage.custom_recognition_param.stage_name` 与 `EventStage.ClickEP2.expected`
2. **EP 标签位置变化**：改 `EventStage.ClickEP1` / `ClickEP2` 的 `roi` 与 `expected`
3. **扫荡次数选项**：`event_sweep_count.cases` 的 `SetBattleCount.custom_action_param.target_count`
4. **商店商品数量变化**：`CheckSoldOutN` / `BuyItemN` / `ConfirmPurchaseN` / `SkipConfirmPurchaseN` /
   `CheckShopRefreshAfterPurchaseN` / `RefreshShopAfterPurchaseN` 是 10 组一一对应的节点，
   增删商品要成套改，并同步 `CheckAllSoldOut` 的 `total_items`
5. **改活动入口识别**：`CheckEventHub` 的 `activity_template` / `global_template` / `global_roi`（在
   `EventStage.EventHub`、`EventHubShop`、`EventHubAfterClick`、`EventHubShopAfterClick` 四处参数里）
6. **改 Custom 逻辑**：`agent/custom/recognition/event_stage.py`
7. **校验**：`pnpm exec maa-tools check`、`pnpm check`；改过 agent 代码再跑 `pnpm check:py`

## 验收清单

1. 活动关卡分别运行 EX2-1、EX2-2、EX3-1、EX4-1，确认地图定位与扫荡次数设置。
2. 活动关卡次数达到 `0/3` 后正常返回主页，不误判普通 OCR。
3. 活动商店已部分售罄时跳过对应商品并购买其余商品。
4. 每次购买完成后，状态已刷新时不点击；状态未更新时只补点一次。
5. 商品全部售罄时直接返回主页；商品 10 购买完成后也能正常返回主页。
6. 任务从活动主页启动时直接进入对应活动流程；从游戏主页启动时进入活动；从其他界面启动时先返回主页再进入活动。
7. 与启动、领取奖励、资源刷取及 PVP 任务组合运行无冲突。
