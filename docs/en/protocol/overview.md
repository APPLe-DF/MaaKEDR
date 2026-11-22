---
order: 1
icon: ri:book-open-line
---

# Project & Resource Conventions

## Resolution baseline

ROI, coordinates, and templates use **1280×720**. Other resolutions are scaled by MaaFramework.

## Entry configs

| File               | Role                                             |
| ------------------ | ------------------------------------------------ |
| `interface.json`   | Controllers, resources, task imports, agent      |
| `maa-project.json` | Scaffold / release / runtime channels            |
| `tasks/*.json`     | GUI tasks: `entry`, options, `pipeline_override` |

Imported tasks in `interface.json`:

- `tasks/startup.json` — launch the game
- `tasks/farm_resources.json` — farm resources
- `tasks/farm_remaining_stamina.json` — remaining stamina farming (fixed drain-stamina mode)
- `tasks/event_stage.json` — event stage farming and event shop clearing
- `tasks/pvp.json` — PVP
- `tasks/claim_rewards.json` — claim rewards and claim remaining rewards
- `tasks/stamina_info.json` — stamina info (home-screen stamina and refill time)
- `tasks/send_gift.json` — send gift (gift friends until the daily quota is used up)

Task presets: `tasks/preset/Daily.json` (daily) and `tasks/preset/Activity.json` (activity). Selecting a preset in the GUI checks the matching task combo at once; the activity preset includes `活动关卡刷取` / `活动商店兑换`, which are enabled by default when chosen.

Task group: `Daily`.

## Task definition structure

A task file (`tasks/<task>.json`, excluding `tasks/preset/`) has exactly two top-level keys: `task` (task list) and
`option` (option table); preset files under `tasks/preset/*.json` use `preset` as their top-level key.

Task fields:

| Field               | Type     | Description                                                          |
| ------------------- | -------- | -------------------------------------------------------------------- |
| `name`              | string   | GUI label, written in Chinese directly (this project has no i18n)    |
| `entry`             | string   | Pipeline **node name**, not a file name                              |
| `default_check`     | bool     | Whether the task is checked by default; `false` tasks need enabling  |
| `description`       | string   | GUI tooltip                                                          |
| `group`             | string[] | Task group; this project uses `["Daily"]` everywhere                 |
| `option`            | string[] | Keys of top-level `option` entries, shown in array order             |
| `pipeline_override` | object   | Task-level override (independent of options), e.g. remaining stamina |

Option fields:

| Field          | Type   | Description                                  |
| -------------- | ------ | -------------------------------------------- |
| `type`         | string | This project only uses `switch` and `select` |
| `label`        | string | Widget label                                 |
| `description`  | string | Widget tooltip                               |
| `cases`        | case[] | Selectable cases                             |
| `default_case` | string | `case.name` selected by default              |

Case fields:

| Field               | Type     | Description                                                                        |
| ------------------- | -------- | ---------------------------------------------------------------------------------- |
| `name`              | string   | Option value, also the value referenced from `preset`                              |
| `label`             | string   | Dropdown text                                                                      |
| `description`       | string   | Tooltip                                                                            |
| `pipeline_override` | object   | Node patch merged into the pipeline when the case is selected                      |
| `option`            | string[] | Nested sub-options: expanded when a `switch` is Yes or the `select` case is chosen |

A `pipeline_override` patch only carries the fields to change (`enabled`, `next`, `roi`, `expected`,
`custom_recognition_param`, `custom_action_param`, …); everything else keeps the pipeline value.

## Option-to-node data flow

```text
GUI task + option selection
  → interface.json `import` loads tasks/*.json into one namespace
  → selected case's pipeline_override (plus the task-level pipeline_override) merges by node name
  → resource[].path loads resource/<pack>/pipeline/*.json in order (later packs override same-name nodes)
  → execution starts at the entry node; Custom nodes are handled by the agent subprocess
```

- Overrides can only target **existing** nodes: renaming a node requires updating `pipeline_override`
- Merge order and field-level rules follow [Project Interface V2](https://maafw.com/docs/3.3-ProjectInterfaceV2);
  this section only records which option patches which nodes

## Resource packs

| name     | Label    | Paths                        |
| -------- | -------- | ---------------------------- |
| base     | Official | `./resource/base`            |
| bilibili | Bilibili | base + `./resource/bilibili` |
| taptap   | TapTap   | base + `./resource/taptap`   |

Later paths override same-name pipeline / image files, which is how server differences are handled (launch package,
login text, entry images).

## Pipeline & image paths

- Pipeline: `resource/<pack>/pipeline/*.json`
- Templates: `resource/<pack>/image/` (use **forward slashes** in JSON)
- OCR models: `resource/base/model/ocr/`

## Agent

Common dev invocation: `uv run python agent/main.py`.  
Release packages switch to the embedded `python/python.exe` (see `tools/build-release.mjs`).

Release packages **no longer bundle** the MaaFramework native runtime: packaging strips
`python/Lib/site-packages/maa/bin/` out of the embedded interpreter, and the Agent reuses the
client's copy instead (MFAA: `runtimes/<platform>/native`, MXU: `maafw/`), saving tens of MiB per
package. Before importing anything from `maa`, `agent/main.py` calls `ensure_maafw_binary_path()`
from `agent/maafw_paths.py` to point `MAAFW_BINARY_PATH` at that directory; if the variable is
already set externally (e.g. the Android runner pointing at the APK's nativeLibraryDir) it is left
untouched.

So **`runtimes/` and the `maafw` pin in `pyproject.toml` must stay in sync**, otherwise the Agent
loads a native library that does not match its Python binding. Verify both after
`pnpm run sync:runtime`.

Custom module registration: put action / recognition modules under `agent/custom/` and register
them in the matching `__init__.py`.

## Conventions (aligned with AGENTS.md)

- Prefer recognition / freezes over hard `pre_delay` / `post_delay`
- Cover expected screens in `next`
- Fix unstable nodes with recognition / retries instead of blind `retry`
