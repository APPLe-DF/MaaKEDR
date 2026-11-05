---
title: "Shared Nodes & Return-to-Home Hub"
order: 3
icon: "ri:home-4-fill"
---

# Shared Nodes & Return-to-Home Hub

`resource/base/pipeline/common.json` holds nodes reused across tasks. MaaFramework merges every JSON file under `pipeline/` into one namespace, so any task file can reference these nodes by name without an import.

## Node inventory

| Node                       | Type          | Purpose                                                                           |
| -------------------------- | ------------- | --------------------------------------------------------------------------------- |
| `Common.EnsureHome`        | DirectHit     | Return-to-home hub: handles known overlays/sub-pages until the home marker hits   |
| `Common.CheckHomePage`     | TemplateMatch | Global home marker (`more.png`, threshold 0.75). Leaf, the hub's exit             |
| `Common.ClickHomeButton`   | TemplateMatch | Clicks the top home button (`return_main.png`)                                    |
| `Common.CheckItemObtained` | TemplateMatch | Full-screen "item obtained" overlay (defined in `claim_rewards.json`, cross-file) |
| `Common.BackButton`        | TemplateMatch | Generic back arrow (defined in `claim_rewards.json`)                              |

## Hub definition

```json
"Common.EnsureHome": {
    "max_hit": 10,
    "recognition": "DirectHit",
    "action": { "type": "DoNothing" },
    "timeout": 30000,
    "next": [
        "[JumpBack]Common.CheckItemObtained",
        "[JumpBack]Common.ClickHomeButton",
        "[JumpBack]Common.BackButton",
        "[JumpBack]FarmResources.ExitStageConfirm",
        "Common.CheckHomePage"
    ]
}
```

`[JumpBack]FarmResources.ExitStageConfirm` is defined in `farm_resources.json`; it dismisses the stage-exit confirmation dialog. Hub `[JumpBack]` handlers may live in any pipeline file — they do not have to be declared in `common.json`, because every JSON under `pipeline/` is merged into one namespace and can be referenced by node name.

## How callers use it

Each task starts with an always-matching **gate node** that lists the task's main path first and the hub last:

```json
"FarmResources.EnsureHome": {
    "max_hit": 6,
    "recognition": "DirectHit",
    "action": { "type": "DoNothing" },
    "next": ["FarmResources.CheckHomePage", "[JumpBack]Common.EnsureHome"]
}
```

When the task entry cannot confirm the home screen, the task no longer fails outright: the hub dismisses the "item obtained" overlay, clicks the top home button, and clicks the generic back button. Once home is reached it **jumps back to the caller** and retries the original list, so the normal flow continues.

The hub **never sends the system back key**: in this game BACK acts as ESC and opens the "are you sure you want to quit?" dialog, and that dialog covers the home marker — which turns into a "home not detected → press ESC again" dead loop. That fallback was removed: failing the task is better than quitting the game.

## Four rules

1. **Always keep the `[JumpBack]` prefix**: the hub's exit `Common.CheckHomePage` is a leaf, and the jump-back is what hands control back to the caller. Without it the hub ends the flow and the task "succeeds" without doing anything.
2. **Always place the hub last**: it is a `DirectHit` node, so anything after it would never be evaluated.
3. **`[JumpBack]` handlers inside the hub must be leaves and must not be `DirectHit`**, otherwise they starve the convergence check. The hub's `next` must also contain no `DirectHit` fallback at all (the system back key in particular), or the convergence check never gets a turn.
4. **List order**: `[JumpBack]` handlers first, the non-JumpBack convergence check last. A node's `next` and `on_error` are counted together, so the same target must not appear twice (`pnpm check:maa` reports `duplicate-next`).

## When to use on_error

Reserve `on_error` for genuine failure fallbacks, for example "the stage-exit button did not respond after several clicks" or "a custom recognition gave up after waiting". **Do not route normal paths through `on_error`** — every hit writes a node-failure and error-handling entry to the log, which inflates log size over long runs and hides real failures.

## Tasks already wired up

| Task                                | Entry                                             | Notes                                                                                                                  |
| ----------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Resource farming / leftover stamina | `FarmResources.EnsureHome`                        | Mid-flow `FarmResources.Start` failures also return to this gate                                                       |
| Reward claiming                     | `ClaimRewards` (already a DirectHit list)         | The hub sits last in that list                                                                                         |
| PVP battles                         | `PVP.EnsureHome`                                  | —                                                                                                                      |
| Stamina info                        | `StaminaInfo.EnsureHome`                          | After the custom recognition gives up the hub takes over                                                               |
| Event stage / event shop            | `EventStage.EventHub` / `EventStage.EventHubShop` | The gate nodes `EnsureHome` / `EnsureHomeShop` are internal routing targets reached via `CheckEventHub`'s `other_next` |
| Game startup                        | Not wired                                         | The game may not be in-game yet; the hub's overlay handling and home check do not apply there                          |

## Adding a new screen

Add one `[JumpBack]` handler to the hub's `next` (a template match or a custom recognition); callers stay unchanged. If the new screen has its own notion of "home" (for example the event page's `flare_home.png`), create a scoped gate node with the same shape instead of modifying the shared hub.
