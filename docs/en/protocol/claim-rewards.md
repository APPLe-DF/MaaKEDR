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

- `ClaimRewards.Start`: weekly entry badge
- `ConfirmInterface`: reward interface; `next` includes `MedalDisplay` and `ExitRewardInterface`
- `CheckDaily` / `CheckWeekly` / `CheckMilitary`: section badges
- `ClaimButton`: claim button; afterwards handle `Common.CheckItemObtained` popup and `MedalDisplay`
- `MedalDisplay`: recognize and click the "medal obtained" popup (see `claim_rewards/daily/medal_display.png`)

### Battle pass

- `BattlePass.ClickEntry` / `RetryClickEntry`: entry, may click fixed coordinates (see pipeline)
- `CheckTaskComplete`: task-complete tab; may switch by fixed coordinates
- `CheckRewardList` / `ClaimRewardButton`: claim rewards from the list

### Dispatch

- `DispatchClaim.Start` → `ClaimButton` → `RedeployConfirm` (optional) → `Exit`

### Mailbox

- `Mailbox.Start` → `ConfirmInterface` → OCR "claim all" → back

### Premium shop (PremiumShop)

Default off (`claim_premium_shop`); for players with a premium account who can claim a free item daily.

```text
MainHub → [JumpBack]ClickShopIcon (max_hit: 1, enter the shop only once per task)
  → ConfirmShopInterface (confirm shop UI)
       → ClickPremiumShop: recognizes the premium-shop entry WITH red dot (claimable state); enters only when hit
       → NoPremiumShopEntry (fallback): no red dot / not enabled → notify and return home
  → ConfirmPremiumShop (confirm premium shop UI) → PurchaseHub (DirectHit)
       → ClickFreeItem: recognizes the "free item" button; click → ConfirmPurchase
            → confirm purchase → [JumpBack]Common.CheckItemObtained (item popup) → back to PurchaseHub
       → no free item → ReturnMain
  → ReturnMain → MainHubIdle (success exit after returning home)
```

Key points:

- **Red dot means claimable**: `premium_shop_entry.png` is captured WITH the red dot (claimable state); without the red dot the match score stays below the threshold and is treated as "already claimed today / not enabled" — the shop is not entered.
- **`NoPremiumShopEntry`**: DirectHit fallback at the end of `ConfirmShopInterface.next` and `ClickPremiumShop.next`; toasts "no claimable premium-shop entry detected, check whether the premium account is enabled" and returns home — no `on_error`, no timeout wait, no error screenshots.
- **`ClickShopIcon.max_hit: 1`**: the shop icon is a permanent element; without this cap the `MainHub` poll would keep entering the shop forever (dead loop).

### Common

- `Common.CheckItemObtained`: item-obtained popup
- `Common.BackButton`: back button

## Image directories

`resource/base/image/claim_rewards/` is organized by sub-module: `daily/` (incl. medal popup), `battlepass/`, `mailbox/`, `dispatch/`, `premium_shop/`; shared templates (`back_button.png`, `item_obtained_dialog.png`, etc.) live in `resource/base/image/`.
