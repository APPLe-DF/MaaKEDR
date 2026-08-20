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

Imported tasks: `startup`, `farm_resources`, `event_stage`, `pvp`, `claim_rewards`, `stamina_info`. Group: `Daily`.

## Resource packs

| name     | Label    | Paths                        |
| -------- | -------- | ---------------------------- |
| base     | Official | `./resource/base`            |
| bilibili | Bilibili | base + `./resource/bilibili` |
| taptap   | TapTap   | base + `./resource/taptap`   |

## Conventions

- Prefer recognition / freezes over hard delays
- Cover expected screens in `next`
- Register custom modules in `__init__.py`
- See root `AGENTS.md` for release and review rules
