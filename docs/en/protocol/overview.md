---
order: 1
icon: ri:book-open-line
---

# Project & Resource Conventions

## Resolution baseline

ROI, coordinates, and templates use **1280×720**. Other resolutions are scaled by MaaFramework.

## Entry configs

| File               | Role                                        |
| ------------------ | ------------------------------------------- |
| `interface.json`   | Controllers, resources, task imports, agent |
| `maa-project.json` | Scaffold / release / runtime channels       |
| `tasks/*.json`     | GUI tasks: `entry`, options, overrides      |

Imported tasks: `startup`, `farm_resources`, `farm_remaining_stamina`, `event_stage`, `pvp`, `claim_rewards`, `stamina_info`. Group: `Daily`.

Task presets: `tasks/preset/Daily.json` (daily) and `tasks/preset/Activity.json` (activity). Selecting a preset in the GUI checks the matching task combo at once; the activity preset includes `活动关卡刷取` / `活动商店兑换`, which are enabled by default when chosen.

## Resource packs

| name     | Label    | Paths                        |
| -------- | -------- | ---------------------------- |
| base     | Official | `./resource/base`            |
| bilibili | Bilibili | base + `./resource/bilibili` |
| taptap   | TapTap   | base + `./resource/taptap`   |

## Pipeline & image paths

- Pipeline: `resource/<pack>/pipeline/*.json`
- Templates: `resource/<pack>/image/` (use **forward slashes** in JSON)
- OCR models: `resource/base/model/ocr/`

## Agent

Common dev invocation: `uv run python -u ./agent/bootstrap.py`.  
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

## Conventions

- Prefer recognition / freezes over hard delays
- Cover expected screens in `next`
- Register custom modules in `__init__.py`
- See root `AGENTS.md` for release and review rules
