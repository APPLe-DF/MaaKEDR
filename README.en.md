<!-- markdownlint-disable MD033 MD041 -->
<div align="center">

<img alt="LOGO" src="resource/base/image/maakedr-logo_512x512.png" width="256" height="256" />

# MaaKEDR

Cedar Automation Assistant. Image recognition + simulated control, free your hands!  
Powered by [MaaFramework](https://github.com/MaaXYZ/MaaFramework)!  
<a href="https://github.com/APPLe-DF/MaaKEDR" target="_blank" style="font-weight: bold;">🔗 GitHub Repository</a><br>
🌟 Star us on the top-right of the repo if you like this project! 🌟

</div>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white">
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blueviolet">
  <img alt="license" src="https://img.shields.io/github/license/APPLe-DF/MaaKEDR">
  <br>
  <img alt="commit" src="https://img.shields.io/github/commit-activity/m/APPLe-DF/MaaKEDR">
  <img alt="stars" src="https://img.shields.io/github/stars/APPLe-DF/MaaKEDR?style=social">
  <a href="https://mirrorchyan.com/zh/projects?rid=MaaKEDR&source=maakedr-badge" target="_blank"><img alt="mirrorc" src="https://img.shields.io/badge/Mirror%E9%85%B1-%239af3f6?logo=countingworkspro&logoColor=4f46e5"></a>
</p>

<div align="center">

[English](./README.en.md) | [简体中文](./README.md)

</div>

## Join Us

- MaaKEDR QQ Group: [1051890489](https://qm.qq.com/q/clvWu1RoWI)

---

> ℹ️ **Project Status: Maintenance Mode**
>
> After completing the daily routine features, this project will enter **maintenance mode**,
> with no active development of new content, only bug fixes and necessary compatibility updates.
>
> For more comprehensive features and active maintenance, please consider the similar open-source project
> [MaaAssistantKedrgame (MAK)](https://github.com/Hollow-YK/MaaAssistantKedrgame).

> 🎵 **Development Approach**
>
> This project was largely developed using **Vibe Coding** — generating code through iterative conversations with an AI assistant (opencode).
> The developer provides requirements, screenshots, ROIs, UI analysis, and validation; the AI implements pipeline logic, Python custom nodes,
> CI/CD configuration, and documentation. This approach greatly improves development efficiency, with code quality ensured by `pnpm check` pipelines.
>
> If you're building a MaaFramework project with AI, this repository can serve as a reference case.
> See [Vibe Coding Development](docs/en/develop/vibe-coding.md) for details.  
> This project also maintains [AGENTS.md](AGENTS.md) as an AI behavior guide to ensure development conventions and consistency.

---

## Features

- Game Launch
- Claim Rewards (dispatch tasks, daily/weekly/military achievements, battle pass, mailbox — individually toggleable)
- Resource Farming (Special Funds, Physical Training, Unit Rating, Vehicle Drill)
- Skill Training (Basic Skills, Advanced Skills)
- Multiple stage selection with configurable battle count (1-6 / max)
- Stamina-drain loop mode

---

## Documentation

- 📘 [Online docs](https://apple-df.github.io/MaaKEDR/) — user manual, development guides, protocol notes
- English: [User Manual](https://apple-df.github.io/MaaKEDR/en/manual/) · [Development](https://apple-df.github.io/MaaKEDR/en/develop/) · [Protocol](https://apple-df.github.io/MaaKEDR/en/protocol/)
- 中文：[用户手册](https://apple-df.github.io/MaaKEDR/zh/manual/) · [开发文档](https://apple-df.github.io/MaaKEDR/zh/develop/) · [协议文档](https://apple-df.github.io/MaaKEDR/zh/protocol/)

---

## User Guide

### Requirements

- Windows 10+
- [VC++ Redistributable 2015+](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- [.NET Desktop Runtime 10.0](https://dotnet.microsoft.com/download/dotnet/10.0)
- ADB set up (for connecting to Android device or emulator)

### Download

Download the latest release from [GitHub Releases](https://github.com/APPLe-DF/MaaKEDR/releases/latest), extract the archive, and run.

- [Mirror酱高速下载](https://mirrorchyan.com/zh/projects?rid=MaaKEDR&source=maakedr-readme) — Faster downloads & auto-updates for CDK holders

```bash
# Install runtime dependencies
DependencySetup_依赖库安装_win.bat

# Launch the GUI
MFAAvalonia.exe
```

Select tasks and configure options in the MFAAvalonia UI to start automation.

---

## Development

```bash
pnpm install          # Install dev dependencies
pnpm check            # Lint + typecheck
pnpm format:all       # Format all files
```

### Project Structure

```
MaaKEDR/
├── resource/base/           # Core resources
│   ├── pipeline/            # Pipeline definitions
│   ├── image/               # Template images
│   └── model/ocr/           # PaddleOCR models
├── agent/                   # Python Agent (custom recognition/actions)
│   └── custom/
│       ├── recognition/     # Custom recognition
│       └── action/          # Custom actions
├── tasks/                   # Task entry points
├── tools/                   # Dev tools
└── interface.json           # MaaFramework project definition
```

For more documentation, visit the [MaaFramework](https://github.com/MaaXYZ/MaaFramework) main repository.

---

## Development Docs

See [docs/](docs/README.md) for detailed development documentation:

- [Pipeline Guide](docs/en_us/develop/pipeline.md)
- [Custom Recognition & Action](docs/en_us/develop/custom.md)
- [Project Structure](docs/en_us/develop/structure.md)
- [Formatting](docs/en_us/develop/formatting.md)
- [Troubleshooting](docs/en_us/develop/fix.md)
- [Vibe Coding Development](docs/en_us/develop/vibe-coding.md)

---

## Acknowledgments

### Core Framework

- [MaaFramework](https://github.com/MaaXYZ/MaaFramework)  
  An automation black-box testing framework based on image recognition

### UI Support

- [MFAAvalonia](https://github.com/SweetSmellFox/MFAAvalonia)  
  Universal MaaFramework GUI solution built with Avalonia UI
- [MXU](https://github.com/MistEO/MXU)  
  A universal GUI client based on MaaFramework PI V2 protocol, built with Tauri + React + TypeScript

### Community Project

- [M9A](https://github.com/MAA1999/M9A)  
  An excellent MaaFramework automation project — referenced during development

### Toolchain

- [create-maa-project](https://github.com/Windsland52/create-maa-project) — Project scaffolding
- [MaaMCP](https://github.com/MAA-AI/MaaMCP) — MaaFramework MCP server

### Developers

Thanks to the following developers who have contributed to this project:

[![Contributors](https://contrib.rocks/image?repo=APPLe-DF/MaaKEDR&max=1000)](https://github.com/APPLe-DF/MaaKEDR/graphs/contributors)

---

## License

[AGPL-3.0](./LICENSE)
