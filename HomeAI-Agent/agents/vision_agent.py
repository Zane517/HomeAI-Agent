"""
视觉理解 Agent (MiMo-V2-Omni)

负责：连接摄像头抓拍 → MiMo-Omni 分析画面 → 输出场景描述与行为识别
"""

import json
from typing import Optional

from loguru import logger

from services.mimo_client import mimo_client
from services.camera_service import camera_service
from models.schemas import SceneInfo, SnapshotResult


class VisionAgent:
    """视觉场景理解 Agent"""

    async def capture_and_analyze(self, camera_id: Optional[str] = None) -> SnapshotResult:
        """抓拍并分析当前室内场景"""
        logger.info("VisionAgent: 开始抓拍并分析场景")

        # 1. 抓拍
        img_base64 = await camera_service.capture_and_encode()
        if not img_base64:
            logger.warning("摄像头抓拍失败")
            return SnapshotResult()

        # 2. MiMo-Omni 场景分析
        scene_json = await mimo_client.detect_scene(img_base64)

        # 3. 解析 AI 返回的 JSON
        scene = self._parse_scene(scene_json)

        return SnapshotResult(
            image_base64=img_base64,
            scene=scene,
        )

    async def analyze_existing(self, image_base64: str) -> SceneInfo:
        """分析已有的图片（不抓拍）"""
        scene_json = await mimo_client.detect_scene(image_base64)
        return self._parse_scene(scene_json)

    def _parse_scene(self, ai_response: str) -> SceneInfo:
        """解析 AI 返回的场景 JSON"""
        try:
            data = json.loads(ai_response)
            return SceneInfo(
                detected_behavior=data.get("behavior", "none"),
                confidence=data.get("confidence", 0.5),
                room=data.get("room", ""),
                object_count=data.get("object_count", 0),
                description=data.get("description", ai_response),
                suggested_actions=data.get("suggestions", [])
                or data.get("suggested_actions", []),
            )
        except (json.JSONDecodeError, TypeError):
            # 非 JSON 格式 → 当作纯文本描述
            return SceneInfo(
                description=ai_response,
                detected_behavior="none",
            )


# 全局单例
vision_agent = VisionAgent()
