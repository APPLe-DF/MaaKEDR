---
title: Protocol
icon: basil:document-solid
index: true
dir:
    order: 2
---

# Protocol Docs

This section records the **conventions** between MaaKEDR and _雪松 (KEDR)_: which files make up each task, which
pipeline nodes the GUI options finally land on, and what to keep in sync when such a flow changes.

These are not MaaFramework general protocols: field semantics follow the
[Pipeline Protocol](https://maafw.com/docs/3.1-PipelineProtocol) and
[Project Interface V2](https://maafw.com/docs/3.3-ProjectInterfaceV2). This section only records how _this_ project
uses them.

## Contents

- [Project & resources](./overview.md) — `interface` / `tasks` / `resource` / resolution baseline
- [Startup & login](./startup.md) — launch flow and server-pack overrides
- [Claim rewards](./claim-rewards.md) — dispatch / daily / battle pass / mailbox / premium shop
- [Farm resources](./farm-resources.md) — stage types, battle count, drain-stamina mode
- [PVP](./pvp.md) — PVP loop, season reset and result reading
- [Event stages and shop](./event-stage.md) — event stage farming, exhausted attempts and shop clearing
- [Stamina info](./stamina-info.md) — home-screen stamina read and refill time

## Code map

| Area                   | Path                                                    |
| ---------------------- | ------------------------------------------------------- |
| Task entries & options | `tasks/*.json`                                          |
| Task presets           | `tasks/preset/Daily.json`, `tasks/preset/Activity.json` |
| Pipeline nodes         | `resource/base/pipeline/*.json`                         |
| Server overrides       | `resource/bilibili/`, `resource/taptap/`                |
| Custom modules         | `agent/custom/recognition/`, `agent/custom/action/`     |
| Return-to-home hub     | `resource/base/pipeline/common.json`                    |

## Fixed structure of a task protocol page

Every task protocol page follows the same order. Use it when adding a page so readers can compare pages side by side:

1. **Task entry**: task name (GUI label), `entry` node, definition file, pipeline file, whether it has options
2. **Data flow**: `tasks/*.json` option → which nodes `pipeline_override` patches → which pipeline file / agent code
3. **Flow**: main path and branches (including failure fallbacks), node names identical to the pipeline files
4. **Key conventions**: node semantics that are easy to break (`max_hit`, `timeout`, `[JumpBack]`, how `on_error` is used)
5. **Files to touch when changing such a flow**: numbered steps + validation commands
6. **Acceptance checklist**: what to verify on a real device, in order

## Checklist when adding or changing a task

1. Define the task and options in `tasks/<task>.json`: `task[]` declares `name` / `entry` / `option`, and options use
   `cases[].pipeline_override` pointing at **existing** node names
2. Register a new task file in the `import` array of `interface.json` (currently 7 task files + 2 preset files)
3. Update `tasks/preset/Daily.json` / `tasks/preset/Activity.json` when the task belongs to a preset (presets reference
   tasks by **task name**)
4. Put flow nodes in `resource/base/pipeline/<task>.json`; put cross-task shared nodes in `common.json`
5. When adding or changing a custom recognition/action, update the implementation under
   `agent/custom/recognition/`, `agent/custom/action/` and its `__init__.py` registration
6. Put template images in `resource/base/image/<module>/`; put server-specific images in `resource/<pack>/image/`
7. Run the checks: `pnpm check` (format + schema + pipeline integrity + project lint),
   `pnpm exec maa-tools check` (pipelines only), and `pnpm check:py` after touching Python
8. Come back here and sync the docs: **node names, option names, file paths** must match the code character by
   character

> [!WARNING]
> Option `pipeline_override` targets nodes by name. If a pipeline node is renamed and the task file is not updated, the
> option **silently stops working** (no error, it just no longer applies). Search the node name across the repository
> before renaming, and re-check every entry on these pages afterwards.

## How this section relates to the other docs

| You want to know                                      | Read                                                      |
| ----------------------------------------------------- | --------------------------------------------------------- |
| Which nodes a task contains, which ones options patch | This section                                              |
| Pipeline fields, recognition/action types, patterns   | [Pipeline Guide](../develop/pipeline.md)                  |
| How to write and register custom recognitions/actions | [Custom Guide](../develop/custom.md)                      |
| The four rules of the return-to-home hub              | [Shared Nodes & Return-to-Home Hub](../develop/common.md) |
| Directory layout, release flow                        | [Project Structure](../develop/structure.md)              |
