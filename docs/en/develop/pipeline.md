---
title: "Pipeline Guide"
order: 2
icon: "ri:git-branch-fill"
---

# Pipeline Guide

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

| Type          | Use Case      | Description                                                       |
| ------------- | ------------- | ----------------------------------------------------------------- |
| TemplateMatch | Static UI     | OpenCV template matching, images in `image/`, threshold 0.7       |
| OCR           | Dynamic text  | PaddleOCR v5, `expected` supports regex, `roi` for text region    |
| DirectHit     | Routing       | Always matches, used for `next` branching                         |
| Custom        | Complex logic | Python custom recognition via `@AgentServer.custom_recognition()` |
| ColorMatch    | Color filter  | Used with OCR `color_filter` field for background removal         |

## Action Types

| Type      | Description                                                                       |
| --------- | --------------------------------------------------------------------------------- |
| Click     | Click matched position. `target: true` for center, `target: [x,y,w,h]` for offset |
| DoNothing | Recognition-only, no action                                                       |
| Swipe     | Swipe with `param.begin` / `param.end` / `param.duration`                         |
| Custom    | Python custom action via `@AgentServer.custom_action()`                           |

## Common Fields

| Field                      | Description                                                   |
| -------------------------- | ------------------------------------------------------------- |
| `pre_delay` / `post_delay` | Wait before/after action (ms). Navigation clicks: 1000-2000ms |
| `post_wait_freezes`        | Wait until screen stops changing (smarter than fixed delay)   |
| `max_hit`                  | Max hits before skip. For looping UI elements                 |
| `timeout`                  | Recognition timeout (ms), default 20000                       |
| `only_rec`                 | Recognition only, no action                                   |
| `focus`                    | Log notification on hit/failure                               |
| `color_filter`             | OCR color pre-filter, references a ColorMatch node            |

## Naming Conventions

- Use **dot-separated hierarchy**: `FarmResources.Start`, `ClaimRewards.CheckDaily`
- Prefix with module name: `PVP.`, `BattlePass.`, `Common.`
- JumpBack nodes must NOT have `next`

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

1. **Sufficient delays** — At least 1000ms after navigation clicks
2. **OCR expected is regex** — `".*"` matches anything, `"^text$"` exact match
3. **ROI at 1280x720** — coordinates `[x, y, w, h]`
4. **Always add `on_error`** — For critical navigation nodes
5. **`next` order matters — highest priority first** — Order `next` by priority: put nodes that must be **excluded first** (pop-ups, error dialogs) before normal branches. Counter-example: if a home-screen node (high match frequency) comes before a pop-up node, the pop-up case matches the home-screen node first and the flow gets stuck on the wrong screen. Within the same priority, sort by match frequency, fastest first
6. **Use `post_wait_freezes`** — More reliable than fixed `post_delay` for animations
