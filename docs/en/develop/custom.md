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
from maa.pipeline import JOCR, JRecognitionType


@AgentServer.custom_recognition("MyRecognizer")
class MyRecognizer(CustomRecognition):
    def analyze(self, context: Context, argv: CustomRecognition.AnalyzeArg) -> CustomRecognition.AnalyzeResult | None:
        params = json.loads(argv.custom_recognition_param)
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


@AgentServer.custom_action("MyAction")
class MyAction(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        params = json.loads(argv.custom_action_param)
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
from maa.event import TaskerEventSink, TaskerEvent


@AgentServer.tasker_sink()
class MySink(TaskerEventSink):
    def on_event(self, event: TaskerEvent) -> None:
        if event.event_type == TaskerEvent.Type.RECOGNITION_FAILED:
            node_name = event.detail.get("node_name", "")
            logger.warning(f"Recognition failed: {node_name}")
```

## Recognition Result Handling

`analyze()` returns either `AnalyzeResult` or `None`:

- Return `AnalyzeResult(box=..., detail=...)`: matches, uses the specified box
- Return `None`: no match, framework takes `on_error` path

The `detail` dict is included in logs for debugging.

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

1. Create a Python file in `agent/custom/recognition/` or `agent/custom/action/`
2. Add `@AgentServer.custom_recognition("Name")` / `@AgentServer.custom_action("Name")` / `@AgentServer.tasker_sink()` decorator
3. Register the module name in `agent/custom/recognition/__init__.py::RECOGNITION_MODULES`
4. Reference via `custom_recognition` / `custom_action` in pipeline JSON

## Development Tips

- Study existing Custom implementations (`farm_resources.py`, `pvp.py`) for patterns
- Test complex logic in a separate Python file before integrating into pipeline
- Use `from utils.logger import logger` for debug output
