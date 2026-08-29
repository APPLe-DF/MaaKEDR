---
title: "Pipeline Guide"
order: 2
icon: "ri:git-branch-fill"
---

# Pipeline Guide

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

This is structurally equivalent to the nested v2 style (`recognition: {"type": ..., "param": {...}}`) in the official docs. The runtime channel is MaaFramework **stable** (see the `maafw` field in `maa-project.json`; the version follows the channel automatically and the packaged runtime is authoritative); field validity is governed by the schemas in `tools/schema/` and `pnpm check:schema`. For generic protocol details see the [MaaFramework Pipeline Protocol](https://maafw.com/docs/3.1-PipelineProtocol).

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

| Field                      | Description                                                                                                                  |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `pre_delay` / `post_delay` | Wait before/after action (ms); **avoid** — prefer `pre_wait_freezes` / `post_wait_freezes` or intermediate recognition nodes |
| `post_wait_freezes`        | Wait until screen stops changing (smarter than fixed delay)                                                                  |
| `max_hit`                  | Max hits before skip. For looping UI elements                                                                                |
| `timeout`                  | Recognition timeout (ms), default 20000                                                                                      |
| `only_rec`                 | Recognition only, no action                                                                                                  |
| `focus`                    | Log notification on hit/failure                                                                                              |
| `color_filter`             | OCR color pre-filter, references a ColorMatch node                                                                           |

## Naming Conventions

- Use **dot-separated hierarchy**: `FarmResources.Start`, `ClaimRewards.CheckDaily`
- Prefix with module name: `PVP.`, `BattlePass.`, `Common.`
- JumpBack nodes must NOT have `next`

## Template Images & Asset Naming

Template images live under `resource/base/image/`:

- **Folders**: organize by pipeline module (e.g. `image/event_stage/`, `image/farm_resources/`); shared images used by multiple modules go directly in `image/`
- **File names**: lowercase `snake_case`, e.g. `flare_title.png`, `no_stamina.png`, `main_option.png`
- **Server-specific images**: put them under `resource/bilibili/image/` or `resource/taptap/image/` (load order follows the `resource` field in `interface.json`)
- **Making templates**: crop from a 1280×720 screenshot at a moderate size (roughly 50×50 to 200×200); oversized templates are prone to false matches. See [Overview](../protocol/overview.md) for ROI and resolution baselines
- **Paths**: in pipeline JSON, `template` is a path relative to the `image/` directory using **forward slashes** (e.g. `event_stage/flare_title.png`)

## Comment & Placeholder Fields

Pipeline nodes support two kinds of comment/placeholder fields (already supported by schema):

1. `doc` / `*_doc`: node description
2. `*_code` / `code`: **placeholder for a required field**, used when the template path is configured centrally in `interface.json` instead of being hardcoded in the pipeline

```json
"EnterBattle": {
    "doc": "Enter battle interface",
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
        "type": "DoNothing",
        "param": { "package": "com.phxh.official.nld" }
    },
    "next": ["ClickToStart"]
},
"ClickToStart": {
    "recognition": "TemplateMatch",
    "template": "click_to_start.png",
    "action": { "type": "Click" },
    "post_delay": 2000,
    "next": ["DailyLoginReward", "CheckHomePage"]
}
```

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

### Task Option Override

`tasks/*.json` uses `pipeline_override` to modify node behavior at runtime:

```json
"pipeline_override": {
    "FarmResources.Start": {
        "next": ["FarmResources.ResourceCollect"]
    }
}
```

Can override `next`, `roi`, `threshold`, `custom_action_param`, etc.

### max_hit Anti-loop

```json
"ClaimButton": {
    "max_hit": 5,
    ...
}
```

Max 5 hits before skip. Counts cross-session.

## Notes

1. **Prefer `wait_freezes` over fixed delays** — The screen may still be transitioning after a navigation click; `post_wait_freezes` waits for the screen to settle, which is more reliable than a fixed `post_delay`. Use fixed delays only when a loading animation cannot be frozen
2. **OCR expected is regex** — `".*"` matches anything, `"^text$"` exact match
3. **ROI at 1280x720** — coordinates `[x, y, w, h]`
4. **Fallback strategy** — Put flow fallbacks (expected paths that don't work) at the end of `next`; reserve `on_error` for genuine error states and mark with `[错误兜底]`. See the Fallback Strategy section above
5. **`next` order matters — highest priority first** — Order `next` by priority: put nodes that must be **excluded first** (pop-ups, error dialogs) before normal branches. Counter-example: if a home-screen node (high match frequency) comes before a pop-up node, the pop-up case matches the home-screen node first and the flow gets stuck on the wrong screen. Within the same priority, sort by match frequency, fastest first
