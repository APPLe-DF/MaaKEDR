---
order: 6
icon: ri:fire-line
---

# 活动关卡与活动商店协议

本页记录耀斑活动的两个每日任务：活动关卡刷取与活动商店兑换。任务定义位于 `tasks/event_stage.json`，共用入口先检查活动主页，再检查游戏主页；两个任务结束后都必须返回游戏主页。

## 任务入口与选项

| 任务         | 入口                  | 选项                               |
| ------------ | --------------------- | ---------------------------------- |
| 活动关卡刷取 | `EventStage.EventHub` | `event_stage`、`event_sweep_count` |
| 活动商店兑换 | `EventStage.EventHub` | 无额外选项，自动处理定额保障商品   |

活动关卡当前支持 `EX2-1`、`EX2-2`、`EX3-1`、`EX4-1`。`event_sweep_count` 支持 1、2、3 次及最大次数；活动关卡每日扫荡上限为 3，且不消耗普通体力。两个活动任务都从 `EventStage.EventHub` 开始：先用活动按钮文字（「踏上征途」或「战果上报」）确认当前已在活动主页；未命中时再用一次固定区域模板确认游戏主页；两者都未命中才通过 `EventStage.ReturnToHome` 返回主页后重试。

## 活动关卡刷取流程

```text
EventHub（活动文字命中）→ ClickJourney
  → 等待地图稳定 → 选择目标 EX 关卡（必要时拖动地图）
  → 检查次数 → StagePrepare → 设置快速战次数
  → PrepareBattle → StartBattle → BattleStage 循环
  → 次数耗尽/回到地图 → ReturnMainFromStage → CheckReturnedHome

EventHub（未命中）→ CheckHomePage（主页模板命中）→ Start → EventHub
EventHub、CheckHomePage 均未命中 → ReturnToHome → CheckHomePage
```

关键约定：

- `FindTargetStage` 使用 Custom Recognition + OCR 定位目标关卡；目标暂不可见时通过 `DragFindStage` 单次横向滑动后重试，最多按 pipeline 配置重试。
- `CheckStageEntryResult` 识别 `关卡通关次数已耗尽`；命中后经 `ReturnMainFromStage` 返回主页，否则进入准备流程。
- `CheckQuickBattleState` 只在快速战关闭时点击开关，已开启时直接进入次数设置。
- `BattleStage` 处理胜利画面、获得物品弹窗、下一轮快速战与退出；快速战结束回到地图后经 `ReturnMainFromStage` 返回主页。
- `FindTargetStage` 和 `CheckAllSoldOut` 会在已成功读取界面后通过 `context.override_next()` 选择后续节点；未命中目标关卡或未确认全部售罄时分别进入拖动重试或逐件检查。

## 活动商店清空

任务选项将 `EventStage.EventHub` 路由到 `ClickBattleReport`，进入活动商店的「定额保障」页：

```text
EventHub（活动文字命中）→ ClickBattleReport
  → SelectFixedGuarantee → CheckAllSoldOut
  → CheckSoldOut1 … CheckSoldOut10
  → 购买可用商品（设置 MAX → 确认购买）
  → ReturnMainFromShop → CheckReturnedHome

活动入口识别失败时，`EventStage.Start` 也会走 `EventStage.ReturnMain`，避免停在非主页状态。
```

- `CheckAllSoldOut` 在商店区域 `[0,180,1280,540]` OCR「已售罄」；确认达到快捷判断阈值时提示全部售罄并返回主页，否则进入逐件检查。
- `CheckSoldOut1` 至 `CheckSoldOut10` 按商品卡片 ROI 判断单件商品：已售罄则跳过，未售罄则进入对应 `BuyItemN`。
- `BuyItemN` 点击商品卡片，随后由 `ConfirmPurchaseN` 识别并点击确认；确认失败时走对应的 `SkipConfirmPurchaseN`，继续检查下一件。
- 商品 10 的购买或跳过路径都进入 `ReturnMainFromShop`，再识别并点击返回按钮回到主页。
- `CheckEventStage`、`CheckAllSoldOut` 在已读取界面但需要选择分支时返回占位 `AnalyzeResult` 并调用 `context.override_next()`；真正的识别失败才返回 `None`。

## 代码位置

| 内容               | 路径                                      |
| ------------------ | ----------------------------------------- |
| 任务与选项         | `tasks/event_stage.json`                  |
| 活动 Pipeline      | `resource/base/pipeline/event_stage.json` |
| Custom Recognition | `agent/custom/recognition/event_stage.py` |
| Recognition 注册   | `agent/custom/recognition/__init__.py`    |
| Interface import   | `interface.json`                          |

## 验收清单

1. 活动关卡分别运行 EX2-1、EX2-2、EX3-1、EX4-1，确认地图定位与扫荡次数设置。
2. 活动关卡次数达到 `0/3` 后正常返回主页，不误判普通 OCR。
3. 活动商店已部分售罄时跳过对应商品并购买其余商品。
4. 每次购买完成后，状态已刷新时不点击；状态未更新时只补点一次。
5. 商品全部售罄时直接返回主页；商品 10 购买完成后也能正常返回主页。
6. 任务从活动主页启动时直接进入对应活动流程；从游戏主页启动时进入活动；从其他界面启动时先返回主页再进入活动。
7. 与启动、领取奖励、资源刷取及 PVP 任务组合运行无冲突。
