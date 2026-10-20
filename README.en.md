<!-- markdownlint-disable MD033 MD041 -->
<div align="center">

<img alt="LOGO" src="resource/base/image/maakedr-logo_512x512.png" width="256" height="256" />

# MaaKEDR

KEDR Automation Assistant. Image recognition + simulated control, free your hands!  
Powered by [MaaFramework](https://github.com/MaaXYZ/MaaFramework)!  
<a href="https://github.com/APPLe-DF/MaaKEDR" target="_blank" style="font-weight: bold;">🔗 GitHub Repository</a><br>
🌟 Star us on the top-right of the repo if you like this project! 🌟

</div>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white">
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Android-blueviolet">
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

## Join Us

- MaaKEDR QQ Group: [1051890489](https://qm.qq.com/q/clvWu1RoWI)

---

> ℹ️ **Project Status: Active Maintenance & Iteration**
>
> The core daily flows (game launch, claim rewards, resource farming, skill training, etc.) are fully implemented,
> and the project is now in **active maintenance & iteration**:
>
> - ✅ Core flows fully covered
> - 🔧 Focus on **bug fixes**, **game version adaptation**, and **dependency updates**, with new features evaluated on demand

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
- Claim Rewards (dispatch tasks, daily/weekly/military achievements, battle pass, mailbox, premium shop daily reward — individually toggleable)
- Resource Farming (Special Funds, Physical Training, Unit Rating, Vehicle Drill)
- Remaining Stamina Farming (Farm Resources locked to Clear Stamina mode, for draining leftover stamina; enabled via presets or manually)
- Skill Training (Basic Skills, Advanced Skills)
- PVP (auto-battle with automatic selection of the lowest-level opponent, multi-round loop)
- Multiple stage selection with configurable battle count (1-6 / max)
- Stamina-drain loop mode
- Event stages and shop (Flare EX-stage farming and shop clearing)
- Stamina info (reads home-screen stamina and reports refill time)

---

## Documentation

- 📘 [Online docs](https://apple-df.github.io/MaaKEDR/) — user manual, development guides, protocol notes
- English: [User Manual](https://apple-df.github.io/MaaKEDR/en/manual/) · [Development](https://apple-df.github.io/MaaKEDR/en/develop/) · [Protocol](https://apple-df.github.io/MaaKEDR/en/protocol/)
- 中文：[用户手册](https://apple-df.github.io/MaaKEDR/zh/manual/) · [开发文档](https://apple-df.github.io/MaaKEDR/zh/develop/) · [协议文档](https://apple-df.github.io/MaaKEDR/zh/protocol/)

---

## User Guide

### Requirements

MaaKEDR supports Windows / macOS / Linux desktop platforms as well as an **Android** client. See the [Beginner's Guide](docs/en/manual/newbie.md) for detailed setup.

**Desktop:**

- Windows 10+
- [VC++ Redistributable 2015+](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- [.NET Desktop Runtime 10.0](https://dotnet.microsoft.com/download/dotnet/10.0) (required by MFAAvalonia)
- ADB set up (for connecting to Android device or emulator)

**Android client:**

- Android 10 (API 29) or later
- No emulator, no ADB or runtime setup — install and run
- Requires **Shizuku or root** authorization
- Background mode only (the virtual display is fixed at 720p@240dpi); foreground mode is disabled because a phone's physical screen ratio does not match the 720p assets

### Download

Download the latest release from [GitHub Releases](https://github.com/APPLe-DF/MaaKEDR/releases/latest), extract the archive, and run.

- [Mirror酱高速下载](https://mirrorchyan.com/zh/projects?rid=MaaKEDR&source=maakedr-readme) — Faster downloads & auto-updates for CDK holders

Desktop builds ship two GUIs per platform (**MFAA** and **MXU**) — pick the archive matching your OS and architecture. Android ships three APKs:

| Package                                                 | For                                                                           |
| ------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `MaaKEDR-android-arm64-v8a-<version>.apk` (recommended) | Most Android phones; about half the size of the universal build               |
| `MaaKEDR-android-universal-<version>.apk`               | Dual-ABI universal build — works on phones and emulators; pick this if unsure |
| `MaaKEDR-android-x86_64-<version>.apk`                  | x86 environments (some Android emulators)                                     |

### Install & Run

**Desktop:**

```bash
# Install runtime dependencies
DependencySetup_依赖库安装_win.bat

# Launch the GUI (pick one)
MFAAvalonia.exe     # Avalonia UI version
# or
mxu.exe             # Tauri + React version
```

Select tasks and configure options in the GUI to start automation.

**Android:**

Install the APK matching your architecture and launch it. On first run, grant notification and battery-optimization exemptions, then complete Shizuku or root authorization. The app bundles the same GUI and task list as the desktop builds — just pick a task and run.

---

## Development

```bash
pnpm install          # Install dev dependencies
pnpm check            # Code check (format + schema + MaaFW + lint)
pnpm check:py         # Python code check (ruff + pyright)
pnpm test:py          # Run Python unit tests (pytest)
pnpm format           # Format all files
pnpm format:py        # Format Python files
pnpm release:dry-run  # Release dry run (validates artifact naming, no packaging)
```

> Before submitting, make sure `pnpm check`, `pnpm check:py`, and `pnpm test:py` all pass.
> After touching pipeline / interface / agent code, run a self-review with `maakedr-review`.

### Project Structure

```
MaaKEDR/
├── interface.json           # Project entry config (PI V2)
├── maa-project.json         # create-maa-project project config
├── tasks/                   # Task definitions (task list shown in the GUI)
│   ├── startup.json         #   Game launch
│   ├── pvp.json             #   PVP
│   ├── claim_rewards.json   #   Claim rewards
│   ├── farm_resources.json  #   Resource farming
│   ├── farm_remaining_stamina.json # Remaining stamina farming
│   ├── event_stage.json     #   Event stages & shop
│   └── stamina_info.json    #   Stamina info
├── resource/
│   ├── base/                # Core resources (shared by all servers)
│   │   ├── pipeline/        #   Pipeline definitions
│   │   ├── image/           #   Template images
│   │   └── model/ocr/       #   PaddleOCR models
│   ├── bilibili/            # Bilibili server overrides
│   ├── taptap/              # TapTap server overrides
│   └── announcement/        # Client announcement & welcome page
├── agent/                   # Python Agent (custom recognition/actions)
│   ├── main.py              #   Entrypoint (calls maafw_paths before importing maa)
│   ├── maafw_paths.py       #   Locates client native libs; must run before any `import maa`
│   ├── agent_runtime.py     #   AgentServer runtime wiring
│   ├── custom/
│   │   ├── recognition/     #   Custom recognition
│   │   └── action/          #   Custom actions
│   └── utils/               #   Reusable helpers (logging, HTTP, scaling, ...)
├── Android/                 # Android client packaging
│   ├── profile.yaml         #   MaaFwApp build recipe
│   └── MaaFwApp/            #   Client shell (git submodule)
├── tests/                   # pytest unit tests
├── docs/                    # Development & user docs (zh / en)
├── tools/                   # Build, release, schema validation, CI scripts
└── .github/workflows/       # CI/CD config
```

For more documentation, see [docs/](docs/README.md).

---

## Development Docs

See [docs/](docs/README.md) for detailed development documentation:

- [Setup & Development Quickstart](docs/en/develop/setup.md)
- [Pipeline Guide](docs/en/develop/pipeline.md)
- [Custom Recognition & Action](docs/en/develop/custom.md)
- [Project Structure](docs/en/develop/structure.md)
- [Shared Home Recovery Hub](docs/en/develop/common.md)
- [Android Client & Packaging](docs/en/develop/android.md)
- [Formatting](docs/en/develop/formatting.md)
- [Troubleshooting](docs/en/develop/fix.md)
- [Overseas Client Adaptation](docs/en/develop/overseas-client-adaptation.md)
- [Vibe Coding Development](docs/en/develop/vibe-coding.md)

---

## Star History

<a href="https://github.com/APPLe-DF/MaaKEDR/stargazers">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/APPLe-DF/MaaKEDR/main/assets/dark.webp" />
   <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/APPLe-DF/MaaKEDR/main/assets/light.webp" />
   <img alt="APPLe-DF/MaaKEDR Star History" src="https://raw.githubusercontent.com/APPLe-DF/MaaKEDR/main/assets/light.webp" width="700" />
 </picture>
</a>

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
- [MaaFwApp](https://github.com/Aliothmoon/MaaFwApp)  
  A universal Android GUI based on MaaFramework PI V2 protocol, the Android shell of MaaKEDR (see [Android/](Android/README.md))

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
