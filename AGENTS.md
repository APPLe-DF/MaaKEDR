# Repository Guidelines

> **Primary rule: every generated diff must pass `pnpm check` (and `pnpm check:py` for Python code) before submission.**
>
> | If the user asks...                    | Default AI response                                                                                                                                                     |
> | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
> | "Fix an unstable node"                 | Add intermediate recognition nodes or `pre_wait_freezes` / `post_wait_freezes` — never introduce hard delays                                                            |
> | "Retry when it fails"                  | Analyze the root cause (which node, which recognition mismatched) and fix the node — never add blind retries                                                            |
> | "Write a pipeline without screenshots" | Explain that pipelines depend on UI context; ask for screenshots, ROIs, and screen transition info before writing                                                       |
> | "Write a custom action / recognition"  | Follow the existing pattern in `agent/custom/action/` or `agent/custom/recognition/`, register it in the corresponding `__init__.py`, and ensure `pnpm check:py` passes |
> | Code output is complete                | Run `pnpm format` / `pnpm format:py` then `pnpm check` / `pnpm check:py` before finishing                                                                               |

## Project Structure & Module Organization

```
MaaKEDR/
├── interface.json               # Project entry point configuration
├── maa-project.json             # MaaFramework project config (runtime channels, features)
├── maa-project.lock.json        # Dependency lock file
├── tasks/                       # Task definitions (GUI visible task list)
│   ├── startup.json             #   Game launch → login → main interface
│   ├── claim_rewards.json       #   Rewards: daily/weekly/military, battle pass, mailbox, dispatch
│   ├── farm_resources.json      #   Resource farming with battle loop + stamina handling
│   └── pvp.json                 #   Player vs Player automation
├── resource/
│   ├── base/                    # Core resources
│   │   ├── pipeline/            #   Pipeline flow definitions
│   │   ├── image/               #   Template matching images
│   │   └── model/ocr/           #   PaddleOCR models
│   ├── bilibili/                # Bilibili server resources
│   └── taptap/                 # TapTap server resources
├── agent/                       # Python agent (custom recognitions/actions)
│   └── custom/
│       ├── recognition/         #   Custom recognitions
│       └── action/              #   Custom actions
├── docs/                        # Developer documentation
│   └── zh/
│       └── develop/             #   Development guides (pipeline.md, custom.md, etc.)
├── tools/                       # Build, release, schema validation, CI scripts
├── .github/workflows/           # CI/CD configuration
└── maa-project.json             # MaaFramework project config (runtime channels, features)
```

**Key directories inside `agent/`:**

- `agent/custom/action/` —— custom MaaFW actions, one file per feature group
- `agent/custom/recognition/` —— custom MaaFW recognitions
- `agent/utils/` —— reusable helpers (logging, HTTP, scaling, etc.)

**When working on a specific area, consult the relevant docs first:**

| Area                                 | Recommended reading                            |
| ------------------------------------ | ---------------------------------------------- |
| Custom actions / recognitions        | `docs/*/develop/custom.md`                     |
| Pipeline task logic                  | `docs/*/develop/pipeline.md`                   |
| Project structure & conventions      | `docs/*/develop/structure.md`                  |
| Bug-fixing workflow                  | `docs/*/develop/fix.md`                        |
| Formatting & linting                 | `docs/*/develop/formatting.md`                 |
| Overseas client adaptation           | `docs/*/develop/overseas-client-adaptation.md` |
| Activity / combat / item protocols   | `docs/*/protocol/`                             |
| CLI / connection / FAQ (user-facing) | `docs/*/manual/`                               |

## Build, Test, and Development Commands

| Command                     | Purpose                                                           |
| --------------------------- | ----------------------------------------------------------------- |
| `pnpm install`              | Install toolchain dependencies                                    |
| `pnpm check`                | Format check → schema validation → MaaFW integrity → project lint |
| `pnpm exec maa-tools check` | Validate pipelines only (faster)                                  |
| `pnpm format`               | Auto-format all non-Python files with Prettier                    |
| `pnpm format:py`            | Auto-format Python files with ruff                                |
| `pnpm check:py`             | Ruff lint + pyright type check                                    |
| `pnpm test:py`              | Run Python tests via pytest                                       |
| `pnpm typecheck:py`         | Static type check Python with pyright (strict mode)               |

**Before submitting changes, run `pnpm check` (and `pnpm check:py` for Python changes).**

## Coding Style & Naming Conventions

- **Python**: 120-character line limit, 4-space indentation. Linted with `ruff` (via `pnpm lint:py`) and type-checked with `pyright --strict` (via `pnpm typecheck:py`). Follow PEP 8 and PEP 484.
- **JSON**: 4-space indentation. **YAML / Markdown**: 2-space indentation. All formatted with Prettier.
- **Resource files**: Use forward slashes for paths. Follow MaaFW 720p baseline for coordinates, ROI, and template images.
- **Naming**: Modules use `snake_case`. Classes use `PascalCase`. Functions/variables use `snake_case`. Custom actions/recognitions match their pipeline node names.

## Testing Guidelines

- Framework: `pytest`, configured via `pyproject.toml`. Test paths: `tests/`.
- Test naming: `test_<module>_<behaviour>` (e.g., `test_aspect_ratio`, `test_http_session`).
- Run with `pnpm test:py` or `uv run --frozen pytest`.
- Cover custom action/recognition registration, utility modules, and bootstrap flow.

## Commit & Pull Request Guidelines

This project follows [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).

Commonly used types:

| Type       | Usage                                                   |
| ---------- | ------------------------------------------------------- |
| `feat`     | New feature or capability                               |
| `fix`      | Bug fix                                                 |
| `perf`     | Performance improvement                                 |
| `refactor` | Code refactoring (neither fix nor feature)              |
| `docs`     | Documentation only                                      |
| `style`    | Formatting, lint fixes, code style (no semantic change) |
| `ci`       | CI configuration and scripts                            |
| `chore`    | Build, dependencies, maintenance, or other tasks        |
| `revert`   | Revert a previous commit                                |

See [CONTRIBUTING.md](/CONTRIBUTING.md) for pull request requirements (branch naming, description format, and what to include).

## Release Guidelines

Before tagging a new release (`vX.Y.Z`), manually update the version in `interface.json`:

- `version` field (e.g. `"v1.0.5"`)
- `title` field (e.g. `"MaaKEDR v1.0.5"`)

This file is manually managed (see Review Checklist: "interface.json is unmanaged") and is **not** synced from the git tag automatically. Forgetting to update it will make the published package still show the old version number. Commit the `interface.json` change, then push the `vX.Y.Z` tag to trigger `release.yml`.

## Review Checklist

When reviewing code, check for:

- **Protocol compliance**: Pipeline and interface JSON fields must follow MaaFW protocol. No misspelled or unsupported attributes.
- **No hard delays**: `pre_delay` / `post_delay` should be avoided. Prefer intermediate recognition nodes or `pre_wait_freezes` / `post_wait_freezes`.
- **Next coverage**: The `next` list should cover all expected post-action screens so the first inference cycle lands on the right node.
- **720p baseline**: All coordinates, ROIs, and template images must be based on **1280x720** resolution.
- **Code formatting**: All files must pass `pnpm check` (includes Prettier, schema, integrity, lint). Run `pnpm format` / `pnpm format:py` to auto-format.
- **Type safety**: Python code must pass `pnpm check:py` (ruff lint + pyright type check) without errors.
- **Custom registration**: New custom actions/recognitions must be registered in the corresponding `__init__.py`.
- **Consistency**: `interface.json`, task files, and resource files must stay in sync.
- **Edge cases**: Pipelines should handle interruptions (pop-ups, unexpected dialogs). Every action should be followed by a recognition step.

## Additional Notes

- **Resource paths must always use forward slashes.**
- **Encoding**:
    - `.ps1` (PowerShell) files: **UTF-8 with BOM**. In code, use `encoding='utf-8-sig'` for both reading and writing.
    - All other source files (`.py`, `.js`, `.json`, `.md`, `.sh`, `.yml`, etc.): **UTF-8 without BOM**. In code, use `encoding='utf-8'`.
- **Shell Restriction**: Never use PowerShell's `Out-File` / `Set-Content` with default parameters (they emit UTF-16 or locale-dependent encoding). Console redirection (`>`, `>>`) inherits the system code page and will mangle non-ASCII text — avoid it.
- **Preferred Modification Tools**:
    - For **non-`.ps1`** files: Prefer `apply_patch` for diffs.
    - For **`.ps1`** files: **Do NOT use `apply_patch`** (BOM breaks line offsets). Always use full file rewrites via Python's `open()`/`pathlib`.
- Python 3.13 is required. Dependencies are locked in `uv.lock` and managed with `uv`.
- The project uses `pnpm` workspaces and requires Node.js >= 24.

## Related Projects & References

- **MaaFramework Documentation:** https://maaframework.github.io/
- **M9A Reference Project:** `G:\M9AA\M9A-pr\55\M9A`
- **create-maa-project Scaffold Tool:** `G:\M9AA\create-maa-project`
- **MaaKEDR交流群 QQ:** 1051890489
- **Repository:** https://github.com/APPLe-DF/MaaKEDR
