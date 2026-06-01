"""
设备控制 API — 自然语言指令 → 设备控制
"""

from fastapi import APIRouter, HTTPException
from agents.control_agent import control_agent
from agents.core_agent import core_agent
from services.miot_service import miot_service
from models.schemas import ControlRequest, ControlResult, APIResponse

router = APIRouter(prefix="/control", tags=["设备控制"])


@router.post("/command", response_model=APIResponse)
async def natural_language_control(request: ControlRequest):
    """
    自然语言设备控制。
    
    示例: "把客厅灯调到50%，关闭空调，打开卧室风扇"
    """
    try:
        result = await core_agent.natural_language_control(
            request.command, room=request.room
        )
        return APIResponse(
            success=True,
            message=result.summary,
            data=result.model_dump(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设备控制失败: {str(e)}")


@router.get("/devices", response_model=APIResponse)
async def list_devices(room: str = None):
    """列出所有设备（可按房间过滤）"""
    try:
        devices = await miot_service.list_devices(room=room)
        return APIResponse(
            success=True,
            message=f"共 {len(devices)} 个设备" + (f"（{room}）" if room else ""),
            data={"devices": [d.model_dump() for d in devices]},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取设备列表失败: {str(e)}")


@router.get("/devices/{device_id}", response_model=APIResponse)
async def get_device(device_id: str):
    """获取单个设备详情"""
    device = await miot_service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"设备 {device_id} 未找到")
    return APIResponse(success=True, data={"device": device.model_dump()})


@router.get("/status", response_model=APIResponse)
async def full_status():
    """获取全系统状态"""
    try:
        status = await core_agent.full_status()
        return APIResponse(success=True, data=status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")


@router.get("/alerts", response_model=APIResponse)
async def check_alerts():
    """检查传感器告警"""
    try:
        alerts = await miot_service.check_alerts()
        return APIResponse(
            success=True,
            message=f"共 {len(alerts)} 条告警",
            data={"alerts": alerts},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查告警失败: {str(e)}")
