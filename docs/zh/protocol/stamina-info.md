---
order: 7
icon: ri:heart-pulse-line
---

# 体力信息协议

本页记录「体力信息」任务：在任务链末尾读取主界面体力并输出自然回满时间。任务定义位于 `tasks/stamina_info.json`，
入口 `StaminaInfo.EnsureHome`（恒命中门节点），默认勾选并置于任务链末尾。

## 任务入口与选项

| 任务     | entry                    | 定义                      | 流程                                  | 选项                         |
| -------- | ------------------------ | ------------------------- | ------------------------------------- | ---------------------------- |
| 体力信息 | `StaminaInfo.EnsureHome` | `tasks/stamina_info.json` | `resource/base/pipeline/stamina.json` | 无（读取固定 ROI，默认执行） |

## 数据链路

```text
tasks/stamina_info.json（无选项、无 pipeline_override）
  → resource/base/pipeline/stamina.json（6 个节点）
  → agent/custom/recognition/stamina.py
       CheckStaminaPage（入口路由）、ReadStamina（读数字 + 算回满时间）
  → 输出：日志一行「体力将在 <YYYY-MM-DD HH:MM> 回满。(Xh Ym 后)」
```

## 流程

```text
StaminaInfo.EnsureHome（门节点，恒命中，max_hit: 6）
  ├─ StaminaInfo（CheckStaminaPage 路由：在主界面？）
  │    ├─ 是 → StaminaInfo.Read（失败经 ReadRetry 重试，合计最多 3 次）→ 输出回满信息（仍失败 → 任务失败）
  │    └─ 否 → StaminaInfo.ClickHome（不匹配经 ClickHomeRetry 重试，合计最多 3 次）→ 重新确认
  └─ 上面两项都没命中（连续 3 次点主页按钮无效、自定义识别放弃）→ Common.EnsureHome 通用枢纽回主页后重试
```

关键约定：

- `StaminaInfo.EnsureHome` 是恒命中门节点：`next` 先放主路径 `StaminaInfo`，末位挂通用枢纽 `[JumpBack]Common.EnsureHome`（跨文件复用，见[通用节点与回主页枢纽](../develop/common.md)）。
- `StaminaInfo` 入口使用自定义识别 `CheckStaminaPage`（`agent/custom/recognition/stamina.py`）路由：用模板 `more.png` 确认主界面；在主界面则路由到 `StaminaInfo.Read`，不在主界面则路由到 `StaminaInfo.ClickHome` 点击主页按钮返回后重新确认。
- 路由通过 `context.override_next` 实现（与 `CheckEventHub` 同模式），避免把 `Read` 与 `ClickHome` 并列在 `next` 列表中——否则 `Read` 识别失败会顺序回落到 `ClickHome`，而 `ClickHome` 在主界面同样命中并点击，形成"读取失败 → 点主页 → 再读取"的无限循环。
- `StaminaInfo.Read` 使用自定义识别 `ReadStamina`（`agent/custom/recognition/stamina.py`）；识别失败（如识别不到完整体力数值）时最多重试 2 次（合计 3 次读取尝试），仍失败则任务以失败结束、不进入循环。尝试次数由 `StaminaInfo.ReadRetry` 闸门节点控制（`max_hit=2` + `timeout=0`，每轮截图只识别一次），与设备 OCR 速度无关，不会长时间空转。
- `StaminaInfo.ClickHome` 分支对称地由 `StaminaInfo.ClickHomeRetry` 闸门控制（`max_hit=2` + `timeout=0`）：返回主页按钮不匹配时合计最多尝试 3 次；`other_max`（默认 3）次连续未回主页（点击无效）时 `CheckStaminaPage` 返回识别失败——此时不再由本任务判定失败，而是由门节点末位的通用枢纽接管（关闭获得物品弹窗 / 点顶部主页按钮 / 通用返回），回到主页后重新路由到 `StaminaInfo`。

## ReadStamina 识别约定

主界面体力数字以 **-45° 倾斜** 显示，`ReadStamina` 会对两个 ROI 分别按 `tilt_angle`（默认 `-45`，纠正角取其相反数旋转扶正）后再 OCR，提取第一个整数：

| 参数          | 默认值                | 说明                                          |
| ------------- | --------------------- | --------------------------------------------- |
| `current_roi` | `[1120, 512, 38, 44]` | 当前体力数字 ROI                              |
| `cap_roi`     | `[1152, 484, 28, 30]` | 体力上限数字 ROI                              |
| `tilt_angle`  | `-45`                 | 屏幕上数字的倾斜角（兼容旧名 `rotate_angle`） |
| `stamina_cap` | 无                    | 可选兜底：上限识别失败时使用的数值上限        |

- 上表两个 ROI 与 `tilt_angle` 写在 `StaminaInfo.Read.custom_recognition_param` 里；识别器内部的默认 ROI 是空值，不配置会告警并跳过。
- 若未配置 `current_roi` / `cap_roi`、ROI 宽高非正或超出截图范围，会告警并跳过 OCR，不中断任务链。
- `stamina_cap` 读取后会强制整数化校验，非法值告警并忽略。

## 回满时间计算

- 恢复速率：**4 分钟 / 1 点**（`STAMINA_RECOVER_MINUTES_PER_POINT`）。
- 未达上限：`missing = cap - current`，`full_time = now + missing * 4min`，输出对齐 MAA 风格：

    ```text
    体力将在 <YYYY-MM-DD HH:MM> 回满。(Xh Ym 后)
    ```

- 达到自然恢复上限后不再随时间增长，明确提示「已达自然恢复上限，不再随时间恢复」；超出上限（如领取体力道具导致当前 > 上限）则提示「已超出自然恢复上限，不再随时间恢复」。
- 任何读写失败都仅跳过本次输出，不影响其它任务。

## 代码位置

| 内容               | 路径                                                                  |
| ------------------ | --------------------------------------------------------------------- |
| 任务定义           | `tasks/stamina_info.json`                                             |
| Pipeline           | `resource/base/pipeline/stamina.json`                                 |
| Custom Recognition | `agent/custom/recognition/stamina.py`                                 |
| Recognition 注册   | `agent/custom/recognition/__init__.py`                                |
| 主页 / 返回模板    | `resource/base/image/more.png`、`resource/base/image/return_main.png` |

## 改动这类流程要动哪些文件

1. **体力数字位置变化**（换分辨率基准、UI 改版）：改 `StaminaInfo.Read.custom_recognition_param` 的 `current_roi` / `cap_roi` / `tilt_angle`
2. **恢复速率变化**（游戏改数值）：改 `agent/custom/recognition/stamina.py` 的 `STAMINA_RECOVER_MINUTES_PER_POINT`
3. **重试次数**：改 `StaminaInfo.ReadRetry` / `StaminaInfo.ClickHomeRetry` 的 `max_hit`（当前 2，即合计 3 次）
4. **路由目标**：`StaminaInfo.custom_recognition_param` 的 `home_next` / `other_next` 与 `StaminaInfo` 节点的静态
   `next` 要一起改（静态 `next` 是 `override_next` 的兜底，两处不一致时兜底路径会跑偏）
5. **主页判定**：复用 `more.png` 与 ROI `[1199,6,77,83]`，不要为本任务另造主页特征图
6. **校验**：`pnpm exec maa-tools check`、`pnpm check`；改过 agent 代码再跑 `pnpm check:py`

## 验收清单

改动本任务后按以下顺序验证：

1. 主界面直接运行：能读到体力与上限，日志输出回满时间与剩余时长
2. 不在主界面运行（如停在关卡界面）：先点主页按钮回到主界面再读取，不进入「读取 → 点主页」循环
3. 体力已满 / 超出上限两种状态：输出「已达自然恢复上限」类提示，不计算回满时间
4. OCR 读不到数字时：最多 3 次尝试后任务失败，不空转
5. 与其它任务串联：作为任务链最后一个任务运行时不影响前面任务的结果
