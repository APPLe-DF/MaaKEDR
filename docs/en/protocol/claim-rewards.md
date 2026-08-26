---
order: 3
icon: ri:gift-line
---

# Claim Rewards

| Item     | Value                                       |
| -------- | ------------------------------------------- |
| Entry    | `ClaimRewards`                              |
| Task     | `tasks/claim_rewards.json`                  |
| Pipeline | `resource/base/pipeline/claim_rewards.json` |

## Options

| Key                   | Meaning                                 |
| --------------------- | --------------------------------------- |
| `claim_dispatch`      | Dispatch rewards                        |
| `dispatch_redeploy`   | Redeploy after claim                    |
| `claim_daily_rewards` | Daily / weekly / military               |
| `claim_battle_pass`   | Battle pass                             |
| `claim_mailbox`       | Mailbox                                 |
| `claim_premium_shop`  | Premium shop daily reward (default off) |

## Flow

```text
ClaimRewards
  → CheckMainInterface (confirm home, then enter MainHub)
  → MainHub (home-screen feature recognition; polls every sub-module entry)
       → DispatchClaim.*
       → ClaimRewards.Start / ConfirmInterface / CheckDaily|Weekly|Military
       → BattlePass.*
       → Mailbox.*
       → PremiumShop.* (default off)
       → Common.CheckItemObtained (item popup fallback)
       → MainHubIdle (all claimed → recognize home screen as success exit)
```

### Exit mechanics (JumpBack stack)

Every sub-module entry in `MainHub.next` is a `[JumpBack]` node: once hit and executed it pushes the caller and jumps back to `MainHub` to poll the next entry; an entry becomes unrecognizable after its reward is claimed, so the poll advances naturally. When no entry can be recognized anymore, `MainHubIdle` (a plain node at the end of `next`, matching `main_option.png`) is hit — the JumpBack stack is empty and the node has no `next`, so the task succeeds.

> [!NOTE]
> Do not use `on_error` for normal branches such as "nothing to claim": `on_error` automatically saves a screenshot on trigger, which will bloat the log directory if fired often. Normal branches belong at the end of `next` as fallbacks.

## Key nodes

### Home check

- `ClaimRewards.CheckMainInterface`: confirm home and click, `next` → `MainHub` (no `[JumpBack]`, otherwise the JumpBack stack would prevent the task from ending).
- `ClaimRewards.MainHubIdle`: recognize home screen; success exit when everything is claimed. Sits at the end of `MainHub.next`.

### Daily / weekly / military

- `ClaimRewards.Start`: weekly entry — "claimable" is decided by **ColorMatch** (entry red-dot color range RGB ~[200-255, 60-150, 20-100], connected pixels ≥ 50; hit means there is something to claim; miss falls through to the next entry)
- `ConfirmInterface`: reward interface; `next` includes `MedalDisplay` and `ExitRewardInterface`
- `CheckDaily` / `CheckWeekly` / `CheckMilitary`: section "claimable" checks (also **ColorMatch** red-dot color match)
- `ClaimButton`: claim button; afterwards handle `MedalDisplay` (medal popup) first, then `Common.CheckItemObtained` (item popup)
- `MedalDisplay`: recognize and click the "medal obtained" popup (see `claim_rewards/daily/medal_display.png`)

### Battle pass

- `BattlePass.Start` / `ClickEntry` / `RetryClickEntry`: battle-pass entry — "claimable" decided by **ColorMatch** red-dot color match; `ClickEntry` may click fixed coordinates (see pipeline)
- `CheckTaskComplete`: task-complete tab (ColorMatch locates the claimable red dot; may switch by fixed coordinates)
- `CheckRewardList` / `ClaimRewardButton`: claim rewards from the list

### Dispatch

- `DispatchClaim.Start` / `RetryClick`: dispatch entry — "claimable" decided by **ColorMatch** red-dot color match → `ClaimButton` → `RedeployConfirm` (optional) → `Exit`

### Mailbox

- `Mailbox.Start` → `ConfirmInterface` → OCR "claim all" → back

### Premium shop (PremiumShop)

Default off (`claim_premium_shop`); for players with a premium account who can claim a free item daily.

```text
MainHub → [JumpBack]ClickShopIcon (ColorMatch detects the shop icon red dot (claimable state), clicks to enter; max_hit: 1, enter the shop only once per task)
  → ConfirmShopInterface (confirm shop UI)
       → ClickPremiumShop: ColorMatch recognizes the premium-shop entry WITH red dot (claimable state); enters only when hit
       → NoPremiumShopEntry (fallback): no red dot / not enabled → notify and return home
  → ConfirmPremiumShop (confirm premium shop UI) → PurchaseHub (DirectHit)
       → ClickFreeItem: ColorMatch recognizes the "free item" button red dot; click → ConfirmPurchase
            → confirm purchase → [JumpBack]Common.CheckItemObtained (item popup) → back to PurchaseHub
       → no free item → ReturnMain
  → ReturnMain → MainHubIdle (success exit after returning home)
```

Key points:

- **Red dot means claimable**: `ClickPremiumShop` uses **ColorMatch** (red-dot color range RGB [200-255, 60-150, 20-100], connected pixels ≥ 50) to decide whether the entry is in a claimable state; without the red dot the recognition fails and is treated as "already claimed today / not enabled" — the shop is not entered.
- **`NoPremiumShopEntry`**: DirectHit fallback at the end of `ConfirmShopInterface.next` and `ClickPremiumShop.next`; toasts "no claimable premium-shop entry detected, check whether the premium account is enabled" and returns home — no `on_error`, no timeout wait, no error screenshots.
- **Red dot gates entry**: `ClickShopIcon` / `RetryClickShopIcon` use **ColorMatch** to decide whether the home-screen shop icon carries a red dot (claimable content); without it the recognition fails and the shop is not entered, falling through to the next poll entries.
- **`ClickShopIcon.max_hit: 1`**: the shop icon is a permanent element; without this cap the `MainHub` poll would keep entering the shop forever (dead loop).

### Common

- `Common.CheckItemObtained`: item-obtained popup
- `Common.BackButton`: back button

## Recognition approach

This task decides "is there anything claimable" with **ColorMatch color matching** instead of small templates:

- Entry red dots / corner badges (daily / weekly / military tabs, battle pass, dispatch, premium shop, free item) are detected by a color range (RGB lower/upper ≈ `[200, 60, 20]` ~ `[255, 150, 100]`); `connected: true` (only connected pixel blocks count) + `count: 50` (minimum pixel count) suppress false positives;
- Color-based detection is insensitive to subtle visual changes (UI animation, anti-aliasing, image-compression processing) and needs no multi-template variants; entry-icon style changes no longer affect the "claimable or not" decision;
- Tune the exact color band per node in `claim_rewards.json` (`param.lower`/`param.upper`) if a new entry's red dot has a different color.

## Image directories

`resource/base/image/claim_rewards/` is organized by sub-module: `daily/` (incl. medal popup), `battlepass/`, `mailbox/`, `dispatch/`, `premium_shop/`; shared templates (`back_button.png`, `item_obtained_dialog.png`, etc.) live in `resource/base/image/`. Red-dot / badge elements are decided by ColorMatch and have no dedicated template images.

## Acceptance checklist

After changing this task, verify in order:

1. Each sub-module entry (dispatch / daily / battle pass / mailbox / premium shop) runs alone and claims everything
2. End-to-end with all sub-modules enabled: polls in order, no dead loop
3. Restart halfway through: remaining rewards are still claimed (JumpBack stack rebuilt correctly)
4. Task ends normally when everything is claimed (hits `MainHubIdle`, not `on_error`)
5. Item popup / medal popup during claiming are handled
6. Entry icons with multiple styles/states (multi-template): every variant is recognized and entered correctly
7. Full regression: runs together with other tasks (startup, farm, PVP) without conflict
