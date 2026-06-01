"""
设备控制 Agent (MiMo-V2-Pro)

负责：自然语言指令 → 意图解析 → 设备控制计划 → 执行
"""

from loguru import logger

from services.mimo_client import mimo_client
from services.miot_service import miot_service
from models.schemas import (
    ControlRequest,
    ControlPlan,
    ControlResult,
    DeviceAction,
    DeviceActionResult,
)


class ControlAgent:
    """自然语言设备控制 Agent"""

    async def execute_command(self, request: ControlRequest) -> ControlResult:
        """处理自然语言设备控制指令"""
        logger.info(f"ControlAgent: 收到指令 '{request.command}'")

        # 1. 获取可用设备列表
        devices = await miot_service.get_devices_for_ai()
        if not devices:
            return ControlResult(
                plan=ControlPlan(intent="", steps=[], reasoning="无可用设备"),
                results=[],
                summary="当前无在线设备",
            )

        # 2. MiMo-Pro 意图解析 → 设备控制计划
        plan_data = await mimo_client.parse_intent(request.command, devices)

        # 3. 构建控制计划
        plan = ControlPlan(
            intent=plan_data.get("intent", ""),
            steps=[
                DeviceAction(
                    device_id=s["device_id"],
                    action=s["action"],
                    params=s.get("params", {}),
                )
                for s in plan_data.get("steps", [])
            ],
            reasoning=plan_data.get("reasoning", ""),
        )

        # 4. 执行设备控制
        results = await miot_service.execute_plan(plan.steps)

        # 5. 生成摘要
        successes = sum(1 for r in results if r.success)
        summary = f"执行完成: {successes}/{len(results)} 成功"

        return ControlResult(plan=plan, results=results, summary=summary)

    async def execute_scene_actions(
        self, scene_description: str, detected_behavior: str
    ) -> list[DeviceActionResult]:
        """根据场景分析结果执行设备联动"""
        logger.info(f"ControlAgent: 场景联动 → {detected_behavior}")

        devices = await miot_service.get_devices_for_ai()
        plan_data = await mimo_client.plan_scene_actions(
            scene_description, detected_behavior, devices
        )

        actions = [
            DeviceAction(
                device_id=s["device_id"],
                action=s["action"],
                params=s.get("params", {}),
            )
            for s in plan_data.get("steps", [])
        ]

        return await miot_service.execute_plan(actions)


# 全局单例
control_agent = ControlAgent()
