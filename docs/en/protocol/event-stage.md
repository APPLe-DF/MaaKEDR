---
order: 6
icon: ri:fire-line
---

# Event Stage and Event Shop Protocol

This page documents the two daily tasks for the Flare event: farming event stages and clearing the event shop. The task definition is `tasks/event_stage.json`; both tasks share `EventStage.CheckHomePage` as their entry.

## Entries and options

| Task                | Entry                      | Options                                                                |
| ------------------- | -------------------------- | ---------------------------------------------------------------------- |
| Event stage farming | `EventStage.CheckHomePage` | `event_stage`, `event_sweep_count`                                     |
| Event shop clearing | `EventStage.CheckHomePage` | No additional options; fixed-guarantee items are handled automatically |

Supported stages are `EX2-1`, `EX2-2`, `EX3-1`, and `EX4-1`. `event_sweep_count` supports 1, 2, 3, or maximum sweeps. Event stages do not consume normal stamina and have a daily sweep limit of 3. If the task starts away from the home screen, `EventStage.CheckHomePage` uses `EventStage.ReturnToHome` to try to return home before checking again.

## Event stage farming

```text
CheckHomePage → Start → EventHub → ClickJourney
  → wait for the map → select the target EX stage (swipe if needed)
  → check remaining attempts → StagePrepare → set sweep count
  → PrepareBattle → StartBattle → BattleStage loop
  → attempts exhausted / map returned → ReturnMainFromStage → CheckReturnedHome
```

Key conventions:

- `FindTargetStage` uses Custom Recognition and OCR to locate the selected stage. If it is not visible, `DragFindStage` performs a horizontal swipe and retries according to the pipeline.
- `CheckStageEntryResult` recognizes `关卡通关次数已耗尽`; that result returns home through `ReturnMainFromStage`, while other results enter preparation.
- `CheckQuickBattleState` clicks the switch only when quick battle is disabled; an already-enabled switch proceeds directly to count setup.
- `BattleStage` handles victory screens, obtained-item dialogs, the next sweep, and exit. When the sweep loop returns to the map, `ReturnMainFromStage` returns to the home screen.
- `FindTargetStage` and `CheckAllSoldOut` use `context.override_next()` after reading the current UI to choose the next node; stage misses retry by swiping, while a shop that is not confirmed fully sold out checks items individually.

## Clearing the event shop

The shop task overrides `EventStage.EventHub` to `ClickBattleReport` and opens the `定额保障` (fixed-guarantee) tab:

```text
CheckHomePage → Start → EventHub → ClickBattleReport
  → SelectFixedGuarantee → CheckAllSoldOut
  → CheckSoldOut1 … CheckSoldOut10
  → buy available items (set MAX → confirm)
  → ReturnMainFromShop → CheckReturnedHome
```

- `CheckAllSoldOut` OCRs `已售罄` in shop ROI `[0,180,1280,540]`. If the shortcut check confirms the shop is sold out, the task returns home; otherwise it checks items one by one.
- `CheckSoldOut1` through `CheckSoldOut10` inspect each item-card ROI. Sold-out items are skipped; available items enter the corresponding `BuyItemN` node.
- `BuyItemN` clicks the item, then `ConfirmPurchaseN` recognizes and clicks confirmation. If confirmation is absent, `SkipConfirmPurchaseN` continues to the next item.
- Both purchase and skip routes for item 10 enter `ReturnMainFromShop`, which recognizes and clicks the back button before finishing at home.
- `CheckEventStage` and `CheckAllSoldOut` return a placeholder `AnalyzeResult` and call `context.override_next()` when the UI was read successfully but a state branch is needed; `None` is reserved for actual recognition failures.

## Code map

| Area                     | Path                                      |
| ------------------------ | ----------------------------------------- |
| Task and options         | `tasks/event_stage.json`                  |
| Event pipeline           | `resource/base/pipeline/event_stage.json` |
| Custom Recognition       | `agent/custom/recognition/event_stage.py` |
| Recognition registration | `agent/custom/recognition/__init__.py`    |
| Interface import         | `interface.json`                          |

## Acceptance checklist

1. Run EX2-1, EX2-2, EX3-1, and EX4-1 separately; verify stage location and sweep-count setup.
2. Verify that the exact `0/3` state returns home without false positives.
3. With some shop items already sold out, verify that they are skipped and remaining items are purchased.
4. After each purchase, verify that a refreshed state does not click and a missing marker triggers exactly one fallback click.
5. Verify that an entirely sold-out shop returns home and that item 10 also returns home after purchase.
6. Start from a non-home screen and verify the task returns home before entering the event flow.
7. Run together with startup, claim rewards, farm resources, and PVP without conflicts.
