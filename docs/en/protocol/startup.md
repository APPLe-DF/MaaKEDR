---
order: 2
icon: ri:play-circle-line
---

# Startup & Login Protocol

The startup task is the first step of the whole task chain: launch the game process, click through the start screen
and the daily login reward, and stop on a recognizable home screen. It deliberately does **not** use the shared
return-to-home hub `Common.EnsureHome` — during launch the game may not be in-game yet, and pressing the back key can
quit the game.

## Task entry

| Item     | Value                                                                              |
| -------- | ---------------------------------------------------------------------------------- |
| Task     | 启动游戏 (`tasks/startup.json`, `default_check: true`)                             |
| Entry    | `LaunchGame`                                                                       |
| Pipeline | `resource/base/pipeline/startup.json`                                              |
| Packs    | `resource/bilibili/pipeline/startup.json`, `resource/taptap/pipeline/startup.json` |
| Options  | none                                                                               |

## Data flow

```text
tasks/startup.json (no options)
  → no task-level pipeline_override
  → resource/base/pipeline/startup.json: LaunchGame → … → CheckHomePageStable
  → server packs' startup.json only overrides LaunchGame.action.param.package (which install to launch)
  → no Custom nodes, so no agent code involved
```

## Typical flow

```text
LaunchGame (StartApp launches the game process)
  → WaitGameLoading (wait for loading to finish)
  → ClickToStart (click start, up to 3 times)
  → DailyLoginReward (daily login reward popup, clicked twice)
  → CheckHomePage (recognize the home marker main_option.png)
       ├─ matched but a popup is still there → [JumpBack]DailyLoginReward, then re-check
       └─ not matched → ClickHomePage (click the screen center 5 times)
            → [JumpBack]DailyLoginReward → CheckHomePageStable (home is stable, leaf node)
```

## Nodes and fields

| Node                  | Recognition / action                           | Key fields                                                                               |
| --------------------- | ---------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `LaunchGame`          | DirectHit / `StartApp`                         | `package: com.phxh.official.nld`, `timeout: 60000`                                       |
| `WaitGameLoading`     | TemplateMatch `game_loading.png` / DoNothing   | `roi [595,653,146,64]`, `post_wait_freezes: 500`, `post_delay: 4000`                     |
| `ClickToStart`        | TemplateMatch `startgame1.png` / Click         | `repeat: 3`, `pre_delay: 1000`, `post_delay: 4000`, `timeout: 30000`                     |
| `DailyLoginReward`    | TemplateMatch `daily_login_reward.png` / Click | `roi [405,115,103,106]`, `repeat: 2`, `post_delay: 500`                                  |
| `CheckHomePage`       | TemplateMatch `main_option.png` / DoNothing    | `roi [1199,6,77,83]`, `threshold: 0.75`, `next` starts with `[JumpBack]DailyLoginReward` |
| `ClickHomePage`       | DirectHit / Click                              | `target [588,369,9,11]`, `repeat: 5`, `repeat_delay: 500`                                |
| `CheckHomePageStable` | TemplateMatch `main_option.png` / DoNothing    | Leaf node, the task's success exit                                                       |

## Templates

Templates live in the `resource/base/image/` root (startup images are shared across tasks):

- `game_loading.png` — loading screen
- `startgame1.png` — start button
- `daily_login_reward.png` — daily login reward popup
- `main_option.png` — home-screen marker at the top right (also used by `Common.CheckHomePage` and others)

## Server overrides

The three servers differ only in the launch package, so a same-name node override is enough; every other task reuses
`base`:

| Pack     | File                                      | Override                           |
| -------- | ----------------------------------------- | ---------------------------------- |
| base     | `resource/base/pipeline/startup.json`     | `com.phxh.official.nld` (official) |
| bilibili | `resource/bilibili/pipeline/startup.json` | `com.phxh.nlddev.bilibili`         |
| taptap   | `resource/taptap/pipeline/startup.json`   | `com.phxh.taptap.nld`              |

When adding a server, change the launch package first; only add same-name nodes / images to that pack when the login
entry or channel-specific art really differs.

## Development notes

- Launch animation is long: use recognition nodes or `post_wait_freezes` instead of long fixed delays
- Popup order may change: list popup nodes side by side in `next` and use `[JumpBack]` for re-entrant popups
- Home detection always uses `main_option.png` (`roi [1199,6,77,83]`, threshold 0.75); do not invent another marker
- The flow must end on a **leaf node** (`CheckHomePageStable`), otherwise the task never succeeds

## Files to touch when changing this flow

1. Change the launch flow / add a screen: edit `resource/base/pipeline/startup.json`
2. Change the launch package (another server or channel): edit that pack's `pipeline/startup.json`, **not** `base`
3. Add a template image: put it in `resource/base/image/`, lower-case `snake_case` file name
4. Change the task description / default check: edit `description`, `default_check` in `tasks/startup.json`
5. Validate: `pnpm exec maa-tools check` (pipeline integrity), `pnpm check` before submitting

## Acceptance checklist

After changing this task, verify in order:

1. All three resource packs (official / bilibili / taptap) launch correctly (server package override applies)
2. Cold start (no process) and warm start (process already running) both work
3. Daily login popup present / absent paths both verified
4. Screenshots during launch animation are not taken before the screen settles (recognition / `post_wait_freezes` works)
5. Launch failure (e.g. network error popup) shows a fallback notice instead of hanging
6. Full regression: launch followed by claim / farm tasks runs without conflict
