---
order: 7
icon: ri:heart-pulse-line
---

# Stamina Info Protocol

This page documents the **Stamina Info** task, which reads the stamina shown on the home screen at the end of the daily task chain and reports the estimated time until it refills naturally. The task is defined in `tasks/stamina_info.json`, enters at `StaminaInfo`, is checked by default, and runs last in the task chain.

## Task entry and options

| Task         | Entry         | Options                            |
| ------------ | ------------- | ---------------------------------- |
| Stamina Info | `StaminaInfo` | None (fixed ROIs, runs by default) |

## Flow

```text
StaminaInfo →（confirm home）→ StaminaInfo.Read → output refill info
            └─（not on home）→ StaminaInfo.ClickHome → StaminaInfo
```

Conventions:

- `StaminaInfo` confirms the main interface with template `main_option.png`; if it is not reached within `timeout` (60s), `StaminaInfo.ClickHome` taps the home button and re-confirms, ensuring the read starts from the home screen.
- `StaminaInfo.Read` uses the custom recognition `ReadStamina` (`agent/custom/recognition/stamina.py`).

## ReadStamina recognition

The home-screen stamina digits are rendered at a **-45° tilt**. `ReadStamina` rotates each ROI by the opposite of `tilt_angle` to straighten the digits before OCR, then extracts the first integer:

| Param         | Default               | Description                                              |
| ------------- | --------------------- | -------------------------------------------------------- |
| `current_roi` | `[1120, 512, 38, 44]` | ROI of the current stamina digits                        |
| `cap_roi`     | `[1152, 484, 28, 30]` | ROI of the stamina cap digits                            |
| `tilt_angle`  | `-45`                 | Screen tilt of the digits (legacy alias: `rotate_angle`) |
| `stamina_cap` | none                  | Optional fallback cap value if OCR of `cap_roi` fails    |

- Missing ROIs, non-positive ROI width/height, or an ROI beyond the screenshot bounds produce a warning and skip OCR without aborting the task.
- `stamina_cap` is coerced to `int` and validated; invalid values are warned and ignored.

## Refill-time calculation

- Recovery rate: **4 min / 1 point** (`STAMINA_RECOVER_MINUTES_PER_POINT`).
- Below cap: `missing = cap - current`, `full_time = now + missing * 4min`, following MAA-style output:

    ```text
    Stamina will be full at <YYYY-MM-DD HH:MM>. (Xh Ym remaining)
    ```

- At the natural-recovery cap, stamina no longer grows: reports "already at the natural recovery cap, no longer refilling over time"; if above cap (e.g. after a stamina item), reports "above the natural recovery cap, no longer refilling over time".
- Any read/write failure only skips this output; other tasks are unaffected.
