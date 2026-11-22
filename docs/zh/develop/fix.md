---
title: "Bug 排查"
order: 3
icon: "ri:bug-fill"
---

# Bug 排查

修 Bug 是开发中重要的一环。本文按「收集信息 → 看日志 → 分类定位 → 验证修复」的顺序说明排查流程。

## 前置准备

先和问题提出者确认以下信息，能省掉大量猜测：

- 问题的细节描述：发生时间、所在任务、操作到哪一步、期望结果与实际结果
- 运行环境：模拟器或真机、分辨率、MFAAvalonia / MXU 版本、资源包版本
- 必要文件：`debug/maafw.log`、`debug/` 下的截图、能复现问题的界面截图

> 日志请以文件形式提供，不要粘贴长段文本或只发日志截图（见 [CONTRIBUTING.md](https://github.com/APPLe-DF/MaaKEDR/blob/main/CONTRIBUTING.md)）。

## 日志文件位置

| 路径              | 说明                                                                                    |
| ----------------- | --------------------------------------------------------------------------------------- |
| `debug/maafw.log` | MaaFramework 运行日志（工作目录下的 `debug/`）                                          |
| `debug/custom/`   | Agent 自定义模块日志（loguru 文件输出，按日期命名）                                     |
| `debug/on_error/` | 错误现场截图（`resource/base/config/maa_option.json` 里 `save_on_error` 默认为 `true`） |

## 日志分析工具

### MaaLogAnalyzer

推荐使用 [MaaLogAnalyzer](https://github.com/Windsland52/MAALogAnalyzer) 可视化分析 `maafw.log`，它可以：

- 自动识别 MaaFramework 版本
- 可视化展示 Pipeline 执行流程
- 快速定位出错和异常节点
- 分析节点匹配情况与执行耗时

使用步骤：

1. 从 [Releases](https://github.com/Windsland52/MAALogAnalyzer/releases) 下载并启动
2. 导入 `debug/maafw.log`
3. 按任务/节点过滤，查看每条识别记录的 `reco_id`、算法、`box` 与细节，并结合 `debug/` 截图对照当前画面

### 手动分析（备用方案）

无法使用 MaaLogAnalyzer 时，可以直接在日志里搜索。每行日志的格式是 `[时间][级别][进程][线程][源文件][行号] 内容`，级别有 `TRC` / `DBG` / `INF` / `WRN` / `ERR` 五种：

1. **先扫错误**：搜索 `[ERR]`，错误行通常已经写明失败的模块（如 `PipelineParser`、`AdbControlUnit`）
2. **按节点名搜索**：节点解析时日志会打印 `[name=<节点名>]`，用出错节点的完整名称搜索，看它前后的识别与动作记录
3. **任务提前结束**：`[ERR]` 里没有线索时，回头检查该节点的 `next` 与 `on_error` 配置是否覆盖了实际画面

### MaaEvidenceKit

[MaaEvidenceKit](https://github.com/Windsland52/MaaEvidenceKit) 是面向 MaaFramework 的证据提取与诊断工具包（CLI/SDK）：借助 MaaLogAnalyzer 从日志与项目中提取可定位的运行时与静态证据，输出 JSON/文本，供 Codex、Claude Code 等 AI 助手按需诊断。

### Maa Pipeline Support

开发调试时也可使用 **Maa Pipeline Support**（VSCode 插件）实时查看识别过程（见 [环境搭建](./setup.md#调试与开发工具)）。

## 问题分类

排查前先判断问题属于哪一类：启动、资源加载、连接、运行时、识别。分类不同，看日志的重点和修复方式也不同；用户侧的资源加载失败与连接问题，可以先对照 [常见问题](../manual/faq.md) 里的排查顺序。

### 启动类

#### Agent 启动失败

现象：`Python >=3.13,<3.14 is required`

原因：系统 Python 版本不匹配。项目需要 Python 3.13.x。

解决：项目使用 `uv` 管理 Python 版本，确保已安装 `uv` 并执行过 `uv sync --frozen`。

#### Custom 模块未注册

现象：自定义识别或动作执行失败，返回 `success: false`

常见原因：新增的模块没有加入 `agent/custom/recognition/__init__.py` 的 `RECOGNITION_MODULES`，或没有加入 `agent/custom/action/__init__.py` 的 `ACTION_MODULES`。

解决：在对应的元组里补上模块名。当前内容以两个 `__init__.py` 为准，例如 `RECOGNITION_MODULES = ("farm_resources", "pvp", "stamina", "event_stage")`。

### 资源加载类

现象：日志出现 `key already exists [key=<节点名>]`（`PipelineResMgr::parse_config`）

原因：两个 pipeline 文件里定义了同名节点，或覆盖安装时旧资源没清干净。

解决：先确认 `resource/base/pipeline/*.json` 中没有重复节点名；重新部署资源时清空旧的 `resource/` 目录再解压，不要直接覆盖。

### 连接类

现象：日志出现 `failed to connect [adb_path_=...] [adb_serial_=127.0.0.1:16384]`（`ControlUnitMgr::connect`）

原因：模拟器没启动、ADB 路径或地址端口与连接配置不一致，或端口被其他实例占用。

解决：确认模拟器已启动并开启 ADB 调试；核对连接设置中的 ADB 路径与地址（见 [连接设置](../manual/connection.md)）；必要时重启模拟器后重连。

### 运行时类

#### Pipeline 节点卡住

现象：任务在某节点停留不动直到超时

常见原因：

1. **截图过时** — 前一个操作后画面还没稳定就截图。改用 `post_wait_freezes` 等待画面静止，或补一个中间识别节点确认目标界面出现后再继续
2. **ROI 不匹配** — 游戏更新后 UI 位置变了，需更新 ROI
3. **模板图片过时** — 游戏 UI 变更后模板图失效，需重新截图
4. **节点没有兜底** — 重要的导航节点没加 `on_error`

#### JumpBack 节点异常

现象：JumpBack 节点执行后行为不符合预期

原因：JumpBack 节点设置了 `next`。参考规则：**JumpBack 节点不能有 `next`**。

#### 清体力模式循环

现象：体力不足时一直在减次数，减到 1 后仍然继续

常见原因：清体力模式的 `FarmResources.ExitStageConfirm` 的 `next` 指向了 `FarmResources.BattleStage` 而不是退出路径。

解决：检查 `tasks/farm_resources.json` 中「清空体力」模式的 override，确保 `FarmResources.ExitStageConfirm` 的 `next` 是 `FarmResources.ReturnMainFromFarm` / `Common.CheckHomePage`。

### 识别类

#### 关卡识别不到

现象：`CheckResourceStage` 一直返回失败

可能原因：

1. 关卡未解锁（文字灰色，OCR 无法识别）— 检查 `farm_resources/lock_icon.png` 模板
2. 需要先向左滑动复位（关卡列表偏移了）— 确认 `FarmResources.SwipeToBegin` 节点已执行
3. `custom_recognition_param` 中的 `stage_index` 或 `resource_type` 不匹配

#### 体力不足时流程卡住

现象：体力耗尽后任务不退出

原因：`farm_resources/no_stamina.png` 模板图片不存在或 ROI 不对，导致无法识别体力不足弹窗。

#### Schema 验证失败

现象：CI 报错 `must NOT have unevaluated properties`

原因：使用了不被当前 schema 支持的字段。常见如 `only_rec` 搭配 TemplateMatch 使用。

解决：检查 `tools/schema/` 下的 schema 定义，移除不支持的字段。

## 日志分析

运行日志（`debug/maafw.log`）中包含每次识别的详细结果：

```json
{
    "reco_id": 400000431,
    "algorithm": "Custom",
    "box": null,
    "detail": {"all": [], "best": null},
    "name": "PVP.ReadResult"
}
```

- `box: null` — 识别未命中
- `box: [x, y, w, h]` — 识别成功，返回区域坐标
- `detail.all` — 所有识别结果
- `detail.best` — 最佳匹配结果

查看 `debug/` 目录下的截图可以确认当前画面是否与预期一致。

## 验证修复

修复后应验证，而不是直接提交：

1. **本地检查**：`pnpm check`（改动 Python 时同时执行 `pnpm check:py`）
2. **实机复跑**：在 GUI 中勾选对应任务，连续运行 2–3 次，确认问题不再出现
3. **回归确认**：检查 `debug/` 截图与 `debug/maafw.log`，确认识别结果符合预期、无 `on_error` 异常路径触发
4. **边界场景**：如改动涉及流程分支，额外验证相邻状态（启动页/主页/弹窗等）未被破坏

若修复涉及行为变化，请同步更新 [协议文档](../protocol/) 与 [验收清单](../protocol/event-stage.md) 等对应文档；PR 描述里写清根因、验证命令与结果（见 [CONTRIBUTING.md](https://github.com/APPLe-DF/MaaKEDR/blob/main/CONTRIBUTING.md)）。
