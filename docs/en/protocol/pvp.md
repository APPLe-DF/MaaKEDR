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
