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

Main hub after home check → dispatch / daily / battle pass / mailbox / premium shop (default off) modules → return to hub or exit.

`CheckMainInterface` must `next` into `MainHub` to avoid loops. Item popups: `Common.CheckItemObtained`.
