---
order: 8
icon: ri:hand-heart-line
---

# 赠送礼物协议

「赠送礼物」是每日向好友送礼的收尾流程：从主界面点好友入口进好友列表，每轮点**最靠上且可赠送**的那一个好友
送一次礼物，再上滑一屏，直到 OCR 读到今日额度「20/20」或轮数兜底用尽。「可赠送」由
[组合识别取交集](../develop/custom.md) 判定——模板框必须与金色连通块重叠，已赠送的灰色按钮自然被跳过。

本页的实现与 MAK（`MaaAssistantKedrgame`）的 `SendGift` 任务逐节点一致，唯一差异是**进好友列表的导航方式**：
MAK 用 `SceneJump` 场景图跳到 `Friend_FriendList`，本项目换成「回主页枢纽 + 主页好友图标 + OCR 确认好友列表」，
流程逻辑、ROI、模板、`max_hit` 与滑动手势完全沿用 MAK。

## 任务入口

| 任务     | entry                 | 定义                   | 流程                                    | 默认勾选 | 选项                        |
| -------- | --------------------- | ---------------------- | --------------------------------------- | -------- | --------------------------- |
| 赠送礼物 | `SendGift.EnsureHome` | `tasks/send_gift.json` | `resource/base/pipeline/send_gift.json` | 是       | 无（固定行为，无 GUI 选项） |

任务分组为 `Daily`，GUI 中默认勾选；不进入 `tasks/preset/Daily.json` 的日常任务链，选择「日常」预设时不会自动带上，
需要时在 GUI 里单独勾选。

## 数据链路

```text
tasks/send_gift.json（无 option、无 pipeline_override）
  → resource/base/pipeline/send_gift.json
       ├─ 导航：Common.EnsureHome 枢纽 + SendGift.ClickFriendEntry + SendGift.CheckFriendList
       └─ 主循环：SendGift.Loop → SendGift.Step → SendGift.Do / SendGift.Swipe
  → SendGift.Do 用 Custom 识别 AllOfIntersect（agent/custom/recognition/general.py，
    在 agent/custom/recognition/__init__.py 的 RECOGNITION_MODULES 注册为 general）
  → 模板 resource/base/image/send_gift/homepage_friend.png、send_gift/gift_button.png
```

`SendGift.Do` 的 `custom_recognition_param` 与 MAK 一样直接写 **JSON 对象**（不要序列化成字符串），
内容只把模板路径换成本项目目录：

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

> 为什么用对象而不是字符串：MaaFW 把 `custom_recognition_param` 交给 Python 回调时会统一转成 JSON 字符串。
> 节点里写对象只序列化一次，回调拿到 `{"all_of": ...}`；节点里写 JSON 字符串则会被再序列化一次，变成
> `"{\"all_of\": ...}"`（双重转义）——`parse_params` 两种都能解开，但字符串写法可读性差，还会多一层转义。

## 流程

```text
SendGift.EnsureHome（DirectHit 门节点）
  ├─ SendGift.CheckHomePage（more.png 全局主页标记）
  │    ├─ SendGift.ClickFriendEntry（homepage_friend.png，点击后 post_wait_freezes 500）
  │    │    ├─ SendGift.CheckFriendList（OCR「好友列表」）→ SendGift.Loop
  │    │    ├─ SendGift.RetryClickFriendEntry（点击丢失时再点一次）
  │    │    └─ [JumpBack]Common.CheckItemObtained
  │    └─ [JumpBack]Common.EnsureHome
  └─ [JumpBack]Common.EnsureHome

SendGift.Loop（DirectHit，每轮第一件事是查额度）
  ├─ SendGift.QuotaFull（OCR 20/20）→ SendGift.Finish
  ├─ [JumpBack]SendGift.Step
  └─ SendGift.Finish

SendGift.Step（DirectHit，max_hit 50）
  ├─ SendGift.Do（AllOfIntersect，max_hit 20）→ SendGift.Swipe
  └─ SendGift.Swipe（子树终点：滑完由 [JumpBack] 回跳 Loop）
```

`SendGift.QuotaFull` 读好友列表右下角 `[1120, 665, 135, 25]`，`expected` 为 `20\s*[/／]\s*20`（半角与全角斜杠都认）。
`SendGift.Swipe` 是 `[680, 420, 200, 10] → [680, 270, 200, 10]`、`end_hold: 1000`，把下面几行好友带进可视区。

## 与 MAK 节点对照

| MAK（`pipeline/Friend/SendGift.json`） | 本项目                                                                           | 说明                            |
| -------------------------------------- | -------------------------------------------------------------------------------- | ------------------------------- |
| `SendGiftMain`（`SceneJump`）          | `SendGift.EnsureHome` + `CheckHomePage` + `ClickFriendEntry` + `CheckFriendList` | 导航范式换成回主页枢纽          |
| `SendGiftLoop`                         | `SendGift.Loop`                                                                  | `next` 顺序不变                 |
| `SendGiftQuotaFull`                    | `SendGift.QuotaFull`                                                             | ROI / `expected` 不变           |
| `SendGiftStep`                         | `SendGift.Step`                                                                  | `max_hit: 50` 不变              |
| `SendGiftDo`                           | `SendGift.Do`                                                                    | 识别参数与 `action: Click` 不变 |
| `SendGiftSwipe`                        | `SendGift.Swipe`                                                                 | 手势参数不变                    |
| `SendGiftFinish`                       | `SendGift.Finish`                                                                | `focus` 日志文案不变            |

## 关键约定

- **`[JumpBack]SendGift.Step` 是循环的关键**：`SendGift.Step` 的子树在 `SendGift.Swipe` 处走空即结束，靠回跳把控制权交回
  `SendGift.Loop`，于是每轮都会重新判断额度并再走一轮。不要给 `SendGift.Swipe` 补 `next`，否则循环变成一条直线。
- **`max_hit` 计的是成功次数**：`SendGift.Do` 满 20 次后被跳过，剩余轮次只滑动；`SendGift.Step` 满 50 个成功轮次后
  `SendGift.Loop` 只可能命中 `SendGift.Finish`，即轮数兜底。
- **`ColorMatch` 子识别必须 `connected: true`**：否则整条 ROI 会被当成一个结果，交集判定失效，`SendGift.Do` 会误点已赠送好友。
- **每日上限写死在识别正则里**：游戏改上限时同步改 `SendGift.QuotaFull.expected` 的两个数字。
- **阈值与颜色区间沿用 MAK 默认**：模板匹配走框架默认阈值 0.7（`green_mask` 去掉礼物图标的绿底），
  `ColorMatch` 用 RGB 方法（`method` 默认 4）、金色区间 `[235,235,80]`–`[255,255,115]`、`count: 600`。
- **没有新增等待**：导航节点用 `post_wait_freezes` 收敛界面，主循环内不引入 `pre_delay` / `post_delay`。
- **未处理的边界（与 MAK 一致）**：赠送时若弹出二次确认或「获得物品」弹窗，当前流程不处理；
  需要时把 `[JumpBack]Common.CheckItemObtained` 挂进 `SendGift.Do.next` 或另补节点。

## 改动这类流程要动哪些文件

1. 流程节点改 `resource/base/pipeline/send_gift.json`（节点名 `SendGift.*` 不要随便改，`tasks/send_gift.json` 的 `entry` 依赖它）
2. 组合识别逻辑改 `agent/custom/recognition/general.py` 的 `AllOfIntersect`；新增/改名时同步 `__init__.py` 的 `RECOGNITION_MODULES`
3. 模板图换 `resource/base/image/send_gift/` 下的两张图（720p 基准裁剪）
4. 导航接入方式变化（例如换入口图标）时，只改 `SendGift.ClickFriendEntry` / `SendGift.RetryClickFriendEntry` 的模板与 ROI
5. 任务名、分组、描述改 `tasks/send_gift.json`；新增任务文件要登记到 `interface.json` 的 `import`
6. 跑校验：`pnpm check`（格式 + schema + pipeline 完整性 + 项目 lint）、`pnpm exec maa-tools check`（只查 pipeline）、
   改过 Python 再跑 `pnpm check:py`、`pnpm test:py`
7. 回到本页同步文档：节点名、文件路径必须与代码逐字一致

## 验收清单

1. 主界面勾选「赠送礼物」开跑：能点好友图标进入好友列表，未误点其它顶栏按钮
2. 好友列表中出现金色赠送按钮的好友被逐个点掉；已赠送（灰色）按钮不被点
3. 每点一次后上滑一屏，下面几行好友进入可视区
4. 额度用尽时 OCR 命中「20/20」，任务以 `今日赠礼已达上限` + `赠送礼物完成！` 结束
5. 额度未满但好友已滑到底时，靠 `SendGift.Step` 的 `max_hit` 兜底正常结束（不报错、不卡死）
6. 不在主界面时（例如刚从关卡退出）任务能先回主页再进入好友列表
