---
title: Development Docs
description: MaaKEDR development docs overview — environment setup, Pipeline and Custom authoring, shared nodes, project structure, bug triage, formatting and docs conventions.
icon: ph:code-bold
dir:
    order: 1
---

# Development Docs

This section is for developers who want to contribute code or adapt new content to MaaKEDR. Start with **Getting Started** to get a working environment, then move on to **Authoring Guides** or **Engineering Practices** as needed.

If you only want to tweak a little JSON or documentation and are not familiar with Git, start at [Setup & Development Quickstart](./setup.md#contributing-pull-requests) → "Contributing & Pull Requests".

## Getting Started

- [Setup & Development Quickstart](./setup.md) — System requirements, dependency installation, runtime and OCR model sync, your first pipeline, contributing and pull requests.
- [Project Structure](./structure.md) — Responsibilities of each directory, the three-layer architecture, and where release packages and build scripts live.

## Authoring Guides

- [Pipeline Guide](./pipeline.md) — MaaFramework core concepts: describing "recognition → action → next" flows in JSON, plus design patterns and fallback strategies.
- [Shared Nodes & the Home Hub](./common.md) — Inventory of cross-task nodes in `pipeline/common.json` and how the `Common.EnsureHome` hub converges.
- [Custom Guide](./custom.md) — Registering custom recognitions, actions and sinks through `AgentServer` for logic JSON pipelines cannot express.

## Engineering Practices

- [Vibe Coding](./vibe-coding.md) — The AI-assisted development model this project largely relies on.
- [Bug Triage](./fix.md) — Locating logs, triaging the problem class, and verifying a fix.
- [Formatting & Conventions](./formatting.md) — Encoding rules, naming conventions, commit style and a command cheat sheet.
- [Writing Documentation](./doc.md) — Docs site layout, front matter, MarkdownLint rules and writing requirements.
- [Overseas Client Adaptation](./overseas-client-adaptation.md) — Adaptation boundaries, principles and current status for the international client.
- [Android Packaging (MaaFwApp)](./android.md) — Building an Android APK through the MaaFwApp submodule and build recipe.

Task and resource conventions live in [Protocol](../protocol/).
