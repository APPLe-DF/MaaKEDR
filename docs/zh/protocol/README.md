---
title: 协议文档
icon: basil:document-solid
index: true
dir:
    order: 2
---

# 协议文档

本栏目记录 MaaKEDR 与《雪松》之间的**约定**：每个任务由哪些文件组成、GUI 选项最终落到哪些 pipeline 节点、
改动这类流程时要按什么规则同步。

不是 MaaFramework 通用协议：字段语义以 [Pipeline 协议](https://maafw.com/docs/3.1-PipelineProtocol) 与
[Project Interface V2](https://maafw.com/docs/3.3-ProjectInterfaceV2) 为准，本目录只记录「本项目怎么用」。

## 导航

- [项目与资源约定](./overview.md) — `interface` / `tasks` / `resource` / 分辨率基线
- [启动与登录](./startup.md) — 启动任务流程与区服包覆盖
- [领取奖励](./claim-rewards.md) — 派遣 / 日常 / 战令 / 邮箱 / 高账商店
- [资源刷取](./farm-resources.md) — 关卡类型、次数、清空体力
- [玩家对战](./pvp.md) — PVP 循环、赛季重置与结果识别
- [活动关卡与活动商店](./event-stage.md) — 活动关卡刷取、次数耗尽与商店清空
- [体力信息](./stamina-info.md) — 主界面体力读取与回满时间

## 相关代码位置

| 内容            | 路径                                                    |
| --------------- | ------------------------------------------------------- |
| 任务入口与选项  | `tasks/*.json`                                          |
| 任务预设        | `tasks/preset/Daily.json`、`tasks/preset/Activity.json` |
| Pipeline 节点   | `resource/base/pipeline/*.json`                         |
| 区服差异资源    | `resource/bilibili/`、`resource/taptap/`                |
| 自定义识别/动作 | `agent/custom/recognition/`、`agent/custom/action/`     |
| 通用回主页枢纽  | `resource/base/pipeline/common.json`                    |

## 任务协议页的固定结构

每篇任务协议都按同一顺序写，新增页面时照此补齐，读者才能横向对照：

1. **任务入口**：任务名（GUI 显示名）、`entry` 节点、定义文件、流程文件、有无选项
2. **数据链路**：`tasks/*.json` 的选项 → `pipeline_override` 改了哪些节点 → 落到哪个 pipeline 文件 / agent 代码
3. **流程**：主路径与分支（含失败兜底），节点名与 pipeline 文件逐字一致
4. **关键约定**：容易改坏的节点语义（`max_hit`、`timeout`、`[JumpBack]`、`on_error` 的用法）
5. **改动这类流程要动哪些文件**：编号步骤 + 校验命令
6. **验收清单**：改完按顺序真机验证的项目

## 新增或改动任务时的检查清单

1. 任务与选项写在 `tasks/<task>.json`：`task[]` 声明 `name` / `entry` / `option`，选项用 `cases[].pipeline_override`
   指向**已存在**的节点名
2. 新增任务文件要登记到 `interface.json` 的 `import` 数组（当前为 7 个任务文件 + 2 个预设文件）
3. 任务要进预设时同步 `tasks/preset/Daily.json` / `tasks/preset/Activity.json`（预设按**任务名**引用）
4. 流程节点写进 `resource/base/pipeline/<task>.json`；跨任务复用的通用节点放 `common.json`
5. 新增或改动 Custom 识别/动作时，同步 `agent/custom/recognition/`、`agent/custom/action/` 下的实现与对应
   `__init__.py` 注册
6. 模板图放 `resource/base/image/<module>/`；区服差异图放 `resource/<pack>/image/`
7. 跑校验：`pnpm check`（格式 + schema + pipeline 完整性 + 项目 lint）、`pnpm exec maa-tools check`
   （只查 pipeline）、改过 Python 再跑 `pnpm check:py`
8. 回到本目录同步文档：**节点名、选项名、文件路径**三样必须与代码逐字一致

> [!WARNING]
> 选项的 `pipeline_override` 按节点名定向。改名 pipeline 节点时若漏改任务文件，选项会**静默失效**
> （不报错，只是不再生效）。改名前先全库搜节点名，改完按本目录逐条核对。

## 与其他文档的分工

| 想知道                                 | 看哪里                                       |
| -------------------------------------- | -------------------------------------------- |
| 某个任务由哪些节点组成、选项覆盖了谁   | 本目录                                       |
| Pipeline 字段、识别/动作类型、设计模式 | [Pipeline 编写指南](../develop/pipeline.md)  |
| Custom 识别/动作怎么写、怎么注册       | [Custom 编写指南](../develop/custom.md)      |
| 通用回主页枢纽的四条约束               | [通用节点与回主页枢纽](../develop/common.md) |
| 目录结构、发布流程                     | [项目结构](../develop/structure.md)          |
