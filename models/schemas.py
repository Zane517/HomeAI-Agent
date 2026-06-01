"""
Pydantic 数据模型 — API 请求/响应、设备、场景定义
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


# ==================== 设备模型 ====================

class DeviceType(str, Enum):
    LIGHT = "light"
    SWITCH = "switch"
    CURTAIN = "curtain"
    AC = "ac"
    FAN = "fan"
    HUMIDIFIER = "humidifier"
    CAMERA = "camera"
    SENSOR = "sensor"
    SPEAKER = "speaker"
    OTHER = "other"


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class Device(BaseModel):
    id: str
    name: str
    type: DeviceType
    room: str = "默认房间"
    status: DeviceStatus = DeviceStatus.UNKNOWN
    properties: dict = Field(default_factory=dict)
    last_updated: Optional[datetime] = None


class DeviceAction(BaseModel):
    """单次设备操作指令"""
    device_id: str
    action: str  # e.g., "turn_on", "set_brightness", "set_temperature"
    params: dict = Field(default_factory=dict)


class DeviceActionResult(BaseModel):
    device_id: str
    success: bool
    message: str = ""
    new_state: dict = Field(default_factory=dict)


# ==================== 场景识别模型 ====================

class SceneInfo(BaseModel):
    """场景分析结果"""
    detected_behavior: str = ""  # e.g., "reading", "sleeping", "away"
    confidence: float = 0.0
    room: str = ""
    object_count: int = 0
    description: str = ""
    suggested_actions: list[DeviceAction] = Field(default_factory=list)


class SnapshotRequest(BaseModel):
    camera_id: Optional[str] = None
    room: Optional[str] = None


class SnapshotResult(BaseModel):
    image_base64: Optional[str] = None
    scene: Optional[SceneInfo] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ==================== 设备控制模型 ====================

class ControlRequest(BaseModel):
    """自然语言设备控制请求"""
    command: str  # e.g., "把客厅灯光调暗到 30%，打开空调设为 26 度"
    room: Optional[str] = None


class ControlPlan(BaseModel):
    """AI 生成的设备控制计划"""
    intent: str
    steps: list[DeviceAction]
    reasoning: str = ""


class ControlResult(BaseModel):
    plan: ControlPlan
    results: list[DeviceActionResult]
    summary: str = ""


# ==================== TTS 语音播报模型 ====================

class TTSRequest(BaseModel):
    text: str
    voice: str = "default"
    speed: float = 1.0
    volume: float = 1.0


class TTSResult(BaseModel):
    audio_base64: Optional[str] = None
    audio_url: Optional[str] = None
    duration_ms: int = 0


class BroadcastEvent(str, Enum):
    WEATHER = "weather"
    PACKAGE = "package"
    TEMP_ALERT = "temp_alert"
    HUMIDITY_ALERT = "humidity_alert"
    CUSTOM = "custom"


class BroadcastRequest(BaseModel):
    event: BroadcastEvent
    message: Optional[str] = None
    room: str = "客厅"


# ==================== 统一响应模型 ====================

class APIResponse(BaseModel):
    success: bool = True
    message: str = ""
    data: Optional[dict] = None
