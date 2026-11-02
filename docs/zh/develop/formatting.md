---
title: "格式化规范"
order: 4
icon: "ri:paint-brush-fill"
---

# 格式化与规范

仓库用 Prettier 与 ruff 统一代码和资源文件的风格。CI 会检查格式，本地也可以手动格式化。

## 编码与换行

- 编码：UTF-8（无 BOM；`.ps1` 例外，见 AGENTS.md）
- 换行：LF（`.editorconfig` 与 `.gitattributes` 强制）
- 缩进：JSON 4 空格；YAML / TypeScript 2 空格；Markdown 4 空格（Prettier `tabWidth: 4`）

## 格式化工具

| 文件类型                            | 工具                                                                      |
| ----------------------------------- | ------------------------------------------------------------------------- |
| JSON / YAML / Markdown / TypeScript | [Prettier](https://prettier.io/)（配置见 `.prettierrc.mjs`）              |
| Python                              | [ruff](https://docs.astral.sh/ruff/formatter/)（配置见 `pyproject.toml`） |

`.prettierignore` 排除了生成物与第三方目录（`node_modules/`、`dist/`、`.venv/`、`MaaCommonAssets/`、`tools/schema/*.json` 等），格式化不会碰它们。

## 安装依赖

```bash
pnpm install        # 安装 Prettier 等 Node 依赖
uv sync --frozen    # 安装 ruff、pyright 等 Python 开发依赖
```

## 手动格式化

```bash
pnpm format         # Prettier 格式化全仓库（prettier --write .）
pnpm format:check   # 只检查格式、不写入
pnpm format:py      # ruff 格式化 Python 代码
```

也可以直接调用 ruff：

```bash
uv run --frozen ruff check --fix .   # 检查并自动修复 Python 问题
uv run --frozen ruff format .        # 格式化 Python 代码
```

## Pipeline 命名

- 节点名称：点分隔层级（`FarmResources.Start`、`ClaimRewards.CheckDaily`）
- 模板图片：描述性 snake_case（`quick_battle.png`、`start_battle.png`）
- ROI 坐标：`[x, y, w, h]`，1280x720 分辨率

## JSON 注释

Pipeline 文件和 task 文件支持 `//` 注释（JSON-with-Comments）。

## 提交规范

- 前缀：`feat:`、`fix:`、`docs:`、`chore:` 等 Conventional Commits 格式
- 信息：一句简短但逻辑清晰的话
- 粒度：每笔提交只关注一个改动

## 开发命令

| 命令                       | 说明                                                       |
| -------------------------- | ---------------------------------------------------------- |
| `pnpm install`             | 安装工具链                                                 |
| `pnpm format`              | Prettier 格式化全仓库                                      |
| `pnpm format:check`        | Prettier 只检查、不写入                                    |
| `pnpm format:py`           | ruff 格式化 Python                                         |
| `pnpm lint`                | 项目结构与一致性检查（`node tools/check-project.mjs`）     |
| `pnpm lint:py`             | ruff lint 检查 Python                                      |
| `pnpm typecheck:py`        | pyright 严格类型检查                                       |
| `pnpm check`               | 完整检查（format:check → check:schema → check:maa → lint） |
| `pnpm check:ci`            | CI 使用的检查子集（format:check + lint）                   |
| `pnpm check:schema`        | JSON Schema 校验                                           |
| `pnpm check:maa`           | 仅检查 pipeline（`maa-tools check`）                       |
| `pnpm check:py`            | Python 检查（`lint:py` + `typecheck:py`）                  |
| `pnpm test:py`             | 运行 Python 测试（pytest）                                 |
| `pnpm sync:runtime`        | 同步 MaaFW 运行时与 OCR 模型                               |
| `pnpm optimize:images`     | 用 oxipng 压缩 PNG 图片                                    |
| `pnpm run release:dry-run` | 仅校验版本与产物名（不打包、不冒烟）                       |
