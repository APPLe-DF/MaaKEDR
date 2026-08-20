---
title: "Project Structure"
order: 5
icon: "ri:folder-tree-fill"
---

# Project Structure

```
MaaKEDR/
├── interface.json                  # MaaFW project definition
├── maa-project.json / .lock.json   # Tooling state files
├── package.json                    # Node toolchain scripts
├── maatools.config.mts             # MaaTools config
│
├── resource/base/
│   ├── default_pipeline.json       # Global defaults
│   ├── pipeline/                   # Pipeline node definitions
│   │   ├── startup.json            # Game startup
│   │   ├── claim_rewards.json      # Reward claiming
│   │   ├── farm_resources.json     # Resource farming
│   │   └── event_stage.json         # Event stages and shop
│   ├── image/                      # Template images
│   │   ├── claim_rewards/          # Reward images
│   │   ├── farm_resources/         # Farming images
│   │   └── ...
│   ├── model/ocr/                  # PaddleOCR v5 models
│   └── WELCOME.md                  # GUI welcome page
│
├── agent/                          # Python Agent
│   ├── bootstrap.py                # Entry: env check → main.py
│   ├── main.py                     # Shim → run_agent()
│   ├── agent_runtime.py            # Core: register → AgentServer
│   ├── custom/
│   │   ├── recognition/            # Custom recognition
│   │   └── action/                 # Custom actions
│   └── utils/                      # Utility modules
│
├── tasks/                          # Task entry definitions
│   ├── startup.json
│   ├── claim_rewards.json
│   ├── farm_resources.json
│   └── event_stage.json            # Event stages and shop
│
├── tools/                          # Dev tools
│   ├── build-release.mjs           # Release packaging
│   ├── check-project.mjs           # Project validation
│   ├── sync-runtime.mjs            # Runtime sync
│   └── schema/                     # JSON Schema
│
└── docs/                           # Documentation
    └── ...
```

## Three-Layer Architecture

```
tasks/*.json ──→ pipeline/*.json ──→ agent/custom/
(task entry)     (node graph)        (Python logic)
```

- **Layer 1 — Tasks** (`tasks/*.json`): GUI task entries and options
- **Layer 2 — Pipeline** (`resource/base/pipeline/*.json`): JSON node graphs, 90% of logic
- **Layer 3 — Agent** (`agent/custom/`): Python code for complex logic
