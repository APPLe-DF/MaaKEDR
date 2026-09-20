---
order: 5
icon: ri:sword-line
---

# PVP

| Item     | Value                             |
| -------- | --------------------------------- |
| Task     | `tasks/pvp.json`                  |
| Pipeline | `resource/base/pipeline/pvp.json` |

## Flow

Home → entry → battle UI → select opponent (custom: OCR 3 levels, pick lowest) → init count → challenge limit → `StartBattle` → begin combat (retry until in battle) → `CheckInBattle` → `[JumpBack]Speed2x` (clicks 2x speed, then jumps back) → `BattleLoop` → skip OCR → read result → exit → `BackToBattleInterface` (runs `ResetCount` to clear the speed-button hit counter) → next fight or main.

`SelectOpponent` uses `SelectPVPOpponent` custom recognition to OCR 3 opponent slots and click the one with the lowest level. `BeginCombat` should retry if one click does nothing. Challenge limit ends the task. Automation does not guarantee wins.

`Speed2x` is a `[JumpBack]` leaf node (it has no `next`): on a hit it clicks 2x speed and jumps back to `CheckInBattle`, which re-evaluates its `next` from the top. To get **exactly one click per battle** without depending on whether the button changes appearance after being clicked, `max_hit: 1` blocks the repeat hit from the jump-back (otherwise it would click over and over, possibly toggling the speed), and `PVP.BackToBattleInterface` — which every battle passes through after the settlement, with its action switched to `ResetCount` — clears the `PVP.Speed2x` hit counter (`max_hit` accumulates per task run and is not reset per battle, so without this the second battle could not click). The last entry of `CheckInBattle.next` is the always-matching `BattleLoop`, so the battle loop is entered even when the speed button is not recognized or has been skipped by `max_hit`, instead of failing the task after the 20s timeout.

## Precondition

The task entry is `PVP.EnsureHome`, an always-matching gate node. The game should normally start on the main screen. When home cannot be confirmed, the shared return-to-home hub `Common.EnsureHome` takes over: it dismisses the "item obtained" overlay, clicks the top home button, clicks the generic back button, and finally sends the system back key. Once home is reached the original flow is retried, so the entry itself never fails just because the game is not on the main screen. The hub tries up to 10 rounds; the task fails only if home still cannot be reached.

## Acceptance checklist

After changing this task, verify in order:

1. Opponent pick: three levels OCR correctly, lowest one is clicked
2. One full battle end-to-end: home → battle UI → start → settle → back to battle UI
3. Restart at any progress (in battle / settling / result screen) resumes or exits correctly
4. Daily challenge limit reached: notifies and returns home
5. Abnormal settlement (loss / disconnect) has a fallback path
6. Full regression: runs together with other tasks (startup, claim, farm) without conflict
7. Speed button: exactly one `PVP.Speed2x` hit per battle, followed by `BattleLoop`, and never a second one inside the same battle (on returning to the battle UI you should see `PVP.BackToBattleInterface` run `ResetCount` so the next battle can click again); with `PVP.Speed2x` temporarily set to `enabled: false` the flow still reaches the battle loop instead of failing the task
