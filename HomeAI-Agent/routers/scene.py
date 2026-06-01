"""
场景理解 API — 摄像头抓拍、场景分析
"""

from fastapi import APIRouter, HTTPException
from agents.vision_agent import vision_agent
from agents.core_agent import core_agent
from models.schemas import SnapshotRequest, APIResponse

router = APIRouter(prefix="/scene", tags=["场景理解"])


@router.post("/snapshot", response_model=APIResponse)
async def capture_and_analyze(request: SnapshotRequest = SnapshotRequest()):
    """
    抓拍当前摄像头画面，使用 MiMo-Omni 进行场景分析。
    
    - 识别用户行为（读书、睡觉、离家、看手机等）
    - 分析室内光线条件
    - 返回建议触发的设备联动方案
    """
    try:
        result = await vision_agent.capture_and_analyze(camera_id=request.camera_id)
        return APIResponse(
            success=result.scene is not None,
            message=f"检测行为: {result.scene.detected_behavior if result.scene else '无'}",
            data=result.model_dump(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"场景分析失败: {str(e)}")


@router.post("/scene-pipeline", response_model=APIResponse)
async def full_scene_pipeline():
    """
    完整场景感知闭环：
    抓拍 → 视觉分析 → 场景联动规划 → 自动执行设备控制
    """
    try:
        result = await core_agent.scene_pipeline()
        return APIResponse(success=True, message="场景闭环执行完成", data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"场景闭环失败: {str(e)}")


@router.post("/analyze", response_model=APIResponse)
async def analyze_image(image_base64: str):
    """传入 Base64 图片进行场景分析"""
    try:
        scene = await vision_agent.analyze_existing(image_base64)
        return APIResponse(
            success=True,
            message=f"检测行为: {scene.detected_behavior}",
            data=scene.model_dump(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片分析失败: {str(e)}")
