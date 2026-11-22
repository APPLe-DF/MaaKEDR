---
title: "Troubleshooting"
order: 3
icon: "ri:bug-fill"
---

# Troubleshooting

Fixing bugs is an important part of development. This page follows the order "collect information → read the logs → classify and locate → verify the fix".

## Before You Start

Confirm the following with the reporter first — it saves a lot of guessing:

- A detailed description: when it happened, which task, how far the run got, expected vs. actual result
- Environment: emulator or physical device, resolution, MFAAvalonia / MXU version, resource pack version
- Files: `debug/maafw.log`, screenshots under `debug/`, and a screenshot of the screen that reproduces the problem

> Attach logs as files instead of pasting long text or sending screenshots of logs (see [CONTRIBUTING.md](https://github.com/APPLe-DF/MaaKEDR/blob/main/CONTRIBUTING.md)).

## Log Files

| Path              | Description                                                                                      |
| ----------------- | ------------------------------------------------------------------------------------------------ |
| `debug/maafw.log` | MaaFramework runtime log (under the working directory's `debug/`)                                |
| `debug/custom/`   | Agent custom-module logs (loguru file output, named by date)                                     |
| `debug/on_error/` | Error screenshots (`save_on_error` defaults to `true` in `resource/base/config/maa_option.json`) |

## Log Analysis Tools

### MaaLogAnalyzer

Use [MaaLogAnalyzer](https://github.com/Windsland52/MAALogAnalyzer) to visually analyze `maafw.log`. It can:

- Identify the MaaFramework version automatically
- Visualize the pipeline execution flow
- Locate failing and abnormal nodes quickly
- Analyze node match results and execution time

Steps:

1. Download and launch [MaaLogAnalyzer](https://github.com/Windsland52/MAALogAnalyzer/releases)
2. Import `debug/maafw.log`
3. Filter by task/node and inspect each recognition record's `reco_id`, algorithm, `box`, and details; compare with the `debug/` screenshots to see the actual screen state

### Manual Analysis (Fallback)

If MaaLogAnalyzer is not available, search the log directly. Each line has the form `[time][level][process][thread][source file][line] message`, with levels `TRC` / `DBG` / `INF` / `WRN` / `ERR`:

1. **Start with errors**: search for `[ERR]`; the line usually names the failing module (e.g. `PipelineParser`, `AdbControlUnit`)
2. **Search by node name**: node parsing logs `[name=<node name>]`; search the full name of the failing node and read the recognition/action records around it
3. **Task ends prematurely**: when `[ERR]` gives no clue, re-check whether the node's `next` and `on_error` cover the screen that actually appeared

### MaaEvidenceKit

[MaaEvidenceKit](https://github.com/Windsland52/MaaEvidenceKit) is a deterministic evidence extraction and diagnostic toolkit for MaaFramework (CLI/SDK): it extracts locatable runtime and static evidence from logs and the project via MaaLogAnalyzer, outputting JSON/text for on-demand diagnosis by AI assistants such as Codex or Claude Code.

### Maa Pipeline Support

During development you can also use **Maa Pipeline Support** (VSCode extension) to watch recognition in real time (see [Environment Setup](./setup.md#debugging-tools)).

## Categories

Classify the problem first: startup, resource loading, connection, runtime, or recognition. The category decides what to look for in the log and how to fix it; for user-facing resource-loading and connection failures, start with the troubleshooting order in [FAQ](../manual/faq.md).

### Startup Issues

#### Agent fails to start

Error: `Python >=3.13,<3.14 is required`

Cause: Wrong Python version. Project requires Python 3.13.x.

Fix: Use `uv` for Python management; make sure `uv` is installed and `uv sync --frozen` has been run.

#### Custom module not registered

Error: Custom action/recognition returns `success: false`

Cause: A new module was not added to `RECOGNITION_MODULES` in `agent/custom/recognition/__init__.py`, or not added to `ACTION_MODULES` in `agent/custom/action/__init__.py`.

Fix: Add the module name to the matching tuple. The two `__init__.py` files are the source of truth, e.g. `RECOGNITION_MODULES = ("farm_resources", "pvp", "stamina", "event_stage")`.

### Resource Loading Issues

Error: `key already exists [key=<node name>]` (`PipelineResMgr::parse_config`)

Cause: The same node name is defined in two pipeline files, or an overwrite install left stale resources behind.

Fix: First confirm `resource/base/pipeline/*.json` has no duplicate node names; when redeploying resources, clear the old `resource/` directory instead of overwriting it.

### Connection Issues

Error: `failed to connect [adb_path_=...] [adb_serial_=127.0.0.1:16384]` (`ControlUnitMgr::connect`)

Cause: The emulator is not running, the ADB path or address/port does not match the connection settings, or the port is taken by another instance.

Fix: Make sure the emulator is running with ADB debugging enabled; check the ADB path and address in the connection settings (see [Connection Settings](../manual/connection.md)); restart the emulator and reconnect if needed.

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

Cause: In the stamina drain mode, `FarmResources.ExitStageConfirm` has `next` pointing at `FarmResources.BattleStage` instead of the exit path.

Fix: Check the "clear stamina" mode override in `tasks/farm_resources.json` and make sure `FarmResources.ExitStageConfirm` points at `FarmResources.ReturnMainFromFarm` / `Common.CheckHomePage`.

### Recognition Issues

#### Stage not found

Symptoms: `CheckResourceStage` keeps failing

Common causes:

1. Stage locked — check the `farm_resources/lock_icon.png` template
2. Stage list offset — confirm `FarmResources.SwipeToBegin` executed
3. Wrong `stage_index` or `resource_type` in `custom_recognition_param`

#### Stamina popup not recognized

Cause: `farm_resources/no_stamina.png` template missing or wrong ROI, so the out-of-stamina popup cannot be detected.

#### Schema validation fails

Error: `must NOT have unevaluated properties`

Cause: Using a field the current schema does not support, e.g. `only_rec` together with TemplateMatch.

Fix: Remove unsupported fields after checking the schema definitions under `tools/schema/`.

## Log Analysis

Runtime logs (`debug/maafw.log`) contain detailed recognition results:

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
- `detail.all` — all recognition results
- `detail.best` — best match
- `debug/` screenshots show actual screen state

## Verifying a Fix

Verify your fix before committing:

1. **Local checks**: `pnpm check` (also run `pnpm check:py` if Python code changed)
2. **Re-run in the GUI**: enable the affected task and run it 2–3 times to confirm the issue is gone
3. **Regression check**: inspect `debug/` screenshots and `debug/maafw.log` to confirm recognition results match expectations and no error paths (`on_error`) fired unexpectedly
4. **Edge cases**: if the change touches flow branches, also verify adjacent states (startup/home/popups) are unaffected

If the fix changes behavior, update the corresponding [Protocol](../protocol/) docs and their acceptance checklists (e.g. [Event Stages](../protocol/event-stage.md)); describe the root cause, validation commands and results in the PR (see [CONTRIBUTING.md](https://github.com/APPLe-DF/MaaKEDR/blob/main/CONTRIBUTING.md)).
