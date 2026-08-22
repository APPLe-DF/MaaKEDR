---
order: 8
icon: jam:write-f
---

# Writing Docs

How to edit the MaaKEDR docs site (VuePress Theme Plume).

## Layout

```text
docs/zh|en/{manual,develop,protocol}/
docs/.vuepress/config/navigation.ts   # navbar + sidebar
```

Add new pages to **both** locale sidebars when applicable.

## Frontmatter

```yaml
---
order: 1
icon: ri:tools-fill
---
```

## Containers

::: tip
Tip box
:::

::: warning
Warning
:::

## MarkdownLint

Docs must pass **MarkdownLint**. The config lives at `docs/.markdownlint.yaml` (rule overrides and the reasons for disabling rules are annotated there).

- Rule reference: [MarkdownLint Rules](https://github.com/DavidAnson/markdownlint/blob/master/docs/RULES.md)
- The [VSCode extension](https://github.com/DavidAnson/vscode-markdownlint) picks up `.markdownlint.yaml` automatically for live hints
- Division of labor with Prettier: **Prettier handles formatting** (indentation, line breaks, table alignment); **MarkdownLint handles conventions** (heading levels, list correctness, link validity). They do not conflict: noisy rules unrelated to Prettier (e.g. MD013 line length) are disabled in `.markdownlint.yaml`

## Preview

```bash
pnpm docs:dev
pnpm docs:build
```

Keep user manuals aligned with `tasks/*.json`. Keep protocol pages aligned with pipelines. Release notes: update `interface.json` `version` / `title` manually (see `AGENTS.md`).
