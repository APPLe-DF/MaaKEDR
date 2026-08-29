---
title: "Formatting"
order: 4
icon: "ri:paint-brush-fill"
---

# Formatting & Conventions

## Encoding & Line Endings

- Encoding: UTF-8
- Line endings: LF (enforced by `.editorconfig`)
- JSON/YAML indent: 4 spaces
- TypeScript/Markdown indent: 2 spaces

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

| Command                    | Description                                    |
| -------------------------- | ---------------------------------------------- |
| `pnpm install`             | Install toolchain                              |
| `pnpm check`               | Full validation (format + schema + maa + lint) |
| `pnpm check:py`            | Python type + lint check                       |
| `pnpm format`              | Format all files                               |
| `pnpm run release:dry-run` | Simulate release packaging                     |
| `pnpm run sync:runtime`    | Sync MaaFW runtime                             |
