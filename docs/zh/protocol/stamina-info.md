---
order: 7
icon: ri:heart-pulse-line
---

# 体力信息协议

本页记录「体力信息」任务：在任务链末尾读取主界面体力并输出自然回满时间。任务定义位于 `tasks/stamina_info.json`，入口 `StaminaInfo`，默认勾选并置于任务链末尾。

## 任务入口与选项

| 任务     | 入口          | 选项                         |
| -------- | ------------- | ---------------------------- |
| 体力信息 | `StaminaInfo` | 无（读取固定 ROI，默认执行） |

## 流程

```text
StaminaInfo →（确认主页）→ StaminaInfo.Read → 输出回满信息
            └─（不在主页）→ StaminaInfo.ClickHome → StaminaInfo
```

关键约定：

- `StaminaInfo` 用模板 `main_option.png` 确认主界面；匹配失败且 `timeout`（60s）内未到主页时，`StaminaInfo.ClickHome` 点击主页按钮返回后重新确认，保证任务从主页读取体力。
- `StaminaInfo.Read` 使用自定义识别 `ReadStamina`（`agent/custom/recognition/stamina.py`）。

## ReadStamina 识别约定

主界面体力数字以 **-45° 倾斜** 显示，`ReadStamina` 会对两个 ROI 分别按 `tilt_angle`（默认 `-45`，纠正角取其相反数旋转扶正）后再 OCR，提取第一个整数：

| 参数          | 默认值                | 说明                                          |
| ------------- | --------------------- | --------------------------------------------- |
| `current_roi` | `[1120, 512, 38, 44]` | 当前体力数字 ROI                              |
| `cap_roi`     | `[1152, 484, 28, 30]` | 体力上限数字 ROI                              |
| `tilt_angle`  | `-45`                 | 屏幕上数字的倾斜角（兼容旧名 `rotate_angle`） |
| `stamina_cap` | 无                    | 可选兜底：上限识别失败时使用的数值上限        |

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
