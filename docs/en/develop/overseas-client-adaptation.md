---
title: "Overseas Client Adaptation"
order: 9
icon: "ri:earth-fill"
---

# Overseas Client Adaptation

::: note
Placeholder doc: MaaKEDR currently supports CN channels only (official / bilibili / TapTap); there is no overseas client yet. If an overseas version appears in the future, adapt within the boundaries below and solve the rest as it comes.
:::

## Adaptation Boundary

Differences with the CN client are usually concentrated in **startup & login**:

- `resource/<pack>/pipeline/startup.json`, `shutdown.json` — launch/shutdown flow (login entry, channel differences)
- `resource` list in `interface.json` — add an overseas resource pack (reuse `base` as the foundation, overlay changes on top)
- Login copy / entry images — template images and OCR `expected` text

## Principles

1. **Only adapt startup & login first**: other tasks (claim rewards, farm, PVP) should reuse `base`; do not copy whole pipelines into the overseas pack
2. Prefer overriding `expected` / template images for language differences over restructuring the flow
3. When adding a resource pack, update the pack table in `docs/*/protocol/overview.md`
4. See the MaaFramework [ProjectInterface V2](https://maafw.com/docs/3.3-ProjectInterfaceV2) protocol for the `interface.json` resource-switching mechanism

## Current Status

| Channel  | Status | Note                 |
| -------- | ------ | -------------------- |
| Official | ✅     | `resource/base`      |
| bilibili | ✅     | `resource/bilibili`  |
| TapTap   | ✅     | `resource/taptap`    |
| Overseas | ⏳     | Not adapted, no pack |
