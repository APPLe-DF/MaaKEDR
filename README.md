<!-- markdownlint-disable MD033 MD041 -->
<div align="center">

<img alt="LOGO" src="resource/base/image/maakedr-logo_512x512.png" width="256" height="256" />

# MaaKEDR

《雪松》小助手。图像技术 + 模拟控制，解放双手！  
由 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 强力驱动！  
<a href="https://github.com/APPLe-DF/MaaKEDR" target="_blank" style="font-weight: bold;">🔗 本项目 GitHub 仓库</a><br>
🌟 喜欢本项目就在仓库右上角点个星星吧 🌟

</div>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white">
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blueviolet">
  <img alt="license" src="https://img.shields.io/github/license/APPLe-DF/MaaKEDR">
  <br>
  <img alt="commit" src="https://img.shields.io/github/commit-activity/m/APPLe-DF/MaaKEDR">
  <img alt="downloads" src="https://img.shields.io/github/downloads/APPLe-DF/MaaKEDR/total?style=social">
  <img alt="stars" src="https://img.shields.io/github/stars/APPLe-DF/MaaKEDR?style=social">
  <a href="https://mirrorchyan.com/zh/projects?rid=MaaKEDR&source=maakedr-badge" target="_blank"><img alt="mirrorc" src="https://img.shields.io/badge/Mirror%E9%85%B1-%239af3f6?logo=countingworkspro&logoColor=4f46e5"></a>
</p>

<div align="center">

[English](./README.en.md) | [简体中文](./README.md)

</div>

## 加入我们

- MaaKEDR 交流群 QQ：[1051890489](https://qm.qq.com/q/clvWu1RoWI)

---

> ✅ **项目状态：持续维护与迭代**
>
> 本项目已完成**每日主要流程**（启动游戏、领取奖励、资源刷取、技能演练等核心循环）的完整实现，
> 现进入**持续维护与迭代**阶段：
>
> - ✅ 核心流程已完整覆盖
> - 🔧 后续以 **Bug 修复**、**游戏版本适配**、**依赖更新** 为主，同时按需评估新功能、新任务、新流程

> 🎵 **开发方式**
>
> 本项目很大程度上使用了 **Vibe Coding** 开发模式 —— 通过与 AI 助手对话逐步生成代码。
> 开发者负责提供需求、截图、ROI 坐标、UI 分析和验收，AI 负责实现 pipeline 逻辑、Python 自定义节点、
> CI/CD 配置和文档编写。这种模式下开发效率大幅提升，代码质量通过 `pnpm check` 流水线保证。
>
> 如果你也在用 AI 做 MaaFramework 项目，这个仓库可以作为一个参考案例。
> 详见 [Vibe Coding 开发说明](docs/zh/develop/vibe-coding.md)。  
> 本项目还维护了 [AGENTS.md](AGENTS.md) 作为 AI 助手的行为指南，确保开发规范和一致性。

---

## 功能列表

- 启动游戏
- 领取奖励（派遣任务、每日/每周/军旅成就、战令通行证、邮箱、高级账号商店每日奖励，可独立开关）
- 资源刷取（特别军费行动、作战体能训练、兵种能力评级、载具对抗演练）
- 剩余体力刷取（固定清空体力模式的资源刷取，用于刷尽剩余体力，随预设/手动启用）
- 技能演练（基础技能、专业技能）
- 玩家对战（PVP 自动战斗，自动选择等级最低的对手，支持多场循环）
- 多关卡选择，可配置战斗次数（1~6 次 / 最大）
- 清空体力循环模式
- 活动关卡与活动商店（耀斑 EX 关卡刷取、商店商品清空）
- 体力信息（读取主界面体力并提示回满时间）

---

## 文档

- 📘 [在线文档站](https://apple-df.github.io/MaaKEDR/) — 用户手册、开发文档、协议约定
- 中文：[用户手册](https://apple-df.github.io/MaaKEDR/zh/manual/) · [开发文档](https://apple-df.github.io/MaaKEDR/zh/develop/) · [协议文档](https://apple-df.github.io/MaaKEDR/zh/protocol/)
- English: [User Manual](https://apple-df.github.io/MaaKEDR/en/manual/) · [Development](https://apple-df.github.io/MaaKEDR/en/develop/) · [Protocol](https://apple-df.github.io/MaaKEDR/en/protocol/)

---

## 使用说明

### 环境要求

- Windows 10+
- [VC++ Redistributable 2015+](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- .NET Desktop Runtime 8.0+（MFAAvalonia 需要）
- ADB 已配置（用于连接 Android 设备或模拟器）

### 下载安装

前往 [GitHub Releases](https://github.com/APPLe-DF/MaaKEDR/releases/latest) 下载最新版本压缩包，解压后运行即可。

- [Mirror酱高速下载](https://mirrorchyan.com/zh/projects?rid=MaaKEDR&source=maakedr-readme) — 已拥有 CDK 的用户可前往高速下载与自动更新

### 安装运行

```bash
# 安装运行时依赖
DependencySetup_依赖库安装_win.bat

# 启动 GUI（两个版本任选其一）
MFAAvalonia.exe     # Avalonia UI 版本
# 或
mxu.exe             # Tauri + React 版本（MaaEnd 同款）
```

在 GUI 界面中选择任务并配置选项即可开始自动化。

---

## 开发相关

```bash
pnpm install          # 安装开发依赖
pnpm check            # 代码检查（格式 + schema + MaaFW + lint）
pnpm check:py         # Python 代码检查（ruff + pyright）
pnpm format           # 格式化所有文件
pnpm format:py        # 格式化 Python 文件
```

### 项目结构

```
MaaKEDR/
├── interface.json               # 项目入口配置
├── tasks/                       # 任务定义（GUI 中显示的任务列表）
│   ├── startup.json             #   启动游戏
│   ├── pvp.json                 #   玩家对战
│   ├── claim_rewards.json       #   领取奖励
│   ├── farm_resources.json      #   资源刷取
│   ├── event_stage.json         #   活动关卡与活动商店
│   └── stamina_info.json        #   体力信息
├── resource/base/               # 核心资源
│   ├── pipeline/                #   Pipeline 流程定义
│   ├── image/                   #   模板匹配用图片
│   └── model/ocr/               #   PaddleOCR 模型
├── agent/                       # Python Agent（自定义识别/动作）
│   └── custom/
│       ├── recognition/         #   自定义识别
│       └── action/              #   自定义动作
├── docs/                        # 开发文档
├── tools/                       # 开发工具
└── .github/workflows/           # CI/CD 配置
```

更多文档请前往 [docs/](docs/README.md) 查看。

---

## 开发文档

详细的项目开发文档请参见 [docs/](docs/README.md)，包含：

- [Pipeline 编写指南](docs/zh/develop/pipeline.md)
- [Custom 识别与动作开发](docs/zh/develop/custom.md)
- [项目结构说明](docs/zh/develop/structure.md)
- [格式化规范](docs/zh/develop/formatting.md)
- [Bug 排查](docs/zh/develop/fix.md)
- [Vibe Coding 开发说明](docs/zh/develop/vibe-coding.md)

---

## Star 历史

<a href="https://github.com/APPLe-DF/MaaKEDR/stargazers">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/APPLe-DF/MaaKEDR/main/assets/dark.webp" />
   <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/APPLe-DF/MaaKEDR/main/assets/light.webp" />
   <img alt="APPLe-DF/MaaKEDR Star History" src="https://raw.githubusercontent.com/APPLe-DF/MaaKEDR/main/assets/light.webp" width="700" />
 </picture>
</a>

---

## 鸣谢

### 核心框架

- [MaaFramework](https://github.com/MaaXYZ/MaaFramework)  
  基于图像识别的自动化黑盒测试框架

### UI 支持

- [MFAAvalonia](https://github.com/SweetSmellFox/MFAAvalonia)  
  基于 Avalonia UI 构建的 MaaFramework 通用 GUI 解决方案
- [MXU](https://github.com/MistEO/MXU)  
  基于 MaaFramework PI V2 协议的通用 GUI 客户端，使用 Tauri + React + TypeScript 构建

### 社区项目

- [M9A](https://github.com/MAA1999/M9A)  
  优秀的 MaaFramework 自动化项目，开发过程中多有参考

### 工具链

- [create-maa-project](https://github.com/Windsland52/create-maa-project) — 项目脚手架
- [MaaMCP](https://github.com/MAA-AI/MaaMCP) — MaaFramework MCP 服务器

### 开发者

感谢以下开发者对本项目作出的贡献:

[![Contributors](https://contrib.rocks/image?repo=APPLe-DF/MaaKEDR&max=1000)](https://github.com/APPLe-DF/MaaKEDR/graphs/contributors)

---

## 许可证

[AGPL-3.0](./LICENSE)
