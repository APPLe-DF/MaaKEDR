---
title: "Formatting"
order: 4
icon: "ri:paint-brush-fill"
---

# Formatting & Conventions

The repository uses Prettier and ruff to keep code and resource files consistent. CI checks formatting, and you can also format manually.

## Encoding & Line Endings

- Encoding: UTF-8 without BOM (`.ps1` is the exception — see `AGENTS.md`)
- Line endings: LF (enforced by `.editorconfig` and `.gitattributes`)
- Indent: 4 spaces for JSON; 2 spaces for YAML / TypeScript; 4 spaces for Markdown (Prettier `tabWidth: 4`)

## Formatters

| File Types                          | Tool                                                                        |
| ----------------------------------- | --------------------------------------------------------------------------- |
| JSON / YAML / Markdown / TypeScript | [Prettier](https://prettier.io/) (config in `.prettierrc.mjs`)              |
| Python                              | [ruff](https://docs.astral.sh/ruff/formatter/) (config in `pyproject.toml`) |

`.prettierignore` excludes generated output and third-party directories (`node_modules/`, `dist/`, `.venv/`, `MaaCommonAssets/`, `tools/schema/*.json`, etc.), so formatting never touches them.

## Installing Dependencies

```bash
pnpm install        # Node dependencies such as Prettier
uv sync --frozen    # Python dev dependencies such as ruff and pyright
```

## Formatting Manually

```bash
pnpm format         # Prettier across the whole repo (prettier --write .)
pnpm format:check   # check only, do not write
pnpm format:py      # format Python with ruff
```

You can also call ruff directly:

```bash
uv run --frozen ruff check --fix .   # lint and auto-fix Python issues
uv run --frozen ruff format .        # format Python code
```

## Naming

- Pipeline nodes: Dot-separated hierarchy (`FarmResources.Start`, `ClaimRewards.CheckDaily`)
- Template images: Descriptive snake_case (`quick_battle.png`, `start_battle.png`)
- ROI: `[x, y, w, h]` in pixels at 1280x720 resolution

## JSON Comments

Pipeline and task files support `//` comments (JSON-with-Comments).

## Commit Style

- Prefix: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`)
- Message: Short, clear, one change per commit
- Language: Chinese for project-specific messages

## Commands

| Command                    | Description                                                              |
| -------------------------- | ------------------------------------------------------------------------ |
| `pnpm install`             | Install toolchain                                                        |
| `pnpm format`              | Format the whole repo with Prettier                                      |
| `pnpm format:check`        | Check formatting only, no write                                          |
| `pnpm format:py`           | Format Python with ruff                                                  |
| `pnpm lint`                | Project structure and consistency check (`node tools/check-project.mjs`) |
| `pnpm lint:py`             | Lint Python with ruff                                                    |
| `pnpm typecheck:py`        | Strict type check with pyright                                           |
| `pnpm check`               | Full validation (format:check → check:schema → check:maa → lint)         |
| `pnpm check:ci`            | The CI subset (format:check + lint)                                      |
| `pnpm check:schema`        | Validate JSON schemas                                                    |
| `pnpm check:maa`           | Validate pipelines only (`maa-tools check`)                              |
| `pnpm check:py`            | Python checks (`lint:py` + `typecheck:py`)                               |
| `pnpm test:py`             | Run Python tests (pytest)                                                |
| `pnpm sync:runtime`        | Sync the MaaFW runtime and OCR models                                    |
| `pnpm optimize:images`     | Compress PNG images with oxipng                                          |
| `pnpm run release:dry-run` | Validate version and names only (no packaging, no smoke test)            |
