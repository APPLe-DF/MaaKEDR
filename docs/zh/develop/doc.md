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

## 参考

- [VuePress Theme Plume](https://theme-plume.vuejs.press/)
- [MaaFramework 文档](https://maafw.com/docs/1.1-QuickStarted)
