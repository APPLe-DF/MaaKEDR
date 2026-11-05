---
order: 3
icon: ri:gift-line
---

# Claim Rewards Protocol

"Claim rewards" sweeps the rewards scattered across home-screen entries in one run: dispatch, daily / weekly /
military achievements, battle pass, mailbox, plus the premium-shop daily free item (off by default). The whole flow is
driven by `ClaimRewards.MainHub` polling, and every sub-module entry is a `[JumpBack]` node.

## Task entry

| Task                           | Entry          | Definition                 | Pipeline                                    | Default | Options                                                                                             |
| ------------------------------ | -------------- | -------------------------- | ------------------------------------------- | ------- | --------------------------------------------------------------------------------------------------- |
| 领取奖励 (claim rewards)       | `ClaimRewards` | `tasks/claim_rewards.json` | `resource/base/pipeline/claim_rewards.json` | on      | `claim_dispatch`, `claim_daily_rewards`, `claim_battle_pass`, `claim_mailbox`, `claim_premium_shop` |
| 剩余奖励领取 (claim remaining) | `ClaimRewards` | same                       | same                                        | off     | same                                                                                                |

Both tasks share the same entry and the same options; they differ only in where they run. `剩余奖励领取` sits late in
the task chain to collect rewards produced by earlier tasks (e.g. PVP settlement rewards, usually in the mailbox); the
`Daily` / `Activity` presets schedule it once before and once after the main tasks.

## Data flow

```text
tasks/claim_rewards.json
  ├─ task[0] 领取奖励 (default_check: true) + task[1] 剩余奖励领取 (default_check: false)
  └─ option: 6 switches → cases[].pipeline_override only patches the entry node
       claim_dispatch=No        → DispatchClaim.Start.enabled = false
       claim_daily_rewards=No   → ClaimRewards.Start.enabled = false
       claim_battle_pass=No     → BattlePass.Start.enabled = false
       claim_mailbox=No         → Mailbox.Start.enabled = false
       claim_premium_shop=No    → PremiumShop.ClickShopIcon.enabled = false
       dispatch_redeploy=No     → rewrites DispatchClaim.ClaimButton.next + DispatchClaim.RedeployConfirm
  → resource/base/pipeline/claim_rewards.json (also defines Common.BackButton / Common.CheckItemObtained)
  → no Custom nodes: "is anything claimable" is decided purely by ColorMatch red dots
```

## Sub-module switches

| Option key            | Widget | Default | Meaning                   | Patched nodes                                                                                                            |
| --------------------- | ------ | ------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `claim_dispatch`      | switch | on      | Dispatch rewards          | off → `DispatchClaim.Start.enabled = false` (the whole dispatch chain is skipped)                                        |
| `dispatch_redeploy`   | switch | on      | Redeploy after claiming   | off → `DispatchClaim.RedeployConfirm` becomes DirectHit + DoNothing and is dropped from `DispatchClaim.ClaimButton.next` |
| `claim_daily_rewards` | switch | on      | Daily / weekly / military | off → `ClaimRewards.Start.enabled = false`                                                                               |
| `claim_battle_pass`   | switch | on      | Battle pass               | off → `BattlePass.Start.enabled = false`                                                                                 |
| `claim_mailbox`       | switch | on      | Mailbox                   | off → `Mailbox.Start.enabled = false`                                                                                    |
| `claim_premium_shop`  | switch | off     | Premium shop daily reward | off → `PremiumShop.ClickShopIcon.enabled = false`                                                                        |

`dispatch_redeploy` is a nested sub-option of `claim_dispatch`: it only appears in the GUI when dispatch is on.

## Overall flow (MainHub)

```text
ClaimRewards (DirectHit entry list)
  ├─ ClaimRewards.EnsureHome (confirm home; otherwise [JumpBack]Common.EnsureHome)
  ├─ ClaimRewards.CheckMainInterface (home marker + click, clears leftover popups)
  ├─ ClaimRewards.MainHub (polling hub)
  └─ [JumpBack]Common.EnsureHome (trailing fallback)

MainHub.next (polled in order; a hit runs and jumps back)
  → [JumpBack]DispatchClaim.Start
  → [JumpBack]ClaimRewards.Start
  → [JumpBack]BattlePass.Start
  → [JumpBack]Mailbox.Start
  → [JumpBack]PremiumShop.ClickShopIcon (off by default)
  → [JumpBack]Common.CheckItemObtained (item popup fallback)
  → ClaimRewards.MainHubIdle (all claimed → home marker as the success exit)
```

### Exit mechanics (JumpBack stack)

Every sub-module entry in `MainHub.next` is a `[JumpBack]` node: once hit and executed it pushes the caller and jumps back to `MainHub` to poll the next entry; an entry becomes unrecognizable after its reward is claimed, so the poll advances naturally. When no entry can be recognized anymore, `MainHubIdle` (a plain node at the end of `next`, matching `more.png`) is hit — the JumpBack stack is empty and the node has no `next`, so the task succeeds.

> [!NOTE]
> Do not use `on_error` for normal branches such as "nothing to claim": `on_error` automatically saves a screenshot on trigger, which will bloat the log directory if fired often. Normal branches belong at the end of `next` as fallbacks.

## Key nodes

### Home check

- `ClaimRewards.EnsureHome`: matches `more.png` (`timeout: 60000`); on a hit it goes to `CheckMainInterface`, otherwise `[JumpBack]Common.EnsureHome` returns home and retries.
- `ClaimRewards.CheckMainInterface`: recognizes the home marker and **clicks once**, `next` → `MainHub` (no `[JumpBack]`, otherwise the JumpBack stack would prevent the task from ending).
- `ClaimRewards.MainHubIdle`: recognizes the home marker; success exit when everything is claimed. Sits at the end of `MainHub.next`.

### Daily / weekly / military

- `ClaimRewards.Start`: weekly entry — "claimable" is decided by **ColorMatch** (entry red-dot color range RGB ~[200-255, 60-150, 20-100], connected pixels ≥ 50; hit means there is something to claim; miss falls through to the next entry), `max_hit: 5`, `timeout: 5000`
- `ConfirmInterface`: reward interface (`claim_rewards/daily/reward_interface.png`, `max_hit: 10`); `next` includes `MedalDisplay` and `ExitRewardInterface`
- `CheckDaily` / `CheckWeekly` / `CheckMilitary`: section "claimable" checks (also **ColorMatch** red-dot color match, `max_hit: 5`); a hit clicks that section
- `ClaimButton`: claim button (`claim_rewards/daily/claim_button.png`); afterwards handle `MedalDisplay` (medal popup) first, then `Common.CheckItemObtained` (item popup)
- `MedalDisplay`: recognize and click the "medal obtained" popup (see `claim_rewards/daily/medal_display.png`)

### Battle pass

- `BattlePass.Start` / `ClickEntry` / `RetryClickEntry`: battle-pass entry — "claimable" decided by **ColorMatch** red-dot color match; `Start` only recognizes, the click is done by `ClickEntry` / `RetryClickEntry`
- `CheckTaskComplete`: task-complete tab (ColorMatch locates the claimable red dot and clicks it, `max_hit: 1` to avoid clicking the tab repeatedly)
- `CheckRewardList` / `ClaimRewardButton`: claim rewards from the list (`CheckRewardList` uses ColorMatch, `max_hit: 5`; `ClaimRewardButton` uses `claim_rewards/battlepass/battlepass_claim_button.png`)
- `RewardDisplay`: battle-pass reward display (`claim_rewards/battlepass/battlepass_reward_display.png`), clicked on a hit

### Dispatch

- `DispatchClaim.Start`: dispatch entry — "claimable" decided by **ColorMatch** red-dot color match → `ClaimButton` → `RedeployConfirm` (optional) → `Exit`; `Start.next` also lists `Exit`, so a panel that opens straight into "Close" finishes cleanly
- The entry "retry click" node was removed: re-clicking with the same red-dot criterion while the panel is animating lands inside the panel and desyncs the claim state (Issue #86). If the entry click fails, `Start` times out and fails instead of clicking again
- `DispatchClaim.Start` carries `max_hit: 1`, so the dispatch branch is entered at most once per task run. Otherwise, if the red dot has not disappeared yet, `[JumpBack]DispatchClaim.Start` in `MainHub.next` would re-enter it right after `Exit` and loop "open panel → close panel", starving the remaining branches
- With `dispatch_redeploy` off: `DispatchClaim.ClaimButton.next` becomes `[Common.CheckItemObtained, DispatchClaim.RedeployConfirm, DispatchClaim.Exit]`, and `DispatchClaim.RedeployConfirm` becomes an empty DirectHit + DoNothing node — still on the path, but it no longer clicks "redeploy"

### Mailbox

- `Mailbox.Start` (`max_hit: 5`) → `Mailbox.ClickEntry` → `Mailbox.ConfirmInterface` (`mailbox_interface.png`) → `Mailbox.ClaimButton` (OCR "一键领取", `max_hit: 1`) → `Mailbox.BackButton` back out

### Premium shop (PremiumShop)

Off by default (`claim_premium_shop`); for players with a premium account who can claim a free item daily.

```text
MainHub → [JumpBack]ClickShopIcon (ColorMatch detects the shop icon red dot (claimable state), clicks to enter; max_hit: 2, enter the shop at most twice per task)
  → ConfirmShopInterface (confirm shop UI)
       → ClickPremiumShop: ColorMatch recognizes the premium-shop entry WITH red dot (claimable state); enters only when hit
       → NoPremiumShopEntry (fallback): no red dot / not enabled → return home
  → ConfirmPremiumShop (confirm premium shop UI) → PurchaseHub (DirectHit)
       → ClickFreeItem: ColorMatch recognizes the "free item" button red dot; click → ConfirmPurchase
            → confirm purchase → [JumpBack]Common.CheckItemObtained (item popup) → back to PurchaseHub
       → no free item → ReturnMain
  → ReturnMain → MainHubIdle (success exit after returning home)
```

Key points:

- **Red dot means claimable**: `ClickPremiumShop` uses **ColorMatch** (red-dot color range RGB [200-255, 60-150, 20-100], connected pixels ≥ 50) to decide whether the entry is in a claimable state; without the red dot the recognition fails and is treated as "already claimed today / not enabled" — the shop is not entered.
- **`NoPremiumShopEntry`**: DirectHit fallback at the end of `ConfirmShopInterface.next` and `ClickPremiumShop.next`; it returns home through `ReturnMain` — no `on_error`, no timeout wait, no error screenshots.
- **Red dot gates entry**: `ClickShopIcon` / `RetryClickShopIcon` use **ColorMatch** to decide whether the home-screen shop icon carries a red dot (claimable content); without it the recognition fails and the shop is not entered, falling through to the next poll entries.
- **`ClickShopIcon.max_hit: 2`**: the shop icon is a permanent element; without this cap the `MainHub` poll would keep entering the shop forever (dead loop).
- **`on_error` is only for real failures**: `ClickPremiumShop` / `RetryClickPremiumShop` / `ConfirmPremiumShop` point `on_error` at `PremiumShop.ReturnMain`, so a premium entry that cannot be clicked or a UI confirmation failure exits safely.

### Common

- `Common.CheckItemObtained`: item-obtained popup (`item_obtained_dialog.png`), defined in this file and referenced by name from `Common.EnsureHome`
- `Common.BackButton`: back arrow (`back_button.png`), same situation

## Recognition approach

This task decides "is there anything claimable" with **ColorMatch color matching** instead of small templates:

- Entry red dots / corner badges (daily / weekly / military tabs, battle pass, dispatch, premium shop, free item) are detected by a color range (RGB lower/upper ≈ `[200, 60, 20]` ~ `[255, 150, 100]`); `connected: true` (only connected pixel blocks count) + `count: 50` (minimum pixel count) suppress false positives;
- Color-based detection is insensitive to subtle visual changes (UI animation, anti-aliasing, image-compression processing) and needs no multi-template variants; entry-icon style changes no longer affect the "claimable or not" decision;
- Tune the exact color band per node in `claim_rewards.json` (`param.lower`/`param.upper`) if a new entry's red dot has a different color.

## Files to touch when changing this flow

1. **Add a sub-module**: add an entry node in `resource/base/pipeline/claim_rewards.json` (red-dot check + `[JumpBack]`-friendly) and insert it into `ClaimRewards.MainHub.next` in the right place (before the trailing `MainHubIdle`)
2. **Add a switch**: add a `switch` in `tasks/claim_rewards.json`; when off, its `cases[].pipeline_override` should only carry `{"<entry node>": {"enabled": false}}`
3. **Attach it to both tasks**: `领取奖励` and `剩余奖励领取` each have their own `option` array — add the new option to **both**
4. **Add a template image**: put it in `resource/base/image/claim_rewards/<sub-module>/`; red dots need no template
5. **Tune the red-dot color band**: change `lower` / `upper` / `count` of that node's `ColorMatch`
6. **Validate**: `pnpm exec maa-tools check`, `pnpm check` before submitting

## Image directories

`resource/base/image/claim_rewards/` is organized by sub-module: `daily/` (incl. medal popup), `battlepass/`, `mailbox/`, `dispatch/`, `premium_shop/`; shared templates (`back_button.png`, `item_obtained_dialog.png`, etc.) live in `resource/base/image/`. Red-dot / badge elements are decided by ColorMatch and have no dedicated template images.

## Acceptance checklist

After changing this task, verify in order:

1. Each sub-module entry (dispatch / daily / battle pass / mailbox / premium shop) runs alone and claims everything
2. End-to-end with all sub-modules enabled: polls in order, no dead loop
3. With `dispatch_redeploy` off, dispatch claims everything and closes the screen without clicking "redeploy"
4. Restart halfway through: remaining rewards are still claimed (JumpBack stack rebuilt correctly)
5. Task ends normally when everything is claimed (hits `MainHubIdle`, not `on_error`)
6. Item popup / medal popup during claiming are handled
7. Entry icons with multiple styles/states (multi-template): every variant is recognized and entered correctly
8. Full regression: runs together with other tasks (startup, farm, PVP) without conflict
