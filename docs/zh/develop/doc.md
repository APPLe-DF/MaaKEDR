---
order: 8
icon: jam:write-f
---

# 文档编写

本文说明如何为 MaaKEDR 文档站（VuePress Theme Plume）编写与修改文档。

## 目录约定

```text
docs/
├── README.md           # 语言选择首页
├── zh/                 # 简体中文
│   ├── README.md
│   ├── manual/         # 用户手册
│   ├── develop/        # 开发文档
│   └── protocol/       # 任务/资源协议
└── en/                 # English（结构与 zh 对齐）
```

- 路径与站内链接使用正斜杠
- 侧边栏在 `docs/.vuepress/config/navigation.ts` 的 `collections.sidebar` 中维护
- 新增页面后请同步修改 **中英文** sidebar（若有英文对照）

## 首页

两份首页（`docs/zh/README.md`、`docs/en/README.md`）用的是 Plume 的 `home` frontmatter，`config` 里的区块顺序就是页面顺序。

- 三个自定义区块在 `docs/.vuepress/components/`：`HomeDownload`（快捷下载）、`HomeStats`（项目规模）、`HomePointerField`（背景的识别框装饰层）。必须先在同目录的 `client.ts` 里注册，`config` 中的 `type:` 才认得它们
- 首页专属样式只有 `docs/.vuepress/styles/home-hero.css` 一个文件，选择器一律以 `.vp-home` 开头，以免漏到文档页上
- `docs/.vuepress/data/*.json` 是构建期生成的：`pnpm docs:build` / `docs:dev` 会先跑 `tools/gen-docs-downloads.mjs` 和 `tools/gen-docs-stats.mjs` 写出 release 资产和仓库规模统计。**不要手改**，改了也会被下次构建覆盖
- `HomePointerField` 里的节点名标签是从 `resource/base/pipeline/*.json` 抄来的一份静态快照，重命名或删除 pipeline 节点不会自动反映到首页

## Frontmatter

常用字段：

```yaml
---
order: 1
icon: ri:tools-fill
title: 可选标题
---
```

目录索引页可用：

```yaml
---
title: 开发文档
icon: ph:code-bold
dir:
    order: 1
---
```

## 提示容器

Plume 支持容器语法：

::: note
注释
:::

::: tip
提示
:::

::: warning
警告
:::

::: caution
危险
:::

::: details
折叠详情
:::

也可用 GitHub 风格（渲染取决于主题配置）：

```markdown
> [!NOTE]
> 说明文字
```

## MarkdownLint 规范

文档需符合 **MarkdownLint** 规范，配置见 `docs/.markdownlint.yaml`（规则覆盖、关闭项及原因均在其中注明）。

- 规则说明请参考 [MarkdownLint 规则](https://github.com/DavidAnson/markdownlint/blob/master/docs/RULES.md)
- 可使用 [VSCode 插件](https://github.com/DavidAnson/vscode-markdownlint) 实时提示（自动读取 `.markdownlint.yaml`）
- 仓库目前**没有**把 MarkdownLint 接进 `pnpm check` 或 CI，也没有装相关依赖 —— 它靠编辑器插件在本地生效，所以不要期待有一条失败的 CI 来提醒你
- 与 Prettier 的分工：**Prettier 负责格式**（缩进、换行、表格对齐），**MarkdownLint 负责规范**（标题层级、列表正确性、链接有效性等）。两者不冲突：`.markdownlint.yaml` 中已关闭与 Prettier 无关的噪音规则（如 MD013 行长）

## 写作要求

- 用户手册：步骤可操作，选项与 `tasks/*.json` 一致
- 开发文档：路径、命令与仓库现状一致；避免写已废弃的 CLI/工具
- 协议文档：描述约定与节点关系，细节以 JSON 为准并给文件路径
- 发版相关：`interface.json` 的 `version` / `title` 需手动改（见 AGENTS.md Release Guidelines）

## 本地预览

```bash
pnpm docs:dev
pnpm docs:build
```

构建产物在 `docs/.vuepress/dist`（已 gitignore）。

- `pnpm docs:preview` 目前和站点的 `base: /MaaKEDR/` 对不上，直接开根路径会 404；要看效果请用 `pnpm docs:dev`
- 绕开 pnpm 直接跑 `vuepress dev docs` 会跳过数据生成，`docs/.vuepress/data/` 不存在时首页两个区块会直接构建失败
- `pnpm docs:build` 带 `--clean-cache --clean-temp`，会顺手清掉正在跑的 dev server，两者不要同时开

## 参考

- [VuePress Theme Plume](https://theme-plume.vuejs.press/)
- [MaaFramework 文档](https://maafw.com/docs/1.1-QuickStarted)
