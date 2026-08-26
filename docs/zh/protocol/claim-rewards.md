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
  → CheckMainInterface（确认主页，点击后进入 MainHub）
  → MainHub（主界面特征识别，next 轮询各子流程入口）
       → DispatchClaim.*
       → ClaimRewards.Start / ConfirmInterface / CheckDaily|Weekly|Military
       → BattlePass.*
       → Mailbox.*
       → PremiumShop.*（默认关闭）
       → Common.CheckItemObtained（物品弹窗兜底）
       → MainHubIdle（全部领完 → 识别主界面作为成功退出条件）
```

### 退出机制（JumpBack 栈）

`MainHub` 的 `next` 中所有子流程入口均为 `[JumpBack]` 节点：命中执行后压栈跳回 `MainHub` 继续轮询下一个入口；入口在对应奖励领完后即无法识别，轮询会自然推进。当所有入口均无法识别时，`next` 末尾的 `MainHubIdle`（普通节点，识别 `main_option.png`）命中——此时 JumpBack 栈为空，节点无 `next`，任务成功结束。

> [!NOTE]
> 不要用 `on_error` 承担"无奖励退出"等正常逻辑：`on_error` 触发时会自动保存截图（`save on error`），频繁触发会撑爆日志目录。正常分支一律放在 `next` 末尾做兜底。

## 关键节点约定

### 主页确认

- `ClaimRewards.CheckMainInterface`：确认在主界面并点击，`next` 指向 `MainHub`（不再使用 `[JumpBack]`，避免 JumpBack 栈导致任务无法结束）。
- `ClaimRewards.MainHubIdle`：识别主界面，作为"全部奖励已领完"的成功退出条件，位于 `MainHub.next` 末尾。

### 日常成就

- `ClaimRewards.Start`：周常入口有可领取奖励的判定（**ColorMatch**：入口红点颜色匹配，RGB 区间约 [200-255, 60-150, 20-100] 且连通像素数 ≥ 50，命中即视为有可领取奖励；无红点时识别失败，正常跳过该入口）
- `ConfirmInterface`：奖励界面；`next` 中含 `MedalDisplay`（获得勋章弹窗识别）与 `ExitRewardInterface` 退出
- `CheckDaily` / `CheckWeekly` / `CheckMilitary`：分栏可领取判定（同为 **ColorMatch** 红点颜色匹配）
- `ClaimButton`：领取按钮；领完后优先处理 `MedalDisplay` 勋章弹窗，再处理 `Common.CheckItemObtained` 物品弹窗
- `MedalDisplay`：识别"获得勋章"弹窗并点击关闭（见 `claim_rewards/daily/medal_display.png`）

### 战令

- `BattlePass.Start` / `ClickEntry` / `RetryClickEntry`：战令入口有可领取奖励的判定（**ColorMatch** 红点颜色匹配；`ClickEntry` 入口也可改为固定坐标点击，见 pipeline）
- `CheckTaskComplete`：任务完成页签（ColorMatch 定位可领红点；识别后可固定坐标切入）
- `CheckRewardList` / `ClaimRewardButton`：奖励列表领取

### 派遣

- `DispatchClaim.Start` / `RetryClick`：派遣入口有可领取奖励的判定（**ColorMatch** 红点颜色匹配）→ `ClaimButton` → `RedeployConfirm`（可选）→ `Exit`

### 邮箱

- `Mailbox.Start` → `ConfirmInterface` → OCR「一键领取」→ 返回

### 高级账号商店（PremiumShop）

默认关闭（`claim_premium_shop`），面向已开通高级账号、每日可领取免费商品的玩家。

```text
MainHub → [JumpBack]ClickShopIcon（ColorMatch 检测商店图标红点（可领取状态），命中后点击进入；max_hit: 1，整个任务只进一次商店）
  → ConfirmShopInterface（确认在商店界面）
       → ClickPremiumShop：ColorMatch 识别"带红点（可领取状态）"的高账入口，命中才点击进入
       → NoPremiumShopEntry（兜底）：入口无红点/未开通 → 提示后返回主页
  → ConfirmPremiumShop（确认在高账商店界面）→ PurchaseHub（购买中枢，DirectHit）
       → ClickFreeItem：ColorMatch 识别"免费商品"按钮红点，命中点击 → ConfirmPurchase
            → 确认购买 → [JumpBack]Common.CheckItemObtained（物品弹窗）→ 跳回 PurchaseHub 继续
       → 无免费商品 → ReturnMain
  → ReturnMain → MainHubIdle（回主页后成功退出）
```

关键点：

- **红点即可领取**：`ClickPremiumShop` 用 **ColorMatch**（红点色区间 RGB [200-255, 60-150, 20-100]、连通像素数 ≥ 50）判定入口是否处于"有可领取状态"；无红点时识别失败，视为今日已领完/未开通，不进商店。
- **`NoPremiumShopEntry`**：DirectHit 兜底节点，位于 `ConfirmShopInterface.next` 与 `ClickPremiumShop.next` 末尾，命中时 toast「未检测到高账商店可领取提示，请检查是否已开通高级账号」并返回主页——不依赖 `on_error`，无超时等待、不触发错误截图。
- **红点即可进入**：`ClickShopIcon` / `RetryClickShopIcon` 用 **ColorMatch** 判定主页商店图标带红点（有可领取内容），无红点时识别失败、不进商店，直接进入后续轮询。
- **`ClickShopIcon` 的 `max_hit: 1`**：商店图标是常驻元素，不加限制会在 `MainHub` 轮询中反复进商店导致死循环。

### 通用

- `Common.CheckItemObtained`：获得物品弹窗
- `Common.BackButton`：返回键

## 识别方式说明

本任务的"是否有可领取奖励"判定统一使用 **ColorMatch 颜色匹配**，而非小尺寸模板：

- 各入口（每日/每周/军旅分栏、战令、派遣、高账商店、免费商品）的红点/角标通过颜色区间（RGB 下限/上限约 `[200, 60, 20]` ~ `[255, 150, 100]`）识别，`connected: true`（只计连通块）+ `count: 50`（最少像素数）抗误报；
- 颜色判定对画面轻微变化（UI 动效、抗锯齿、图片压缩处理）不敏感，无需维护多套模板变体；入口图标样式变化不再影响"是否有奖励"的判断；
- 具体色板取值见 `claim_rewards.json` 中各 `ColorMatch` 节点的 `param.lower/upper`，如遇新入口的红点颜色不同，按实测调整对应节点即可。

## 图片目录

`resource/base/image/claim_rewards/` 按任务分子目录：`daily/`（含勋章弹窗）、`battlepass/`、`mailbox/`、`dispatch/`、`premium_shop/`；通用图（`back_button.png`、`item_obtained_dialog.png` 等）在 `resource/base/image/` 根目录。红点/角标类元素由 ColorMatch 颜色判定，无专用模板图。

## 验收清单

改动本任务后按以下顺序验证：

1. 每个子模块入口（派遣 / 日常 / 战令 / 邮箱 / 高账商店）单独跑一遍，确认能进入并领完
2. 全部子模块开启时端到端跑一遍，确认按序轮询、无死循环
3. 领到一半时重启任务，确认剩余奖励能继续领完（JumpBack 栈正确重建）
4. 全部领完后任务正常收尾退出（命中 `MainHubIdle`，不依赖 `on_error`）
5. 领奖过程中出现物品弹窗 / 勋章弹窗时能正常处理
6. 入口图标存在多种样式/状态时（多模板），各变体均能正常识别进入
7. 全量回归：与其它任务（启动、刷取、PVP）组合跑一遍无冲突
