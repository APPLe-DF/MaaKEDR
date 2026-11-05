---
order: 4
icon: ri:treasure-map-line
---

# 资源刷取协议

「资源刷取」与「剩余体力刷取」共用一条 pipeline（`resource/base/pipeline/farm_resources.json`）：
从主页进作战界面 → 选板块 / 资源类型 / 关卡 → 设快速战次数 → 开战循环 → 体力不足退出。
两个任务的区别只在选项树与默认的战斗模式。

## 任务入口

| 任务         | entry                      | 定义                                | 流程                                         | 默认勾选 | 选项                                          |
| ------------ | -------------------------- | ----------------------------------- | -------------------------------------------- | -------- | --------------------------------------------- |
| 资源刷取     | `FarmResources.EnsureHome` | `tasks/farm_resources.json`         | `resource/base/pipeline/farm_resources.json` | 是       | `farm_battle_mode`、`farm_category`           |
| 剩余体力刷取 | `FarmResources.EnsureHome` | `tasks/farm_remaining_stamina.json` | 同上                                         | 否       | `remaining_farm_category`（固定清空体力模式） |

## 数据链路

```text
tasks/farm_resources.json
  ├─ task 资源刷取：option = [farm_battle_mode, farm_category]
  └─ option 树（靠 case.option 逐层嵌套展开）
       farm_battle_mode ─┬─ 单次战斗 → farm_battle_count（1–6 次 / 最大）
                         └─ 清空体力 → 直接改 6 个节点
       farm_category ────┬─ 资源收集 → farm_resource_type → farm_resource_stage_1..4
                         └─ 技能演练 → farm_skill_type → farm_skill_stage_1..2
  → 覆盖落点：FarmResources.Start / SelectResourceType / SelectSkillType /
              ClickStage / ClickSkillStage / CheckSkillLocked /
              SetBattleCount / QuickBattle / CheckStamina / BattleStage / ExitStageConfirm
  → resource/base/pipeline/farm_resources.json
  → agent/custom/action/farm_resources.py（SetBattleCount、ReduceBattleCount）
     agent/custom/recognition/farm_resources.py（CheckResourceStage）
```

## 选项结构

```text
farm_battle_mode（战斗模式）
  ├─ 单次战斗 → farm_battle_count（1–6 次 / 最大）
  └─ 清空体力 → pipeline_override（最大次数 + 减次数 + 退出路径）

farm_category（刷取板块）
  ├─ 资源收集 → farm_resource_type → farm_resource_stage_1~4
  └─ 技能演练 → farm_skill_type → farm_skill_stage_1~2
```

## 选项与覆盖

| 选项                       | 控件   | 默认                  | 覆盖的节点                                                                                                                            | 覆盖内容                                                                                                                              |
| -------------------------- | ------ | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `farm_battle_mode`         | select | 单次战斗              | 清空体力 case 改 `FarmResources.QuickBattle` / `ClickStage` / `ClickSkillStage` / `CheckStamina` / `BattleStage` / `ExitStageConfirm` | 见「战斗模式 · 清空体力」                                                                                                             |
| `farm_battle_count`        | select | 1次                   | `FarmResources.SetBattleCount`                                                                                                        | `custom_action_param.target_count` = `1`–`6` 或 `"max"`                                                                               |
| `farm_category`            | select | 资源收集              | `FarmResources.Start`                                                                                                                 | `next` = `[FarmResources.ResourceCollect]` / `[FarmResources.SkillTraining]`                                                          |
| `farm_resource_type`       | select | 特别军费行动          | `FarmResources.SelectResourceType`                                                                                                    | `next` 指向 `SelectSpecialFunds` / `SelectPhysicalTraining` / `SelectUnitRating` / `SelectVehicleDrill`                               |
| `farm_skill_type`          | select | 基础技能演练          | `FarmResources.SelectSkillType`                                                                                                       | `next` 指向 `SelectBasicSkill` / `SelectAdvancedSkill`                                                                                |
| `farm_resource_stage_1..4` | select | 1-1 / 2-1 / 3-1 / 4-1 | `FarmResources.ClickStage`（第 4、5 关另加 `FarmResources.SelectStage`）                                                              | `custom_recognition_param` = `stage_name` / `stage_index` / `resource_type`；4/5 关加 `next → SwipeToRight`                           |
| `farm_skill_stage_1..2`    | select | 基础训练1 / 专业训练1 | `FarmResources.ClickSkillStage`、`FarmResources.CheckSkillLocked`、`FarmResources.SelectSkillStage`                                   | `ClickSkillStage` 的 `roi` + `expected`；2/3 号另给 `CheckSkillLocked.roi`；1 号另把 `SelectSkillStage.next` 收成 `[ClickSkillStage]` |

## 剩余体力刷取

| 项       | 值                                                                              |
| -------- | ------------------------------------------------------------------------------- |
| 任务名   | 剩余体力刷取                                                                    |
| entry    | `FarmResources.EnsureHome`（复用刷取流程入口）                                  |
| 定义     | `tasks/farm_remaining_stamina.json`                                             |
| 选项     | `remaining_farm_category` 起的独立选项树（`remaining_*` 前缀）                  |
| 覆盖方式 | **任务级** `pipeline_override`（不随选项变化），内容与「清空体力」case 完全一致 |

固定为「清空体力」模式的资源刷取：任务级 `pipeline_override` 直接携带最大次数（`SetBattleCountMax`）、体力不足减次数（`CheckStamina → CheckCountOCR / ReduceCount`）与退出路径。选项用一套与「资源刷取」**各自独立**的 `remaining_farm_category`（刷取板块 → 资源类型 → 关卡），用于榨干执行到此步时的剩余体力，通常在任务预设中启用，默认不勾选。

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

`CheckResourceStage`（`agent/custom/recognition/farm_resources.py`）按 `resource_type` + `stage_index` 查内置 ROI 表
（`RESOURCE_STAGES`）定位关卡卡片，再 OCR `stage_name` 确认；`stage_index > 1` 时会先在该 ROI 内查锁定图标
（`lock_template`，默认 `farm_resources/lock_icon.png`），命中则路由到 `FarmResources.StageLocked`。

第 4、5 关（可见需要滑动时）会对 `SelectStage` 注入 `next → SwipeToRight`；进入关卡选择前 `SelectStage` 默认先走
`SwipeToBegin` 把列表复位到最左。

## 技能演练

| 类型         | stage 选项           | 关卡名示例   |
| ------------ | -------------------- | ------------ |
| 基础技能演练 | `farm_skill_stage_1` | 基础训练 1–3 |
| 专业技能演练 | `farm_skill_stage_2` | 专业训练 1–3 |

通过 `ClickSkillStage` 的 ROI + OCR `expected` 定位（基础值 `expected: "farm_stage"` 是占位，实际值由选项注入）；锁定态用 `CheckSkillLocked` 的 `skill_lock_icon.png` 模板判定，其 ROI 同样由选项按关卡注入。

`SelectSkillStage` 的 `next` 采用**并列候选**（`CheckSkillLocked` → `ClickSkillStage`）：命中锁图标=锁定停止，未命中=自动回落到 `ClickSkillStage` 点击进入；不在候选节点上依赖 `on_error` 兜底（候选识别失败不触发自身 on_error，会导致死循环超时，见 `docs/*/develop/pipeline.md`）。选择第 1 关时选项会把 `SelectSkillStage.next` 收成 `[ClickSkillStage]`，跳过锁定判定。

## 战斗模式

> **终止语义**：两种模式都以「体力不足」为最终终止条件。`BattleStage` 战斗循环结束后回到关卡界面，若体力仍足以继续，会再次进入下一场战斗；直到 `CheckStamina` 命中「体力不足」弹窗（或快速战按钮消失走退出路径）才收尾。

### 单次战斗

`QuickBattle` → `SetBattleCount`（按选项 `target_count`）→ `PrepareBattle` → 体力检测 → 开战 → `BattleStage` 循环。

战斗次数选项控制的是**每次开战批次**的场次数；任务整体会刷到体力不足（`no_stamina` 弹窗）为止，而非严格刷满 N 场即停。

### 清空体力

`pipeline_override` 改这 6 个节点：

| 节点                             | 覆盖后 `next`                                                                                                                                                               |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FarmResources.QuickBattle`      | `[FarmResources.SetBattleCountMax]`                                                                                                                                         |
| `FarmResources.ClickStage`       | `[FarmResources.QuickBattle, FarmResources.SetBattleCountMax]`                                                                                                              |
| `FarmResources.ClickSkillStage`  | `[FarmResources.QuickBattle, FarmResources.SetBattleCountMax]`                                                                                                              |
| `FarmResources.CheckStamina`     | `[FarmResources.CheckCountOCR, FarmResources.ReduceCount]`                                                                                                                  |
| `FarmResources.BattleStage`      | `[[JumpBack]FarmResources.ClickVictory, [JumpBack]FarmResources.ClickItemDialog, FarmResources.QuickBattle, FarmResources.ReturnMainFromFarm, FarmResources.PrepareBattle]` |
| `FarmResources.ExitStageConfirm` | `[FarmResources.ReturnMainFromFarm, Common.CheckHomePage]`                                                                                                                  |

减次数循环：体力不足 → `ReduceCount`（`ReduceBattleCount`，每次只减 1）→ 回 `PrepareBattle` 重试；
`CheckCountOCR` 用 OCR `^1$` 判断次数已到 1 → `ReductionDone` → `ExitStageConfirm` 退出。
`ReduceCount` 已到最小次数时动作返回失败，`on_error` 指向 `FarmResources.NoStamina` 同样走退出。

与单次战斗的区别：体力不足时**逐步减次**（每次减 1，直到次数为 1 后经 `ReductionDone` 退出），尽量榨干剩余体力；单次战斗则在体力不足时直接退出，剩余不足一场的体力会被浪费。

## 任务前置条件

任务以 `FarmResources.EnsureHome` 为入口（恒命中门节点）：开始前通常应处于游戏主界面。未确认到主页时，由通用回主页枢纽 `Common.EnsureHome` 接管——依次尝试关闭「获得物品」弹窗、点击顶部主页按钮、点击通用返回按钮；回到主页后自动重试原流程，因此任务入口本身不会因为「不在主页」而失败。枢纽最多尝试 10 轮，仍无法回到主页时任务才会失败。

`FarmResources.Start`（从主页进作战界面）识别失败时，`on_error` 也指向 `FarmResources.EnsureHome`，即回主页后重跑整条列表。

## 关键节点

| 节点                                                   | 识别 / 动作                                                    | 说明                                                                    |
| ------------------------------------------------------ | -------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `FarmResources.EnsureHome`                             | DirectHit（`max_hit: 6`）                                      | 任务入口门节点，`next` 末位挂 `[JumpBack]Common.EnsureHome`             |
| `FarmResources.CheckHomePage`                          | TemplateMatch `more.png` / Click                               | 确认主页并点屏幕中心，消除残留弹窗                                      |
| `FarmResources.Start`                                  | TemplateMatch `battle_entry.png` / Click                       | 从主页进作战界面；`on_error` → `EnsureHome`                             |
| `FarmResources.ResourceCollect` / `SkillTraining`      | 页签模板 / Click                                               | 进入「资源收集」/「技能演练」板块                                       |
| `FarmResources.SelectResourceType` / `SelectSkillType` | DirectHit                                                      | 纯路由节点，`next` 由选项改写                                           |
| `FarmResources.SelectSpecialFunds` 等 4 个             | 模板 / Click                                                   | 选资源类型（特别军费行动 / 作战体能训练 / 兵种能力评级 / 载具对抗演练） |
| `FarmResources.SelectStage`                            | DirectHit                                                      | 纯路由节点；4/5 关由选项注入 `next → SwipeToRight`                      |
| `FarmResources.SwipeToBegin` / `SwipeToRight`          | DirectHit / Swipe                                              | 关卡列表复位到最左 / 滑到最右                                           |
| `FarmResources.ClickStage`                             | Custom `CheckResourceStage` / Click（`timeout: 10000`）        | 识别并点击关卡；`on_error` → `StageLocked`                              |
| `FarmResources.SelectSkillStage`                       | DirectHit                                                      | 技能关卡选择入口（并列候选 `CheckSkillLocked` → `ClickSkillStage`）     |
| `FarmResources.CheckSkillLocked`                       | TemplateMatch `skill_lock_icon.png`                            | 命中=关卡锁定停止，未命中=可点                                          |
| `FarmResources.ClickSkillStage`                        | OCR `expected`（选项注入）/ Click                              | 点击技能关卡                                                            |
| `FarmResources.QuickBattle`                            | TemplateMatch `quick_battle.png` / Click（`max_hit: 3`）       | 点快速战斗；`on_error` → `QuickBattleLocked`                            |
| `FarmResources.SetBattleCount`                         | Custom `SetBattleCount`                                        | 点加减号设置次数                                                        |
| `FarmResources.SetBattleCountMax`                      | Custom `SetBattleCount`（`target_count: "max"`）               | 设最大次数（清空体力模式）                                              |
| `FarmResources.PrepareBattle`                          | TemplateMatch `prepare_battle.png` / Click                     | 点准备快速战斗                                                          |
| `FarmResources.CheckStamina`                           | TemplateMatch `no_stamina.png` / Click                         | 无体力弹窗                                                              |
| `FarmResources.ReduceCount`                            | Custom `ReduceBattleCount`                                     | 体力不足时减次数；`on_error` → `NoStamina`                              |
| `FarmResources.CheckCountOCR`                          | OCR `^1$`                                                      | 次数已到 1（减次数循环的终止条件）                                      |
| `FarmResources.ReductionDone`                          | DirectHit                                                      | 已减到最小 → `ExitStageConfirm`                                         |
| `FarmResources.NoStamina`                              | DirectHit                                                      | 体力不足 → `ExitStageConfirm`                                           |
| `FarmResources.ExitStageConfirm`                       | TemplateMatch `exit_stage_confirm.png` / Click（`max_hit: 5`） | 点关卡界面退出键；`on_error` → `[JumpBack]Common.EnsureHome`            |
| `FarmResources.ReturnMainFromFarm`                     | TemplateMatch `return_main.png` / Click                        | 回主页                                                                  |
| `FarmResources.StartBattle` / `BattleStage`            | 模板 / DirectHit                                               | 开战、战斗循环父节点                                                    |
| `FarmResources.ClickVictory` / `ClickItemDialog`       | 模板 / Click                                                   | 胜利画面 / 获得物品弹窗                                                 |
| `FarmResources.StageLocked` / `QuickBattleLocked`      | DirectHit                                                      | 锁定提示（`focus` 措辞刻意中性，避免 GUI 误判任务失败）                 |

Custom 实现：`SetBattleCount`、`ReduceBattleCount` 在 `agent/custom/action/farm_resources.py`；
`CheckResourceStage` 在 `agent/custom/recognition/farm_resources.py`，并在对应 `__init__.py` 注册。

## 改动这类流程要动哪些文件

1. **新增同板块关卡**：在 `agent/custom/recognition/farm_resources.py` 的 `RESOURCE_STAGES` 里给该板块补
   `关卡序号 → ROI`，再在 `tasks/farm_resources.json` 的 `farm_resource_stage_N.cases` 加一项
   （`stage_name` / `stage_index` / `resource_type` 三件套）
2. **新增板块**：`RESOURCE_STAGES` 加板块键 → `farm_resource_type.cases` 加一项并让
   `SelectResourceType.next` 指向新节点 → pipeline 里补该板块的入口模板节点
3. **新增技能关卡**：`farm_skill_stage_N.cases` 加一项，写 `ClickSkillStage.roi` + `expected`；
   有锁定态再补 `CheckSkillLocked.roi`
4. **同步「剩余体力刷取」**：`tasks/farm_remaining_stamina.json` 有一套独立的 `remaining_*` 选项树，
   新增关卡/板块必须**两处都加**，否则该任务选不到新关卡
5. **改战斗次数选项**：`farm_battle_count.cases` 的 `custom_action_param.target_count`（`1`–`6` 或 `"max"`）
6. **改清空体力逻辑**：同时改 `farm_resources` 的「清空体力」case 与 `farm_remaining_stamina` 的任务级
   `pipeline_override`（两处内容当前完全一致）
7. **校验**：`pnpm exec maa-tools check`、`pnpm check`；改过 agent 代码再跑 `pnpm check:py`

## 图片目录

`resource/base/image/farm_resources/`（入口、快速战、准备、胜利、锁定等）：

- 入口与页签：`battle_entry.png`、`resource_collect_tab.png`、`skill_training_tab.png`
- 资源类型：`special_funds.png`、`physical_training.png`、`unit_rating.png`、`vehicle_drill.png`
- 技能类型：`basic_skill.png`、`advanced_skill.png`、`skill_lock_icon.png`
- 战斗流程：`quick_battle.png`、`prepare_battle.png`、`start_battle.png`、`battle_victory.png`、`exit_stage_confirm.png`、`no_stamina.png`
- 次数设置：`max_count.png`（「最大」按钮）、`lock_icon.png`（资源关卡锁定图标）

## 验收清单

改动本任务后按以下顺序验证：

1. 四个资源板块各选一个关卡单独跑一遍（含需滑动选关的 4/5 关）
2. 单次战斗模式端到端跑一遍，确认按选项次数收尾
3. 清空体力模式跑一遍：体力不足时减次数、减到 1 后正常退出
4. 战斗中胜利画面 / 物品弹窗 / 快速战按钮分别验证
5. 关卡锁定态（灰色文字）验证：正确提示未解锁而非卡死
6. 技能演练两个类型各跑一遍，确认 `expected` 与锁定 ROI 生效
7. 「剩余体力刷取」用它的 `remaining_*` 选项各选一个关卡跑通
8. 全量回归：与其它任务（启动、领取奖励、PVP）组合跑一遍无冲突
