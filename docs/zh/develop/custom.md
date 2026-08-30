---
title: "Custom 编写指南"
order: 2
icon: "ri:code-s-slash-fill"
---

# Custom 编写指南

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

## 注册模块

1. 在 `agent/custom/recognition/`、`agent/custom/action/` 或 `agent/custom/sink/` 下创建 Python 文件
2. 添加 `@AgentServer.custom_recognition("Name")` / `@AgentServer.custom_action("Name")` / `@AgentServer.tasker_sink()` 装饰器
3. 在对应的 `agent/custom/*/__init__.py` 的 `RECOGNITION_MODULES` / `ACTION_MODULES` / `SINK_MODULES` 中注册模块名
4. Pipeline 中通过 `custom_recognition` / `custom_action` 字段引用；Sink 无需 pipeline 引用，任务事件发生时自动触发

## 开发建议

- 先阅读项目已有的 Custom 实现（`farm_resources.py`、`pvp.py`、`event_stage.py`）了解模式
- 复杂逻辑先在单独的 Python 文件中测试，再集成到 Pipeline 中
- 使用 `from utils.logger import logger` 输出日志，方便调试

## 开发资源

- **MaaFramework 官方文档**：[快速开始](https://maafw.com/docs/1.1-QuickStarted)、[Custom & Agent 教程](https://maafw.com/docs/1.3-Custom&Agent)、[集成接口一览](https://maafw.com/docs/2.2-集成接口一览)
- **Python Binding 源码**：[MaaFramework `source/binding/Python`](https://github.com/MaaXYZ/MaaFramework/tree/main/source/binding/Python) —— API 行为细节以源码为准
- **调试工具**：见 [环境搭建](./setup.md#调试与开发工具)（MaaDebugger、Maa Pipeline Support 插件、MaaLogAnalyzer）
- **项目实例**：直接查看 `agent/custom/` 下现有实现，并按 [注册模块](#注册模块) 的步骤接入

::: tip 学习路径
建议按以下顺序学习：先读项目现有 custom 实现了解惯用模式，再参考 MaaFramework 官方文档理解核心概念，最后结合 Python Binding 源码深入理解 API 行为。
:::
