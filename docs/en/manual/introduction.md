---
order: 4
icon: mdi:information-outline
---

# Feature Introduction

MaaKEDR automates daily tasks in _雪松 (KEDR)_ to save you time.

## General Notes

- **Prerequisites**: apart from "Launch Game", every task expects the game to be running and interactive. Each task entry first checks whether the game is on the **home screen**; if not, the shared home-return hub tries, in order, closing the "item obtained" popup, tapping the top home button, tapping the common back button — then resumes the original flow. The hub retries up to 10 rounds before the task fails.
- **Task order**: tasks run top to bottom in the list. The recommended order is "Game Launch → farming / event → Claim Rewards → Remaining Stamina → PVP → Claim Remaining Rewards → Stamina Info"; see [Task Presets](#task-presets) below.
- **Options**: every task's options live under **Task Settings** in the GUI; see the matching section below for their meaning. Leave anything not mentioned at its default.

---

## Launch Game

Automatically starts the game and navigates to the main menu.

**Prerequisites:** the game is installed in the emulator.

**Features:**

- Launch the game process
- Click "Start Game"
- Handle daily login reward popups
- Detect and enter the main menu

**Options:** none — just enable the task.

> [!NOTE]
>
> Both a cold start (game not running) and a warm start (game already running) are supported. Keeping this task first in the chain is recommended.

---

## Claim Rewards

Claim various rewards with individual toggles.

**Prerequisites:** the game is logged in and on the home screen (the task confirms the home screen before claiming).

**Options:**

| Option                        | Type   | Default | Description                                                                  |
| :---------------------------- | :----- | :------ | :--------------------------------------------------------------------------- |
| Dispatch Claim                | Toggle | On      | Whether to open the dispatch screen and claim finished dispatches            |
| Redeploy                      | Toggle | On      | Shown when "Dispatch Claim" is on: redeploy after claiming, off = just close |
| Daily/Weekly/Military Rewards | Toggle | On      | Claim daily, weekly, and military achievement rewards                        |
| Battle Pass                   | Toggle | On      | Claim battle pass rewards                                                    |
| Mailbox                       | Toggle | On      | Claim mail attachments                                                       |
| Premium Shop Daily Reward     | Toggle | Off     | Claim the premium shop free item                                             |

### Dispatch Claim

When enabled, MaaKEDR will:

1. Enter the dispatch interface
2. Collect completed dispatch rewards
3. If **Redeploy** is on, redeploy missions
4. Close the dispatch interface

### Daily/Weekly/Military Rewards

Claims daily check-in, weekly mission, and military achievement rewards.

### Battle Pass

Claims unlocked battle pass rewards.

### Mailbox

Automatically collects mail attachments.

### Premium Shop Daily Reward

Automatically enters the premium shop and claims the daily free item (only when a claimable indicator is present; default off).

---

## Claim Remaining Rewards

The supplementary claim at the tail of the chain: collects rewards earned while the chain was running (PVP rewards, for example, usually land in the mailbox).

**Prerequisites:** the game is on the home screen; presets normally place it after "PVP".

**Options:** identical to [Claim Rewards](#claim-rewards) (dispatch, achievements, battle pass, mailbox, premium shop).

> [!TIP]
>
> "Claim Rewards" and "Claim Remaining Rewards" run the same flow — the only difference is where they sit in the chain: the first clears existing rewards up front, the second collects whatever the run itself produced.

---

## Farm Resources

Auto-battle resource stages with stamina management.

**Prerequisites:** the game is on the home screen; the target stage is unlocked (locked skill-training stages are detected and skipped).

**Options:**

| Option        | Type   | Default                | Description                                      |
| :------------ | :----- | :--------------------- | :----------------------------------------------- |
| Battle Mode   | Select | Single Battle          | Single Battle / Clear Stamina                    |
| Battle Count  | Select | 1                      | 1–6 / Max (Single Battle mode only)              |
| Category      | Select | Resource Collection    | Resource Collection / Skill Training             |
| Resource Type | Select | Special Funds          | Available under Resource Collection, see below   |
| Skill Type    | Select | Basic Skill Training   | Available under Skill Training, see below        |
| Stage         | Select | 1-1 / Basic Training 1 | Depends on the resource or skill type, see below |

### Battle Mode

- **Single Battle**: Runs the set number of battles then stops
- **Clear Stamina**: Keeps battling until stamina is depleted — ideal for overnight farming

### Resource Collection

| Resource Type     | Description                    |
| :---------------- | :----------------------------- |
| Special Funds     | Currency stages                |
| Physical Training | XP and upgrade material stages |
| Unit Rating       | Unit promotion material stages |
| Vehicle Drill     | Vehicle material stages        |

Stage counts differ by type (selectable in options):

- Special Funds: 1-1 … 1-5
- Physical Training: 2-1 … 2-4
- Unit Rating: 3-1 … 3-4
- Vehicle Drill: 4-1 … 4-5

### Skill Training

| Skill Type              | Description                      | Stages                |
| :---------------------- | :------------------------------- | :-------------------- |
| Basic Skill Training    | Basic skill upgrade materials    | Basic Training 1–3    |
| Advanced Skill Training | Advanced skill upgrade materials | Advanced Training 1–3 |

> [!NOTE]
>
> Skill-training stages must be unlocked in-game first; while a stage is locked the task detects the lock icon and does not enter it.

---

## Remaining Stamina

A Farm Resources variant **locked to Clear Stamina** mode, used to drain whatever stamina is left when the chain reaches this point.

**Prerequisites:** the game is on the home screen; a category has been selected.

**Options:**

| Option        | Type   | Default                | Description                          |
| :------------ | :----- | :--------------------- | :----------------------------------- |
| Category      | Select | Resource Collection    | Resource Collection / Skill Training |
| Resource Type | Select | Special Funds          | Available under Resource Collection  |
| Skill Type    | Select | Basic Skill Training   | Available under Skill Training       |
| Stage         | Select | 1-1 / Basic Training 1 | Same stage ranges as Farm Resources  |

> [!NOTE]
>
> This task uses **its own option set, separate from "Farm Resources"**, so it can farm a different stage. It is unchecked by default and normally enabled by the "Daily / Activity" presets; it reduces the battle count and exits by itself once stamina runs short.

---

## Event Stages and Shop

Farm Flare event stages and redeem available event-shop items automatically.

**Prerequisites:** the Flare event is unlocked; event stages can only be swept after clearing every stage of the event (EX stages included).

**Event stage options:**

| Option      | Type   | Default | Description                   |
| :---------- | :----- | :------ | :---------------------------- |
| Event Stage | Select | EX2-1   | EX2-1 / EX2-2 / EX3-1 / EX4-1 |
| Sweep Count | Select | 3       | 1 / 2 / 3 / Max               |

Event stages do not consume normal stamina and are limited to three sweeps per day.

**Event shop:**

Opens the `定额保障` (fixed-guarantee) tab, buys available items in order, skips sold-out items, and finishes when no items remain.

> [!NOTE]
>
> Both event tasks enter the event from the game home screen and return to it afterwards, so they can be safely inserted in the middle of a chain.

---

## Stamina Info

Reads the current stamina and cap on the home screen, then reports when it will refill naturally.

**Prerequisites:** the game is on the home screen (the task returns there automatically). Running it **last** is recommended.

**Options:** none.

It automatically:

1. Confirms it is on the home screen (returns home automatically if not: home button / generic back)
2. Reads the home-screen stamina digits
3. Computes and reports the refill time (once at the natural-recovery cap, stamina no longer refills over time and the task reports so)

> [!NOTE]
>
> Stamina regenerates at 1 point per 4 minutes. A failed read is retried; if it still fails, only this report is skipped and other tasks are unaffected.

---

## PVP

Auto-battle PVP with configurable rounds.

**Prerequisites:** the game is on the home screen; today's battle allowance is not exhausted (when it is, the task reports it and returns home).

**Options:**

| Option       | Type   | Default | Description                                        |
| :----------- | :----- | :------ | :------------------------------------------------- |
| Battle Count | Select | 1       | 1–6 rounds (6 for premium-account fail protection) |

There are 5 PVP attempts per day; a premium account gets first-loss protection (the first loss costs no attempt), so up to 6 battles are possible — pick "6" to use them all.

MaaKEDR will automatically:

1. Enter the PVP interface
2. Match and start battles
3. Detect battle results
4. Repeat until the target count is reached

> [!NOTE]
>
> PVP outcomes depend on your roster and gear. MaaKEDR only automates the process — it does not guarantee wins. When picking an opponent it prefers the lowest-level one.

---

## Send Gift

Each day, enters the friend list from the home screen and gifts the **topmost still giftable** friends one by one; each round gifts one friend and swipes up one screen until the daily quota `20/20` is used up or the round-limit fallback ends the task.

**Prerequisites:** the game is on the home screen (the task returns there automatically); the friend list is on the "Friend List" tab.

**Options:** none (fixed behaviour, checked by default; not part of the "Daily" preset — tick it manually when needed).

It automatically:

1. Confirms it is on the home screen (returns home automatically if not)
2. Clicks the friend icon at the top-right of the home screen and confirms with OCR
3. Uses the "gift-button template ∩ golden connected region" combined recognition to pick giftable buttons and clicks the topmost one
4. Swipes up one screen and repeats until the daily quota is used up or the round-limit fallback triggers
5. When the quota is used up, logs 「今日赠礼已达上限」 and 「赠送礼物完成！」 (Chinese log text)

> [!NOTE]
>
> Task success only means the flow finished; it does not guarantee gifts were sent. A second confirmation dialog or an "item obtained" popup is not handled by the current flow.

---

## Task Presets

Presets check a set of common tasks in one click for different scenarios:

- **Daily**: Game Launch → Farm Resources → Claim Rewards → Remaining Stamina → PVP → Claim Remaining Rewards → Stamina Info
- **Activity**: Game Launch → Event Stage (EX2-1 / EX2-2 / EX3-1 / EX4-1, one each) → Event Shop → Farm Resources → Claim Rewards → Remaining Stamina → PVP → Claim Remaining Rewards → Stamina Info

When the **Activity** preset is selected, `Event Stage` and `Event Shop` are enabled by default and all four event stages are set to sweep "Max" times; the **Daily** preset does not include event tasks.
