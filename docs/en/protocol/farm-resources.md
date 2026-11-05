---
order: 4
icon: ri:treasure-map-line
---

# Farm Resources Protocol

"Farm resources" and "remaining stamina farming" share one pipeline (`resource/base/pipeline/farm_resources.json`):
home screen → battle entry → pick board / resource type / stage → set quick-battle count → battle loop → exit when
stamina runs out. The two tasks differ only in their option tree and the default battle mode.

## Task entry

| Task                             | Entry                      | Definition                          | Pipeline                                     | Default | Options                                      |
| -------------------------------- | -------------------------- | ----------------------------------- | -------------------------------------------- | ------- | -------------------------------------------- |
| 资源刷取 (farm resources)        | `FarmResources.EnsureHome` | `tasks/farm_resources.json`         | `resource/base/pipeline/farm_resources.json` | on      | `farm_battle_mode`, `farm_category`          |
| 剩余体力刷取 (remaining stamina) | `FarmResources.EnsureHome` | `tasks/farm_remaining_stamina.json` | same                                         | off     | `remaining_farm_category` (fixed drain mode) |

## Data flow

```text
tasks/farm_resources.json
  ├─ task 资源刷取: option = [farm_battle_mode, farm_category]
  └─ option tree (expanded layer by layer through case.option)
       farm_battle_mode ─┬─ 单次战斗 (single battle) → farm_battle_count (1–6 / max)
                         └─ 清空体力 (drain stamina) → patches 6 nodes directly
       farm_category ────┬─ 资源收集 (resource collect) → farm_resource_type → farm_resource_stage_1..4
                         └─ 技能演练 (skill training) → farm_skill_type → farm_skill_stage_1..2
  → patched nodes: FarmResources.Start / SelectResourceType / SelectSkillType /
                   ClickStage / ClickSkillStage / CheckSkillLocked /
                   SetBattleCount / QuickBattle / CheckStamina / BattleStage / ExitStageConfirm
  → resource/base/pipeline/farm_resources.json
  → agent/custom/action/farm_resources.py (SetBattleCount, ReduceBattleCount)
     agent/custom/recognition/farm_resources.py (CheckResourceStage)
```

## Option structure

```text
farm_battle_mode (battle mode)
  ├─ 单次战斗 (single battle) → farm_battle_count (1–6 / max)
  └─ 清空体力 (drain stamina) → pipeline_override (max count + count reduction + exit path)

farm_category (board)
  ├─ 资源收集 (resource collect) → farm_resource_type → farm_resource_stage_1~4
  └─ 技能演练 (skill training) → farm_skill_type → farm_skill_stage_1~2
```

## Options and overrides

| Option                     | Widget | Default               | Patched nodes                                                                                                                           | Patch content                                                                                                                                       |
| -------------------------- | ------ | --------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `farm_battle_mode`         | select | 单次战斗              | drain case patches `FarmResources.QuickBattle` / `ClickStage` / `ClickSkillStage` / `CheckStamina` / `BattleStage` / `ExitStageConfirm` | see "Battle modes · Drain stamina"                                                                                                                  |
| `farm_battle_count`        | select | 1次                   | `FarmResources.SetBattleCount`                                                                                                          | `custom_action_param.target_count` = `1`–`6` or `"max"`                                                                                             |
| `farm_category`            | select | 资源收集              | `FarmResources.Start`                                                                                                                   | `next` = `[FarmResources.ResourceCollect]` / `[FarmResources.SkillTraining]`                                                                        |
| `farm_resource_type`       | select | 特别军费行动          | `FarmResources.SelectResourceType`                                                                                                      | `next` → `SelectSpecialFunds` / `SelectPhysicalTraining` / `SelectUnitRating` / `SelectVehicleDrill`                                                |
| `farm_skill_type`          | select | 基础技能演练          | `FarmResources.SelectSkillType`                                                                                                         | `next` → `SelectBasicSkill` / `SelectAdvancedSkill`                                                                                                 |
| `farm_resource_stage_1..4` | select | 1-1 / 2-1 / 3-1 / 4-1 | `FarmResources.ClickStage` (stages 4 and 5 also patch `FarmResources.SelectStage`)                                                      | `custom_recognition_param` = `stage_name` / `stage_index` / `resource_type`; stages 4/5 add `next → SwipeToRight`                                   |
| `farm_skill_stage_1..2`    | select | 基础训练1 / 专业训练1 | `FarmResources.ClickSkillStage`, `FarmResources.CheckSkillLocked`, `FarmResources.SelectSkillStage`                                     | `roi` + `expected` on `ClickSkillStage`; `CheckSkillLocked.roi` for stages 2/3; stage 1 also narrows `SelectSkillStage.next` to `[ClickSkillStage]` |

## Remaining stamina

| Item       | Value                                                                                        |
| ---------- | -------------------------------------------------------------------------------------------- |
| Task       | 剩余体力刷取                                                                                 |
| Entry      | `FarmResources.EnsureHome` (reuses the farm flow)                                            |
| Definition | `tasks/farm_remaining_stamina.json`                                                          |
| Options    | its own tree prefixed `remaining_*`, starting at `remaining_farm_category`                   |
| Override   | **task-level** `pipeline_override` (option-independent), identical to the drain-stamina case |

A copy of Farm Resources locked to **drain-stamina** mode: the task-level `pipeline_override` carries max count (`SetBattleCountMax`), stamina-low count reduction (`CheckStamina → CheckCountOCR / ReduceCount`) and the exit path. It uses its own independent option set `remaining_farm_category` (board → resource type → stage, separate from `farm_resources`), meant to drain whatever stamina is left at that point, usually enabled via task presets rather than checked by default.

## Resource-collect stages

| Board                            | Stage option key        | Stage numbering             |
| -------------------------------- | ----------------------- | --------------------------- |
| 特别军费行动 (special funds)     | `farm_resource_stage_1` | **1-1 … 1-5** (has stage 5) |
| 作战体能训练 (physical training) | `farm_resource_stage_2` | **2-1 … 2-4** (no stage 5)  |
| 兵种能力评级 (unit rating)       | `farm_resource_stage_3` | **3-1 … 3-4** (no stage 5)  |
| 载具对抗演练 (vehicle drill)     | `farm_resource_stage_4` | **4-1 … 4-5** (has stage 5) |

The stage is passed through `FarmResources.ClickStage`'s `custom_recognition_param`:

```json
{
    "stage_name": "1-1",
    "stage_index": 1,
    "resource_type": "特别军费行动"
}
```

`CheckResourceStage` (`agent/custom/recognition/farm_resources.py`) looks up a built-in ROI table (`RESOURCE_STAGES`) by
`resource_type` + `stage_index` to locate the stage card, then OCRs `stage_name` to confirm. For `stage_index > 1` it
first checks the lock icon inside that ROI (`lock_template`, default `farm_resources/lock_icon.png`) and routes to
`FarmResources.StageLocked` on a hit.

Stages 4 and 5 (when the list has to scroll) get `next → SwipeToRight` injected into `SelectStage`; before selecting a
stage, `SelectStage` normally goes through `SwipeToBegin` to reset the list to the leftmost position.

## Skill training

| Board                   | Stage option         | Stage names  |
| ----------------------- | -------------------- | ------------ |
| 基础技能演练 (basic)    | `farm_skill_stage_1` | 基础训练 1–3 |
| 专业技能演练 (advanced) | `farm_skill_stage_2` | 专业训练 1–3 |

Stages are located by `ClickSkillStage`'s ROI + OCR `expected` (the base value `expected: "farm_stage"` is a
placeholder; the real value is injected by the option). Locked stages are detected by `CheckSkillLocked` with the
`skill_lock_icon.png` template, whose ROI is also injected per stage by the option.

`SelectSkillStage.next` uses **parallel candidates** (`CheckSkillLocked` → `ClickSkillStage`): a lock-icon hit means
"locked, stop", a miss falls through to `ClickSkillStage` and enters the stage. Do not rely on `on_error` on candidate
nodes (a candidate recognition failure does not trigger its own `on_error` and ends in a dead-loop timeout — see
`docs/*/develop/pipeline.md`). For stage 1 the option narrows `SelectSkillStage.next` to `[ClickSkillStage]`, skipping
the lock check.

## Battle modes

> **Termination semantics**: both modes end when stamina runs out. After the `BattleStage` loop returns to the stage screen, the next battle starts if stamina remains; only the "no stamina" popup (or the quick-battle button disappearing) ends the task.

### Single battle

`QuickBattle` → `SetBattleCount` (from the option's `target_count`) → `PrepareBattle` → stamina check → start → `BattleStage` loop.

The battle-count option controls the number of battles **per batch**; the task as a whole farms until stamina runs out (the `no_stamina` popup) rather than stopping after exactly N battles.

### Drain stamina

`pipeline_override` patches these 6 nodes:

| Node                             | Patched `next`                                                                                                                                                              |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FarmResources.QuickBattle`      | `[FarmResources.SetBattleCountMax]`                                                                                                                                         |
| `FarmResources.ClickStage`       | `[FarmResources.QuickBattle, FarmResources.SetBattleCountMax]`                                                                                                              |
| `FarmResources.ClickSkillStage`  | `[FarmResources.QuickBattle, FarmResources.SetBattleCountMax]`                                                                                                              |
| `FarmResources.CheckStamina`     | `[FarmResources.CheckCountOCR, FarmResources.ReduceCount]`                                                                                                                  |
| `FarmResources.BattleStage`      | `[[JumpBack]FarmResources.ClickVictory, [JumpBack]FarmResources.ClickItemDialog, FarmResources.QuickBattle, FarmResources.ReturnMainFromFarm, FarmResources.PrepareBattle]` |
| `FarmResources.ExitStageConfirm` | `[FarmResources.ReturnMainFromFarm, Common.CheckHomePage]`                                                                                                                  |

Count-reduction loop: low stamina → `ReduceCount` (`ReduceBattleCount`, one step at a time) → back to `PrepareBattle`
to retry; `CheckCountOCR` uses OCR `^1$` to detect that the count reached 1 → `ReductionDone` → `ExitStageConfirm`.
When the count is already minimal, the action returns failure and its `on_error` points at `FarmResources.NoStamina`,
which exits the same way.

Unlike single-battle mode, it squeezes out the remaining stamina instead of wasting it: the count is reduced by one each time until it reaches 1, then `ReductionDone` exits.

## Precondition

The task entry is `FarmResources.EnsureHome`, an always-matching gate node. The game should normally start on the main screen. When home cannot be confirmed, the shared return-to-home hub `Common.EnsureHome` takes over: it dismisses the "item obtained" overlay, clicks the top home button, clicks the generic back button. Once home is reached the original flow is retried, so the entry itself never fails just because the game is not on the main screen. The hub tries up to 10 rounds; the task fails only if home still cannot be reached.

If `FarmResources.Start` (home → battle entry) fails, its `on_error` also points at `FarmResources.EnsureHome`, i.e.
return home and rerun the whole list.

## Key nodes

| Node                                                   | Recognition / action                                          | Notes                                                                                           |
| ------------------------------------------------------ | ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `FarmResources.EnsureHome`                             | DirectHit (`max_hit: 6`)                                      | Entry gate; `[JumpBack]Common.EnsureHome` sits last in `next`                                   |
| `FarmResources.CheckHomePage`                          | TemplateMatch `more.png` / Click                              | Confirm home and click the screen center to clear leftover popups                               |
| `FarmResources.Start`                                  | TemplateMatch `battle_entry.png` / Click                      | Home → battle entry; `on_error` → `EnsureHome`                                                  |
| `FarmResources.ResourceCollect` / `SkillTraining`      | tab template / Click                                          | Enter the "resource collect" / "skill training" board                                           |
| `FarmResources.SelectResourceType` / `SelectSkillType` | DirectHit                                                     | Pure routing nodes; `next` is rewritten by options                                              |
| `FarmResources.SelectSpecialFunds` and the other 3     | template / Click                                              | Pick the resource type (special funds / physical training / unit rating / vehicle drill)        |
| `FarmResources.SelectStage`                            | DirectHit                                                     | Pure routing node; stages 4/5 get `next → SwipeToRight` from the option                         |
| `FarmResources.SwipeToBegin` / `SwipeToRight`          | DirectHit / Swipe                                             | Reset the stage list to the left / swipe to the right                                           |
| `FarmResources.ClickStage`                             | Custom `CheckResourceStage` / Click (`timeout: 10000`)        | Recognize and click the stage; `on_error` → `StageLocked`                                       |
| `FarmResources.SelectSkillStage`                       | DirectHit                                                     | Skill stage entry (parallel candidates `CheckSkillLocked` → `ClickSkillStage`)                  |
| `FarmResources.CheckSkillLocked`                       | TemplateMatch `skill_lock_icon.png`                           | Hit = stage locked, stop; miss = clickable                                                      |
| `FarmResources.ClickSkillStage`                        | OCR `expected` (injected by option) / Click                   | Click the skill stage                                                                           |
| `FarmResources.QuickBattle`                            | TemplateMatch `quick_battle.png` / Click (`max_hit: 3`)       | Click quick battle; `on_error` → `QuickBattleLocked`                                            |
| `FarmResources.SetBattleCount`                         | Custom `SetBattleCount`                                       | Click plus / minus to set the count                                                             |
| `FarmResources.SetBattleCountMax`                      | Custom `SetBattleCount` (`target_count: "max"`)               | Set the maximum count (drain-stamina mode)                                                      |
| `FarmResources.PrepareBattle`                          | TemplateMatch `prepare_battle.png` / Click                    | Click prepare quick battle                                                                      |
| `FarmResources.CheckStamina`                           | TemplateMatch `no_stamina.png` / Click                        | No-stamina popup                                                                                |
| `FarmResources.ReduceCount`                            | Custom `ReduceBattleCount`                                    | Reduce the count on low stamina; `on_error` → `NoStamina`                                       |
| `FarmResources.CheckCountOCR`                          | OCR `^1$`                                                     | Count reached 1 (loop termination condition)                                                    |
| `FarmResources.ReductionDone`                          | DirectHit                                                     | Already minimal → `ExitStageConfirm`                                                            |
| `FarmResources.NoStamina`                              | DirectHit                                                     | No stamina → `ExitStageConfirm`                                                                 |
| `FarmResources.ExitStageConfirm`                       | TemplateMatch `exit_stage_confirm.png` / Click (`max_hit: 5`) | Click the stage-exit button; `on_error` → `[JumpBack]Common.EnsureHome`                         |
| `FarmResources.ReturnMainFromFarm`                     | TemplateMatch `return_main.png` / Click                       | Return home                                                                                     |
| `FarmResources.StartBattle` / `BattleStage`            | template / DirectHit                                          | Start the battle, battle-loop parent node                                                       |
| `FarmResources.ClickVictory` / `ClickItemDialog`       | template / Click                                              | Victory screen / item-obtained popup                                                            |
| `FarmResources.StageLocked` / `QuickBattleLocked`      | DirectHit                                                     | Locked notices (`focus` wording is deliberately neutral so GUIs do not mark the task as failed) |

Custom implementations: `SetBattleCount` and `ReduceBattleCount` live in `agent/custom/action/farm_resources.py`;
`CheckResourceStage` lives in `agent/custom/recognition/farm_resources.py`, registered in the matching `__init__.py`.

## Files to touch when changing this flow

1. **Add a stage to an existing board**: add `stage index → ROI` for that board in `RESOURCE_STAGES`
   (`agent/custom/recognition/farm_resources.py`), then add a case to `farm_resource_stage_N.cases` in
   `tasks/farm_resources.json` with the `stage_name` / `stage_index` / `resource_type` triple
2. **Add a board**: add the board key to `RESOURCE_STAGES` → add a case to `farm_resource_type.cases` and point
   `SelectResourceType.next` at the new node → add the board entry template node in the pipeline
3. **Add a skill stage**: add a case to `farm_skill_stage_N.cases` with `ClickSkillStage.roi` + `expected`; add
   `CheckSkillLocked.roi` if the stage can be locked
4. **Keep "remaining stamina farming" in sync**: `tasks/farm_remaining_stamina.json` has its own `remaining_*` option
   tree, so a new stage/board must be added in **both** files, otherwise that task cannot select it
5. **Change the battle-count option**: `farm_battle_count.cases[].custom_action_param.target_count` (`1`–`6` or `"max"`)
6. **Change the drain-stamina logic**: patch both the drain case in `farm_resources` and the task-level
   `pipeline_override` in `farm_remaining_stamina` (currently identical)
7. **Validate**: `pnpm exec maa-tools check`, `pnpm check`; `pnpm check:py` after touching agent code

## Image directories

`resource/base/image/farm_resources/` (entries, quick battle, prepare, victory, locks, …):

- Entries and tabs: `battle_entry.png`, `resource_collect_tab.png`, `skill_training_tab.png`
- Resource types: `special_funds.png`, `physical_training.png`, `unit_rating.png`, `vehicle_drill.png`
- Skill types: `basic_skill.png`, `advanced_skill.png`, `skill_lock_icon.png`
- Battle flow: `quick_battle.png`, `prepare_battle.png`, `start_battle.png`, `battle_victory.png`, `exit_stage_confirm.png`, `no_stamina.png`
- Count setup: `max_count.png` (the "max" button), `lock_icon.png` (resource-stage lock icon)

## Acceptance checklist

After changing this task, verify in order:

1. One stage per resource board runs alone (including 4/5 stages that need swiping)
2. Single-battle mode end-to-end: finishes after the configured count
3. Drain-stamina mode: count is reduced when stamina is low, exits normally at 1
4. Victory screen / item popup / quick-battle button verified separately
5. Locked stage (grey text): notifies "not unlocked" instead of hanging
6. Both skill-training boards run once, confirming `expected` and the lock ROIs apply
7. "Remaining stamina farming" runs once per stage using its `remaining_*` options
8. Full regression: runs together with other tasks (startup, claim, PVP) without conflict
