---
order: 3
icon: ri:gift-line
---

# 领取奖励协议

「领取奖励」把散落在主界面各入口的奖励一次性收掉：派遣、日常/每周/军旅成就、战令通行证、邮箱，
以及默认关闭的高级账号商店每日免费商品。整条流程由 `ClaimRewards.MainHub` 轮询驱动，
每个子模块入口都是 `[JumpBack]` 节点。

## 任务入口

| 任务         | entry          | 定义                       | 流程                                        | 默认勾选 | 选项                                                                                                |
| ------------ | -------------- | -------------------------- | ------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------- |
| 领取奖励     | `ClaimRewards` | `tasks/claim_rewards.json` | `resource/base/pipeline/claim_rewards.json` | 是       | `claim_dispatch`、`claim_daily_rewards`、`claim_battle_pass`、`claim_mailbox`、`claim_premium_shop` |
| 剩余奖励领取 | `ClaimRewards` | 同上                       | 同上                                        | 否       | 同上                                                                                                |

两个任务共用同一 entry 与同一套选项，区别只在执行位置：`剩余奖励领取` 放在任务链后段，
用于收掉前面任务（如 PVP 结算奖励，通常进邮箱）新产生的奖励；`Daily` / `Activity` 预设里前后各排一次。

## 数据链路

```text
tasks/claim_rewards.json
  ├─ task[0] 领取奖励（default_check: true）+ task[1] 剩余奖励领取（default_check: false）
  └─ option：6 个开关 → cases[].pipeline_override 只改「入口节点」
       claim_dispatch=No        → DispatchClaim.Start.enabled = false
       claim_daily_rewards=No   → ClaimRewards.Start.enabled = false
       claim_battle_pass=No     → BattlePass.Start.enabled = false
       claim_mailbox=No         → Mailbox.Start.enabled = false
       claim_premium_shop=No    → PremiumShop.ClickShopIcon.enabled = false
       dispatch_redeploy=No     → 改 DispatchClaim.ClaimButton.next + DispatchClaim.RedeployConfirm
  → resource/base/pipeline/claim_rewards.json（含 Common.BackButton / Common.CheckItemObtained 定义）
  → 无 Custom 节点：「有没有可领奖励」全部由 ColorMatch 红点判定
```

## 子模块开关

| 选项 key              | 控件   | 默认 | 说明                 | 覆盖的节点                                                                                                        |
| --------------------- | ------ | ---- | -------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `claim_dispatch`      | switch | 开   | 派遣任务领取         | 关闭时 `DispatchClaim.Start.enabled = false`（整条派遣链路失效）                                                  |
| `dispatch_redeploy`   | switch | 开   | 领取后是否再次派遣   | 关闭时把 `DispatchClaim.RedeployConfirm` 改为 DirectHit + DoNothing，并从 `DispatchClaim.ClaimButton.next` 移除它 |
| `claim_daily_rewards` | switch | 开   | 每日/每周/军旅成就   | 关闭时 `ClaimRewards.Start.enabled = false`                                                                       |
| `claim_battle_pass`   | switch | 开   | 战令通行证           | 关闭时 `BattlePass.Start.enabled = false`                                                                         |
| `claim_mailbox`       | switch | 开   | 邮箱                 | 关闭时 `Mailbox.Start.enabled = false`                                                                            |
| `claim_premium_shop`  | switch | 关   | 高级账号商店每日奖励 | 关闭时 `PremiumShop.ClickShopIcon.enabled = false`                                                                |

`dispatch_redeploy` 是 `claim_dispatch` 的嵌套子选项：只有派遣开关为「开」时才会在 GUI 中展开。

## 总流程（MainHub）

```text
ClaimRewards（DirectHit 入口列表）
  ├─ ClaimRewards.EnsureHome（确认主页；未确认 → [JumpBack]Common.EnsureHome）
  ├─ ClaimRewards.CheckMainInterface（主页特征 + 点击，消除残留弹窗）
  ├─ ClaimRewards.MainHub（轮询枢纽）
  └─ [JumpBack]Common.EnsureHome（末位兜底）

MainHub.next（按顺序轮询，命中即执行并回跳）
  → [JumpBack]DispatchClaim.Start
  → [JumpBack]ClaimRewards.Start
  → [JumpBack]BattlePass.Start
  → [JumpBack]Mailbox.Start
  → [JumpBack]PremiumShop.ClickShopIcon（默认关闭）
  → [JumpBack]Common.CheckItemObtained（物品弹窗兜底）
  → ClaimRewards.MainHubIdle（全部领完 → 识别主页作为成功退出条件）
```

### 退出机制（JumpBack 栈）

`MainHub` 的 `next` 中所有子模块入口均为 `[JumpBack]` 节点：命中执行后压栈跳回 `MainHub` 继续轮询下一个入口；
入口在对应奖励领完后即无法识别，轮询会自然推进。当所有入口均无法识别时，`next` 末尾的 `MainHubIdle`
（普通节点，识别 `more.png`）命中——此时 JumpBack 栈为空，节点无 `next`，任务成功结束。

> [!NOTE]
> 不要用 `on_error` 承担"无奖励退出"等正常逻辑：`on_error` 触发时会自动保存截图（`save on error`），频繁触发会撑爆日志目录。正常分支一律放在 `next` 末尾做兜底。

## 关键节点约定

### 主页确认

- `ClaimRewards.EnsureHome`：识别 `more.png`（`timeout: 60000`），命中后进入 `CheckMainInterface`，否则由 `[JumpBack]Common.EnsureHome` 回主页后重试。
- `ClaimRewards.CheckMainInterface`：识别主页并**点击一次**，`next` 指向 `MainHub`（不带 `[JumpBack]`，避免 JumpBack 栈导致任务无法结束）。
- `ClaimRewards.MainHubIdle`：识别主页，作为"全部奖励已领完"的成功退出条件，位于 `MainHub.next` 末尾。

### 日常成就

- `ClaimRewards.Start`：周常入口有可领取奖励的判定（**ColorMatch**：入口红点颜色匹配，RGB 区间约 [200-255, 60-150, 20-100] 且连通像素数 ≥ 50，命中即视为有可领取奖励；无红点时识别失败，正常跳过该入口），`max_hit: 5`、`timeout: 5000`
- `ConfirmInterface`：奖励界面（`claim_rewards/daily/reward_interface.png`，`max_hit: 10`）；`next` 中含 `MedalDisplay`（获得勋章弹窗识别）与 `ExitRewardInterface` 退出
- `CheckDaily` / `CheckWeekly` / `CheckMilitary`：分栏可领取判定（同为 **ColorMatch** 红点颜色匹配，`max_hit: 5`），命中即点击该分栏
- `ClaimButton`：领取按钮（`claim_rewards/daily/claim_button.png`）；领完后优先处理 `MedalDisplay` 勋章弹窗，再处理 `Common.CheckItemObtained` 物品弹窗
- `MedalDisplay`：识别"获得勋章"弹窗并点击关闭（见 `claim_rewards/daily/medal_display.png`）

### 战令

- `BattlePass.Start` / `ClickEntry` / `RetryClickEntry`：战令入口有可领取奖励的判定（**ColorMatch** 红点颜色匹配；`Start` 只识别不点击，点击交给 `ClickEntry` / `RetryClickEntry`）
- `CheckTaskComplete`：任务完成页签（ColorMatch 定位可领红点后直接点击，`max_hit: 1`，避免在页签上反复点击）
- `CheckRewardList` / `ClaimRewardButton`：奖励列表领取（`CheckRewardList` 用 ColorMatch，`max_hit: 5`；`ClaimRewardButton` 用 `claim_rewards/battlepass/battlepass_claim_button.png`）
- `RewardDisplay`：战令奖励展示界面（`claim_rewards/battlepass/battlepass_reward_display.png`），命中即点击

### 派遣

- `DispatchClaim.Start`：派遣入口有可领取奖励的判定（**ColorMatch** 红点颜色匹配）→ `ClaimButton` → `RedeployConfirm`（可选）→ `Exit`；`Start.next` 同时挂 `Exit`，面板一打开就是「关闭」时直接收尾
- 不保留入口「重试点击」节点：面板展开动画期间用同一红点判据再点一次会把点击落进面板、导致领取状态错位（Issue #86）。入口点击失败时由 `Start` 自身超时后判失败，不重复点击
- `DispatchClaim.Start` 带 `max_hit: 1`：单次任务只进入一次。否则红点未及时消失时，`Exit` 回到 `MainHub` 后会被 `[JumpBack]DispatchClaim.Start` 反复重入，形成「开面板 → 关面板」循环并饿死后续分支
- 关闭 `dispatch_redeploy` 时：`DispatchClaim.ClaimButton.next` 变为 `[Common.CheckItemObtained, DispatchClaim.RedeployConfirm, DispatchClaim.Exit]`，同时 `DispatchClaim.RedeployConfirm` 被改成 DirectHit + DoNothing 的空节点——保留在链路上但不再点「再次派遣」

### 邮箱

- `Mailbox.Start`（`max_hit: 5`）→ `Mailbox.ClickEntry` → `Mailbox.ConfirmInterface`（`mailbox_interface.png`）→ `Mailbox.ClaimButton`（OCR「一键领取」，`max_hit: 1`）→ `Mailbox.BackButton` 返回

### 高级账号商店（PremiumShop）

默认关闭（`claim_premium_shop`），面向已开通高级账号、每日可领取免费商品的玩家。

```text
MainHub → [JumpBack]ClickShopIcon（ColorMatch 检测商店图标红点（可领取状态），命中后点击进入；max_hit: 2，整个任务最多进两次商店）
  → ConfirmShopInterface（确认在商店界面）
       → ClickPremiumShop：ColorMatch 识别"带红点（可领取状态）"的高账入口，命中才点击进入
       → NoPremiumShopEntry（兜底）：入口无红点/未开通 → 返回主页
  → ConfirmPremiumShop（确认在高账商店界面）→ PurchaseHub（购买中枢，DirectHit）
       → ClickFreeItem：ColorMatch 识别"免费商品"按钮红点，命中点击 → ConfirmPurchase
            → 确认购买 → [JumpBack]Common.CheckItemObtained（物品弹窗）→ 跳回 PurchaseHub 继续
       → 无免费商品 → ReturnMain
  → ReturnMain → MainHubIdle（回主页后成功退出）
```

关键点：

- **红点即可领取**：`ClickPremiumShop` 用 **ColorMatch**（红点色区间 RGB [200-255, 60-150, 20-100]、连通像素数 ≥ 50）判定入口是否处于"有可领取状态"；无红点时识别失败，视为今日已领完/未开通，不进商店。
- **`NoPremiumShopEntry`**：DirectHit 兜底节点，位于 `ConfirmShopInterface.next` 与 `ClickPremiumShop.next` 末尾，命中时直接经 `ReturnMain` 返回主页——不依赖 `on_error`，无超时等待、不触发错误截图。
- **红点即可进入**：`ClickShopIcon` / `RetryClickShopIcon` 用 **ColorMatch** 判定主页商店图标带红点（有可领取内容），无红点时识别失败、不进商店，直接进入后续轮询。
- **`ClickShopIcon.max_hit: 2`**：商店图标是常驻元素，不加限制会在 `MainHub` 轮询中反复进商店导致死循环。
- **`on_error` 只用于真失败**：`ClickPremiumShop` / `RetryClickPremiumShop` / `ConfirmPremiumShop` 的 `on_error` 指向 `PremiumShop.ReturnMain`，用于高账入口点不动、界面确认失败时安全退出。

### 通用

- `Common.CheckItemObtained`：获得物品弹窗（`item_obtained_dialog.png`），定义在本文件，`Common.EnsureHome` 跨文件按名引用
- `Common.BackButton`：返回箭头（`back_button.png`），同上

## 识别方式说明

本任务的"是否有可领取奖励"判定统一使用 **ColorMatch 颜色匹配**，而非小尺寸模板：

- 各入口（每日/每周/军旅分栏、战令、派遣、高账商店、免费商品）的红点/角标通过颜色区间（RGB 下限/上限约 `[200, 60, 20]` ~ `[255, 150, 100]`）识别，`connected: true`（只计连通块）+ `count: 50`（最少像素数）抗误报；
- 颜色判定对画面轻微变化（UI 动效、抗锯齿、图片压缩处理）不敏感，无需维护多套模板变体；入口图标样式变化不再影响"是否有奖励"的判断；
- 具体色板取值见 `claim_rewards.json` 中各 `ColorMatch` 节点的 `param.lower/upper`，如遇新入口的红点颜色不同，按实测调整对应节点即可。

## 改动这类流程要动哪些文件

1. **新增子模块**：在 `resource/base/pipeline/claim_rewards.json` 新增入口节点（红点判定 + `[JumpBack]` 友好），再把入口插进 `ClaimRewards.MainHub.next` 的合适位置（末尾 `MainHubIdle` 之前）
2. **加开关**：在 `tasks/claim_rewards.json` 的 `option` 里新增 `switch`，`cases[].pipeline_override` 关闭时只写 `{"<入口节点>": {"enabled": false}}`
3. **同时挂到两个任务**：`领取奖励` 与 `剩余奖励领取` 各有一份 `option` 数组，新增选项要**两处都加**
4. **新增模板图**：放 `resource/base/image/claim_rewards/<子模块>/`；红点类元素不需要模板图
5. **调红点色板**：改对应节点 `ColorMatch` 的 `lower` / `upper` / `count`
6. **校验**：`pnpm exec maa-tools check`，提交前 `pnpm check`

## 图片目录

`resource/base/image/claim_rewards/` 按任务分子目录：`daily/`（含勋章弹窗）、`battlepass/`、`mailbox/`、`dispatch/`、`premium_shop/`；通用图（`back_button.png`、`item_obtained_dialog.png` 等）在 `resource/base/image/` 根目录。红点/角标类元素由 ColorMatch 颜色判定，无专用模板图。

## 验收清单

改动本任务后按以下顺序验证：

1. 每个子模块入口（派遣 / 日常 / 战令 / 邮箱 / 高账商店）单独跑一遍，确认能进入并领完
2. 全部子模块开启时端到端跑一遍，确认按序轮询、无死循环
3. 关闭 `dispatch_redeploy` 再跑派遣，确认领完后直接关闭界面、不点「再次派遣」
4. 领到一半时重启任务，确认剩余奖励能继续领完（JumpBack 栈正确重建）
5. 全部领完后任务正常收尾退出（命中 `MainHubIdle`，不依赖 `on_error`）
6. 领奖过程中出现物品弹窗 / 勋章弹窗时能正常处理
7. 入口图标存在多种样式/状态时（多模板），各变体均能正常识别进入
8. 全量回归：与其它任务（启动、刷取、PVP）组合跑一遍无冲突
