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
- `tasks/claim_rewards.json` — 领取奖励与剩余奖励领取
- `tasks/stamina_info.json` — 体力信息（主界面体力与回满时间）

任务预设：`tasks/preset/Daily.json`（日常）、`tasks/preset/Activity.json`（活动）——在 GUI 选择预设即可一键勾选对应任务组合；活动预设内含「活动关卡刷取 / 活动商店兑换」，选择即默认开启。

任务组：`Daily`（日常任务）。

## 任务定义结构

任务文件（`tasks/<task>.json`，不含 `tasks/preset/`）只有两个顶层键：`task`（任务列表）与 `option`（选项表）；
预设文件 `tasks/preset/*.json` 的顶层键是 `preset`。

任务字段：

| 字段                | 类型     | 说明                                                       |
| ------------------- | -------- | ---------------------------------------------------------- |
| `name`              | string   | GUI 显示名，直接写中文（本项目没有 i18n 机制）             |
| `entry`             | string   | pipeline **节点名**，不是文件名                            |
| `default_check`     | bool     | GUI 中默认是否勾选；`false` 的任务需手动开启               |
| `description`       | string   | GUI 悬停说明                                               |
| `group`             | string[] | 任务分组，本项目统一 `["Daily"]`                           |
| `option`            | string[] | 引用顶层 `option` 的键名，按数组顺序显示                   |
| `pipeline_override` | object   | 任务级覆盖（不随选项变化），如「剩余体力刷取」固定清空体力 |

选项字段：

| 字段           | 类型   | 说明                              |
| -------------- | ------ | --------------------------------- |
| `type`         | string | 本项目只用到 `switch` 与 `select` |
| `label`        | string | 控件标签                          |
| `description`  | string | 控件说明                          |
| `cases`        | case[] | 可选项列表                        |
| `default_case` | string | 默认选中的 `case.name`            |

case 字段：

| 字段                | 类型     | 说明                                                            |
| ------------------- | -------- | --------------------------------------------------------------- |
| `name`              | string   | 选项值，也是 `preset` 里引用的值                                |
| `label`             | string   | 下拉显示文本                                                    |
| `description`       | string   | 悬停说明                                                        |
| `pipeline_override` | object   | 选中后合并进 pipeline 的节点补丁                                |
| `option`            | string[] | 嵌套子选项：`switch` 选 Yes 时展开，`select` 选中该 case 时展开 |

`pipeline_override` 的补丁只写要改的字段（`enabled`、`next`、`roi`、`expected`、`custom_recognition_param`、
`custom_action_param` 等），其余字段沿用 pipeline 原值。

## 选项到节点的数据链路

```text
GUI 勾选任务 + 选项
  → interface.json 的 import 把 tasks/*.json 载入同一命名空间
  → 选中 case 的 pipeline_override（叠加任务级 pipeline_override）按节点名合并
  → resource[].path 依次加载 resource/<pack>/pipeline/*.json（后者覆盖同名节点）
  → 从 entry 节点开始执行；Custom 节点由 agent 子进程处理
```

- 覆盖目标只能是**已存在**的节点：改名节点必须同步 `pipeline_override`
- 合并顺序与字段级规则以 [Project Interface V2](https://maafw.com/docs/3.3-ProjectInterfaceV2) 为准；
  本目录只记录「哪个选项动了哪些节点」

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

开发态常见配置：`uv run python agent/main.py`。  
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
