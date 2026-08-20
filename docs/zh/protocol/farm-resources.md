---
order: 4
icon: ri:treasure-map-line
---

# 资源刷取协议

## 任务入口

| 项     | 值                                           |
| ------ | -------------------------------------------- |
| 任务名 | 资源刷取                                     |
| entry  | `FarmResources.CheckHomePage`                |
| 定义   | `tasks/farm_resources.json`                  |
| 流程   | `resource/base/pipeline/farm_resources.json` |

## 选项结构

```text
farm_battle_mode（战斗模式）
  ├─ 单次战斗 → farm_battle_count（1–6 / 最大）
  └─ 清空体力 → pipeline_override（最大次数 + 减次数 + 退出路径）

farm_category（刷取板块）
  ├─ 资源收集 → farm_resource_type → farm_resource_stage_1~4
  └─ 技能演练 → farm_skill_type → farm_skill_stage_1~2
```

## 剩余体力刷取

| 项     | 值                                            |
| ------ | --------------------------------------------- |
| 任务名 | 剩余体力刷取                                  |
| entry  | `FarmResources.CheckHomePage`（复用刷取流程） |
| 定义   | `tasks/farm_remaining_stamina.json`           |

固定为「清空体力」模式的资源刷取：任务级 `pipeline_override` 直接携带最大次数（`SetBattleCountMax`）、体力不足减次数（`CheckStamina → CheckCountOCR / ReduceCount`）与退出路径。使用一套与「资源刷取」**各自独立**的选项 `remaining_farm_category`（刷取板块 → 资源类型 → 关卡），用于榨干执行到此步时的剩余体力，通常在任务预设中启用，默认不勾选。

## 资源收集关卡

| 类型         | stage 选项 key          | 关卡编号约定               |
| ------------ | ----------------------- | -------------------------- |
| 特别军费行动 | `farm_resource_stage_1` | **1-1 ~ 1-5**（有第 5 关） |
| 作战体能训练 | `farm_resource_stage_2` | **2-1 ~ 2-4**（无第 5 关） |
| 兵种能力评级 | `farm_resource_stage_3` | **3-1 ~ 3-4**（无第 5 关） |
| 载具对抗演练 | `farm_resource_stage_4` | **4-1 ~ 4-5**（有第 5 关） |

关卡选择通过 `FarmResources.ClickStage` 的 `custom_recognition_param` 传入：

```json
{
    "stage_name": "1-1",
    "stage_index": 1,
    "resource_type": "特别军费行动"
}
```

第 4、5 关（可见需要滑动时）会对 `SelectStage` 注入 `next → SwipeToRight`。

## 技能演练

| 类型         | stage 选项           | 关卡名示例   |
| ------------ | -------------------- | ------------ |
| 基础技能演练 | `farm_skill_stage_1` | 基础训练 1–3 |
| 专业技能演练 | `farm_skill_stage_2` | 专业训练 1–3 |

通过 `ClickSkillStage` 的 ROI + OCR `expected` 定位；锁定态用 `CheckSkillLocked`。

## 战斗模式

> **终止语义**：两种模式都以「体力不足」为最终终止条件。`BattleStage` 战斗循环结束后回到关卡界面，若体力仍足以继续，会再次进入下一场战斗；直到 `CheckStamina` 命中「体力不足」弹窗（或快速战按钮消失走退出路径）才收尾。

### 单次战斗

`QuickBattle` → `SetBattleCount`（按选项 target_count）→ `PrepareBattle` → 体力检测 → 开战 → `BattleStage` 循环。

战斗次数选项控制的是**每次开战批次**的场次数；任务整体会刷到体力不足（`no_stamina` 弹窗）为止，而非严格刷满 N 场即停。

### 清空体力

`pipeline_override` 将：

- `QuickBattle.next` → `SetBattleCountMax`
- `CheckStamina.next` → `CheckCountOCR` / `ReduceCount`（体力不足时减次数再试）
- `BattleStage` 增加回主页 / 再准备等兜底
- 退出走 `ExitStageConfirm` → `ReturnMainFromFarm`

与单次战斗的区别：体力不足时**逐步减次**（每次减 1，直到次数为 1 后经 `ReductionDone` 退出），尽量榨干剩余体力；单次战斗则在体力不足时直接退出，剩余不足一场的体力会被浪费。

## 任务前置条件

任务以 `FarmResources.CheckHomePage` 为入口：开始前通常应处于游戏主界面。若主页识别失败，Pipeline 会通过 `FarmResources.ReturnToHome` 尝试识别并点击返回按钮，再回到主页重新检查；如果仍无法确认主页，任务才会失败。

## 关键节点

| 节点                     | 作用                         |
| ------------------------ | ---------------------------- |
| `SetBattleCount`         | Custom：点加减设置次数       |
| `SetBattleCountMax`      | Custom：设为最大             |
| `ReduceCount`            | Custom：体力不足时减次数     |
| `CheckStamina`           | 无体力弹窗                   |
| `BattleStage`            | 胜利用 / 物品弹窗 / 再快速战 |
| `ClickVictory`           | 胜利画面                     |
| `ClickItemDialog`        | 获得物品                     |
| `StageLocked` / 锁定提示 | 关卡或快速战未解锁           |

Custom 实现：`agent/custom/` 下与 `SetBattleCount`、`ReduceBattleCount`、关卡识别等相关模块。

## 图片目录

`resource/base/image/farm_resources/`（入口、快速战、准备、胜利、锁定等）。

## 验收清单

改动本任务后按以下顺序验证：

1. 四个资源板块各选一个关卡单独跑一遍（含需滑动选关的 4/5 关）
2. 单次战斗模式端到端跑一遍，确认按选项次数收尾
3. 清空体力模式跑一遍：体力不足时减次数、减到 1 后正常退出
4. 战斗中胜利画面 / 物品弹窗 / 快速战按钮分别验证
5. 关卡锁定态（灰色文字）验证：正确提示未解锁而非卡死
6. 全量回归：与其它任务（启动、领取奖励、PVP）组合跑一遍无冲突
