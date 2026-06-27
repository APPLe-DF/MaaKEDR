# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MaaFramework (MaaFW) pipeline-based automation project for **雪松 (KEDR)**, scaffolded by `create-maa-project`. This is a declarative automation system — pipelines are defined in JSON, not imperative code. The GUI frontend is **MFAAvalonia** (.NET 10.0 desktop app). Target resolution is 1280x720 (16:9), controlled via ADB on Android emulators/devices.

## Commands

```bash
pnpm install          # Install dependencies (MaaTools CLI, etc.)
pnpm check            # Run pipeline validation/linting via MaaTools
pnpm format:all       # Format all files (JSON + Python)
pnpm lint:py          # Python linting
pnpm typecheck        # Python type checking
```

Release: push a git tag (e.g. `v0.1.0`).

Runtime setup: run `DependencySetup_依赖库安装_win.bat` to install VC++ Redistributable 2015+ and .NET Desktop Runtime 10.0. Then launch `MFAAvalonia.exe`.

## Architecture

### Pipeline System

All automation logic lives in `resource/<slug>/pipeline/*.json` files. Each pipeline node is a JSON object keyed by its name (dot-separated hierarchy, e.g. `Tutorial.Start`):

```json
{
    "NodeName": {
        "recognition": "OCR | TemplateMatch | DirectHit | Custom",
        "expected": ".*",              // OCR text pattern (regex)
        "roi": [x, y, w, h],          // screen region to search
        "threshold": 0.7,             // match confidence
        "action": "Click | LongPress | Swipe | DoNothing | Custom",
        "target": true,               // click at recognized position
        "next": ["NextNode"],         // subsequent nodes
        "on_error": ["ErrorNode"],    // nodes when recognition fails
        "pre_delay": 200,             // ms before action
        "post_delay": 200,            // ms after action
        "max_hit": 5,                 // max recognition hits
        "timeout": 10000,             // max recognition time (ms)
        "focus": {                    // UI notifications
            "Node.Recognition.Succeeded": "消息内容"
        }
    }
}
```

Nodes form a directed graph via `next` arrays. Default parameters (timeouts, thresholds) are inherited from `resource/base/default_pipeline.json`.

### Recognition Types

- **OCR** — PaddleOCR v5 text detection/recognition (models in `model/ocr/`)
- **TemplateMatch** — OpenCV image matching (images in `image/`)
- **DirectHit** — always matches (unconditional entry point)
- **Custom** — Agent custom recognition (defined in `agent/custom/recognition/`)

### Action Types

- **Click** — Click at recognized position
- **Swipe** — Swipe gesture
- **DoNothing** — No action
- **Custom** — Agent custom action (defined in `agent/custom/action/`)

### Agent System

Custom recognition and actions are implemented in Python via MaaFramework's Agent system:

```
agent/
├── main.py                      # Agent entry point
├── custom/
│   ├── recognition/
│   │   └── farm_resources.py    # Custom recognition & actions
│   └── action/
│       └── ocr_logger.py        # OCR result logger
└── utils/
    ├── logger.py                # Loguru logger config
    └── params.py                # Parameter parsing utility
```

**Custom Recognition:**

- `CheckResourceStage` — Dynamic ROI resource stage detection with lock checking

**Custom Actions:**

- `SetBattleCount` — Set battle count (1-6 or max)
- `ReduceBattleCount` — Reduce battle count by 1

### Task Entry Points

Tasks in `tasks/*.json` define what appears in the MFAAvalonia GUI:

```json
{
    "task": [
        {
            "name": "任务名称",
            "entry": "Pipeline.NodeName",
            "option": ["option_name"]
        }
    ],
    "option": {
        "option_name": {
            "type": "select | switch",
            "label": "选项标签",
            "cases": [...]
        }
    }
}
```

### Configuration Files

- `interface.json` — MaaFW project definition: controller type, resources, task imports, agent config
- `maa-project.json` — Project metadata for `create-maa-project` tooling
- `maatools.config.mts` — MaaTools CLI config (resource paths, check settings)
- `config/maa_pi_config.json` — Plugin interface config (gitignored, local only)

### Runtime Stack

- **MFAAvalonia** — GUI frontend (.NET 10.0, Avalonia UI)
- **MaaFramework** — Native automation engine
- **ONNX Runtime + PaddleOCR v5** — OCR inference
- **OpenCV** — Image/template matching
- **Python 3.14** — Agent/plugin scripting
- **MaaAgentClient/Server** — Plugin communication protocol
- **Loguru** — Python logging

## Conventions

- **Encoding:** UTF-8, LF line endings (enforced by `.editorconfig` and `.gitattributes`)
- **Indentation:** 4 spaces for JSON/YAML, 2 spaces for TypeScript/Markdown
- **JSON-with-Comments:** Pipeline files, task files, and `interface.json` support `//` comments
- **ONNX files are binary** in git (tracked but not diffable)
- **Resource structure:** `resource/<slug>/` with subdirectories `pipeline/`, `image/`, `model/`
- **Pipeline naming:** Dot-separated hierarchical names (e.g. `FarmResources.Start`, `ClaimRewards.CheckDaily`)
- **ROI coordinates:** `[x, y, width, height]` in pixels at 1280x720 resolution
- **Gitignored:** `node_modules/`, `.venv/`, `config/`, `dist/`, `debug/`, `.create-maa-project/`, `test_*.json`

## File Layout

```
resource/base/
├── default_pipeline.json    # Inherited default parameters for all nodes
├── pipeline/                # Pipeline node definitions (JSON-with-Comments)
│   ├── startup.json         # 启动游戏流程
│   ├── claim_rewards.json   # 奖励领取流程
│   └── farm_resources.json  # 资源刷取流程
├── image/                   # Template images for TemplateMatch recognition
│   ├── claim_rewards/       # 奖励领取相关图片
│   └── farm_resources/      # 资源刷取相关图片
└── model/ocr/               # PaddleOCR v5 models

agent/                       # Python Agent代码
├── main.py                  # Agent入口
├── custom/
│   ├── recognition/         # 自定义识别
│   └── action/              # 自定义动作
└── utils/                   # 工具模块

tasks/                       # Task entry-point definitions
├── startup.json             # 启动游戏任务
├── claim_rewards.json       # 奖励领取任务
└── farm_resources.json      # 资源刷取任务

tools/                       # 开发工具
├── minify_json.py           # JSON压缩工具
└── validate_schema.py       # Schema验证工具

deps/tools/                  # JSON Schema文件
.vscode/                     # VSCode配置
```

## Key Design Decisions

1. **纯Pipeline架构** — 当前使用纯Pipeline实现，Agent仅用于复杂识别逻辑
2. **动态ROI** — 资源刷取使用Agent实现动态ROI，根据资源类型和关卡编号选择不同的识别区域
3. **清体力模式** — 每次刷1次，循环直到体力不足，参考M9A实现
4. **锁定检测** — 使用模板匹配检测锁定图标，支持技能演练和资源收集
5. **快速战斗** — 支持1-6次和最大次数选择，通过OCR识别当前次数并点击加号/减号调整
