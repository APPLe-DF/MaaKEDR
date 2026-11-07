---
title: "Pipeline Guide"
order: 2
icon: "ri:git-branch-fill"
---

# Pipeline Guide

## What Is a Pipeline?

A Pipeline is the core concept of MaaFramework: a JSON description of how an automation task runs. Each Pipeline is made of **nodes**, and every node defines three things:

- **Recognition** (`recognition`): how to find the target on screen
- **Action** (`action`): what to do once the target is found
- **Next nodes** (`next`): which nodes to try after the current one finishes

This project is built on three layers: `tasks/*.json` declares the task entries shown in the GUI, `resource/base/pipeline/*.json` describes the flow as a node graph (most of the logic lives here), and `agent/custom/` holds Python code for complex logic. See [Project Structure](./structure.md) for the responsibility of each layer.

## Protocol Version

This project is generated from the create-maa-project pipeline template and uses the **classic style**: `recognition` / `action` are strings with parameters flattened at the node top level:

```json
{
    "NodeName": {
        "recognition": "TemplateMatch",
        "template": "button.png",
        "threshold": 0.8,
        "action": {"type": "Click"}
    }
}
```

This is structurally equivalent to the nested v2 style (`recognition: {"type": ..., "param": {...}}`) in the official docs. The runtime channel is MaaFramework **stable** (see the `maafw` field in `maa-project.json`; the version follows the channel automatically, and because the package reuses the client's native runtime the `runtimes/` copy and the `maafw` pin in `pyproject.toml` must match); field validity is governed by the schemas in `tools/schema/` and `pnpm check:schema`. For generic protocol details see the [MaaFramework Pipeline Protocol](https://maafw.com/docs/3.1-PipelineProtocol).

## Node Structure

Each pipeline node defines a recognition → action → transition step:

```json
{
    "NodeName": {
        "recognition": "TemplateMatch",
        "roi": [
            100,
            200,
            80,
            50
        ],
        "template": "button.png",
        "threshold": 0.8,
        "action": {"type": "Click"},
        "next": ["NextNode"],
        "on_error": ["FallbackNode"]
    }
}
```

The full field set and defaults are defined by `tools/schema/pipeline.schema.json` (`threshold` defaults to 0.7, `timeout` to 20000, `rate_limit` to 1000); this page only covers the common ones.

## Execution Flow

### Node Execution Order

A Pipeline run is essentially one loop. The schema defines `timeout` as `while (!timeout) { foreach(next); sleep_until(rate_limit); }`, which expands to:

1. Start from the entry node (declared by a task in `tasks/*.json` or by `interface.json`)
2. Try every candidate node in the current node's `next` list, in order
3. The first candidate that matches runs its action and becomes the new current node
4. Repeat step 2 until `next` is empty or `timeout` expires (default 20000 ms; `-1` never times out)
5. Every recognition round costs at least `rate_limit` (default 1000 ms); the remainder is spent sleeping

Inside a single node (when `repeat` > 1) the order is:

```text
pre_wait_freezes → pre_delay → action → [repeat_wait_freezes → repeat_delay → action] × (repeat-1) → post_wait_freezes → post_delay
```

**A recognition miss has two different meanings** — keep them apart:

- The node itself misses → the flow follows its own `on_error` (if any), otherwise it stops
- The node misses while being a **candidate** in a parent's `next` list → it only means "this candidate did not match"; the framework tries the next candidate and does **not** fire that candidate's `on_error`

This distinction is the basis of the [Fallback Strategy](#fallback-strategy) section.

### Node Connection

Nodes are connected through `next`. An element of `next` may carry an attribute prefix (schema: `node name, may carry a prefix such as [JumpBack]NodeName`):

```json
{
    "StartTask": {
        "next": [
            "CheckStatus",
            "[JumpBack]HandleError"
        ]
    }
}
```

| Attribute    | Effect                                                                                                                 | Usage in this project                                                                                 |
| ------------ | ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `[JumpBack]` | After the matched node finishes its action, jump **back to the parent** and retry the `next` list instead of advancing | The standard pattern for error handling, pop-up dismissal and reusable utility nodes (73 occurrences) |
| `[Anchor]`   | Reference the node an anchor name currently points to; a node binds itself with the `anchor` field                     | Not used yet (no `anchor` in `resource/base/pipeline/`); introduce it only when needed                |

Besides `next` / `on_error`, `[Anchor]` may also appear in `roi` / `target` (`[Anchor]anchorName`) to reuse the position that node recognised most recently.

## Recognition Types

| Type          | Use Case      | Description                                                                                                                                                      |
| ------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| TemplateMatch | Static UI     | OpenCV template matching, images in `image/`, threshold 0.7; `template` accepts an array (any match hits — useful when an entry icon has multiple styles/states) |
| OCR           | Dynamic text  | PaddleOCR v5, `expected` supports regex, `roi` for text region                                                                                                   |
| DirectHit     | Routing       | Always matches, used for `next` branching                                                                                                                        |
| Custom        | Complex logic | Python custom recognition via `@AgentServer.custom_recognition()`                                                                                                |
| ColorMatch    | Color filter  | Used with OCR `color_filter` field for background removal                                                                                                        |

## Action Types

| Type      | Description                                                                       |
| --------- | --------------------------------------------------------------------------------- |
| Click     | Click matched position. `target: true` for center, `target: [x,y,w,h]` for offset |
| DoNothing | Recognition-only, no action                                                       |
| Swipe     | Swipe with `param.begin` / `param.end` / `param.duration`                         |
| Custom    | Python custom action via `@AgentServer.custom_action()`                           |

## Common Fields

| Field                      | Description                                                                                                                                                                                                               |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pre_delay` / `post_delay` | Wait before/after action (ms); **avoid** — prefer `pre_wait_freezes` / `post_wait_freezes` or intermediate recognition nodes                                                                                              |
| `pre_wait_freezes`         | Wait for the screen to settle after recognition and before the action (replaces fixed delays)                                                                                                                             |
| `post_wait_freezes`        | Wait until screen stops changing (smarter than fixed delay). The dominant style here is the integer shorthand (`"post_wait_freezes": 500`); the object form `{"time": 500, "target": [x, y, w, h]}` watches a region only |
| `repeat` / `repeat_delay`  | Action repeat count and per-repeat delay (e.g. `ClickHomePage` taps 5 times, 500 ms apart); `repeat_wait_freezes` waits for the screen to settle before each repeat                                                       |
| `max_hit`                  | Max hits before skip. For looping UI elements                                                                                                                                                                             |
| `timeout`                  | Recognition timeout (ms), default 20000; `-1` means never time out                                                                                                                                                        |
| `rate_limit`               | Minimum duration of one recognition round (ms, default 1000) — throttle high-frequency nodes; only a few nodes set it explicitly                                                                                          |
| `enabled`                  | Whether the node is active; when `false`, other nodes skip it in their `next` (the `DisableNode` custom action overrides it to `false`)                                                                                   |
| `inverse`                  | Invert the recognition result; **use with caution**, see [Writing Best Practices](#writing-best-practices)                                                                                                                |
| `only_rec`                 | Recognition only, no action                                                                                                                                                                                               |
| `focus`                    | Log notification on hit/failure                                                                                                                                                                                           |
| `color_filter`             | OCR color pre-filter, references a ColorMatch node                                                                                                                                                                        |
| `replace`                  | OCR text replacement (`[["wrong", "right"]]`) for text the model keeps misreading                                                                                                                                         |
| `desc` / `doc`             | Node description, see [Comment & Placeholder Fields](#comment-placeholder-fields)                                                                                                                                         |

## Naming Conventions

- Use **dot-separated hierarchy**: `FarmResources.Start`, `ClaimRewards.CheckDaily`
- Prefix with module name: `PVP.`, `BattlePass.`, `Common.`
- JumpBack nodes must NOT have `next`

## Template Images & Asset Naming

Template images live under `resource/base/image/`:

- **Folders**: organize by pipeline module (e.g. `image/event_stage/`, `image/farm_resources/`); shared images used by multiple modules go directly in `image/`
- **File names**: lowercase `snake_case`, e.g. `flare_title.png`, `no_stamina.png`, `more.png`
- **Server-specific differences**: `resource/bilibili/` and `resource/taptap/` are additive layers over the official resources (load order follows the `resource` field in `interface.json`); today both only override `pipeline/startup.json`, and server-specific templates should follow the same `image/` sub-folder layout
- **Making templates**: crop from a 1280×720 screenshot at a moderate size (roughly 50×50 to 200×200); oversized templates are prone to false matches. See [Overview](../protocol/overview.md) for ROI and resolution baselines
- **Paths**: in pipeline JSON, `template` is a path relative to the `image/` directory using **forward slashes** (e.g. `event_stage/flare_title.png`)

## Writing Best Practices

:::tip Node connection principles

- **`next` holds exits**: `next` answers "where can we go once this stage is done", not "the next line to execute"
- **`[JumpBack]` holds interruptions**: pop-up dismissal, going back one level, returning home — all of these hang off `[JumpBack]` so they jump back after finishing and never pollute the main flow
- **Keep coupling low**: highly reusable nodes (`Common.BackButton`, `Common.EnsureHome`) are `[JumpBack]` leaves referenced from many `next` lists
- **Self-loop**: when an operation may not take effect, put the node into its own `next` (e.g. `FarmResources.ExitStageConfirm` clicks the stage-exit ✕, re-checks, and clicks again while the ✕ is still there, converging via `max_hit`)
- **Page transitions**: after clicking into a new screen, add `post_wait_freezes` and continue only once the screen is stable
- **Swipe operations**: follow a swipe with another recognition or click so the next decision is not made while the list is still coasting

:::

:::warning Caveats

- **Use `inverse` sparingly**: inverted recognition makes the flow hard to reason about; if you must, pair it with `post_wait_freezes` to pin the state
- **Avoid unconditional matching**: `DirectHit` has no condition at all, so abusing it in `next` produces unintended loops (here it appears mainly on hub/routing nodes and a few unconditional action nodes)
- **Priority order**: sort `next` by what must be excluded first, never upside down
- **Match frequency**: within the same priority, put the faster-recognised node first

:::

**Priority ordering example** (pop-up vs. home screen):

```text
Scenario: Node B detects a small pop-up (high priority, low frequency);
          Node A detects the home screen (low priority, high frequency).

If A can still match while the pop-up is showing, B must come first:
  "next": ["B", "A"]   OK  - B is evaluated first and the pop-up is handled
  "next": ["A", "B"]   BAD - A matches first and the flow is stuck on the pop-up
```

## Comment & Placeholder Fields

Pipeline nodes support two kinds of comment/placeholder fields (already supported by schema):

1. `doc` / `*_doc` / `desc` / `*_desc`: node description; the schema pattern is `.*_doc$|^doc$|.*_desc$|^desc$`
2. `*_code` / `code`: **placeholder for a required field**, used when the template path is configured centrally in `interface.json` instead of being hardcoded in the pipeline; the schema pattern is `.*_code$|^code$`

**This project uses `desc` consistently**: `resource/base/pipeline/` currently holds 250 `desc` fields and zero `doc` fields, so follow `desc` when writing new nodes.

```json
"EnterBattle": {
    "desc": "Enter battle interface",
    "template_code": "configure template via pipeline_override in interface.json",
    "recognition": "TemplateMatch",
    "roi": [885, 123, 340, 183],
    "action": { "type": "Click" },
    "next": ["CheckBattleInterface"]
}
```

:::tip Why `*_code` placeholders?

`TemplateMatch` requires a `template` field, but if template paths are injected centrally via `pipeline_override` in `interface.json` (change once for resolution/server adaptation), there is nothing to fill in the pipeline file. `template_code` passes schema validation while telling developers "the template is configured elsewhere".

:::

## Design Patterns

### Linear Flow

Best for sequential operations (e.g., game launch):

```json
"LaunchGame": {
    "recognition": "DirectHit",
    "action": {
        "type": "StartApp",
        "param": { "package": "com.phxh.official.nld" }
    },
    "timeout": 60000,
    "next": ["WaitGameLoading", "ClickToStart", "CheckHomePage"]
},
"WaitGameLoading": {
    "desc": "Wait for the game to finish loading",
    "recognition": "TemplateMatch",
    "roi": [595, 653, 146, 64],
    "template": "game_loading.png",
    "threshold": 0.8,
    "post_wait_freezes": 500,
    "next": ["ClickToStart"]
},
"ClickToStart": {
    "recognition": "TemplateMatch",
    "template": "startgame1.png",
    "threshold": 0.8,
    "action": { "type": "Click", "param": { "target_offset": [120, 0, 0, 0] } },
    "repeat": 3,
    "next": ["DailyLoginReward", "CheckHomePage"]
}
```

`LaunchGame` starts with `DirectHit` and its three `next` candidates cover "still loading / login screen / already on the home screen", so one chain serves both cold and warm starts. The snippet above is abridged: in the source file `WaitGameLoading` and `ClickToStart` still carry fixed `post_delay` values (an early style); new nodes should prefer `post_wait_freezes`.

### DirectHit Hub

```json
"HubNode": {
    "recognition": "DirectHit",
    "action": { "type": "DoNothing" },
    "next": ["BranchA", "BranchB"]
}
```

`next` is OR logic: tries from top to bottom, executes the first match.

### [JumpBack] Central Hub

Suitable for repeating sub-module visits (e.g., reward claim loop):

```json
"ClaimRewards.MainHub": {
    "recognition": "DirectHit",
    "action": { "type": "DoNothing" },
    "next": [
        "[JumpBack]DispatchClaim.Start",
        "[JumpBack]ClaimRewards.Start",
        "[JumpBack]BattlePass.Start",
        "[JumpBack]Mailbox.Start"
    ]
}
```

`[JumpBack]` nodes return to the parent after execution. Only non-JumpBack nodes can exit the loop.

**A JumpBack leaf node should not carry a `next` field** — it returns as soon as it finishes, and routing is controlled by the parent's `next`. If such a node genuinely needs a sub-chain (for example a hub node itself), its `next` is expanded normally and the jump-back happens only after the whole sub-chain completes; when the matched node's action fails, the flow goes to `on_error` and does not jump back (see the [official protocol](https://maafw.com/docs/3.1-PipelineProtocol#jump-back-jumpback)).

On top of this pattern the project provides a reusable **return-to-home hub** (`Common.EnsureHome`): put handlers for known screens into the hub's `next` and attach `[JumpBack]Common.EnsureHome` last in the caller's `next` to recover from a stuck screen and continue. See [Shared Nodes & Return-to-Home Hub](./common.md) for the hub definition, the four rules and the tasks already wired up.

### Battle Loop

```json
"BattleStage": {
    "recognition": "DirectHit",
    "action": { "type": "DoNothing" },
    "next": [
        "[JumpBack]ClickVictory",
        "[JumpBack]ClickItemDialog",
        "QuickBattle"
    ]
}
```

Battle won → click → jump back and re-check → fight again → exit when stamina runs out.

### Task Option Override

`tasks/*.json` uses `pipeline_override` to modify node behavior at runtime:

```json
"pipeline_override": {
    "FarmResources.Start": {
        "next": ["FarmResources.ResourceCollect"]
    },
    "FarmResources.ClickStage": {
        "custom_recognition_param": {
            "stage_name": "1-1",
            "stage_index": 1,
            "resource_type": "特别军费行动"
        }
    }
}
```

Can override `next`, `roi`, `threshold`, `custom_action_param`, etc. Like `custom_action_param`, `custom_recognition_param` can be written as a plain JSON object; the JSON-string form also works but is serialized a second time (see [Custom recognition](custom.md)).

### max_hit Anti-loop

```json
"ClaimButton": {
    "max_hit": 5,
    "recognition": "TemplateMatch",
    ...
}
```

Max 5 hits before skip — suited to claim buttons that reappear in a loop. Hit counts **accumulate for the duration of a task run** and are not cleared by screen changes or by finishing a single battle; to reset a counter mid-run use the Custom Action `ResetCount` (it calls `context.clear_hit_count`), which is how `PVP.Speed2x` is clicked exactly once per battle — see the [PVP protocol](../protocol/pvp.md).

### color_filter OCR Pre-processing

For strongly coloured text, a ColorMatch node can pre-filter the background and raise OCR accuracy:

```json
"GoldTextFilter": {
    "recognition": "ColorMatch",
    "method": 4,
    "lower": [[38, 31, 30]],
    "upper": [[50, 44, 44]],
    "count": 1000,
    "connected": true
}
```

Reference it from the OCR node:

```python
JOCR(roi=(x, y, w, h), color_filter="GoldTextFilter")
```

## Fallback Strategy

There are two kinds of fallback. Tell them apart by what the node means and **never mix them**:

### Flow Fallback (prefer the `next` list)

When a recognition miss is a normal flow branch (e.g. "no daily medal → check the weekly one"), put the fallback node after the current one in the parent's `next` list and let MaaFW's **ordered OR** semantics reach it.

In MaaFW, once the parent node matches, the framework tries each child in the `next` list in order until one of them matches. If an earlier child misses, it automatically falls through to the next child. Putting the fallback node last in `next` therefore means it is reached naturally when every normal branch above it misses.

```json
"ConfirmInterface": {
    "next": [
        "CheckDaily",        // try the daily medal first
        "CheckWeekly",       // falls through to the weekly medal when CheckDaily misses
        "CheckMilitary"      // and to the military medal when both miss
    ]
}
```

**Note**: this "miss → try the next node" behaviour belongs to the **parent's `next` list**. A single node's own `next` is entered only when that node matches; if the node itself misses, the flow goes straight to its `on_error` (if any) or stops. Consequently a "negative check" (match = stop, miss = continue) cannot be built from a single node's `next` — keep `on_error` for that (see below).

### Real-Error Fallback (keep `on_error`, mark it `[错误兜底]`)

When the fallback path is only for abnormal/unexpected states (stage UI unrecognised, quick-battle button gone), keep `on_error` and mark it:

```json
"FarmResources.Start": {
    "desc": "从主页进入作战界面 [错误兜底: FarmResources.EnsureHome]",
    "recognition": "TemplateMatch",
    "template": "farm_resources/battle_entry.png",
    "on_error": ["FarmResources.EnsureHome"]
}
```

Hitting such a node means an unexpected UI state occurred, so the `on_error` screenshot is valuable for debugging — keep it.

### Special Case: Negative Check (Parallel Candidates)

For a node meant to "stop when X is recognized, continue when it is not" (e.g., checking whether a stage is locked), **do not rely on the node's own `on_error` for fallback**: when the node is a candidate in a parent's `next` list, a recognition miss only means "this candidate did not match" — it does **not** trigger the candidate's own `on_error`. If the list has no further candidate, the whole list fails and retries, causing a timeout loop (verified in production: `FarmResources.SelectSkillStage` looped 21 attempts × 20s and failed the task).

The correct pattern is **parallel candidates** — put the "continue" node after the check node in the `next` list so it falls through naturally:

```json
"SelectStage": {
    "recognition": "DirectHit",
    "next": [
        "CheckLocked",   // hit = locked, stop; miss = fall through to next candidate
        "ClickStage"     // continue branch (actually clicks into the stage)
    ]
},
"CheckLocked": {
    "recognition": "TemplateMatch",
    "template": "lock_icon.png",
    // No on_error (does not fire in candidate position; keeping it only misleads)
    "focus": {
        "Node.Recognition.Succeeded": "Locked, stop",
        "Node.Recognition.Failed": "Unlocked, continue"
    }
}
```

`CheckLocked` is evaluated once as a candidate; on miss the framework tries the next candidate (`ClickStage`). Only when all candidates miss does the whole list fail. Mark such nodes with "negative check (parallel candidates)" in `desc`.

## Practical Examples

Every example below comes from real nodes in this repository's `resource/base/pipeline/`, so you can read them against the source files. Fields irrelevant to the point being made (`pre_delay` / `post_delay`, etc.) are omitted for brevity.

### Example 1: Linear Progress with Multiple `next` Candidates

Game launch chain (`startup.json`):

```json
"LaunchGame": {
    "recognition": "DirectHit",
    "action": {
        "type": "StartApp",
        "param": { "package": "com.phxh.official.nld" }
    },
    "timeout": 60000,
    "next": ["WaitGameLoading", "ClickToStart", "CheckHomePage"]
},
"ClickToStart": {
    "recognition": "TemplateMatch",
    "template": "startgame1.png",
    "threshold": 0.8,
    "action": { "type": "Click", "param": { "target_offset": [120, 0, 0, 0] } },
    "repeat": 3,
    "next": ["DailyLoginReward", "CheckHomePage"]
}
```

**Analysis**:

- `LaunchGame` starts unconditionally with `DirectHit`; its three `next` candidates cover "still loading / login screen / already on the home screen", so cold and warm starts share one chain
- `ClickToStart` uses `repeat: 3` plus `target_offset` to tap repeatedly and survive a first tap that does not register
- Its two `next` candidates cover "daily login reward popped up / already home", folding pop-up handling into the main flow instead of adding a delay

### Example 2: Page Transition and Waiting

Event stage entry (`event_stage.json`):

```json
"EventStage.ClickJourney": {
    "desc": "Click 踏上征途 to enter stage selection (fixed tap on the bottom-right button centre, confirmed by OCR)",
    "max_hit": 3,
    "recognition": "OCR",
    "roi": [920, 570, 320, 100],
    "expected": "踏上征途",
    "only_rec": true,
    "threshold": 0.5,
    "action": { "type": "Click", "param": { "target": [1025, 607, 1, 1] } },
    "next": ["EventStage.WaitStageMapStable"]
},
"EventStage.WaitStageMapStable": {
    "desc": "Confirm the EX stage map is open: continue once the bottom EP tab is visible; retry 踏上征途 otherwise",
    "recognition": "OCR",
    "roi": [80, 590, 560, 130],
    "expected": "EP\\.?[1-4]",
    "threshold": 0.7,
    "action": { "type": "DoNothing" },
    "post_wait_freezes": 1000,
    "next": ["EventStage.ClickEP2"],
    "on_error": ["EventStage.ClickJourney"]
}
```

**Analysis**:

- When the button position is fixed but its text varies, OCR with `only_rec: true` only proves the button exists while `target` pins the tap position
- `WaitStageMapStable` answers "did we actually get in": `post_wait_freezes: 1000` waits for the map to settle before moving on
- A failed transition goes to `on_error` and retries the click node, which is more reliable than a fixed delay

### Example 3: JumpBack Battle Loop and Error Recovery

Battle loop (`farm_resources.json`):

```json
"FarmResources.BattleStage": {
    "desc": "Battle loop parent: polls victory screen / item dialog / quick-battle button",
    "recognition": "DirectHit",
    "action": { "type": "DoNothing" },
    "next": [
        "[JumpBack]FarmResources.ClickVictory",
        "[JumpBack]FarmResources.ClickItemDialog",
        "FarmResources.QuickBattle",
        "FarmResources.ExitStageConfirm",
        "FarmResources.PrepareBattle"
    ]
},
"FarmResources.ClickVictory": {
    "desc": "Detect and click the victory screen",
    "recognition": "TemplateMatch",
    "roi": [14, 6, 270, 119],
    "template": "farm_resources/battle_victory.png",
    "threshold": 0.8,
    "action": { "type": "Click" }
}
```

**Analysis**:

- The first two `[JumpBack]` candidates handle the victory screen and item dialog that can pop up at any time mid-battle; after clicking they jump back to `FarmResources.BattleStage` and keep polling
- The last three plain candidates are exits taken only once the current battle ends (quick battle / exit confirmation / prepare the next one) — whichever matches first leaves the loop
- `FarmResources.ClickVictory` carries no `next`: it only dismisses the pop-up and routing stays with the parent, so it can be reused in several places
- The return-to-home fallback is not part of this loop; callers attach `[JumpBack]Common.EnsureHome` last in their own `next`, see [Shared Nodes & Return-to-Home Hub](./common.md)

## Notes

1. **Prefer `wait_freezes` over fixed delays** — The screen may still be transitioning after a navigation click; `post_wait_freezes` waits for the screen to settle, which is more reliable than a fixed `post_delay`. Use fixed delays only when a loading animation cannot be frozen
2. **OCR expected is regex** — `".*"` matches anything, `"^text$"` exact match
3. **ROI at 1280x720** — coordinates `[x, y, w, h]`
4. **Fallback strategy** — Put flow fallbacks (expected paths that don't work) at the end of `next`; reserve `on_error` for genuine error states and mark with `[错误兜底]`. See the Fallback Strategy section above
5. **`next` order matters — highest priority first** — Order `next` by priority: put nodes that must be **excluded first** (pop-ups, error dialogs) before normal branches. Counter-example: if a home-screen node (high match frequency) comes before a pop-up node, the pop-up case matches the home-screen node first and the flow gets stuck on the wrong screen. Within the same priority, sort by match frequency, fastest first
6. **Add `roi` when the full screenshot is noisy** — a narrower region is both faster and more accurate
7. **Use `ReduceBattleCount` in stamina-drain mode** — the `ReduceBattleCount` custom action decreases the battle count dynamically
8. **Write `desc`, not `doc`** — existing nodes all use `desc` for descriptions; both are valid but do not mix them

## References

- [MaaFramework Pipeline Protocol](https://maafw.com/docs/3.1-PipelineProtocol): authoritative definitions of field semantics, defaults and node attributes such as `[JumpBack]` / `[Anchor]`
- [MaaFramework Project Interface Protocol](https://maafw.com/docs/3.3-ProjectInterfaceV2): how to write `interface.json` and `pipeline_override`
- `tools/schema/pipeline.schema.json` in this repository: the schema actually used here (synced from upstream by `pnpm sync:schema`); field validity follows it and `pnpm check:schema` enforces it
- Related docs: [Project Structure](./structure.md), [Shared Nodes & Return-to-Home Hub](./common.md), [Custom Guide](./custom.md), [Setup](./setup.md)
