---
order: 1
icon: ri:book-open-line
---

# 项目与资源约定

## 分辨率基线

所有 ROI、坐标、模板图以 **1280×720（720p）** 为基准。其它分辨率由 MaaFramework 等比缩放。

## 入口配置

| 文件               | 作用                                                      |
| ------------------ | --------------------------------------------------------- |
| `interface.json`   | 控制器、资源包、任务 import、Agent 配置（手动维护版本号） |
| `maa-project.json` | 脚手架/发布/运行时渠道等项目元配置                        |
| `tasks/*.json`     | GUI 可见任务：`entry`、选项、`pipeline_override`          |

当前 `interface.json` 导入的任务：

- `tasks/startup.json` — 启动游戏
- `tasks/farm_resources.json` — 资源刷取
- `tasks/farm_remaining_stamina.json` — 剩余体力刷取（固定清空体力模式）
- `tasks/event_stage.json` — 活动关卡刷取与活动商店兑换
- `tasks/pvp.json` — 玩家对战
- `tasks/claim_rewards.json` — 领取奖励
- `tasks/stamina_info.json` — 体力信息（主界面体力与回满时间）

任务预设：`tasks/preset/Daily.json`（日常）、`tasks/preset/Activity.json`（活动）——在 GUI 选择预设即可一键勾选对应任务组合；活动预设内含「活动关卡刷取 / 活动商店兑换」，选择即默认开启。

任务组：`Daily`（日常任务）。

## 资源包（Resource）

| name     | 标签      | 路径顺序                     |
| -------- | --------- | ---------------------------- |
| base     | 官服      | `./resource/base`            |
| bilibili | B 服      | base → `./resource/bilibili` |
| taptap   | TapTap 服 | base → `./resource/taptap`   |

后挂载路径会覆盖同名 pipeline / 图片，用于区服差异（如启动登录文案或入口图）。

## Pipeline 与图片路径

- Pipeline：`resource/<pack>/pipeline/*.json`
- 模板图：`resource/<pack>/image/`（路径在 JSON 中使用**正斜杠**）
- OCR 模型：`resource/base/model/ocr/`

## Agent

开发态常见配置：`uv run python -u ./agent/bootstrap.py`。  
发布包会改为内嵌 `python/python.exe` 启动（见 `tools/build-release.mjs`）。

发布包**不再自带** MaaFramework 原生库：打包时会剥离内嵌解释器中的
`python/Lib/site-packages/maa/bin/`，Agent 改为复用客户端那一份
（MFAA 在 `runtimes/<platform>/native`，MXU 在 `maafw/`），单包因此省下数十 MiB。
`agent/main.py` 在导入任何 `maa` 之前调用 `agent/maafw_paths.py` 的
`ensure_maafw_binary_path()` 把 `MAAFW_BINARY_PATH` 指向该目录；若这个变量已被外部设置
（例如 Android runner 指向 APK 的 nativeLibraryDir），则保持不动。

因此 **`runtimes/` 与 `pyproject.toml` 里 pin 的 `maafw` 必须版本一致**，否则 Agent 会加载
到与 Python 绑定不匹配的原生库。`pnpm run sync:runtime` 之后请核对两者版本。

自定义模块注册：`agent/custom/` 下 action / recognition，并在对应 `__init__.py` 注册。

## 设计约定（与 AGENTS.md 一致）

- 避免硬编码 `pre_delay` / `post_delay`；优先中间识别节点或 `pre_wait_freezes` / `post_wait_freezes`
- 动作后的 `next` 应覆盖所有预期界面
- 不稳定节点优先补识别/重试，不盲目 `retry`
