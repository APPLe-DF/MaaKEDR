---
order: 6
icon: ri:fire-line
---

# Event Stage and Event Shop Protocol

This page documents the two daily tasks for the Flare event: farming event stages and clearing the event shop. The task definition is `tasks/event_stage.json`; the two tasks enter at `EventStage.EventHub` (stage) and `EventStage.EventHubShop` (shop) respectively, both check the activity home first and the game home second, and both must return to the game home when finished.

## Entries and options

| Task                | Entry                     | Default | Options                                                           |
| ------------------- | ------------------------- | ------- | ----------------------------------------------------------------- |
| Event stage farming | `EventStage.EventHub`     | off     | `event_stage`, `event_sweep_count`                                |
| Event shop clearing | `EventStage.EventHubShop` | off     | no extra options; fixed-guarantee items are handled automatically |

Supported stages are `EX2-1`, `EX2-2`, `EX3-1`, and `EX4-1`. Event stages do not consume normal stamina and have a daily sweep limit of 3; the prerequisite is having cleared all Flare event stages (including the EX ones).

Options and their patches:

| Option              | Widget | Default | Patched nodes                                                                                                                                                               |
| ------------------- | ------ | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `event_stage`       | select | EX2-1   | `EventStage.FindTargetStage.custom_recognition_param` (`stage_name` / `stage_roi`), `EventStage.ClickEP2.expected`; EX3-1 also patches `EventStage.WaitStageMapStable.next` |
| `event_sweep_count` | select | 3次     | `EventStage.SetBattleCount.custom_action_param.target_count` (`1` / `2` / `3` / `"max"`)                                                                                    |

Current target-stage → EP-tab mapping (decided by the `event_stage` option):

| Option  | `ClickEP2.expected` | Extra patch                                                                            |
| ------- | ------------------- | -------------------------------------------------------------------------------------- |
| `EX2-1` | `EP\.?2`            | —                                                                                      |
| `EX2-2` | `EP\.?3`            | —                                                                                      |
| `EX3-1` | `EP\.?4`            | `WaitStageMapStable.next = [ClickEP1, ClickEP2]` (leave the tab first, then come back) |
| `EX4-1` | `EP\.?4`            | —                                                                                      |

`ClickEP1` exists because the map may already be parked on the rightmost chapter: clicking EP.4 directly can do
nothing, so the flow clicks EP.1 first to move away, then clicks back.

## Data flow

```text
tasks/event_stage.json
  ├─ Event stage farming: option [event_stage, event_sweep_count]
  │    + task-level pipeline_override: EventStage.EventHub's custom_recognition_param / next (fixed entry routing)
  └─ Event shop clearing: no options, goes straight to EventStage.EventHubShop
  → resource/base/pipeline/event_stage.json
  → agent/custom/recognition/event_stage.py (CheckEventHub, CheckEventStage, CheckAllSoldOut,
     CheckShopItemSoldOut, CheckShopRefreshAfterPurchase)
     agent/custom/action/farm_resources.py (SetBattleCount, shared with farm resources)
```

Entry routing is three-state: `EventStage.EventHub` / `EventStage.EventHubShop` use the `CheckEventHub` custom
recognition to decide whether the current screen is the **activity home** (`flare_home.png`), the **game home**
(`more.png`, ROI `[1199,6,77,83]`), or **another screen**, then route via `context.override_next()` to the
activity flow entry / `EventStage.Start` / the gate node `EventStage.EnsureHome` (the shop task uses
`EventStage.EnsureHomeShop`). The gate hands over to the shared return-to-home hub `Common.EnsureHome` and retries once
home is reached.

## Event stage farming

```text
EventStage.EventHub (three-state routing)
  → EventStage.ClickJourney (OCR "踏上征途")
  → EventStage.WaitStageMapStable (wait for EP tabs to appear)
  → EventStage.ClickEP2 (OCR the EP tab and click; EX3-1 goes through ClickEP1 first)
  → EventStage.FindTargetStage (custom CheckEventStage: locate and click the target stage)
  → EventStage.StagePrepare (DirectHit split)
       → EventStage.CheckQuickBattleState (OCR "打开" → click the switch)
       → EventStage.CheckQuickBattleEnabled (OCR "关闭" → already on, go to count setup)
  → EventStage.SetBattleCount (custom SetBattleCount)
  → EventStage.PrepareBattle (OCR "准备(快速)战斗") → EventStage.StartBattle
  → EventStage.BattleStage (battle loop parent)
       → [JumpBack]ClickVictory / [JumpBack]ClickItemDialog
       → CheckQuickBattleState (another round)
       → ExitStageConfirm / CheckBackOnMap (back on the map)
  → EventStage.ReturnMainFromStage → EventStage.CheckReturnedHome (home screen, task success exit)

Home branch: EventHub miss → EventStage.CheckHomePage → EventStage.Start (click the "耀斑" wordmark)
Other screen: EventHub / CheckHomePage both miss → EventStage.EnsureHome → Common.EnsureHome → retry once home
```

Key conventions:

- `EventStage.FindTargetStage` uses `CheckEventStage` to OCR the target stage name inside `stage_roi` (default full
  screen `[0,0,1280,640]`) and clicks it on a hit; the recognizer itself decides the next step via `override_next`:
    - target not in view → `EventStage.DragFindStage` (drag the map left, `max_hit: 8`, then back to `FindTargetStage`)
    - stage card locked → `EventStage.StageLocked`
    - the badge above the card OCRs as `0/3` (attempts exhausted) → `EventStage.ReturnMainFromStage`
    - found normally → `EventStage.StagePrepare`
- `EventStage.WaitStageMapStable`'s `on_error` returns to `ClickJourney` (map did not load → click "踏上征途" again);
  `ClickEP2`'s `on_error` returns to `WaitStageMapStable`.
- `EventStage.BattleStage` handles victory screens, obtained-item dialogs, the next sweep and exit; `EventStage.CheckBackOnMap`
  confirms with OCR that the map is back, then `ReturnMainFromStage` returns home.
- `EventStage.CheckBattlePage` (OCR EP tabs, `max_hit: 3`) confirms "we really are back on the map" after an exit
  confirmation and retries itself on a miss.
- The exit is always `EventStage.CheckReturnedHome` (matches `more.png`, leaf node); if the home screen is not
  recognized, `on_error` → `EventStage.ReturnMain` clicks the HOME key again.

> [!NOTE]
> `EventStage.ClickEX2_1` ~ `ClickEX4_1`, `EventStage.CheckStageEntryResult`, `EventStage.ReturnToStageSelect` and
> `EventStage.EventHubRetry` are legacy nodes from the early "one click node per EX stage" design. The live flow now
> uses the single `CheckEventStage` recognizer and **no node references them**. Do not keep them in sync when changing
> the flow.

## Clearing the event shop

The shop task's entry is `EventStage.EventHubShop`, which routes to `EventStage.ClickBattleReport` and opens the `定额保障` (fixed-guarantee) tab:

```text
EventHubShop (three-state routing) → ClickBattleReport (OCR "战果上报")
  → SelectFixedGuarantee (OCR "定额保障")
  → CheckAllSoldOut (custom CheckAllSoldOut: roi [0,180,1280,540], total_items 10)
       ├─ all sold out → EventStage.ShopAllSoldOut → ReturnMainFromShop
       └─ not sold out → CheckSoldOut1 … CheckSoldOut10
  → BuyItemN (DirectHit clicks the card) → SetPurchaseMaxN (click "max") → ConfirmPurchaseN
       → WaitPurchaseClosedN → CheckShopRefreshAfterPurchaseN
            ├─ refreshed → next item CheckSoldOut(N+1)
            └─ not refreshed → RefreshShopAfterPurchaseN (one extra click) → next item
  → after item 10 → ReturnMainFromShop → CheckReturnedHome
```

- `CheckAllSoldOut` OCRs `已售罄` in the shop ROI; if the shortcut check confirms the shop is sold out, the task returns home; otherwise it checks items one by one.
- `CheckSoldOut1` ~ `CheckSoldOut10` are decided by `CheckShopItemSoldOut` per item-card ROI: the `sold_out_next` / `buy_next` parameters explicitly provide the "skip" and "buy" branches, so the routing is not written in the pipeline's `next`.
- `BuyItemN` clicks the card → `SetPurchaseMaxN` clicks "max" → `ConfirmPurchaseN` recognizes and clicks confirmation; if the confirm button is absent, `on_error` → `SkipConfirmPurchaseN` continues to the next item.
- After a purchase, `CheckShopRefreshAfterPurchaseN` decides whether the shop has refreshed; if not, `RefreshShopAfterPurchaseN` adds exactly one extra click to avoid double purchases.
- Both purchase and skip routes for item 10 enter `EventStage.ReturnMainFromShop` (`max_hit: 3`), then `CheckReturnedHome` confirms the home screen.
- `CheckEventHub`, `CheckEventStage`, `CheckAllSoldOut`, `CheckShopItemSoldOut` and `CheckShopRefreshAfterPurchase` return a placeholder `AnalyzeResult` (a box such as `(0,0,1,1)`) plus `context.override_next()` when the UI was read successfully but a branch must be chosen; only a real recognition failure returns `None`.

## Code map

| Area                              | Path                                                                      |
| --------------------------------- | ------------------------------------------------------------------------- |
| Task and options                  | `tasks/event_stage.json`                                                  |
| Event pipeline                    | `resource/base/pipeline/event_stage.json`                                 |
| Custom recognition                | `agent/custom/recognition/event_stage.py`                                 |
| Custom action (shared)            | `agent/custom/action/farm_resources.py`                                   |
| Recognition / action registration | `agent/custom/recognition/__init__.py`, `agent/custom/action/__init__.py` |
| Interface import                  | `interface.json`                                                          |
| Event images                      | `resource/base/image/event_stage/`, `resource/base/image/flare_home.png`  |

## Files to touch when changing this flow

1. **New event, new stage names / positions**: add or change a case in `tasks/event_stage.json`'s `event_stage.cases`,
   updating both `EventStage.FindTargetStage.custom_recognition_param.stage_name` and `EventStage.ClickEP2.expected`
2. **EP tab positions changed**: update the `roi` and `expected` of `EventStage.ClickEP1` / `ClickEP2`
3. **Sweep-count option**: `event_sweep_count.cases[].pipeline_override.EventStage.SetBattleCount.custom_action_param.target_count`
4. **Shop item count changed**: `CheckSoldOutN` / `BuyItemN` / `ConfirmPurchaseN` / `SkipConfirmPurchaseN` /
   `CheckShopRefreshAfterPurchaseN` / `RefreshShopAfterPurchaseN` are 10 matching groups — add or remove them as a set
   and update `CheckAllSoldOut`'s `total_items`
5. **Change event entry detection**: `activity_template` / `global_template` / `global_roi` of `CheckEventHub` (used in
   four parameter blocks: `EventStage.EventHub`, `EventHubShop`, `EventHubAfterClick`, `EventHubShopAfterClick`)
6. **Change custom logic**: `agent/custom/recognition/event_stage.py`
7. **Validate**: `pnpm exec maa-tools check`, `pnpm check`; `pnpm check:py` after touching agent code

## Acceptance checklist

1. Run EX2-1, EX2-2, EX3-1, and EX4-1 separately; verify stage location and sweep-count setup.
2. Verify that the exact `0/3` state returns home without false positives.
3. With some shop items already sold out, verify that they are skipped and remaining items are purchased.
4. After each purchase, verify that a refreshed state does not click and a missing marker triggers exactly one fallback click.
5. Verify that an entirely sold-out shop returns home and that item 10 also returns home after purchase.
6. Start from a non-home screen and verify the task returns home before entering the event flow.
7. Run together with startup, claim rewards, farm resources, and PVP without conflicts.
