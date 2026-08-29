---
title: "Troubleshooting"
order: 3
icon: "ri:bug-fill"
---

# Troubleshooting

## Log Files

| File                        | Description                             |
| --------------------------- | --------------------------------------- |
| `debug/agent-bootstrap.log` | Agent startup log                       |
| `maafw.log`                 | MaaFramework runtime log (project root) |
| `debug/`                    | Debug screenshots                       |

## Log Analysis Tools

Use [MaaLogAnalyzer](https://github.com/Windsland52/MAALogAnalyzer) to visually analyze `maafw.log`:

1. Download and launch [MaaLogAnalyzer](https://github.com/Windsland52/MAALogAnalyzer/releases)
2. Open `maafw.log` (project root) or the `debug/` directory
3. Filter by task/node and inspect each recognition record's `reco_id`, algorithm, `box`, and details; compare with the `debug/` screenshots to see the actual screen state

In addition, [MaaEvidenceKit](https://github.com/Windsland52/MaaEvidenceKit) is a deterministic evidence extraction and diagnostic toolkit for MaaFramework (CLI/SDK): it extracts locatable runtime and static evidence from logs and the project via MaaLogAnalyzer, outputting JSON/text for on-demand diagnosis by AI assistants such as Codex or Claude Code.

During development you can also use **Maa Pipeline Support** (VSCode extension) to watch recognition in real time (see [Environment Setup](./setup.md#debugging-tools)).

## Categories

### Startup Issues

#### Agent fails to start

Error: `Python >=3.13,<3.14 is required`

Cause: Wrong Python version. Project requires Python 3.13.x.

Fix: Use `uv` for Python management, run `uv sync`.

#### Custom module not registered

Error: Custom action/recognition returns `success: false`

Cause: Module not added to `RECOGNITION_MODULES` in `agent/custom/recognition/__init__.py`.

Fix: Add module name, e.g. `RECOGNITION_MODULES = ("farm_resources", "pvp", "stamina", "event_stage")` (check `agent/custom/recognition/__init__.py` for the actual list).

### Runtime Issues

#### Pipeline node stuck

Symptoms: Task hangs on a node until timeout.

Common causes:

1. Stale screenshot — screen hadn't settled when captured. Use `post_wait_freezes` to wait for the screen to settle, or add an intermediate recognition node to confirm the target screen appeared before continuing
2. ROI mismatch — Game UI changed, update ROI
3. Outdated template — UI changed, re-screenshot
4. Missing fallback — Critical nodes lack `on_error`

#### JumpBack node misbehavior

Cause: JumpBack node has `next` field. **JumpBack nodes must NOT have `next`.**

#### Stamina drain mode loops

Cause: `ExitStage` and `ExitStageConfirm` override points to `BattleStage` instead of exit path.

Fix: Check the clear stamina mode override in `tasks/farm_resources.json`.

### Recognition Issues

#### Stage not found

Symptoms: `CheckResourceStage` keeps failing

Common causes:

1. Stage locked — update `lock_icon.png` template
2. Stage list offset — confirm `SwipeToBegin` executed
3. Wrong `stage_index` or `resource_type` in params

#### Stamina popup not recognized

Cause: `no_stamina.png` template missing or wrong ROI.

#### Schema validation fails

Error: `must NOT have unevaluated properties`

Cause: Using unsupported field in the current schema.

Fix: Remove unsupported fields or update `tools/schema/` definitions.

### Log Analysis

Runtime logs (`maafw.log`) contain detailed recognition results:

```json
{
    "reco_id": 400000431,
    "algorithm": "Custom",
    "box": null,
    "detail": {"all": [], "best": null},
    "name": "PVP.ReadResult"
}
```

- `box: null` — no match
- `box: [x, y, w, h]` — match found
- `debug/` screenshots show actual screen state

## Verifying a Fix

Verify your fix before committing:

1. **Local checks**: `pnpm check` (also run `pnpm check:py` if Python code changed)
2. **Re-run in the GUI**: enable the affected task and run it 2–3 times to confirm the issue is gone
3. **Regression check**: inspect `debug/` screenshots and `maafw.log` to confirm recognition results match expectations and no error paths (`on_error`) fired unexpectedly
4. **Edge cases**: if the change touches flow branches, also verify adjacent states (startup/home/popups) are unaffected

If the fix changes behavior, update the corresponding [Protocol](../protocol/) docs and their acceptance checklists (e.g. [Event Stages](../protocol/event-stage.md)).
