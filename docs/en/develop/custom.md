---
title: "Custom Recognition & Action"
order: 2
icon: "ri:code-s-slash-fill"
---

# Custom Recognition & Action

## Module Types

Three types of custom modules can be registered via `@AgentServer` decorators.

### Custom Recognition

Use when TemplateMatch or OCR can't handle your needs (dynamic ROI, conditional logic).

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
        detail = context.run_recognition_direct(
            JRecognitionType.OCR,
            JOCR(expected=["text"], roi=(x, y, w, h)),
            argv.image,
        )
        if not detail or not detail.box:
            return None
        return CustomRecognition.AnalyzeResult(box=detail.box, detail={"status": "found"})
```

Pipeline usage:

```json
"NodeName": {
    "recognition": "Custom",
    "custom_recognition": "MyRecognizer",
    "custom_recognition_param": "{\"key\": \"value\"}",
    "action": { "type": "Click" }
}
```

> `custom_recognition_param` is a JSON **string** (serialized), not an object.

### Custom Action

For stateful operations or complex logic.

```python
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from utils.params import parse_params


@AgentServer.custom_action("MyAction")
class MyAction(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        params = parse_params(argv.custom_action_param)
        return CustomAction.RunResult(success=True)
```

Pipeline usage:

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

> `custom_action_param` is a JSON **object** (passed directly, not serialized).

### Custom Sink (Event Listener)

Sinks listen to task events (start, complete, error) for pre-checks, logging, or monitoring.

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
        logger.info("Task started: {}", detail.entry)
```

Real example: `agent/custom/sink/aspect_ratio.py` — checks the controller resolution is 16:9 once at the start of a task pipeline (only before the first task of each run; the flag is reset on `MaaTaskerPostStop`), calls `tasker.post_stop()` otherwise (see resolution baseline in `docs/*/protocol/overview.md`).

## Recognition Result Handling

`analyze()` returns either `AnalyzeResult` or `None`:

- Return `AnalyzeResult(box=..., detail=...)`: matches, uses the specified box
- Return `None`: no match, framework takes the `on_error` path
- A recognizer that successfully reads the current UI but must choose a next node based on state may instead return a placeholder `AnalyzeResult` and call `context.override_next(argv.node_name, [target])` for dynamic routing. For example, `CheckShopRefreshAfterPurchase` uses shop OCR to choose between continuing item checks and performing one fallback refresh click.

Reserve `None` / `on_error` for actual recognition or parameter-parsing failures; expected UI-state branches should not be modeled as errors.

## Context API Reference

```python
# OCR
ocr = context.run_recognition_direct(
    JRecognitionType.OCR,
    JOCR(expected=["text"], roi=(x, y, w, h)),
    image,
)
if ocr and ocr.all_results:
    text = ocr.all_results[0].text

# Template match
match = context.run_recognition_direct(
    JRecognitionType.TemplateMatch,
    JTemplateMatch(template="path.png", roi=(x, y, w, h), threshold=0.8),
    image,
)

# Click
context.run_action_direct(JActionType.Click, JClick(), box, "")

# Get cached screenshot
image = context.tasker.controller.cached_image

# Send click (bypass pipeline)
context.tasker.controller.post_click(x, y).wait()

# Override next transition
context.override_next(argv.node_name, ["NextNodeA", "NextNodeB"])

# Override pipeline config dynamically
context.override_pipeline({"SomeNode": {"next": ["CustomNext"]}})
```

## Registration

1. Create a Python file in `agent/custom/recognition/`, `agent/custom/action/` or `agent/custom/sink/`
2. Add `@AgentServer.custom_recognition("Name")` / `@AgentServer.custom_action("Name")` / `@AgentServer.tasker_sink()` decorator
3. Register the module name in the matching `agent/custom/*/__init__.py` (`RECOGNITION_MODULES` / `ACTION_MODULES` / `SINK_MODULES`)
4. Reference via `custom_recognition` / `custom_action` in pipeline JSON; sinks need no pipeline reference — they fire automatically on task events

## Development Tips

- Study existing Custom implementations (`farm_resources.py`, `pvp.py`, `event_stage.py`) for patterns
- Test complex logic in a separate Python file before integrating into pipeline
- Use `from utils.logger import logger` for debug output

## Resources

- **MaaFramework official docs**: [Quick Started](https://maafw.com/docs/1.1-QuickStarted), [Custom & Agent](https://maafw.com/docs/1.3-Custom&Agent), [Integration Interfaces](https://maafw.com/docs/2.2-集成接口一览)
- **Python binding source**: [MaaFramework `source/binding/Python`](https://github.com/MaaXYZ/MaaFramework/tree/main/source/binding/Python) — API behavior details follow the source
- **Debugging tools**: see [Environment Setup](./setup.md#debugging-tools) (MaaDebugger, Maa Pipeline Support extension, MaaLogAnalyzer)
- **In-repo examples**: read the implementations under `agent/custom/` and wire new modules in per [Registration](#registration)

::: tip Learning path
Recommended order: read existing custom implementations for common patterns first, then the MaaFramework official docs for core concepts, and finally the Python binding source for precise API behavior.
:::
