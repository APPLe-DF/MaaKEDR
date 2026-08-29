---
order: 1
icon: ri:tools-fill
---

# 环境搭建与开发入门

## 概述

本文档面向希望参与 MaaKEDR 开发的贡献者，帮助快速搭建开发环境并完成第一个 Pipeline。

## 环境准备

### 系统要求

| 项目     | 要求                        |
| -------- | --------------------------- |
| 操作系统 | Windows 10+ / macOS / Linux |
| Python   | 3.13                        |
| Node.js  | >= 24                       |
| 包管理器 | pnpm（corepack 管理） + uv  |
| 版本控制 | Git                         |

### 安装步骤

#### 1. Python 3.13

```bash
python --version   # 须为 3.13.x
```

> 如果版本不符，请从 [python.org](https://www.python.org/downloads/) 下载 Python 3.13。

#### 2. 安装 uv

[uv](https://docs.astral.sh/uv/) 是 Python 包管理器，用于管理项目依赖和虚拟环境。

```bash
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

确认安装成功：

```bash
uv --version
```

#### 3. 安装 Node.js 和 pnpm

从 [nodejs.org](https://nodejs.org/) 下载 Node.js >= 24，安装后通过 corepack 启用 pnpm：

```bash
corepack enable
corepack prepare pnpm@latest --activate
pnpm --version
```

### 获取项目

日常开发可直接克隆主仓库：

```bash
git clone --recurse-submodules https://github.com/APPLe-DF/MaaKEDR.git
cd MaaKEDR
```

项目通过 `MaaCommonAssets` 子模块提供 OCR 模型（`resource/base/model/ocr/`）。该目录已被 `.gitignore` 忽略，模型在构建时从子模块复制，因此**必须初始化子模块**，否则运行任务时会因缺少模型而识别失败。

若克隆时忘了加参数，可事后补：

```bash
git submodule update --init --recursive
```

若要提交 PR，请先 Fork 再克隆你的仓库，并使用独立功能分支（见下文「贡献与 PR」）。

### 安装依赖

```bash
pnpm install
uv sync --frozen
```

> `uv sync --frozen` 会根据 `uv.lock` 锁定文件安装指定版本的依赖，确保环境一致性。

### 同步运行时与 OCR 模型

```bash
pnpm sync:runtime
```

这一步会下载 MaaFW 运行时，并把 OCR 模型从 `MaaCommonAssets` 子模块复制到 `resource/base/model/ocr/`。

**首次搭建必须执行**：子模块初始化只是把模型源文件取到本地，实际的模型文件要等这一步才会复制过去。跳过它不会报错，但运行时所有 OCR 识别都会失败。

如果只是模型目录缺失、不想重新拉取整套运行时，可只复制模型：

```bash
pnpm dlx create-maa-project@latest --update ocr-models
```

### 验证环境

```bash
pnpm check
pnpm check:py
```

> 首次运行需要下载 MaaFramework 运行时和 PaddleOCR 模型，请确保网络畅通。

## 调试与开发工具

| 工具                                                                                           | 简介                                                                      |
| ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| [MaaDebugger](https://github.com/MaaXYZ/MaaDebugger)                                           | 独立调试工具：连接控制器、实时查看识别结果与截图                          |
| [Maa Pipeline Support](https://marketplace.visualstudio.com/items?itemName=nekosu.maa-support) | VSCode 插件：提供调试、截图、获取 ROI、取色等功能                         |
| [MFAToolsPlus](https://github.com/SweetSmellFox/MFAToolsPlus)                                  | 跨平台开发工具箱：提供便捷的数据获取和模拟测试方法                        |
| [MaaLogAnalyzer](https://github.com/Windsland52/MAALogAnalyzer)                                | 可视化分析 MaaFramework 应用的日志（`maafw.log`）                         |
| [MaaEvidenceKit](https://github.com/Windsland52/MaaEvidenceKit)                                | 面向 MaaFramework 的证据提取与诊断工具包（CLI/SDK），供 AI 助手等按需诊断 |
| [ImageCropper（不推荐）](https://github.com/MaaXYZ/MaaFramework/tree/main/tools/ImageCropper)  | 独立截图及获取 ROI 工具，功能已被 VSCode 插件取代                         |

::: tip 推荐组合
开发调试使用 **Maa Pipeline Support**（VSCode 插件），用户日志分析使用 **MaaLogAnalyzer**（见 [Bug 排查](./fix.md#日志分析工具)）。
:::

## 项目结构速览

```text
MaaKEDR/
├── interface.json        # 入口配置，定义任务列表和连接方式
├── maa-project.json      # MaaFramework 项目配置
├── tasks/                # 任务定义（GUI 可见的任务列表）
├── resource/
│   ├── base/pipeline/    # Pipeline JSON 节点定义
│   ├── base/image/       # 模板匹配图片
│   └── base/model/ocr/   # PaddleOCR 模型
├── agent/custom/         # Python 自定义识别和动作
├── docs/                 # 文档站
└── tools/                # 构建和发布脚本
```

关键概念：

- **Pipeline**：JSON 格式的节点图，每个节点定义一个识别 → 动作 → 跳转的步骤
- **Task**：`tasks/*.json` 定义的任务入口，用户通过 GUI 选择要执行的任务
- **Template Image**：游戏截图中抠出的小图，用于模板匹配定位 UI 元素
- **Custom Module**：Python 编写的自定义识别或动作，应对复杂逻辑

## 第一个 Pipeline

以一个简单场景为例：识别游戏主界面的"开始游戏"按钮并点击。

### 1. 获取截图

使用模拟器或真机的截图功能获取游戏画面，保存为 `start_screen.png`。

### 2. 测量 ROI

用画图工具打开 `start_screen.png`，测量"开始游戏"按钮的位置和尺寸：

```text
示例：按钮在 1280x720 分辨率下
x = 540, y = 600, w = 200, h = 60
```

### 3. 制作模板图片

从截图中抠出按钮的小图，保存到 `resource/base/image/`：

```text
resource/base/image/start_button.png
```

> 模板图片尺寸建议在 50x50 到 200x200 像素之间。

### 4. 编写 Pipeline 节点

在 `resource/base/pipeline/` 下创建一个 JSON 文件：

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

### 5. 定义任务

在 `tasks/` 下创建 JSON 文件，让任务可被 GUI 选择：

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

### 6. 运行验证

本项目**不提供**独立 MaaPiCli 发行包。请使用发布包中的 **MFAAvalonia / MXU** 图形界面勾选任务运行，或按 [AGENTS.md](https://github.com/APPLe-DF/MaaKEDR/blob/main/AGENTS.md) 在开发环境中启动 Agent 后调试。

> 运行前请确保模拟器已启动且游戏在正确界面。

## 开发工作流

```text
截图 → 测量 ROI → 制作模板 → 编写 Pipeline → 任务绑定 → 运行验证 → 迭代优化
```

每次迭代：

1. 运行 `pnpm check` 确保格式和 Schema 通过
2. 运行 Python 自定义模块时执行 `pnpm check:py`
3. 查看 `debug/` 目录下的日志和截图定位问题

## 贡献与 PR

1. Fork 仓库并克隆自己的 fork
2. 从最新 `main` 拉出分支，例如 `feat/xxx`、`fix/xxx`、`docs/xxx`
3. 本地通过 `pnpm check`（及 Python 相关时的 `pnpm check:py`）
4. 推送并打开 Pull Request；一个 PR 只解决一个问题
5. 描述写清改动动机、影响范围与自测方式；识别/流程类问题请附截图或日志

完整约定见仓库 [CONTRIBUTING.md](https://github.com/APPLe-DF/MaaKEDR/blob/main/CONTRIBUTING.md) 与 [AGENTS.md](https://github.com/APPLe-DF/MaaKEDR/blob/main/AGENTS.md)。

**发版**：打 `vX.Y.Z` 标签前，须手动更新 `interface.json` 的 `version` 与 `title`（不会随 tag 自动同步）。

## 参考

- [MaaFramework 文档](https://maafw.com/docs/1.1-QuickStarted)
- [Pipeline 编写指南](./pipeline.md)
- [Custom 编写指南](./custom.md)
- [Bug 排查指南](./fix.md)
- [格式化规范](./formatting.md)
- [文档编写](./doc.md)
- [协议文档](../protocol/)
- [AGENTS.md](https://github.com/APPLe-DF/MaaKEDR/blob/main/AGENTS.md)
