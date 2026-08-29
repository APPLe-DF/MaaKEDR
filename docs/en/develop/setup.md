---
order: 1
icon: ri:tools-fill
---

# Setup & Development Quickstart

## Overview

This guide is for contributors who want to set up a development environment for MaaKEDR and build their first pipeline.

## Prerequisites

### System Requirements

| Item             | Requirement                 |
| ---------------- | --------------------------- |
| OS               | Windows 10+ / macOS / Linux |
| Python           | 3.13                        |
| Node.js          | >= 24                       |
| Package Managers | pnpm (via corepack) + uv    |
| Version Control  | Git                         |

### Setup Steps

#### 1. Python 3.13

```bash
python --version   # must be 3.13.x
```

> Download from [python.org](https://www.python.org/downloads/) if needed.

#### 2. Install uv

```bash
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify:

```bash
uv --version
```

#### 3. Install Node.js and pnpm

Download Node.js >= 24 from [nodejs.org](https://nodejs.org/), then enable pnpm:

```bash
corepack enable
corepack prepare pnpm@latest --activate
pnpm --version
```

### Clone the Project

```bash
git clone --recurse-submodules https://github.com/APPLe-DF/MaaKEDR.git
cd MaaKEDR
```

OCR models (`resource/base/model/ocr/`) come from the `MaaCommonAssets` submodule. That directory is git-ignored and populated from the submodule at build time, so **the submodule must be initialized** — otherwise tasks fail because the models are missing.

If you already cloned without the flag:

```bash
git submodule update --init --recursive
```

For pull requests, fork first and clone your fork (see Contributing below).

### Install Dependencies

```bash
pnpm install
uv sync --frozen
```

> `uv sync --frozen` installs locked versions from `uv.lock` for reproducible builds.

### Sync Runtime and OCR Models

```bash
pnpm sync:runtime
```

This downloads the MaaFW runtime and copies the OCR models from the `MaaCommonAssets` submodule into `resource/base/model/ocr/`.

**Required on first setup**: `git submodule update --init --recursive` downloads the full `MaaCommonAssets` submodule (roughly 344 MB), not just the OCR files; during runtime synchronization, only the OCR files are copied into the project. If either this sync or the submodule initialization is skipped, nothing fails loudly — every OCR recognition will fail at runtime.

To restore just the models without re-downloading the whole runtime:

```bash
pnpm dlx create-maa-project@latest --update ocr-models
```

### Verify Setup

```bash
pnpm check
pnpm check:py
```

> The first run downloads the MaaFramework runtime — ensure network connectivity.

## Debugging Tools

| Tool                                                                                                  | Description                                                                                                               |
| ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| [MaaDebugger](https://github.com/MaaXYZ/MaaDebugger)                                                  | Standalone debugger: connect a controller, inspect recognition results and screenshots live                               |
| [Maa Pipeline Support](https://marketplace.visualstudio.com/items?itemName=nekosu.maa-support)        | VSCode extension: debugging, screenshots, ROI acquisition, color picking                                                  |
| [MFAToolsPlus](https://github.com/SweetSmellFox/MFAToolsPlus)                                         | Cross-platform toolbox: convenient data acquisition and mock testing                                                      |
| [MaaLogAnalyzer](https://github.com/Windsland52/MAALogAnalyzer)                                       | Visual log analysis for MaaFramework apps (`maafw.log`)                                                                   |
| [MaaEvidenceKit](https://github.com/Windsland52/MaaEvidenceKit)                                       | Deterministic evidence extraction/diagnostic toolkit for MaaFramework (CLI/SDK), for on-demand diagnosis by AI assistants |
| [ImageCropper (not recommended)](https://github.com/MaaXYZ/MaaFramework/tree/main/tools/ImageCropper) | Standalone screenshot/ROI tool, superseded by the VSCode extension                                                        |

::: tip Recommended combo
Use **Maa Pipeline Support** (VSCode extension) for development and debugging, and **MaaLogAnalyzer** for analyzing user logs (see [Troubleshooting](./fix.md#log-analysis-tools)).
:::

## Project Structure Overview

```text
MaaKEDR/
├── interface.json        # Entry config — tasks and connection settings
├── maa-project.json      # MaaFramework project configuration
├── tasks/                # Task definitions (visible in GUI task list)
├── resource/
│   ├── base/pipeline/    # Pipeline JSON node definitions
│   ├── base/image/       # Template matching images
│   └── base/model/ocr/   # PaddleOCR models
├── agent/custom/         # Python custom recognition and action modules
├── docs/                 # Documentation site
└── tools/                # Build and release scripts
```

Key concepts:

- **Pipeline**: JSON node graph — each node defines a recognize → act → transition step
- **Task**: `tasks/*.json` entry points selectable from the GUI
- **Template Image**: A cropped game screenshot region used for template matching
- **Custom Module**: Python code for complex recognition or action logic

## Your First Pipeline

Scenario: detect a "Start Game" button and click it.

### 1. Capture a Screenshot

Take a screenshot from your emulator or device. Save as `start_screen.png`.

### 2. Measure the ROI

Open `start_screen.png` in an image editor and measure the button:

```text
Example at 1280x720 resolution:
x = 540, y = 600, w = 200, h = 60
```

### 3. Create a Template Image

Crop the button from the screenshot and save to `resource/base/image/`:

```text
resource/base/image/start_button.png
```

> Keep template images between 50x50 and 200x200 pixels for best performance.

### 4. Write the Pipeline Node

Create a JSON file under `resource/base/pipeline/`:

```json
{
    "ClickStart": {
        "recognition": "TemplateMatch",
        "template": "start_button.png",
        "roi": [
            500,
            570,
            280,
            100
        ],
        "threshold": 0.8,
        "action": "Click",
        "next": ["CheckMainPage"]
    },
    "CheckMainPage": {
        "recognition": "DirectHit",
        "action": "DoNothing",
        "next": []
    }
}
```

### 5. Define a Task

Create a JSON file in `tasks/` to make it selectable:

```json
{
    "TestClickStart": {
        "pipeline_override": {
            "ClickStart": {
                "next": []
            }
        }
    }
}
```

### 6. Run and Verify

This project does **not** ship a standalone MaaPiCli package. Use the **MFAAvalonia / MXU** GUI from the release package to run tasks, or start the Agent in a local dev setup as described in [AGENTS.md](https://github.com/APPLe-DF/MaaKEDR/blob/main/AGENTS.md).

> Make sure your emulator is running and the game is on the correct screen.

## Development Workflow

```text
Screenshot → Measure ROI → Create Template → Write Pipeline → Bind Task → Run → Iterate
```

Each iteration:

1. Run `pnpm check` to validate formatting and schemas
2. Run `pnpm check:py` for Python module changes
3. Check logs and screenshots in `debug/` to diagnose issues

## Contributing & Pull Requests

1. Fork and clone your fork
2. Branch from latest `main` (`feat/…`, `fix/…`, `docs/…`)
3. Pass `pnpm check` (and `pnpm check:py` when touching Python)
4. Open a focused PR (one concern per PR)
5. Describe motivation, scope, and how you tested

See [CONTRIBUTING.md](https://github.com/APPLe-DF/MaaKEDR/blob/main/CONTRIBUTING.md) and [AGENTS.md](https://github.com/APPLe-DF/MaaKEDR/blob/main/AGENTS.md).

**Release**: before tagging `vX.Y.Z`, manually update `interface.json` `version` and `title`.

## References

- [MaaFramework Documentation](https://maafw.com/docs/1.1-QuickStarted)
- [Pipeline Guide](./pipeline.md)
- [Custom Module Guide](./custom.md)
- [Troubleshooting](./fix.md)
- [Formatting Guide](./formatting.md)
- [Writing Docs](./doc.md)
- [Protocol](../protocol/)
- [AGENTS.md](https://github.com/APPLe-DF/MaaKEDR/blob/main/AGENTS.md)
