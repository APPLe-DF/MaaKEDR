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

- Four custom blocks live in `docs/.vuepress/components/`: `HomeDownload`, `HomeStats`, `HomePointerField` (the drifting detection-box layer behind the content) and `HomeFX` (scroll progress bar + card pointer spotlight + scroll-in reveal). They must be registered in `client.ts` before `config` can reference them by `type:`
- `HomeFX` is a pure enhancement layer: after mount it only sets markers on the DOM (`data-hp-reveal`, `data-hp-hero-away`, `is-revealed`) and appends a progress bar to `body`; every style keyed off those markers lives in `home-hero.css`. With JS disabled, reduced motion on, or a coarse pointer, the page merely loses the corresponding effect — content stays visible. Follow that contract when adding homepage motion: never make content visibility depend on JS
- All homepage-only CSS sits in the single file `docs/.vuepress/styles/home-hero.css`. Every **rule selector** in it starts with `.vp-home` so it cannot leak into doc pages; the only exception is the `--vp-home-*` custom properties, which have to be declared on the global `:root` / `html[data-theme="dark"]` to be inherited at all — the prefix is what keeps them from colliding with the theme's own variables
- After mount, `HomeDownload` detects the current device and shows only the matching build, collapsing the rest behind a small entry. **Architecture is only reported when there is hard evidence**: Chromium's high-entropy hints, an architecture literally spelled out in the UA (including the emulator's `sdk_gphone64_x86_64`), or the macOS WebGL renderer name. Without evidence it reports “unknown” instead of guessing — a wrong guess sends the visitor to a build that will not run. That leads to three endings: an unknown Mac chip gets two buttons (“Apple silicon” / “Intel”); an unknown Android ABI falls back to arm64-v8a (or universal) for widest coverage; and a mismatch between the local architecture and the suggested build shows a “may not run” warning. **Desktop never falls back across architectures** (there is no Linux aarch64 MXU build upstream, and a fallback would hand ARM users an x64 package). Detection only exists on the client — the SSR output always contains the full list, so there is no hydration mismatch
- **The homepage version and download links are generated, never hand-written**: on every build `tools/gen-docs-downloads.mjs` calls the GitHub Release API for the latest **stable** release (`/releases/latest` skips prereleases) and takes the tag, publish time and asset list, parsing `MaaKEDR-<os>-<arch>-<tag>-<ui>.<ext>` into OS / architecture / interface. Freshness on the site is guaranteed by two triggers in `.github/workflows/deploy-docs.yml`: a change under `docs/**`, and an automatic rebuild **after the Release workflow succeeds** (`workflow_run`). A manual `workflow_dispatch` is available to force a refresh
- The download section already reserves a slot for **Android APKs**: the script recognises `MaaKEDR-android-<universal|arm64-v8a|x86_64>-<tag>.apk` (matching the Rename Release APK step in `android-build.yml`), and an APK's `ui` field is always an empty string (the Android build ships a single shell, with no MFAA/MXU split). The current stable release has no APKs yet, so the "Android" group and the Android recommendation card do not appear; once `release.yml` uploads them, the group shows up automatically and Android browsers get the matching ABI suggested
- Automatic updates depend on the API being reachable: the script reads `GH_TOKEN` / `GITHUB_TOKEN` to authenticate (CI passes it), because the anonymous quota is only 60 requests/hour and once it is exhausted the script silently keeps the previous data and the site keeps showing the old version. When it does pick up a new version the build log prints `wrote N assets for vX.Y.Z`; check that line when it looks stale
- `docs/.vuepress/data/*.json` is generated at build time — `pnpm docs:build` / `docs:dev` run `tools/gen-docs-downloads.mjs` and `tools/gen-docs-stats.mjs` first. When the data cannot be fetched (a fresh clone with no network, for instance) the scripts write a placeholder (empty assets / zeroed figures) and both blocks degrade to a one-line notice instead of breaking the build; a previously generated file that no longer parses, or is missing a figure the homepage reads, is overwritten by that placeholder rather than kept. Never edit those files by hand
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
