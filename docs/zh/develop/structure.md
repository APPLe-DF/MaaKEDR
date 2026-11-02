---
title: "项目结构说明"
order: 5
icon: "ri:folder-tree-fill"
---

# 项目结构

```text
MaaKEDR/
├── .github/                        # CI 配置
│   ├── ISSUE_TEMPLATE/             # Issue 模板
│   ├── workflows/                  # GitHub Actions（check / format / release / android-build / deploy-docs 等）
│   ├── PULL_REQUEST_TEMPLATE.md    # PR 模板
│   ├── cliff.toml                  # 变更日志生成配置
│   └── dependabot.yml              # 依赖自动更新
├── .vscode/                        # 编辑器配置（推荐扩展、任务、工作区设置）
│
├── interface.json                  # MaaFW 项目定义：任务入口、控制器、资源包、agent
├── maa-project.json / .lock.json   # 工具状态文件
├── maatools.config.mts             # MaaTools 配置
├── package.json                    # Node 工具链与 pnpm 脚本
├── pnpm-workspace.yaml             # pnpm 工作区定义
├── pyproject.toml / uv.lock        # Python 项目配置与依赖锁
├── requirements.txt                # Python 依赖（发布与 Android 打包也读它）
├── .prettierrc.mjs                 # Prettier 配置
├── .editorconfig / .gitattributes / .gitignore / .gitmodules
├── .node-version / .python-version # 工具链版本
├── README.md / README.en.md        # 中英文说明
├── CONTRIBUTING.md / LICENSE / CONTACT / logo.ico
│
├── resource/base/                  # 官服资源（interface.json 的 resource.base）
│   ├── default_pipeline.json       # 全局默认参数
│   ├── pipeline/                   # Pipeline 节点定义
│   │   ├── common.json             # 跨任务通用节点（Common.EnsureHome 回主页枢纽等）
│   │   ├── startup.json            # 启动游戏
│   │   ├── claim_rewards.json      # 领取奖励
│   │   ├── farm_resources.json     # 资源刷取
│   │   ├── pvp.json                # 玩家对战
│   │   ├── stamina.json            # 体力信息
│   │   └── event_stage.json        # 活动关卡与活动商店
│   ├── image/                      # 模板图片
│   │   ├── claim_rewards/          # 奖励相关图片
│   │   ├── farm_resources/         # 刷取相关图片
│   │   ├── pvp/                    # PVP 相关图片
│   │   ├── event_stage/            # 活动相关图片
│   │   └── ...                     # 通用图片
│   ├── model/ocr/                  # PP-OCRv6 模型（由 MaaCommonAssets 复制，不入库）
│   ├── config/maa_option.json      # 运行期 MaaFW 选项
│   └── debug/                      # 运行期日志与 on_error 截图
│
├── resource/bilibili/              # B 服增量资源（叠在 resource/base 之上，只放差异文件）
├── resource/taptap/                # TapTap 服增量资源（同上）
├── resource/announcement/          # GUI 欢迎公告（interface.json 的 welcome 指向此处）
│
├── tasks/                          # 任务入口定义
│   ├── startup.json                # 启动游戏
│   ├── claim_rewards.json          # 奖励领取
│   ├── farm_resources.json         # 资源刷取
│   ├── farm_remaining_stamina.json # 剩余体力刷取
│   ├── pvp.json                    # 玩家对战
│   ├── stamina_info.json           # 体力信息
│   ├── event_stage.json            # 活动关卡与商店
│   └── preset/                     # 任务预设（Daily / Activity）
│
├── agent/                          # Python Agent
│   ├── main.py                     # 入口：版本校验 + 解析原生库 → run_agent()
│   ├── maafw_paths.py              # 定位客户端原生库，设置 MAAFW_BINARY_PATH
│   ├── agent_runtime.py            # 核心：记录版本 → 注册 → AgentServer
│   ├── custom/
│   │   ├── recognition/            # 自定义识别
│   │   ├── action/                 # 自定义动作
│   │   └── sink/                   # 自定义事件监听（如分辨率检查）
│   └── utils/                      # 工具模块（logger / params / maa_types / pienv / runtime_paths）
│
├── tests/                          # pytest 测试（自定义模块与工具函数）
│
├── tools/                          # 开发与打包脚本
│   ├── build-release.mjs           # 桌面发布包构建（产物落 dist/）
│   ├── android-packaging.mjs       # Android 打包参数解析（供 android-build.yml 使用）
│   ├── check-project.mjs           # 项目一致性检查（pnpm lint）
│   ├── validate-schema.mjs         # Schema 校验（pnpm check:schema）
│   ├── sync-runtime.mjs            # 运行时同步（pnpm sync:runtime）
│   ├── sync-schema.mjs             # 上游 schema 同步（pnpm sync:schema）
│   ├── optimize-images.mjs         # 模板图优化（pnpm optimize:images）
│   ├── schema/                     # JSON Schema（pipeline / interface / custom.*）
│   └── ...                         # 文档生成、APK 处理等辅助脚本
│
├── Android/                        # Android 出包（MaaFwApp 子模块 + profile.yaml 打包配方）
├── MaaCommonAssets/                # 公共资源子模块（OCR 模型来源）
│
└── docs/                           # 文档站（VuePress）
    ├── .vuepress/                  # 站点配置（config.ts / plume.config.ts / navigation/）
    ├── zh/                         # 中文文档（develop / manual / protocol）
    └── en/                         # 英文文档（与 zh 一一对应）
```

## 三层架构

```text
tasks/*.json ──→ pipeline/*.json ──→ agent/custom/
(task 入口)      (节点图)            (Python 自定义逻辑)
```

- **Layer 1 — Tasks**：`tasks/*.json`，定义 GUI 中显示的任务和选项
- **Layer 2 — Pipeline**：`resource/base/pipeline/*.json`，JSON 节点有向图，90% 的逻辑在此
- **Layer 3 — Agent**：`agent/custom/`，Python 代码处理复杂逻辑

## 目录职责

| 目录 / 文件               | 职责                                                                                                                |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `interface.json`          | 对外入口：任务列表、控制器（ADB）、资源包（`base` 官服 / `bilibili` B 服 / `taptap` TapTap 服）、`agent` 子进程声明 |
| `tasks/`                  | 每个任务一个 JSON：`task` 列表 + 选项 + `pipeline_override`；`preset/` 放任务预设                                   |
| `resource/base/pipeline/` | 节点图本体。一个功能模块一个文件，跨任务通用节点放 `common.json`                                                    |
| `resource/base/image/`    | 模板图，按模块分子目录；命名与制作规范见 [Pipeline 编写指南](./pipeline.md#模板图片与资源命名)                      |
| `resource/<server>/`      | 区服增量资源，加载时叠在 `resource/base` 之上（`interface.json` 的 `resource` 字段决定顺序），只放与官服不同的文件  |
| `agent/`                  | Python 侧全部代码：`main.py` 入口、`agent_runtime.py` 装配、`custom/` 自定义模块、`utils/` 工具模块                 |
| `tests/`                  | pytest 用例，覆盖自定义模块与工具函数；跑 `pnpm test:py`                                                            |
| `tools/`                  | 开发脚本：schema 校验、项目检查、运行时/schema 同步、发布打包、文档生成                                             |
| `docs/`                   | VuePress 文档站；`zh/` 与 `en/` 结构一一对应，`.vuepress/` 放站点配置与导航                                         |

## 本地目录（不入库）

以下目录由 `.gitignore` 排除，属于本地环境或运行期产物，**不要提交、也不要当成项目源码**：

| 目录                              | 来源                                                              |
| --------------------------------- | ----------------------------------------------------------------- |
| `runtimes/`、`libs/`、`plugins/`  | MaaFW 原生运行时与二进制依赖，由 `pnpm sync:runtime` 或客户端补齐 |
| `dist/`                           | `tools/build-release.mjs` 的打包产物                              |
| `config/`、`debug/`               | 运行期生成：客户端配置、日志（`debug/custom/`）、`on_error` 截图  |
| `resource/base/model/ocr/`        | 从 `MaaCommonAssets` 子模块复制，不入库                           |
| `Android/agent-dist/`、`logo.png` | Android 出包产物                                                  |
| `node_modules/`、`.venv/`         | 依赖安装目录                                                      |

## 发布与打包

| 命令                           | 作用                                                            |
| ------------------------------ | --------------------------------------------------------------- |
| `pnpm check`                   | 格式检查 → Schema 校验 → MaaFW 完整性 → 项目 lint（提交前必跑） |
| `pnpm check:py`                | Ruff lint + pyright 类型检查（改 Python 时必跑）                |
| `pnpm test:py`                 | 跑 pytest                                                       |
| `pnpm format`                  | Prettier 全量格式化（`pnpm format:py` 对应 Python）             |
| `pnpm release:dry-run`         | 试跑发布包构建，不落盘                                          |
| `pnpm sync:runtime`            | 同步 MaaFW 原生运行时                                           |
| `pnpm sync:schema`             | 从上游同步 `tools/schema/`                                      |
| `pnpm docs:dev` / `docs:build` | 本地起文档站 / 构建文档站                                       |

- **桌面发布**：`tools/build-release.mjs`（`dist/` 为产物目录），由 `.github/workflows/release.yml` 触发；Mirror 酱更新走 `mirrorchyan_release.yml`
- **Android 出包**：`Android/profile.yaml` 是打包配方（资源指向仓库根目录），`Android/MaaFwApp` 是外壳子模块；`tools/android-packaging.mjs` 负责解析版本与命名参数，`.github/workflows/android-build.yml` 使用它，细节见[Android 打包](./android.md)
- **CI**：`.github/workflows/` 下的 `check.yml`（`pnpm check`）、`format.yml`、`check-docs.yml` / `deploy-docs.yml`（文档站）、`optimize-images.yml`、`schema-sync.yml`、`package-smoke.yml`
