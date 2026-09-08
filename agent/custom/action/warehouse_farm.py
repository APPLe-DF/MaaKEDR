from __future__ import annotations

import json
import math
import time
from typing import Any

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
from maa.define import OCRResult
from maa.pipeline import JOCR, JRecognitionType
from utils import logger
from utils.maa_types import all_results_as
from utils.params import parse_params
from utils.runtime_paths import get_runtime_paths

# ---------------------------------------------------------------------------
# 数据文件（用户可编辑）：材料 -> 刷取来源（关卡 + 掉落 + 快速战斗标记）
# 见 config/warehouse_farm_data.json
# ---------------------------------------------------------------------------
_DATA_PATH = "config/warehouse_farm_data.json"
_SNAPSHOT_PATH = "config/warehouse_inventory.json"

# 材料顺序（即刷取顺序）
_MATERIAL_ORDER = [
    "第二版能元",
    "训练用器材",
    "低级考核材料自选包",
    "中级考核材料自选包",
    "高级考核材料自选包",
    "基础技能材料自选包",
    "优秀毕业证书",
]

# 每场快速战斗最大次数（面板 1/2/3 刻度，按 6 场一批）
_MAX_BATCH = 6
# 单材料安全上限（防数据错误导致的死循环）
_MAX_RUNS_PER_MATERIAL = 300
# 体力低于该值视为不足，直接结束任务（最小关卡消耗约 30）
_MIN_STAMINA = 30
# 主界面体力显示区域（"377/415"）
_STAMINA_ROI = (850, 30, 120, 35)


def _read_json(path: str) -> dict[str, Any] | None:
    file_path = get_runtime_paths().project_root / path
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        logger.error(f"读取 {path} 失败: {error}")
        return None
    return data if isinstance(data, dict) else None


def _read_snapshot() -> dict[str, int]:
    data = _read_json(_SNAPSHOT_PATH)
    counts = (data or {}).get("counts", {})
    return {name: int(value) for name, value in counts.items() if isinstance(value, (int, float))}


def _read_materials() -> dict[str, Any]:
    data = _read_json(_DATA_PATH)
    return (data or {}).get("materials", {})


def _parse_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None
    return None


def _parse_stamina(text: str) -> int | None:
    """从 OCR 文本中提取体力值（取最长数字组）。"""
    import re

    groups = re.findall(r"\d+", text.replace(",", ""))
    if not groups:
        return None
    return int(max(groups, key=len))


@AgentServer.custom_action("WarehouseFarmBattle")
class WarehouseFarmBattle(CustomAction):
    """智能均衡刷取：按材料顺序刷到用户设定的目标库存。

    数据来源 config/warehouse_farm_data.json（关卡/掉落/快速战斗标记，用户可编辑）：
    - 每个材料选择其来源中「单场主目标掉落最多且已启用快速战斗」的关卡；
    - 一关掉落多种材料时，模拟剩余数量同步累加（顺带获得同样计入进度）；
    - quick_battle=false 的来源（技能演练占位，账号尚未解锁快速战斗）跳过并提示；
    - 每场刷取后检查主界面体力：体力不足 < 阈值时立即结束全部刷取返回主页；
    - 刷取复用 FarmResources 全流程（run_task 逐场执行）。
    """

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        try:
            targets_raw = parse_params(argv.custom_action_param).get("targets", {})
        except ValueError as error:
            logger.error("WarehouseFarmBattle: {}", error)
            return CustomAction.RunResult(success=False)

        materials = _read_materials()
        if not materials:
            logger.error(f"数据文件缺失或为空: {_DATA_PATH}")
            return CustomAction.RunResult(success=False)

        targets: dict[str, int | None] = {}
        for name in _MATERIAL_ORDER:
            if name not in targets_raw:
                logger.warning(f"材料 {name} 未配置目标数量，跳过")
                continue
            value = _parse_int(targets_raw[name])
            if value is None or value < 0:
                logger.warning(f"材料 {name} 目标数量非法: {targets_raw[name]!r}，跳过")
                continue
            targets[name] = value
        if not targets:
            logger.error("没有任何有效的目标数量配置，终止")
            return CustomAction.RunResult(success=False)

        counts = _read_snapshot()
        if not counts:
            logger.error(f"仓库数量快照为空（{_SNAPSHOT_PATH}，WarehouseInventoryScan 未成功执行）")
            return CustomAction.RunResult(success=False)

        if self._read_stamina(context) is None:
            logger.info("主界面体力 OCR 不可用，跳过体力预检")

        plan: list[dict[str, Any]] = []
        for name in _MATERIAL_ORDER:
            target = targets.get(name)
            if target is None:
                continue
            current = counts.get(name, 0)
            gap = target - current
            if gap <= 0:
                logger.info(f"{name} 当前 {current} 已达目标 {target}，无需刷取")
                continue
            source = self._pick_source(name, materials.get(name, {}))
            if source is None:
                logger.warning(f"{name} 无可刷取来源（快速战斗未解锁或掉落未填），跳过")
                continue
            runs = max(math.ceil(gap / source["drops"].get(name, 0)), 1)
            plan.append(
                {
                    "name": name,
                    "current": current,
                    "target": target,
                    "gap": gap,
                    "runs": int(runs),
                    "source": source,
                }
            )
            logger.info(
                f"{name} 当前 {current} 目标 {target} 缺口 {gap}，"
                f"选择 {source_info(source)}，计划刷 {runs} 场"
            )

        if not plan:
            logger.info("所有材料均已达标，本次无需刷取")
            return CustomAction.RunResult(success=True)

        remaining_counts = dict(counts)
        successes: list[str] = []
        stopped = False
        for item in plan:
            if stopped:
                break
            name = item["name"]
            source = item["source"]
            remaining = int(item["runs"])
            done = 0
            while remaining > 0 and done < _MAX_RUNS_PER_MATERIAL:
                if self._confirm_stamina(context):
                    logger.warning("体力不足，立即结束刷取并返回主页")
                    stopped = True
                    break
                batch = min(remaining, _MAX_BATCH)
                self._apply_navigation_override(context, source)
                self._apply_battle_count(context, batch)
                logger.info(f"{name} 刷取批次: {batch} 场（剩余 {remaining}）")
                detail = context.run_task("FarmResources.Start")
                if detail is None or detail.status.failed:
                    logger.error(f"{name} 刷取批次失败，剩余 {remaining} 场不再继续")
                    stopped = True
                    break
                # 顺带掉落同样计入模拟剩余数量
                for drop_name, drop_value in source["drops"].items():
                    if drop_value and drop_name in remaining_counts:
                        remaining_counts[drop_name] = int(remaining_counts[drop_name]) + int(drop_value) * batch
                remaining -= batch
                done += batch
                if self._confirm_stamina(context):
                    logger.warning("体力不足，立即结束刷取并返回主页")
                    stopped = True
                    break
                if remaining_counts.get(name, 0) >= item["target"]:
                    remaining = 0
            successes.append(f"{name}x{done}场")

        summary = {
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "plan": [
                {"name": item["name"], "current": item["current"], "target": item["target"], "runs": item["runs"]}
                for item in plan
            ],
            "completed": successes,
            "estimated_counts": {
                name: remaining_counts.get(name, 0) for name in _MATERIAL_ORDER if name in remaining_counts
            },
            "stopped_early": stopped,
        }
        out_path = get_runtime_paths().project_root / "config" / "warehouse_farm_result.json"
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(summary, indent=4, ensure_ascii=False), encoding="utf-8")
        except OSError as error:
            logger.error(f"写入刷取结果失败: {out_path}, {error}")

        logger.info(f"刷取完成（提前结束={stopped}）: {successes}")
        return CustomAction.RunResult(success=True)

    def _pick_source(self, name: str, material: dict[str, Any]) -> dict[str, Any] | None:
        """选出主目标单场掉落最多且未被显式禁用的来源；无则返回 None。

        quick_battle 字段可选：仅当显式设置为 false 时禁用该来源
        （未设置视为可用），方便用户在数据文件中手动排除某个关卡。
        """
        best: dict[str, Any] | None = None
        best_drop = 0
        for source in material.get("sources", []):
            if not isinstance(source, dict):
                continue
            if source.get("quick_battle") is False:
                continue
            drop = _parse_int(source.get("drops", {}).get(name))
            if drop is None or drop <= 0:
                continue
            if drop > best_drop:
                best = source
                best_drop = drop
        return best

    def _confirm_stamina(self, context: Context) -> bool:
        """OCR 主界面体力数字：低于阈值返回 True（体力不足）。"""
        stamina = self._read_stamina(context)
        if stamina is None:
            return False
        return stamina < _MIN_STAMINA

    def _read_stamina(self, context: Context) -> int | None:
        image = context.tasker.controller.cached_image or context.tasker.controller.post_screencap().wait().get()
        detail = context.run_recognition_direct(
            JRecognitionType.OCR,
            JOCR(expected=[], roi=_STAMINA_ROI),
            image,
        )
        text = "".join(result.text or "" for result in all_results_as(detail, OCRResult))
        stamina = _parse_stamina(text)
        logger.debug(f"主界面体力 OCR: '{text}' -> {stamina}")
        return stamina

    def _apply_navigation_override(self, context: Context, source: dict[str, Any]) -> None:
        """按来源设置关卡导航参数（板块入口 + 关卡识别）。"""
        overrides: dict[str, Any] = {}
        if source.get("kind") == "resource":
            tab = {
                "特别军费行动": "FarmResources.SelectSpecialFunds",
                "作战体能训练": "FarmResources.SelectPhysicalTraining",
                "兵种能力评级": "FarmResources.SelectUnitRating",
                "载具对抗演练": "FarmResources.SelectVehicleDrill",
            }.get(source.get("resource_type", ""))
            if tab:
                overrides["FarmResources.SelectResourceType"] = {"next": [tab]}
            overrides["FarmResources.ClickStage"] = {
                "custom_recognition_param": json.dumps(
                    {
                        "stage_name": source["stage_name"],
                        "stage_index": source["stage_index"],
                        "resource_type": source["resource_type"],
                    },
                    ensure_ascii=False,
                )
            }
            overrides["FarmResources.Start"] = {"next": ["FarmResources.ResourceCollect"]}
        else:
            skill_type = source.get("skill_type")
            type_next = "FarmResources.SelectAdvancedSkill" if skill_type == "advanced" else "FarmResources.SelectBasicSkill"
            overrides["FarmResources.Start"] = {"next": ["FarmResources.SkillTraining"]}
            overrides["FarmResources.SelectSkillType"] = {"next": [type_next]}
            overrides["FarmResources.ClickSkillStage"] = {
                "roi": source["stage_roi"],
                "expected": source["expected"],
            }
            lock_roi = source.get("lock_roi")
            if lock_roi:
                # 有锁定检查区域：先检查锁定，未命中再点击
                overrides["FarmResources.SelectSkillStage"] = {
                    "next": ["FarmResources.CheckSkillLocked", "FarmResources.ClickSkillStage"]
                }
                overrides["FarmResources.CheckSkillLocked"] = {"roi": lock_roi}
            else:
                overrides["FarmResources.SelectSkillStage"] = {
                    "next": ["FarmResources.ClickSkillStage"]
                }
            # 技能演练无「快速战斗」入口按钮，点卡片后直接设置次数并准备
            overrides["FarmResources.ClickSkillStage"].update(
                {"next": ["FarmResources.SetBattleCount"]}
            )
        context.override_pipeline(overrides)

    def _apply_battle_count(self, context: Context, batch: int) -> None:
        """设置快速战斗次数（完整参数，避免覆盖丢字段）。"""
        context.override_pipeline(
            {
                "FarmResources.SetBattleCount": {
                    "custom_action_param": {
                        "target_count": batch,
                        "count_roi": [903, 441, 27, 43],
                        "plus_button": [1086, 470],
                        "minus_button": [739, 470],
                        "max_template": "farm_resources/max_count.png",
                    }
                }
            }
        )


def source_info(source: dict[str, Any]) -> str:
    """来源的人类可读描述（日志用）。"""
    if source.get("kind") == "resource":
        stage = source.get("stage_name", "?")
        return f"{source.get('resource_type', '?')} {stage}"
    return f"技能演练 {source.get('expected', '?')}"
