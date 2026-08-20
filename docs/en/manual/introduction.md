---
order: 4
icon: mdi:information-outline
---

# Feature Introduction

MaaKEDR automates daily tasks in _雪松 (KEDR)_ to save you time.

---

## Launch Game

Automatically starts the game and navigates to the main menu.

**Features:**

- Launch the game process
- Click "Start Game"
- Handle daily login reward popups
- Detect and enter the main menu

No configuration needed — just enable the task.

---

## Claim Rewards

Claim various rewards with individual toggles.

**Options:**

| Option                        | Type   | Description                                           |
| :---------------------------- | :----- | :---------------------------------------------------- |
| Dispatch Claim                | Toggle | Collect and redeploy dispatch missions                |
| Daily/Weekly/Military Rewards | Toggle | Claim daily, weekly, and military achievement rewards |
| Battle Pass                   | Toggle | Claim battle pass rewards                             |
| Mailbox                       | Toggle | Claim mail attachments                                |
| Premium Shop Daily Reward     | Toggle | Claim the premium shop free item (default off)        |

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

## Farm Resources

Auto-battle resource stages with stamina management.

**Options:**

| Option        | Type   | Description                          |
| :------------ | :----- | :----------------------------------- |
| Battle Mode   | Select | Single Battle / Clear Stamina        |
| Category      | Select | Resource Collection / Skill Training |
| Resource Type | Select | See below                            |
| Battle Count  | Select | 1–6 / Max                            |

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

| Skill Type              | Description                      |
| :---------------------- | :------------------------------- |
| Basic Skill Training    | Basic skill upgrade materials    |
| Advanced Skill Training | Advanced skill upgrade materials |

---

## Event Stages and Shop

Farm Flare event stages and redeem available event-shop items automatically.

**Event stage options:**

| Option      | Type   | Description                   |
| :---------- | :----- | :---------------------------- |
| Event Stage | Select | EX2-1 / EX2-2 / EX3-1 / EX4-1 |
| Sweep Count | Select | 1 / 2 / 3 / Max               |

Event stages do not consume normal stamina and are limited to three sweeps per day. Complete all Flare stages, including EX stages, before using this task.

**Event shop:**

Opens the `定额保障` (fixed-guarantee) tab, buys available items in order, skips sold-out items, and finishes when no items remain.

---

## PVP

Auto-battle PVP with configurable rounds.

**Options:**

| Option       | Type   | Description |
| :----------- | :----- | :---------- |
| Battle Count | Select | 1–5 rounds  |

MaaKEDR will automatically:

1. Enter the PVP interface
2. Match and start battles
3. Detect battle results
4. Repeat until the target count is reached

> [!NOTE]
>
> PVP outcomes depend on your roster and gear. MaaKEDR only automates the process — it does not guarantee wins.
