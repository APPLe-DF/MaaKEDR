---
title: Protocol
icon: basil:document-solid
index: true
dir:
    order: 2
---

# Protocol Docs

Task, resource, and UI-flow conventions for MaaKEDR (_Cedar_). For the shared project interface, see [Project Interface V2](https://maafw.com/docs/3.3-ProjectInterfaceV2).

## Contents

- [Project & resources](./overview.md)
- [Startup & login](./startup.md)
- [Claim rewards](./claim-rewards.md)
- [Farm resources](./farm-resources.md)
- [PVP](./pvp.md)
- [Event stages and shop](./event-stage.md)
- [Stamina info](./stamina-info.md)

## Code map

| Area             | Path                                     |
| ---------------- | ---------------------------------------- |
| Task options     | `tasks/*.json`                           |
| Pipelines        | `resource/base/pipeline/*.json`          |
| Server overrides | `resource/bilibili/`, `resource/taptap/` |
| Custom modules   | `agent/custom/`                          |
