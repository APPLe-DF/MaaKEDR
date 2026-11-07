---
title: "Project Structure"
order: 5
icon: "ri:folder-tree-fill"
---

# Project Structure

```text
MaaKEDR/
├── .github/                        # CI configuration
│   ├── ISSUE_TEMPLATE/             # Issue templates
│   ├── workflows/                  # GitHub Actions (check / format / release / android-build / deploy-docs, ...)
│   ├── PULL_REQUEST_TEMPLATE.md    # PR template
│   ├── cliff.toml                  # Changelog generation config
│   └── dependabot.yml              # Automated dependency updates
├── .vscode/                        # Editor config (recommended extensions, tasks, workspace settings)
│
├── interface.json                  # MaaFW project definition: tasks, controllers, resource packs, agent
├── maa-project.json / .lock.json   # Tooling state files
├── maatools.config.mts             # MaaTools config
├── package.json                    # Node toolchain and pnpm scripts
├── pnpm-workspace.yaml             # pnpm workspace definition
├── pyproject.toml / uv.lock        # Python project config and dependency lock
├── requirements.txt                # Python dependencies (also read by release and Android packaging)
├── .prettierrc.mjs                 # Prettier config
├── .editorconfig / .gitattributes / .gitignore / .gitmodules
├── .node-version / .python-version # Toolchain versions
├── README.md / README.en.md        # Chinese / English readmes
├── CONTRIBUTING.md / LICENSE / CONTACT / logo.ico
│
├── resource/base/                  # Official-server resources (interface.json resource.base)
│   ├── default_pipeline.json       # Global defaults
│   ├── pipeline/                   # Pipeline node definitions
│   │   ├── common.json             # Shared cross-task nodes (Common.EnsureHome hub, etc.)
│   │   ├── startup.json            # Game startup
│   │   ├── claim_rewards.json      # Reward claiming
│   │   ├── farm_resources.json     # Resource farming
│   │   ├── pvp.json                # PVP battles
│   │   ├── stamina.json            # Stamina info
│   │   ├── send_gift.json          # Send gift
│   │   └── event_stage.json        # Event stages and shop
│   ├── image/                      # Template images
│   │   ├── claim_rewards/          # Reward images
│   │   ├── farm_resources/         # Farming images
│   │   ├── pvp/                    # PVP images
│   │   ├── send_gift/              # Send-gift images
│   │   ├── event_stage/            # Event images
│   │   └── ...                     # Shared images
│   ├── model/ocr/                  # PP-OCRv6 models (copied from MaaCommonAssets, not committed)
│   ├── config/maa_option.json      # Runtime MaaFW options
│   └── debug/                      # Runtime logs and on_error screenshots
│
├── resource/bilibili/              # Bilibili-server additions (layered over resource/base; differences only)
├── resource/taptap/                # TapTap-server additions (same rule)
├── resource/announcement/          # GUI welcome announcement (interface.json → welcome)
│
├── tasks/                          # Task entry definitions
│   ├── startup.json                # Game startup
│   ├── claim_rewards.json          # Reward claiming
│   ├── farm_resources.json         # Resource farming
│   ├── farm_remaining_stamina.json # Remaining-stamina farming
│   ├── pvp.json                    # PVP battles
│   ├── stamina_info.json           # Stamina info
│   ├── send_gift.json              # Send gift
│   ├── event_stage.json            # Event stages and shop
│   └── preset/                     # Task presets (Daily / Activity)
│
├── agent/                          # Python Agent
│   ├── main.py                     # Entry: version check + resolve native libs → run_agent()
│   ├── maafw_paths.py              # Locate the client native runtime, set MAAFW_BINARY_PATH
│   ├── agent_runtime.py            # Core: log version → register → AgentServer
│   ├── custom/
│   │   ├── recognition/            # Custom recognition
│   │   ├── action/                 # Custom actions
│   │   └── sink/                   # Custom event sinks (e.g. aspect-ratio check)
│   └── utils/                      # Utility modules (logger / params / maa_types / pienv / runtime_paths)
│
├── tests/                          # pytest suite (custom modules and utilities)
│
├── tools/                          # Development and packaging scripts
│   ├── build-release.mjs           # Desktop release build (artifacts under dist/)
│   ├── android-packaging.mjs       # Android packaging parameter resolution (used by android-build.yml)
│   ├── check-project.mjs           # Project consistency check (pnpm lint)
│   ├── validate-schema.mjs         # Schema validation (pnpm check:schema)
│   ├── sync-runtime.mjs            # Runtime sync (pnpm sync:runtime)
│   ├── sync-schema.mjs             # Upstream schema sync (pnpm sync:schema)
│   ├── optimize-images.mjs         # Template image optimisation (pnpm optimize:images)
│   ├── schema/                     # JSON Schema (pipeline / interface / custom.*)
│   └── ...                         # Docs generation, APK helpers, etc.
│
├── Android/                        # Android packaging (MaaFwApp submodule + profile.yaml recipe)
├── MaaCommonAssets/                # Shared assets submodule (source of the OCR models)
│
└── docs/                           # Documentation site (VuePress)
    ├── .vuepress/                  # Site config (config.ts / plume.config.ts / navigation/)
    ├── zh/                         # Chinese docs (develop / manual / protocol)
    └── en/                         # English docs (mirrors zh one-to-one)
```

## Three-Layer Architecture

```text
tasks/*.json ──→ pipeline/*.json ──→ agent/custom/
(task entry)     (node graph)        (Python logic)
```

- **Layer 1 — Tasks** (`tasks/*.json`): GUI task entries and options
- **Layer 2 — Pipeline** (`resource/base/pipeline/*.json`): JSON node graphs, 90% of logic
- **Layer 3 — Agent** (`agent/custom/`): Python code for complex logic

## Directory Responsibilities

| Path                      | Responsibility                                                                                                                                           |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `interface.json`          | Public entry: task list, controller (ADB), resource packs (`base` official / `bilibili` / `taptap`), `agent` child-process declaration                   |
| `tasks/`                  | One JSON per task: `task` list + options + `pipeline_override`; `preset/` holds task presets                                                             |
| `resource/base/pipeline/` | The node graphs themselves. One file per feature module; cross-task shared nodes live in `common.json`                                                   |
| `resource/base/image/`    | Template images, grouped into per-module folders; naming and cropping rules in the [Pipeline Guide](./pipeline.md)                                       |
| `resource/<server>/`      | Server-specific additions layered over `resource/base` (order set by the `resource` field in `interface.json`); only put files that differ from official |
| `agent/`                  | All Python code: `main.py` entry, `agent_runtime.py` wiring, `custom/` custom modules, `utils/` helpers                                                  |
| `tests/`                  | pytest cases covering custom modules and utilities; run with `pnpm test:py`                                                                              |
| `tools/`                  | Development scripts: schema validation, project checks, runtime/schema sync, release packaging, docs generation                                          |
| `docs/`                   | VuePress documentation site; `zh/` and `en/` mirror each other, `.vuepress/` holds site config and navigation                                            |

## Local Directories (Not Committed)

The directories below are excluded by `.gitignore`. They are local environment or runtime artifacts — **do not commit them and do not treat them as project source**:

| Path                              | Origin                                                                                    |
| --------------------------------- | ----------------------------------------------------------------------------------------- |
| `runtimes/`, `libs/`, `plugins/`  | MaaFW native runtime and binary dependencies, filled by `pnpm sync:runtime` or the client |
| `dist/`                           | Packaging output of `tools/build-release.mjs`                                             |
| `config/`, `debug/`               | Created at runtime: client config, logs (`debug/custom/`), `on_error` screenshots         |
| `resource/base/model/ocr/`        | Copied from the `MaaCommonAssets` submodule, not committed                                |
| `Android/agent-dist/`, `logo.png` | Android packaging artifacts                                                               |
| `node_modules/`, `.venv/`         | Installed dependencies                                                                    |

## Release and Packaging

| Command                        | Purpose                                                                                   |
| ------------------------------ | ----------------------------------------------------------------------------------------- |
| `pnpm check`                   | Format check → schema validation → MaaFW integrity → project lint (run before submitting) |
| `pnpm check:py`                | Ruff lint + pyright type check (run when Python changes)                                  |
| `pnpm test:py`                 | Run pytest                                                                                |
| `pnpm format`                  | Prettier across the repo (`pnpm format:py` for Python)                                    |
| `pnpm release:dry-run`         | Dry-run the release build without writing artifacts                                       |
| `pnpm sync:runtime`            | Sync the MaaFW native runtime                                                             |
| `pnpm sync:schema`             | Sync `tools/schema/` from upstream                                                        |
| `pnpm docs:dev` / `docs:build` | Serve the docs site locally / build it                                                    |

- **Desktop release**: `tools/build-release.mjs` (artifacts under `dist/`), triggered by `.github/workflows/release.yml`; Mirror酱 updates go through `mirrorchyan_release.yml`
- **Android packaging**: `Android/profile.yaml` is the packaging recipe (resources point at the repository root) and `Android/MaaFwApp` is the shell submodule; `tools/android-packaging.mjs` resolves versions and naming parameters for `.github/workflows/android-build.yml`. Details in [Android Packaging](./android.md)
- **CI**: `check.yml` (`pnpm check`), `format.yml`, `check-docs.yml` / `deploy-docs.yml` (docs site), `optimize-images.yml`, `schema-sync.yml` and `package-smoke.yml` under `.github/workflows/`
