---
title: "格式化规范"
order: 4
icon: "ri:paint-brush-fill"
---

# 格式化与规范

## 编码与换行

- 编码：UTF-8
- 换行：LF（`.editorconfig` 和 `.gitattributes` 强制）
- JSON/YAML 缩进：4 空格
- TypeScript/Markdown 缩进：2 空格

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

| 命令                       | 说明                                        |
| -------------------------- | ------------------------------------------- |
| `pnpm install`             | 安装工具链                                  |
| `pnpm check`               | 完整检查（格式 + schema + maa + 项目 lint） |
| `pnpm check:maa`           | 仅检查 pipeline                             |
| `pnpm check:py`            | Python 类型和 lint 检查                     |
| `pnpm format`              | 格式化所有文件                              |
| `pnpm run release:dry-run` | 模拟打包                                    |
| `pnpm run sync:runtime`    | 同步运行时                                  |
