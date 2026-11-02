---
title: "Custom 编写指南"
order: 2
icon: "ri:code-s-slash-fill"
---

# Custom 编写指南

## 开发方式

本项目采用 **JSON + 自定义逻辑扩展** 的方式开发：能用 Pipeline 节点表达的逻辑都写在 `resource/base/pipeline/*.json` 里，只有 Pipeline 表达不了的部分（动态 ROI、条件分支、跨节点状态、外部数据）才落到 Python。Python 侧统一通过 `AgentServer` 注册自定义识别 / 动作 / Sink，由 Pipeline 节点按名字引用。

判断要不要上 Custom 的顺序：先看 TemplateMatch / OCR / ColorMatch 能否直接覆盖 → 再看能否用多个节点 + `next` 组合表达 → 都不行才写 Custom。

## 模块类型

MaaKEDR 支持三类自定义模块，通过 `@AgentServer` 装饰器注册。

### 自定义识别

当 TemplateMatch 和 OCR 无法满足需求时（如动态 ROI、条件判断），使用 Custom Recognition。

```python
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context
from maa.define import RectType
from maa.pipeline import JOCR, JRecognitionType
from utils.params import parse_params


@AgentServer.custom_recognition("MyRecognizer")
class MyRecognizer(CustomRecognition):
    def analyze(
        self, context: Context, argv: CustomRecognition.AnalyzeArg
    ) -> CustomRecognition.AnalyzeResult | RectType | None:
        params = parse_params(argv.custom_recognition_param)
        # OCR 识别
        detail = context.run_recognition_direct(
            JRecognitionType.OCR,
            JOCR(expected=["text"], roi=(x, y, w, h)),
            argv.image,
        )
        if not detail or not detail.box:
            return None  # 未命中
        return CustomRecognition.AnalyzeResult(box=detail.box, detail={"status": "found"})
```

Pipeline 中调用：

```json
"NodeName": {
    "recognition": "Custom",
    "custom_recognition": "MyRecognizer",
    "custom_recognition_param": "{\"key\": \"value\"}",
    "action": { "type": "Click" }
}
```

> `custom_recognition_param` 是 JSON **字符串**（需序列化），不是 JSON 对象。

**项目实例**：

- `agent/custom/recognition/event_stage.py`：`CheckShopRefreshAfterPurchase` 用商店 OCR 结果在"继续检查"和"一次性补点刷新"之间动态路由
- `agent/custom/recognition/stamina.py`：`ReadStamina` 先旋转扶正 ROI 再 OCR，读不出时返回 `None`
- `agent/custom/recognition/farm_resources.py`：`CheckResourceStage` 按选项传入的关卡名做 OCR 匹配

### 自定义动作

复杂操作（状态管理、条件逻辑）用 Custom Action。

```python
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from utils.params import parse_params


@AgentServer.custom_action("MyAction")
class MyAction(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        params = parse_params(argv.custom_action_param)
        target = params.get("target_count", 1)
        # ... 业务逻辑
        return CustomAction.RunResult(success=True)
```

Pipeline 中调用：

```json
"NodeName": {
    "recognition": "DirectHit",
    "action": {
        "type": "Custom",
        "param": {
            "custom_action": "MyAction",
            "custom_action_param": { "key": "value" }
        }
    }
}
```

> `custom_action_param` 是 JSON **对象**（直接传，不序列化）。

**项目实例**：

- `agent/custom/action/general.py`：`DisableNode`（运行时禁用节点）、`NodeOverride`（透传 `override_pipeline`）、`ResetCount`（清 `max_hit` 计数）、`SubTask`（按序跑子任务）
- `agent/custom/action/farm_resources.py`：`SetBattleCount` / `ReduceBattleCount`（按 OCR 读到的次数点击加减，`ReduceBattleCount` 用于清体力模式动态减次数）

### 自定义 Sink（事件监听器）

Sink 用于监听任务事件（开始、完成、错误等），适合做前置检查、日志记录或性能监控。

```python
from maa.agent.agent_server import AgentServer
from maa.event_sink import NotificationType
from maa.tasker import Tasker, TaskerEventSink
from utils.logger import logger


@AgentServer.tasker_sink()
class MySink(TaskerEventSink):
    def on_tasker_task(
        self,
        tasker: Tasker,
        noti_type: NotificationType,
        detail: TaskerEventSink.TaskerTaskDetail,
    ) -> None:
        if noti_type != NotificationType.Starting:
            return
        logger.info("任务开始: {}", detail.entry)
```

实际实例：`agent/custom/sink/aspect_ratio.py` — 任务流水线开始时检查一次控制器分辨率是否为 16:9（每次运行只在第一个任务前检查，`MaaTaskerPostStop` 后重置），不符合则 `tasker.post_stop()` 停止任务并提示（见 `docs/*/develop/custom.md` 的注册方式与 `docs/*/protocol/overview.md` 的分辨率基线）。

## 识别结果处理

Custom Recognition 的 `analyze` 返回 `AnalyzeResult` 或 `None`：

- 返回 `AnalyzeResult(box=..., detail=...)`：命中，使用指定 box
- 返回 `None`：未命中，框架走 `on_error`
- 对于已经成功读取当前 UI、但需要按状态选择后续节点的识别器，也可以返回占位 `AnalyzeResult`，并调用 `context.override_next(argv.node_name, [target])` 动态路由；例如 `CheckShopRefreshAfterPurchase` 根据商店 OCR 状态在继续检查与一次性补点之间选择路径。

`None` / `on_error` 应保留给真正的识别或参数解析失败；预期的 UI 状态分支不应伪装成错误。

**读取识别结果**：`context.run_recognition_direct(...)` / `context.run_recognition(...)` 无论命中与否都会返回 detail（用 `.hit` 判断是否命中），只有在识别没能启动时（节点不存在、节点被禁用、图像为空等）才返回 `None`。项目里用 `utils/maa_types.py` 的辅助函数统一处理，避免每处手写 `if detail and detail.hit`：

```python
from utils.maa_types import is_hit, ocr_text, ocr_results

detail = context.run_recognition_direct(
    JRecognitionType.OCR,
    JOCR(roi=(x, y, w, h), only_rec=True),
    argv.image,
)
if not is_hit(detail):
    return None
text = ocr_text(detail)  # 最佳 OCR 结果的文本
box = detail.box  # 最佳结果的框 [x, y, w, h]
all_texts = [result.text for result in ocr_results(detail)]  # 全部 OCR 结果
```

| 辅助函数                                                | 用途                                                    |
| ------------------------------------------------------- | ------------------------------------------------------- |
| `is_hit(detail)`                                        | detail 存在、命中且带 box（配合类型收窄使用）           |
| `require_hit(detail)`                                   | 同上，但未命中直接抛 `ValueError`，适合"必须命中"的场景 |
| `ocr_text(detail, default="")`                          | 最佳 OCR 结果的文本                                     |
| `ocr_results(detail)`                                   | 全部 OCR 结果                                           |
| `best_box(detail)`                                      | 最佳结果带 box 时返回该 box，否则 `None`                |
| `has_box_result(result)` / `boxed_results(detail)`      | 过滤出带坐标的结果                                      |
| `results_as(detail, OCRResult)` / `all_results_as(...)` | 按结果类型过滤                                          |

## Context API 参考

```python
# OCR 识别
ocr = context.run_recognition_direct(
    JRecognitionType.OCR,
    JOCR(expected=["text"], roi=(x, y, w, h)),
    image,
)
# 获取结果文本
if ocr and ocr.all_results:
    text = ocr.all_results[0].text

# 模板匹配
match = context.run_recognition_direct(
    JRecognitionType.TemplateMatch,
    JTemplateMatch(template="path.png", roi=(x, y, w, h), threshold=0.8),
    image,
)

# 点击
context.run_action_direct(JActionType.Click, JClick(), box, "")

# 获取缓存截图
image = context.tasker.controller.cached_image

# 发送点击（跳过 pipeline）
context.tasker.controller.post_click(x, y).wait()

# 覆盖 next 跳转
context.override_next(argv.node_name, ["NextNodeA", "NextNodeB"])

# 动态覆盖 pipeline 配置
context.override_pipeline({"SomeNode": {"next": ["CustomNext"]}})
```

常用方法补充：

```python
# 按节点名执行一次识别（不执行动作、不推进 next）
reco = context.run_recognition("NodeName", image)

# 按节点名跑一段任务（可顺带传 pipeline_override）
detail = context.run_task("NodeName")
detail = context.run_task("NodeName", pipeline_override={"SomeNode": {"enabled": False}})

# 覆盖图片：把内存里的图注册成 image 名，供 TemplateMatch 等引用
context.override_image("image_name", image_array)

# 读取节点合并后的当前定义（含 interface.json 的 pipeline_override 结果）
node_data = context.get_node_data("NodeName")

# 清空某节点的 max_hit 计数
context.clear_hit_count("NodeName")
```

:::note 图像格式

MaaFramework 用 OpenCV 处理图像，`context.tasker.controller.cached_image` 与 `post_screencap().wait().get()` 拿到的都是 `numpy.ndarray`，通道顺序为 **BGR**。回传给 MaaFW 时不需要转换；要落盘时注意各库的约定——OpenCV 的 `imencode` 直接吃 BGR，PIL / matplotlib 等按 RGB，需先用 `cv2.cvtColor(img, cv2.COLOR_BGR2RGB)` 转换。

:::

## 工具模块（`agent/utils/`）

`agent/utils/` 下的模块由 `utils/__init__.py` 统一导出，`from utils import logger` 与 `from utils.params import parse_params` 两种写法都可用。

| 模块                  | 内容                                                                                                                                                                      |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `utils.logger`        | loguru 封装，支持 `logger.info("值: {}", v)` 的 `{}` 占位写法；同时输出到控制台与 `debug/custom/<日期>.log`（按天轮转，保留 2 周）                                        |
| `utils.params`        | `parse_params`（解析 `custom_*_param`，支持多层转义 JSON，可声明必填键）、`coerce_roi`、`coerce_point`、`is_int_value`、`extract_custom_param`、`merge_node_custom_param` |
| `utils.maa_types`     | 识别结果辅助函数（见[识别结果处理](#识别结果处理)）                                                                                                                       |
| `utils.pienv`         | 读取 Project Interface 注入的环境变量：`client_name()`、`client_language()`、`controller_name()`、`resource_name()`、`resource_label()` 等                                |
| `utils.runtime_paths` | `get_runtime_paths()` 返回 `config_dir` / `debug_dir` / `interface_file` 等运行期路径                                                                                     |

## 注册模块

1. 在 `agent/custom/recognition/`、`agent/custom/action/` 或 `agent/custom/sink/` 下创建 Python 文件
2. 添加 `@AgentServer.custom_recognition("Name")` / `@AgentServer.custom_action("Name")` / `@AgentServer.tasker_sink()` 装饰器
3. 在对应的 `agent/custom/*/__init__.py` 的 `RECOGNITION_MODULES` / `ACTION_MODULES` / `SINK_MODULES` 中注册模块名
4. Pipeline 中通过 `custom_recognition` / `custom_action` 字段引用；Sink 无需 pipeline 引用，任务事件发生时自动触发

## 开发建议

- 先阅读项目已有的 Custom 实现（`farm_resources.py`、`pvp.py`、`event_stage.py`）了解模式
- 复杂逻辑先在单独的 Python 文件中测试，再集成到 Pipeline 中
- 使用 `from utils.logger import logger` 输出日志，方便调试
- 参数解析失败时返回 `success=False` / `None` 并打日志，不要静默吞掉（参考 `agent/custom/action/general.py` 的写法）
- 改完跑 `pnpm check:py`（ruff + pyright），新增模块别忘第 3 步的注册

## 开发资源

- **MaaFramework 官方文档**：[快速开始](https://maafw.com/docs/1.1-QuickStarted)、[Custom & Agent 教程](https://maafw.com/docs/1.3-Custom&Agent)、[集成接口一览](https://maafw.com/docs/2.2-集成接口一览)
- **Python Binding 源码**：[MaaFramework `source/binding/Python`](https://github.com/MaaXYZ/MaaFramework/tree/main/source/binding/Python) —— API 行为细节以源码为准；本地安装的 binding 在 `.venv/Lib/site-packages/maa/`
- **调试工具**：见 [环境搭建](./setup.md#调试与开发工具)（MaaDebugger、Maa Pipeline Support 插件、MaaLogAnalyzer）
- **项目实例**：直接查看 `agent/custom/` 下现有实现，并按 [注册模块](#注册模块) 的步骤接入

::: tip 学习路径
建议按以下顺序学习：先读项目现有 custom 实现了解惯用模式，再参考 MaaFramework 官方文档理解核心概念，最后结合 Python Binding 源码深入理解 API 行为。
:::
