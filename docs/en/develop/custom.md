---
title: "Custom Recognition & Action"
order: 2
icon: "ri:code-s-slash-fill"
---

# Custom Recognition & Action

## Development Approach

This project follows the **JSON + custom logic extension** approach: anything expressible with pipeline nodes lives in `resource/base/pipeline/*.json`, and only what the pipeline cannot express (dynamic ROI, conditional branches, cross-node state, external data) moves into Python. On the Python side, custom recognitions, actions and sinks are all registered through `AgentServer` and referenced from pipeline nodes by name.

Decide in this order whether you need a custom module: can TemplateMatch / OCR / ColorMatch cover it directly → can a combination of nodes plus `next` express it → only then write a custom module.

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

**In-repo examples**:

- `agent/custom/recognition/event_stage.py`: `CheckShopRefreshAfterPurchase` routes dynamically between "keep checking" and "perform one fallback refresh" based on shop OCR
- `agent/custom/recognition/stamina.py`: `ReadStamina` rotates and straightens the ROI before OCR, and returns `None` when nothing readable is found
- `agent/custom/recognition/farm_resources.py`: `CheckResourceStage` matches a stage name passed in through options

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
        target = params.get("target_count", 1)
        # ... business logic
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

**In-repo examples**:

- `agent/custom/action/general.py`: `DisableNode` (disable a node at runtime), `NodeOverride` (pass an override straight to `override_pipeline`), `ResetCount` (clear `max_hit` counters), `SubTask` (run sub-tasks in order)
- `agent/custom/action/farm_resources.py`: `SetBattleCount` / `ReduceBattleCount` (tap plus/minus based on the OCR-read count; `ReduceBattleCount` is used by stamina-drain mode)

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

**Reading recognition results**: `context.run_recognition_direct(...)` / `context.run_recognition(...)` always return a detail, hit or miss (use `.hit` to tell), and only return `None` when the recognition could not start at all (missing node, disabled node, empty image, ...). The project funnels this through helpers in `utils/maa_types.py` so that no one hand-writes `if detail and detail.hit`:

```python
from utils.maa_types import is_hit, ocr_text, ocr_results

detail = context.run_recognition_direct(
    JRecognitionType.OCR,
    JOCR(roi=(x, y, w, h), only_rec=True),
    argv.image,
)
if not is_hit(detail):
    return None
text = ocr_text(detail)  # text of the best OCR result
box = detail.box  # box of the best result, [x, y, w, h]
all_texts = [result.text for result in ocr_results(detail)]  # every OCR result
```

| Helper                                                  | Purpose                                                        |
| ------------------------------------------------------- | -------------------------------------------------------------- |
| `is_hit(detail)`                                        | detail exists, hit, and carries a box (works as a type guard)  |
| `require_hit(detail)`                                   | same, but raises `ValueError` on a miss — for "must hit" cases |
| `ocr_text(detail, default="")`                          | text of the best OCR result                                    |
| `ocr_results(detail)`                                   | all OCR results                                                |
| `best_box(detail)`                                      | box of the best result when it carries one, otherwise `None`   |
| `has_box_result(result)` / `boxed_results(detail)`      | filter to results that carry coordinates                       |
| `results_as(detail, OCRResult)` / `all_results_as(...)` | filter by result type                                          |

## Context API Reference

```python
# OCR
ocr = context.run_recognition_direct(
    JRecognitionType.OCR,
    JOCR(expected=["text"], roi=(x, y, w, h)),
    image,
)
# Get the result text
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

More commonly used methods:

```python
# Run the recognition of a node once (no action, no next)
reco = context.run_recognition("NodeName", image)

# Run a task by node name (optionally with a pipeline_override)
detail = context.run_task("NodeName")
detail = context.run_task("NodeName", pipeline_override={"SomeNode": {"enabled": False}})

# Override an image: register an in-memory array under an image name for TemplateMatch etc.
context.override_image("image_name", image_array)

# Read a node's current merged definition (after interface.json pipeline_override)
node_data = context.get_node_data("NodeName")

# Clear a node's max_hit counter
context.clear_hit_count("NodeName")
```

:::note Image format

MaaFramework processes images with OpenCV, so both `context.tasker.controller.cached_image` and `post_screencap().wait().get()` return a `numpy.ndarray` in **BGR** channel order. No conversion is needed when handing the array back to MaaFW; when writing to disk mind each library's convention — OpenCV's `imencode` expects BGR directly, while PIL / matplotlib expect RGB and need `cv2.cvtColor(img, cv2.COLOR_BGR2RGB)` first.

:::

## Utility Modules (`agent/utils/`)

Modules under `agent/utils/` are re-exported by `utils/__init__.py`, so both `from utils import logger` and `from utils.params import parse_params` work.

| Module                | Contents                                                                                                                                                                                          |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `utils.logger`        | loguru wrapper supporting `logger.info("value: {}", v)` placeholders; writes to the console and to `debug/custom/<date>.log` (daily rotation, 2-week retention)                                   |
| `utils.params`        | `parse_params` (parses `custom_*_param`, tolerates multiply-escaped JSON, accepts required keys), `coerce_roi`, `coerce_point`, `is_int_value`, `extract_custom_param`, `merge_node_custom_param` |
| `utils.maa_types`     | recognition result helpers (see [Recognition Result Handling](#recognition-result-handling))                                                                                                      |
| `utils.pienv`         | reads the environment variables injected by Project Interface: `client_name()`, `client_language()`, `controller_name()`, `resource_name()`, `resource_label()`, etc.                             |
| `utils.runtime_paths` | `get_runtime_paths()` returns runtime paths such as `config_dir` / `debug_dir` / `interface_file`                                                                                                 |

## Registration

1. Create a Python file in `agent/custom/recognition/`, `agent/custom/action/` or `agent/custom/sink/`
2. Add `@AgentServer.custom_recognition("Name")` / `@AgentServer.custom_action("Name")` / `@AgentServer.tasker_sink()` decorator
3. Register the module name in the matching `agent/custom/*/__init__.py` (`RECOGNITION_MODULES` / `ACTION_MODULES` / `SINK_MODULES`)
4. Reference via `custom_recognition` / `custom_action` in pipeline JSON; sinks need no pipeline reference — they fire automatically on task events

## Development Tips

- Study existing Custom implementations (`farm_resources.py`, `pvp.py`, `event_stage.py`) for patterns
- Test complex logic in a separate Python file before integrating into pipeline
- Use `from utils.logger import logger` for debug output
- On a parameter-parsing failure return `success=False` / `None` and log it — do not swallow it silently (see `agent/custom/action/general.py`)
- Run `pnpm check:py` (ruff + pyright) after editing, and do not forget step 3 of the registration list

## Resources

- **MaaFramework official docs**: [Quick Started](https://maafw.com/docs/1.1-QuickStarted), [Custom & Agent](https://maafw.com/docs/1.3-Custom&Agent), [Integration Interfaces](https://maafw.com/docs/2.2-集成接口一览)
- **Python binding source**: [MaaFramework `source/binding/Python`](https://github.com/MaaXYZ/MaaFramework/tree/main/source/binding/Python) — API behavior details follow the source; the locally installed binding lives in `.venv/Lib/site-packages/maa/`
- **Debugging tools**: see [Environment Setup](./setup.md#debugging-tools) (MaaDebugger, Maa Pipeline Support extension, MaaLogAnalyzer)
- **In-repo examples**: read the implementations under `agent/custom/` and wire new modules in per [Registration](#registration)

::: tip Learning path
Recommended order: read existing custom implementations for common patterns first, then the MaaFramework official docs for core concepts, and finally the Python binding source for precise API behavior.
:::
