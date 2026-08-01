---
order: 3
icon: ri:gift-line
---

# 领取奖励协议

## 任务入口

| 项     | 值                                          |
| ------ | ------------------------------------------- |
| 任务名 | 领取奖励                                    |
| entry  | `ClaimRewards`                              |
| 定义   | `tasks/claim_rewards.json`                  |
| 流程   | `resource/base/pipeline/claim_rewards.json` |

## 子模块开关

| 选项 key              | 说明                 | 关闭时常见行为                               |
| --------------------- | -------------------- | -------------------------------------------- |
| `claim_dispatch`      | 派遣任务领取         | 禁用 `DispatchClaim.Start`                   |
| `dispatch_redeploy`   | 领取后是否再次派遣   | 改 `RedeployConfirm` 路径                    |
| `claim_daily_rewards` | 每日/每周/军旅成就   | 禁用 `ClaimRewards.Start`                    |
| `claim_battle_pass`   | 战令通行证           | 禁用 `BattlePass.Start`                      |
| `claim_mailbox`       | 邮箱                 | 禁用 `Mailbox.Start`                         |
| `claim_premium_shop`  | 高级账号商店每日奖励 | 禁用 `PremiumShop.ClickShopIcon`（默认关闭） |

## 总流程（MainHub）

```text
ClaimRewards
  → CheckMainInterface / ReturnMain（确保主页）
  → MainHub（主界面特征识别）
       → DispatchClaim.*
       → ClaimRewards.Start / ConfirmInterface / CheckDaily|Weekly|Military
       → BattlePass.*
       → Mailbox.*
       → PremiumShop.*（默认关闭）
  → 各子流程结束回 MainHub 或退出
```

## 关键节点约定

### 主页确认

- `ClaimRewards.CheckMainInterface`：确认在主界面后应进入 `MainHub`，避免无 `next` 死循环。

### 日常成就

- `ClaimRewards.Start`：周常入口徽章
- `ConfirmInterface`：奖励界面
- `CheckDaily` / `CheckWeekly` / `CheckMilitary`：分栏徽章
- `ClaimButton`：领取按钮；领完后处理 `Common.CheckItemObtained` 弹窗

### 战令

- `BattlePass.ClickEntry` / `RetryClickEntry`：入口可改为固定坐标点击（见 pipeline）
- `CheckTaskComplete`：任务完成页签；识别后可固定坐标切入
- `CheckRewardList` / `ClaimRewardButton`：奖励列表领取

### 派遣

- `DispatchClaim.Start` → `ClaimButton` → `RedeployConfirm`（可选）→ `Exit`

### 邮箱

- `Mailbox.Start` → `ConfirmInterface` → OCR「一键领取」→ 返回

### 通用

- `Common.CheckItemObtained`：获得物品弹窗
- `Common.BackButton`：返回键

## 图片目录

`resource/base/image/claim_rewards/` 与根目录下通用图（如 `back_button.png`、`item_obtained_dialog.png`）。
