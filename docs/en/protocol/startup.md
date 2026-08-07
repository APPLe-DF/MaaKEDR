---
order: 2
icon: ri:play-circle-line
---

# Startup & Login

| Item      | Value                                        |
| --------- | -------------------------------------------- |
| Task      | `tasks/startup.json`                         |
| Pipeline  | `resource/base/pipeline/startup.json`        |
| Overrides | bilibili / taptap pipeline packs when needed |

## Flow

```text
Launch game → loading / start → daily login popups → main UI → done
```

Templates live under `resource/base/image/` (e.g. `daily_login_reward.png`, `main_option.png`). Prefer freezes/recognition over long fixed delays.

## Acceptance checklist

After changing this task, verify in order:

1. All three resource packs (official / bilibili / taptap) launch correctly (server overrides apply)
2. Cold start (no process) and warm start (process already running) both work
3. Daily login popup present / absent paths both verified
4. Screenshots during launch animation are not taken before the screen settles (freezes/recognition works)
5. Launch failure (e.g. network error popup) shows a fallback notice instead of hanging
6. Full regression: launch followed by claim / farm tasks runs without conflict
