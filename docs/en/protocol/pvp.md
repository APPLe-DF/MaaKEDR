---
order: 5
icon: ri:sword-line
---

# PVP Protocol

"PVP" enters the battle UI from the home screen and plays the configured number of battles in a loop: each battle
picks the lowest-level opponent, starts the fight, clicks 2x speed, reads the settlement score and rank, and returns
home when the battle count runs out. On season reset it first walks through a formation guide.

## Task entry

| Item     | Value                                              |
| -------- | -------------------------------------------------- |
| Task     | 玩家对战 (`tasks/pvp.json`, `default_check: true`) |
| Entry    | `PVP.EnsureHome` (always-matching gate node)       |
| Pipeline | `resource/base/pipeline/pvp.json`                  |
| Options  | `pvp_battle_count`                                 |

## Data flow

```text
tasks/pvp.json
  └─ option pvp_battle_count (select, 6 cases)
       → patches PVP.InitBattleCount.custom_action_param.target_count (1–6)
  → resource/base/pipeline/pvp.json
  → agent/custom/action/pvp.py (InitPVPBattleCount, CheckPVPBattleCount)
     agent/custom/action/general.py (ResetCount)
     agent/custom/recognition/pvp.py (SelectPVPOpponent, ReadPVPResult)
```

## Precondition

The task entry is `PVP.EnsureHome`, an always-matching gate node (`max_hit: 6`). The game should normally start on the main screen. When home cannot be confirmed, the shared return-to-home hub `Common.EnsureHome` takes over: it dismisses the "item obtained" overlay, clicks the top home button, clicks the generic back button. Once home is reached the original flow is retried, so the entry itself never fails just because the game is not on the main screen. The hub tries up to 10 rounds; the task fails only if home still cannot be reached.

## Options

| Option             | Widget | Default | Patched node                                           | Notes                                                                         |
| ------------------ | ------ | ------- | ------------------------------------------------------ | ----------------------------------------------------------------------------- |
| `pvp_battle_count` | select | 1次     | `PVP.InitBattleCount.custom_action_param.target_count` | `1`–`6`; 5 attempts per day, the 6th covers the premium first-loss protection |

The option only changes the counter's initial value and never touches flow nodes: `PVP.InitBattleCount` is a custom
action node whose `target_count` is stored in a module-level variable inside the agent process, and
`PVP.CheckBattleCount` decrements it after every battle.

## Typical flow

```text
PVP.EnsureHome (gate node) → PVP.CheckHomePage
  → PVP.Entry (battle entry)
       → parallel candidate: PVP.SeasonReset.ClickContinue (season reset popup; falls through to CheckBattleInterface)
  → PVP.CheckBattleInterface
  → PVP.InitBattleCount (custom: initialize remaining battles)
  → PVP.SelectOpponent (custom: OCR the 3 opponent levels, click the lowest)
       → PVP.CheckChallengeLimit (daily attempts exhausted → PVP.ReturnMain)
       → PVP.StartBattle
            → PVP.BeginCombat (retry until the battle really starts)
            → PVP.CheckInBattle
                 ├─ [JumpBack]PVP.Speed2x (click 2x speed once per battle)
                 ├─ [JumpBack]PVP.BeginCombat (click again if the battle did not start)
                 └─ PVP.BattleLoop (always-matching convergence, guarantees entering the battle loop)
            → PVP.CheckBattleEnd (OCR "跳过")
            → PVP.WaitSettlement → PVP.ReadResult (custom: read score / rank)
            → PVP.ExitResult → PVP.BackToBattleInterface (ResetCount clears the speed-button hit counter)
            → PVP.CheckBattleCount (custom: battles -1)
                 ├─ remaining → PVP.SelectOpponent
                 └─ exhausted → PVP.ReturnMain
```

## Season reset adaptation

The first entry of `PVP.Entry.next` is the season-reset chain: it normally does not match and only advances when it
does; each node's `next` starts with **itself** ("click again if the click did nothing"), and the last one returns to
`PVP.CheckBattleInterface`.

| Node                                  | OCR `expected`   | Action    |
| ------------------------------------- | ---------------- | --------- |
| `PVP.SeasonReset.ClickContinue`       | `点击任意处继续` | Click     |
| `PVP.SeasonReset.CheckEnterFormation` | `进入布阵`       | DoNothing |
| `PVP.SeasonReset.ClickEdit`           | `编辑`           | Click     |
| `PVP.SeasonReset.ClickQuickFormation` | `快速编队`       | Click     |
| `PVP.SeasonReset.CheckFormationCount` | `\d`             | DoNothing |
| `PVP.SeasonReset.ClickSave`           | `保存`           | Click     |
| `PVP.SeasonReset.ClickEnterFormation` | `进入布阵`       | Click     |
| `PVP.SeasonReset.ClickSavePosition`   | `保存`           | Click     |

If the guide wording changes after a season rollover, only the `expected` values above need updating; the flow
structure stays.

## Key conventions

- **SelectOpponent**: the `SelectPVPOpponent` custom recognition OCRs the three opponent ROIs for levels and clicks the lowest one. `rois` (three level-digit ROIs) and `click_positions` (three opponent-card click points) in `custom_recognition_param` are paired and must both have length 3; an opponent whose level cannot be read is skipped and the rest are still compared
- **InitBattleCount / CheckBattleCount**: both custom actions share one module-level counter (`_remaining` in `agent/custom/action/pvp.py`); `CheckBattleCount` decrements it on every hit and, at 0, uses `context.override_pipeline()` to rewrite `PVP.CheckBattleCount.next` to `[PVP.ReturnMain]`, forcing the task to finish after that battle
- **BeginCombat**: one click may do nothing; `next` / `on_error` must allow retries until `CheckInBattle` succeeds; `timeout: 30000` covers long loading (the loading screen keeps animating, so `post_wait_freezes` cannot be used)
- **Speed2x**: a `[JumpBack]` leaf node (no `next`): on a hit it clicks 2x speed and jumps back to `CheckInBattle`, which re-evaluates its `next` from the top. To get **exactly one click per battle** without depending on whether the button changes appearance after being clicked, `max_hit: 1` blocks the repeat hit from the jump-back (otherwise it would click over and over, possibly toggling the speed), and `PVP.BackToBattleInterface` — which every battle passes through after the settlement, with its action switched to `ResetCount` and `nodes: ["PVP.Speed2x"]` — clears the hit counter (`max_hit` accumulates per task run and is not reset per battle, so without this the second battle could not click). The last entry of `CheckInBattle.next` is the always-matching `BattleLoop`, so the battle loop is entered even when the speed button is not recognized or has been skipped by `max_hit`, instead of failing the task after a 20s timeout
- **BattleLoop**: long-timeout wait for the settlement (`timeout: 300000`); `on_error` falls back to `PVP.ReadResult`
- **ReadResult**: the `ReadPVPResult` custom recognition receives 4 ROIs (`result_roi`, `current_score_roi`, `score_change_roi`, `current_rank_roi`, `rank_change_roi`), and every OCR call passes `color_filter="PVP.TextFilter"`
- **PVP.TextFilter**: not a flow node but a `ColorMatch` node (`method: 4`, two `lower`/`upper` pairs, `count: 1000`) used as the color filter for the OCR calls above, suppressing background colors to improve digit recognition
- **Premium first-loss protection**: only when `score-change OCR is empty` **and** `the settlement text contains 败` is the battle treated as protected (no score loss). "Score unchanged" alone is not enough — OCR misses also read empty; real devices also show normal battles where the score stays the same but the rank still drops, so the rank must not be required to be unchanged either
- **Challenge limit**: a hit on `pvp/challenge_limit.png` goes straight to `PVP.ReturnMain`, ending the task on the home screen

## Files to touch when changing this flow

1. **Change the battle-count option**: `tasks/pvp.json` → `pvp_battle_count.cases[].pipeline_override.PVP.InitBattleCount.custom_action_param.target_count`
2. **Change opponent selection**: `resource/base/pipeline/pvp.json` → `PVP.SelectOpponent.custom_recognition_param.rois` / `click_positions` (change both, both length 3)
3. **Change settlement reading**: the 5 ROIs in `PVP.ReadResult.custom_recognition_param`; when digits are unstable, tune the `PVP.TextFilter` color range first
4. **Season wording change**: update the `expected` values of the `PVP.SeasonReset.*` nodes
5. **Change the counting logic**: `agent/custom/action/pvp.py` (`InitPVPBattleCount`, `CheckPVPBattleCount`)
6. **Validate**: `pnpm exec maa-tools check`, `pnpm check`; `pnpm check:py` after touching agent code

## Image directories

`resource/base/image/pvp/`: `entry.png` (battle entry), `battle_interface.png` (battle UI), `start_battle.png` (start battle), `begin_combat.png` (begin combat), `in_battle.png` (in battle), `speed_2x.png` (2x speed), `exit_result.png` (leave settlement), `challenge_limit.png` (attempts exhausted).

## Acceptance checklist

After changing this task, verify in order:

1. Opponent pick: three levels OCR correctly, lowest one is clicked
2. One full battle end-to-end: home → battle UI → start → settle → back to battle UI
3. Restart at any progress (in battle / settling / result screen) resumes or exits correctly
4. Daily challenge limit reached: notifies and returns home
5. Abnormal settlement (loss / disconnect) has a fallback path
6. Season reset: the first run on reset day walks through the formation guide and reaches the battle UI
7. Full regression: runs together with other tasks (startup, claim, farm) without conflict
8. Speed button: exactly one `PVP.Speed2x` hit per battle, followed by `BattleLoop`, and never a second one inside the same battle (on returning to the battle UI you should see `PVP.BackToBattleInterface` run `ResetCount` so the next battle can click again); with `PVP.Speed2x` temporarily set to `enabled: false` the flow still reaches the battle loop instead of failing the task

## Notes

Automation only performs the flow; it does not guarantee wins.
