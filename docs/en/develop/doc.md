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

## Homepage

Both homepages (`docs/zh/README.md`, `docs/en/README.md`) use Plume's `home` frontmatter; the order of the `config` entries is the order on the page.

- Three custom blocks live in `docs/.vuepress/components/`: `HomeDownload`, `HomeStats` and `HomePointerField` (the drifting detection-box layer behind the content). They must be registered in `client.ts` before `config` can reference them by `type:`
- All homepage-only CSS sits in the single file `docs/.vuepress/styles/home-hero.css`, and every selector there starts with `.vp-home` so it cannot leak into doc pages
- `docs/.vuepress/data/*.json` is generated at build time — `pnpm docs:build` / `docs:dev` run `tools/gen-docs-downloads.mjs` and `tools/gen-docs-stats.mjs` first. Never edit those files by hand
- The node-name labels in `HomePointerField` are a static snapshot taken from `resource/base/pipeline/*.json`; renaming or dropping a pipeline node does not update the homepage

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
- MarkdownLint is **not** wired into `pnpm check` or CI, and no related package is installed — it only runs in your editor, so do not expect a failing CI job to point at your Markdown
- Division of labor with Prettier: **Prettier handles formatting** (indentation, line breaks, table alignment); **MarkdownLint handles conventions** (heading levels, list correctness, link validity). They do not conflict: noisy rules unrelated to Prettier (e.g. MD013 line length) are disabled in `.markdownlint.yaml`

## Preview

```bash
pnpm docs:dev
pnpm docs:build
```

- `pnpm docs:preview` does not match the site's `base: /MaaKEDR/` right now, so the root URL 404s — use `pnpm docs:dev` to look at your work
- Running `vuepress dev docs` directly skips the data generators, and the homepage blocks fail to build when `docs/.vuepress/data/` is missing
- `pnpm docs:build` passes `--clean-cache --clean-temp`, which also kills a dev server that is currently running — do not run both at once

Keep user manuals aligned with `tasks/*.json`. Keep protocol pages aligned with pipelines. Release notes: update `interface.json` `version` / `title` manually (see `AGENTS.md`).
