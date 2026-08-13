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

Home → entry → battle UI → select opponent (custom: OCR 3 levels, pick lowest) → init count → challenge limit → start → begin combat (retry until in battle) → speed → loop → skip OCR → read result → exit → next fight or main.

`SelectOpponent` uses `SelectPVPOpponent` custom recognition to OCR 3 opponent slots and click the one with the lowest level. `BeginCombat` should retry if one click does nothing. Challenge limit ends the task. Automation does not guarantee wins.

## Precondition

The task entry is `PVP.CheckHomePage`: **the game must already be on the main screen** (`main_option`, 5 s timeout with no fallback — the task fails otherwise). Return to the main screen manually or run the "Launch Game" task first.

## Acceptance checklist

After changing this task, verify in order:

1. Opponent pick: three levels OCR correctly, lowest one is clicked
2. One full battle end-to-end: home → battle UI → start → settle → back to battle UI
3. Restart at any progress (in battle / settling / result screen) resumes or exits correctly
4. Daily challenge limit reached: notifies and returns home
5. Abnormal settlement (loss / disconnect) has a fallback path
6. Full regression: runs together with other tasks (startup, claim, farm) without conflict
