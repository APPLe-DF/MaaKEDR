---
title: 协议文档
icon: basil:document-solid
index: true
dir:
    order: 2
---

# 协议文档

本目录描述 MaaKEDR 在《雪松》中的**任务约定、资源路径与界面流程约定**，供编写 / 修改 Pipeline 与 Custom 时对照。

不是 MaaFramework 通用协议；通用协议请见 [Project Interface V2](https://maafw.com/docs/3.3-ProjectInterfaceV2)。

## 导航

- [项目与资源约定](./overview.md) — `interface` / `tasks` / `resource` / 分辨率
- [启动与登录](./startup.md) — 启动任务流程
- [领取奖励](./claim-rewards.md) — 派遣 / 日常 / 战令 / 邮箱
- [资源刷取](./farm-resources.md) — 关卡类型、次数、清体力
- [玩家对战](./pvp.md) — PVP 循环与结果识别
- [活动关卡与活动商店](./event-stage.md) — 活动关卡刷取、次数耗尽与商店清空

## 相关代码位置

| 内容            | 路径                                     |
| --------------- | ---------------------------------------- |
| 任务入口与选项  | `tasks/*.json`                           |
| Pipeline 节点   | `resource/base/pipeline/*.json`          |
| 区服差异资源    | `resource/bilibili/`、`resource/taptap/` |
| 自定义识别/动作 | `agent/custom/`                          |
