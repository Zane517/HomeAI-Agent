"""
语音播报 API — TTS 合成、主动播报
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import base64

from agents.tts_agent import tts_agent
from agents.core_agent import core_agent
from models.schemas import TTSRequest, BroadcastRequest, BroadcastEvent, APIResponse

router = APIRouter(prefix="/tts", tags=["语音播报"])


@router.post("/synthesize", response_model=APIResponse)
async def synthesize_speech(request: TTSRequest):
    """文字转语音"""
    try:
        audio = await tts_agent.speak(request.text, voice=request.voice)
        if not audio:
            raise HTTPException(status_code=500, detail="语音合成失败")
        return APIResponse(
            success=True,
            message="语音合成成功",
            data={"audio_base64": audio},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 合成失败: {str(e)}")


@router.post("/broadcast", response_model=APIResponse)
async def broadcast_event(request: BroadcastRequest):
    """
    语音播报特定事件类型。
    
    支持: weather(天气), package(快递), temp_alert(温度告警), humidity_alert(湿度告警), custom(自定义)
    """
    try:
        if request.event == BroadcastEvent.CUSTOM:
            if not request.message:
                raise HTTPException(status_code=400, detail="自定义播报需要提供 message")
            audio = await tts_agent.speak(request.message)
        else:
            from services.tts_service import tts_service
            audio = await tts_service.broadcast(request.event, message=request.message)

        if not audio:
            raise HTTPException(status_code=500, detail="播报合成失败")
        return APIResponse(
            success=True,
            message=f"播报 {request.event} 成功",
            data={"audio_base64": audio},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"播报失败: {str(e)}")


@router.post("/patrol", response_model=APIResponse)
async def patrol():
    """定时巡检：检查传感器并播报异常"""
    try:
        result = await core_agent.patrol()
        return APIResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"巡检失败: {str(e)}")
