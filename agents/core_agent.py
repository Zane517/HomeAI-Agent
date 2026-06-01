"""
核心调度 Agent (MiMo-V2.5-Pro)

统一管理多模态请求分发、设备指令编排、执行结果反馈。
是所有 Agent 的入口，负责协调 Vision → Control → TTS 的完整闭环。
"""

from typing import Optional

from loguru import logger

from services.mimo_client import mimo_client
from agents.vision_agent import vision_agent
from agents.control_agent import control_agent
from agents.tts_agent import tts_agent
from models.schemas import (
    SnapshotResult,
    ControlRequest,
    ControlResult,
    BroadcastEvent,
    SceneInfo,
    DeviceAction,
)


class CoreAgent:
    """核心调度 Agent — 智能家居的总控大脑"""

    # ==================== 场景感知闭环 ====================

    async def scene_pipeline(self) -> dict:
        """
        完整的 "看 → 想 → 控" 闭环：
        1. 摄像头抓拍
        2. MiMo-Omni 视觉分析
        3. MiMo-Pro 场景联动规划
        4. 执行设备控制
        """
        logger.info("=== CoreAgent: 启动场景感知闭环 ===")

        # Step 1: 抓拍 + 视觉分析
        snapshot = await vision_agent.capture_and_analyze()
        if not snapshot.scene or not snapshot.scene.detected_behavior:
            return {
                "success": True,
                "stage": "vision_only",
                "snapshot": snapshot.model_dump(),
                "message": "未检测到需触发的行为",
            }

        scene = snapshot.scene
        logger.info(f"检测到行为: {scene.detected_behavior} (置信度: {scene.confidence})")

        # Step 2: 场景联动规划 + 执行
        actions = []
        if scene.detected_behavior != "none":
            results = await control_agent.execute_scene_actions(
                scene.description, scene.detected_behavior
            )
            actions = [r.model_dump() for r in results]

        # Step 3: 播报（如有必要）
        audio = None
        if scene.detected_behavior == "away":
            audio = await tts_agent.speak("已检测到您离开家，已自动关闭所有设备。")

        return {
            "success": True,
            "stage": "full_pipeline",
            "scene": scene.model_dump(),
            "actions": actions,
            "audio": audio is not None,
        }

    # ==================== 自然语言控制 ====================

    async def natural_language_control(
        self, command: str, room: Optional[str] = None
    ) -> ControlResult:
        """自然语言一句话控制全屋设备"""
        logger.info(f"CoreAgent: NL控制 → '{command}'")
        request = ControlRequest(command=command, room=room)
        return await control_agent.execute_command(request)

    # ==================== 定时巡检 ====================

    async def patrol(self) -> dict:
        """定时巡检：传感器检查 + 异常播报"""
        logger.info("CoreAgent: 定时巡检")

        # 检查传感器
        result = await tts_agent.auto_check_and_broadcast()
        return {"success": True, **result}

    # ==================== 对话式交互 ====================

    async def chat(self, user_message: str) -> str:
        """对话式智能家居问答"""
        prompt = (
            "你是 HomeAI 智能家居管家。请用自然、友好的语气回答用户问题。"
            "你可以帮助用户：查询设备状态、控制家电、设置场景、检查环境数据等。"
        )
        response = await mimo_client.chat(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_message},
            ],
            model=None,  # 使用默认 orchestrator 模型
        )
        return response

    # ==================== 全量状态 ====================

    async def full_status(self) -> dict:
        """获取系统全量状态"""
        from services.miot_service import miot_service
        from services.camera_service import camera_service

        devices = await miot_service.list_devices()
        sensors = await miot_service.read_sensors()
        alerts = await miot_service.check_alerts()
        last_snapshot = camera_service.get_last_image_base64()

        return {
            "devices_count": len(devices),
            "online_count": sum(1 for d in devices if d.status == "online"),
            "devices": [d.model_dump() for d in devices],
            "sensors": sensors,
            "alerts": alerts,
            "has_recent_snapshot": last_snapshot is not None,
        }


# 全局单例
core_agent = CoreAgent()
