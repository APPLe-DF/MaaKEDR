---
order: 7
icon: ri:heart-pulse-line
---

# Stamina Info Protocol

This page documents the **Stamina Info** task, which reads the stamina shown on the home screen at the end of the daily task chain and reports the estimated time until it refills naturally. The task is defined in `tasks/stamina_info.json`, enters at `StaminaInfo.EnsureHome` (an always-matching gate node), is checked by default, and runs last in the task chain.

## Task entry and options

| Task         | Entry                    | Definition                | Pipeline                              | Options                            |
| ------------ | ------------------------ | ------------------------- | ------------------------------------- | ---------------------------------- |
| Stamina Info | `StaminaInfo.EnsureHome` | `tasks/stamina_info.json` | `resource/base/pipeline/stamina.json` | none (fixed ROIs, runs by default) |

## Data flow

```text
tasks/stamina_info.json (no options, no pipeline_override)
  → resource/base/pipeline/stamina.json (6 nodes)
  → agent/custom/recognition/stamina.py
       CheckStaminaPage (entry routing), ReadStamina (read digits + compute refill time)
  → output: one log line "体力将在 <YYYY-MM-DD HH:MM> 回满。(Xh Ym 后)"
```

## Flow

```text
StaminaInfo.EnsureHome (gate node, always matches, max_hit: 6)
  ├─ StaminaInfo (routed by CheckStaminaPage: on home?)
  │    ├─ yes → StaminaInfo.Read (retried via ReadRetry, 3 attempts max) → output refill info (still failing → task fails)
  │    └─ no  → StaminaInfo.ClickHome (retried via ClickHomeRetry, 3 attempts max) → re-confirm
  └─ neither matched (home button ineffective for 3 rounds, custom recognition gives up) → the shared hub Common.EnsureHome returns home, then retries
```

Conventions:

- `StaminaInfo.EnsureHome` is an always-matching gate: its `next` lists the main path `StaminaInfo` first and the shared hub `[JumpBack]Common.EnsureHome` last (reused across files, see [Shared Nodes & Return-to-Home Hub](../develop/common.md)).
- The `StaminaInfo` entry uses the custom recognition `CheckStaminaPage` (`agent/custom/recognition/stamina.py`) as a router: it confirms the main interface with template `main_option.png`; on the home screen it routes to `StaminaInfo.Read`, otherwise it routes to `StaminaInfo.ClickHome`, which taps the home button and re-confirms that the read starts from the home screen.
- Routing is done via `context.override_next` (same pattern as `CheckEventHub`) instead of listing `Read` and `ClickHome` together in one `next` list: with a plain list, a `Read` recognition failure would fall through to `ClickHome`, which also matches on the home screen and clicks it — an infinite "read fails → tap home → read again" loop.
- `StaminaInfo.Read` uses the custom recognition `ReadStamina` (`agent/custom/recognition/stamina.py`); on failure (e.g. incomplete stamina digits) it is retried at most twice (3 read attempts in total) and then the task ends as failed instead of looping. The attempt count is controlled by the `StaminaInfo.ReadRetry` gate node (`max_hit=2` with `timeout=0`, one recognition per screenshot round), so it is independent of device OCR speed and never spins for a long time.
- The `StaminaInfo.ClickHome` branch is bounded symmetrically by the `StaminaInfo.ClickHomeRetry` gate (`max_hit=2` with `timeout=0`): the home button is matched/clicked at most 3 times; after `other_max` (default 3) consecutive misses (clicks that never reach home) `CheckStaminaPage` returns a recognition failure. That no longer fails the task by itself: the gate's trailing shared hub takes over (dismiss the item-obtained overlay / tap the top home button / generic back / system back key) and re-routes to `StaminaInfo` once home is reached.

## ReadStamina recognition

The home-screen stamina digits are rendered at a **-45° tilt**. `ReadStamina` rotates each ROI by the opposite of `tilt_angle` to straighten the digits before OCR, then extracts the first integer:

| Param         | Default               | Description                                              |
| ------------- | --------------------- | -------------------------------------------------------- |
| `current_roi` | `[1120, 512, 38, 44]` | ROI of the current stamina digits                        |
| `cap_roi`     | `[1152, 484, 28, 30]` | ROI of the stamina cap digits                            |
| `tilt_angle`  | `-45`                 | Screen tilt of the digits (legacy alias: `rotate_angle`) |
| `stamina_cap` | none                  | Optional fallback cap value if OCR of `cap_roi` fails    |

- The two ROIs and `tilt_angle` are written in `StaminaInfo.Read.custom_recognition_param`; the recognizer's internal defaults are empty, so an unconfigured node warns and skips OCR.
- Missing ROIs, non-positive ROI width/height, or an ROI beyond the screenshot bounds produce a warning and skip OCR without aborting the task.
- `stamina_cap` is coerced to `int` and validated; invalid values are warned and ignored.

## Refill-time calculation

- Recovery rate: **4 min / 1 point** (`STAMINA_RECOVER_MINUTES_PER_POINT`).
- Below cap: `missing = cap - current`, `full_time = now + missing * 4min`, following MAA-style output:

    ```text
    体力将在 <YYYY-MM-DD HH:MM> 回满。(Xh Ym 后)
    ```

- At the natural-recovery cap, stamina no longer grows: reports "already at the natural recovery cap, no longer refilling over time"; if above cap (e.g. after a stamina item), reports "above the natural recovery cap, no longer refilling over time".
- Any read/write failure only skips this output; other tasks are unaffected.

## Code map

| Area                     | Path                                                                         |
| ------------------------ | ---------------------------------------------------------------------------- |
| Task definition          | `tasks/stamina_info.json`                                                    |
| Pipeline                 | `resource/base/pipeline/stamina.json`                                        |
| Custom recognition       | `agent/custom/recognition/stamina.py`                                        |
| Recognition registration | `agent/custom/recognition/__init__.py`                                       |
| Home / back templates    | `resource/base/image/main_option.png`, `resource/base/image/return_main.png` |

## Files to touch when changing this flow

1. **Stamina digits moved** (resolution baseline or UI redesign): update `current_roi` / `cap_roi` / `tilt_angle` in `StaminaInfo.Read.custom_recognition_param`
2. **Recovery rate changed** (game value change): update `STAMINA_RECOVER_MINUTES_PER_POINT` in `agent/custom/recognition/stamina.py`
3. **Retry count**: change `max_hit` of `StaminaInfo.ReadRetry` / `StaminaInfo.ClickHomeRetry` (currently 2, i.e. 3 attempts in total)
4. **Routing targets**: `home_next` / `other_next` in `StaminaInfo.custom_recognition_param` and the static `next` of
   the `StaminaInfo` node must change together (the static `next` is the fallback for `override_next`; if they diverge
   the fallback path goes the wrong way)
5. **Home detection**: reuse `main_option.png` with ROI `[1199,6,77,83]`; do not add a task-specific home marker
6. **Validate**: `pnpm exec maa-tools check`, `pnpm check`; `pnpm check:py` after touching agent code

## Acceptance checklist

After changing this task, verify in order:

1. Run from the home screen: stamina and cap are read and the refill time plus remaining duration are logged
2. Run from a non-home screen (e.g. stage screen): the home button is clicked first, then stamina is read — no "read → tap home" loop
3. Full stamina / above-cap states: the "already at the natural recovery cap" style message is printed, no refill time computed
4. When the digits cannot be OCRed: the task fails after at most 3 attempts instead of spinning
5. Chained with other tasks: running last in the task chain does not affect the earlier tasks' results
