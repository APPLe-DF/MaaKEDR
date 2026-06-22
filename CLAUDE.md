# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MaaFramework (MaaFW) pipeline-based automation project for **雪松 (KEDR)**, scaffolded by `create-maa-project`. This is a declarative automation system — pipelines are defined in JSON, not imperative code. The GUI frontend is **MFAAvalonia** (.NET 10.0 desktop app). Target resolution is 1280x720 (16:9), controlled via ADB on Android emulators/devices.

## Commands

```bash
pnpm install          # Install dependencies (MaaTools CLI, etc.)
pnpm check            # Run pipeline validation/linting via MaaTools
```

Release: push a git tag (e.g. `v0.1.0`).

Runtime setup: run `DependencySetup_依赖库安装_win.bat` to install VC++ Redistributable 2015+ and .NET Desktop Runtime 10.0. Then launch `MFAAvalonia.exe`.

## Architecture

### Pipeline System

All automation logic lives in `resource/<slug>/pipeline/*.json` files. Each pipeline node is a JSON object keyed by its name (dot-separated hierarchy, e.g. `Tutorial.Start`):

```json
{
    "NodeName": {
        "recognition": "OCR | TemplateMatch | DirectHit",
        "expected": ".*",              // OCR text pattern (regex)
        "roi": [x, y, w, h],          // screen region to search
        "threshold": 0.7,             // match confidence
        "action": "Click | LongPress | Swipe | DoNothing",
        "target": true,               // click at recognized position
        "next": ["NextNode"],         // subsequent nodes
        "pre_delay": 200,             // ms before action
        "post_delay": 200             // ms after action
    }
}
```

Nodes form a directed graph via `next` arrays. Default parameters (timeouts, thresholds) are inherited from `resource/base/default_pipeline.json`.

### Recognition Types

- **OCR** — PaddleOCR v5 text detection/recognition (models in `model/ocr/`)
- **TemplateMatch** — OpenCV image matching (images in `image/`)
- **DirectHit** — always matches (unconditional entry point)

### Task Entry Points

Tasks in `tasks/*.json` define what appears in the MFAAvalonia GUI:

```json
{
    "task": [
        { "name": "Display Name", "entry": "Pipeline.NodeName" }
    ]
}
```

### Configuration Files

- `interface.json` — MaaFW project definition: controller type, resources, task imports
- `maa-project.json` — Project metadata for `create-maa-project` tooling
- `maatools.config.mts` — MaaTools CLI config (resource paths, check settings)
- `appsettings.json` — MFAAvalonia GUI state (instances, timers)
- `config/maa_pi_config.json` — Plugin interface config (gitignored, local only)

### Runtime Stack

- **MFAAvalonia** — GUI frontend (.NET 10.0, Avalonia UI)
- **MaaFramework** — Native automation engine (in `runtimes/win-x64/native/`)
- **ONNX Runtime + PaddleOCR v5** — OCR inference
- **OpenCV** — Image/template matching
- **Embedded Python 3.14** — Agent/plugin scripting (`python/` directory)
- **MaaAgentClient/Server** — Plugin communication protocol

## Conventions

- **Encoding:** UTF-8, LF line endings (enforced by `.editorconfig` and `.gitattributes`)
- **Indentation:** 4 spaces for JSON/YAML, 2 spaces for TypeScript/Markdown
- **JSON-with-Comments:** Pipeline files, task files, and `interface.json` support `//` comments
- **ONNX files are binary** in git (tracked but not diffable)
- **Resource structure:** `resource/<slug>/` with subdirectories `pipeline/`, `image/`, `model/`
- **Pipeline naming:** Dot-separated hierarchical names (e.g. `Tutorial.Start`, `Combat.Entry`)
- **ROI coordinates:** `[x, y, width, height]` in pixels at 1280x720 resolution
- **Gitignored:** `node_modules/`, `.venv/`, `config/`, `dist/`, `debug/`, `.create-maa-project/`

## File Layout

```
resource/base/
├── default_pipeline.json    # Inherited default parameters for all nodes
├── pipeline/                # Pipeline node definitions (JSON-with-Comments)
├── image/                   # Template images for TemplateMatch recognition
└── model/ocr/               # PaddleOCR v5 models (det.onnx, rec.onnx, keys.txt)

tasks/                       # Task entry-point definitions
interface.json               # MaaFW project interface (controller, resources, tasks)
maatools.config.mts          # MaaTools CLI configuration
```

Runtime binaries (`libs/`, `runtimes/`, `python/`, `plugins/`, `MFAAvalonia.*`, `libloader.dll`) are distributed with the project, not built from source.
