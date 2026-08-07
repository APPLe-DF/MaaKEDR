---
title: "海外客户端适配"
order: 9
icon: "ri:earth-fill"
---

# 海外客户端适配

::: note
本文为占位文档：当前 MaaKEDR 仅支持国服渠道（官服 / B 服 / TapTap），尚无海外客户端。若未来出现海外版本，按本文约定的边界适配即可，其余"具体遇到再解决"。
:::

## 适配边界

海外客户端与国服差异通常集中在**启动与登录**环节，核心适配点：

- `resource/<pack>/pipeline/startup.json`、`shutdown.json` — 启动/关闭流程（登录入口、渠道包差异）
- `interface.json` 的 `resource` 列表 — 新增海外渠道资源包（复用 `base` 作为基底，再叠加覆盖）
- 登录文案 / 入口图 — 模板图与 OCR `expected` 文本

## 原则

1. **优先只改启动与登录**：其余任务（领取奖励、刷取、PVP）尽量复用 `base`，不要在海外包中复制整条流程
2. 语言差异优先通过覆盖 `expected` / 模板图解决，而不是改流程结构
3. 新增资源包时同步更新 `docs/*/protocol/overview.md` 的资源包表格
4. 参考 MaaFramework [ProjectInterface V2](https://maaframework.github.io/docs/zh-cn/develop/1.1-ProjectInterface.html) 协议理解 `interface.json` 的资源切换机制

## 当前状态

| 渠道   | 状态 | 说明                 |
| ------ | ---- | -------------------- |
| 官服   | ✅   | `resource/base`      |
| B 服   | ✅   | `resource/bilibili`  |
| TapTap | ✅   | `resource/taptap`    |
| 海外   | ⏳   | 未适配，无对应资源包 |
