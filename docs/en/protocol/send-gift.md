---
order: 8
icon: ri:hand-heart-line
---

# Send Gift Protocol

The **Send Gift** task is a standalone daily flow: from the home screen it opens the friend list, then in each round
it gifts the **topmost still giftable** friend and swipes up one screen, until the OCR reads the daily quota `20/20`
or the round limit falls back. "Giftable" is decided by
[an intersection of two recognitions](../develop/custom.md): the template box must overlap the golden connected
region, so already-gifted (grey) buttons are skipped naturally.

The implementation maps node-for-node to the `SendGift` task in MAK (`MaaAssistantKedrgame`); the differences are
concentrated in **how the friend list is reached**: MAK jumps to `Friend_FriendList` with the `SceneJump` scene graph,
while this project uses the return-to-home hub plus the home-screen friend icon plus an OCR confirmation. The main
loop's flow logic, ROIs, templates, `max_hit` values and the swipe gesture follow MAK. Two further deviations are not
listed in the table below: MAK's `Common_AllOfIntersect` is renamed to `AllOfIntersect` here, and MAK's
"正在前往好友列表……" entry log is not kept.

## Task entry

| Task      | Entry                 | Definition             | Pipeline                                | Checked | Options                |
| --------- | --------------------- | ---------------------- | --------------------------------------- | ------- | ---------------------- |
| Send Gift | `SendGift.EnsureHome` | `tasks/send_gift.json` | `resource/base/pipeline/send_gift.json` | yes     | none (fixed behaviour) |

The task belongs to the `Daily` group and is checked by default in the GUI; it is **not** part of the
`tasks/preset/Daily.json` chain, so selecting the "daily" preset does not enable it — tick it in the GUI instead.

## Data flow

```text
tasks/send_gift.json (no options, no pipeline_override)
  → resource/base/pipeline/send_gift.json
       ├─ navigation: Common.EnsureHome hub + SendGift.ClickFriendEntry + SendGift.CheckFriendList
       └─ main loop: SendGift.Loop → SendGift.Step → SendGift.Do / SendGift.Swipe
  → SendGift.Do uses the custom recognition AllOfIntersect (`@AgentServer.custom_recognition("AllOfIntersect")` in
    agent/custom/recognition/general.py; the `general` module is listed in `RECOGNITION_MODULES` in `__init__.py`)
  → templates resource/base/image/send_gift/homepage_friend.png, send_gift/gift_button.png
```

`SendGift.Do.custom_recognition_param` is written as a **JSON object** exactly like MAK (do not serialize it into a
string); only the template path changes to this project's directory:

```json
{
    "all_of": [
        {
            "type": "TemplateMatch",
            "param": {
                "template": "send_gift/gift_button.png",
                "roi": [
                    970,
                    110,
                    125,
                    595
                ],
                "green_mask": true
            }
        },
        {
            "type": "ColorMatch",
            "param": {
                "roi": [
                    970,
                    110,
                    125,
                    595
                ],
                "lower": [
                    235,
                    235,
                    80
                ],
                "upper": [
                    255,
                    255,
                    115
                ],
                "connected": true,
                "count": 600
            }
        }
    ],
    "order_by": "Vertical",
    "index": 0
}
```

> Why an object and not a string: MaaFW always hands `custom_recognition_param` to the Python callback as a JSON string.
> An object in the node is serialized once, so the callback receives `{"all_of": ...}`; a JSON string in the node is
> serialized a second time and arrives as `"{\"all_of\": ...}"` (double escaping). `parse_params` unwraps both, but the
> string form is harder to read and adds an escaping layer.

## Flow

```text
SendGift.EnsureHome (DirectHit gate node)
  ├─ SendGift.CheckHomePage (more.png global home marker)
  │    ├─ SendGift.ClickFriendEntry (homepage_friend.png, post_wait_freezes 500)
  │    │    ├─ SendGift.CheckFriendList (OCR "好友列表") → SendGift.Loop
  │    │    ├─ SendGift.RetryClickFriendEntry (retry when the click was lost)
  │    │    └─ [JumpBack]Common.CheckItemObtained
  │    └─ [JumpBack]Common.EnsureHome
  └─ [JumpBack]Common.EnsureHome

SendGift.Loop (DirectHit; every round checks the quota first)
  ├─ SendGift.QuotaFull (OCR 20/20) → SendGift.Finish
  ├─ [JumpBack]SendGift.Step
  └─ SendGift.Finish

SendGift.Step (DirectHit, max_hit 50)
  ├─ SendGift.Do (AllOfIntersect, max_hit 20) → SendGift.Swipe
  └─ SendGift.Swipe (subtree terminus: after the swipe, [JumpBack] returns to Loop)
```

`SendGift.QuotaFull` reads the bottom-right corner of the friend list at `[1120, 665, 135, 25]` with
`expected: 20\s*[/／]\s*20` (both half-width and full-width slashes). `SendGift.Swipe` goes
`[680, 420, 200, 10] → [680, 270, 200, 10]` with `end_hold: 1000`, bringing the next rows of friends into view.

## Node map against MAK

| MAK (`assets/resource/pipeline/Friend/SendGift.json`) | This project                                                                                                                                   | Note                                             |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| `SendGiftMain` (`SceneJump`)                          | `SendGift.EnsureHome` + `SendGift.CheckHomePage` + `SendGift.ClickFriendEntry` + `SendGift.RetryClickFriendEntry` + `SendGift.CheckFriendList` | navigation uses the home hub                     |
| `SendGiftLoop`                                        | `SendGift.Loop`                                                                                                                                | `next` order unchanged                           |
| `SendGiftQuotaFull`                                   | `SendGift.QuotaFull`                                                                                                                           | ROI / `expected` unchanged                       |
| `SendGiftStep`                                        | `SendGift.Step`                                                                                                                                | `max_hit: 50` unchanged                          |
| `SendGiftDo`                                          | `SendGift.Do`                                                                                                                                  | recognition params and `action: Click` unchanged |
| `SendGiftSwipe`                                       | `SendGift.Swipe`                                                                                                                               | gesture unchanged                                |
| `SendGiftFinish`                                      | `SendGift.Finish`                                                                                                                              | `focus` log text unchanged                       |

> Recognizer name: MAK's `Common_AllOfIntersect` is renamed to `AllOfIntersect` here; MAK's `SendGiftMain`
> "正在前往好友列表……" log is not kept.

## Key conventions

- **`[JumpBack]SendGift.Step` is what makes the loop work**: the `SendGift.Step` subtree runs dry at `SendGift.Swipe`, and
  the jump-back hands control back to `SendGift.Loop`, so every round re-checks the quota and walks one more round.
  Never add a `next` to `SendGift.Swipe` — that turns the loop into a straight line.
- **`max_hit` counts successful hits**: after 20 hits `SendGift.Do` is skipped and the remaining rounds only swipe; after
  50 successful rounds of `SendGift.Step`, `SendGift.Loop` can only match `SendGift.Finish` (the round fallback).
- **The `ColorMatch` sub-recognition must keep `connected: true`**: otherwise the whole ROI becomes one result, the
  intersection stops working and `SendGift.Do` may click already-gifted friends.
- **The daily quota is hard-coded in the recognition regex**: when the game changes the limit, update both numbers in
  `SendGift.QuotaFull.expected`.
- **Thresholds and colour range follow MAK defaults**: the template matching inside `SendGift.Do` uses the framework
  default threshold 0.7 (`green_mask` removes the green background of the gift icon); `SendGift.CheckHomePage` keeps
  `Common.CheckHomePage`'s `threshold: 0.75`; `ColorMatch` uses the RGB method (default `method: 4`),
  gold range `[235,235,80]`–`[255,255,115]`, `count: 600`.
- **No new waiting was introduced**: navigation nodes settle the screen with `post_wait_freezes`; the main loop adds no
  `pre_delay` / `post_delay`.
- **Unhandled edge cases (same as MAK)**: a second confirmation dialog or the "item obtained" popup during gifting is not
  handled; add `[JumpBack]Common.CheckItemObtained` to `SendGift.Do.next` or a dedicated node if the game introduces one.

## Files to touch when changing this flow

1. Flow nodes: `resource/base/pipeline/send_gift.json` (do not rename `SendGift.*`; `tasks/send_gift.json` refers to `entry`)
2. Intersection logic: `AllOfIntersect` in `agent/custom/recognition/general.py`; the recognition name is registered by
   `@AgentServer.custom_recognition("AllOfIntersect")`, and the module name is listed in `RECOGNITION_MODULES` in
   `__init__.py`
3. Templates: the two images under `resource/base/image/send_gift/` (cropped from a 720p screenshot)
4. Navigation changes (e.g. a different entry icon): only the template and ROI of `SendGift.ClickFriendEntry` /
   `SendGift.RetryClickFriendEntry`
5. Task name, group and description: `tasks/send_gift.json`; register a new task file in `interface.json`'s `import`
6. Checks: `pnpm check` (format + schema + pipeline integrity + project lint), `pnpm exec maa-tools check` (pipelines only),
   `pnpm check:py` and `pnpm test:py` after touching Python
7. Sync this page: node names and file paths must match the code character by character

## Acceptance checklist

1. Tick "Send Gift" from the home screen: the friend icon opens the friend list, and no other top bar button is hit
2. Friends whose gift button is golden are gifted one by one; already-gifted (grey) buttons are skipped
3. After each gift the list swipes up one screen, bringing the next rows into view
4. When the quota is used up, the OCR hits `20/20` and the task finishes with `今日赠礼已达上限` and `赠送礼物完成！`
5. When the quota is not used up but the list is exhausted, the `SendGift.Step` `max_hit` fallback ends the task cleanly
6. Starting from a non-home screen (e.g. right after leaving a stage) still returns home and enters the friend list
