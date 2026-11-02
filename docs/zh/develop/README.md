---
title: 开发文档
description: MaaKEDR 开发文档总览：环境搭建、Pipeline 与 Custom 编写、通用节点、项目结构、Bug 排查、格式化与文档写作约定。
icon: ph:code-bold
dir:
    order: 1
---

# 开发文档

本栏目面向想给 MaaKEDR 提交代码或适配新内容的开发者。建议先读「入门」把环境跑通，再按需要进入「编写指南」或「工程实践」。

只想改一点点 JSON 或文档、不熟悉 Git 的读者，请直接从 [环境搭建与开发入门](./setup.md#贡献与-pr) 的「贡献与 PR」看起。

## 入门

- [环境搭建与开发入门](./setup.md) —— 系统要求、依赖安装、运行时与 OCR 模型同步、第一个 Pipeline、贡献与 PR 流程。
- [项目结构](./structure.md) —— 仓库各目录的职责、三层架构，以及发布包与打包脚本的位置。

## 编写指南

- [Pipeline 编写指南](./pipeline.md) —— MaaFramework 的核心概念，用 JSON 描述「识别 → 动作 → 跳转」的流程、设计模式与兜底策略。
- [通用节点与回主页枢纽](./common.md) —— `pipeline/common.json` 里跨任务复用的通用节点清单，以及 `Common.EnsureHome` 枢纽的收敛方式。
- [Custom 编写指南](./custom.md) —— 通过 `AgentServer` 注册自定义识别、动作与 Sink，补齐 JSON 流程做不到的逻辑。

## 工程实践

- [Vibe Coding 开发说明](./vibe-coding.md) —— 本项目以 AI 辅助为主力的开发模式与协作约定。
- [Bug 排查](./fix.md) —— 日志定位、问题分诊与修复验证。
- [格式化规范](./formatting.md) —— 编码约定、命名规则、提交规范与开发命令速查。
- [文档编写](./doc.md) —— 文档站目录结构、Frontmatter、MarkdownLint 规范与写作要求。
- [海外客户端适配](./overseas-client-adaptation.md) —— 国际服差异的适配边界、原则与当前状态。
- [安卓打包（MaaFwApp）](./android.md) —— 通过 MaaFwApp 子模块与打包配方产出 Android APK。

任务与资源约定见 [协议文档](../protocol/)。
