---
order: 4
icon: ri:treasure-map-line
---

# Farm Resources

| Item     | Value                                        |
| -------- | -------------------------------------------- |
| Entry    | `FarmResources.CheckHomePage`                |
| Task     | `tasks/farm_resources.json`                  |
| Pipeline | `resource/base/pipeline/farm_resources.json` |

## Stages (resource collect)

| Type              | Stages                 |
| ----------------- | ---------------------- |
| Special funds     | **1-1 … 1-5**          |
| Physical training | **2-1 … 2-4** (no 2-5) |
| Unit rating       | **3-1 … 3-4** (no 3-5) |
| Vehicle drill     | **4-1 … 4-5**          |

## Modes

> **Termination semantics**: both modes end when stamina runs out. After the `BattleStage` loop returns to the stage screen, the next battle starts if stamina remains; only the "no stamina" popup (or the quick-battle button disappearing) ends the task.

- **Single battle**: `SetBattleCount` from option (1–6 / max). The count is the battles per batch, not a hard task limit — the task farms until stamina is insufficient.
- **Drain stamina**: `SetBattleCountMax`, `ReduceCount` on low stamina (count −1 per cycle until 1, then exit via `ReductionDone`), exit via confirm → main. Unlike single-battle mode, it squeezes out the remaining stamina instead of wasting it.

Skill training: basic / advanced stages via OCR + lock checks. Custom actions: battle count helpers in `agent/custom/`.

## Precondition

The task entry is `FarmResources.CheckHomePage`: **the game must already be on the main screen** (`main_option`, 5 s timeout with no fallback — the task fails otherwise). Return to the main screen manually or run the "Launch Game" task first.

## Acceptance checklist

After changing this task, verify in order:

1. One stage per resource board runs alone (including 4/5 stages that need swiping)
2. Single-battle mode end-to-end: finishes after the configured count
3. Drain-stamina mode: count is reduced when stamina is low, exits normally at 1
4. Victory screen / item popup / quick-battle button verified separately
5. Locked stage (grey text): notifies "not unlocked" instead of hanging
6. Full regression: runs together with other tasks (startup, claim, PVP) without conflict
