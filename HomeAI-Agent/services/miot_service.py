"""
米家 IoT 设备控制服务

提供统一的设备状态查询和指令下发接口。
实际部署时配置米家开放平台凭证即可对接真实设备；
开发阶段提供模拟设备用于测试。
"""

import asyncio
import hashlib
import hmac
import time
from typing import Optional

import httpx
from loguru import logger

from config import settings
from models.schemas import (
    Device,
    DeviceType,
    DeviceStatus,
    DeviceAction,
    DeviceActionResult,
)


# ==================== 模拟设备数据（开发/测试用） ====================

_MOCK_DEVICES: list[Device] = [
    Device(id="light_living_01", name="客厅主灯", type=DeviceType.LIGHT, room="客厅",
           status=DeviceStatus.ONLINE, properties={"power": "on", "brightness": 80, "color_temp": 4000}),
    Device(id="light_living_02", name="客厅灯带", type=DeviceType.LIGHT, room="客厅",
           status=DeviceStatus.ONLINE, properties={"power": "off", "brightness": 50, "color": "#FF9900"}),
    Device(id="light_bedroom_01", name="卧室吸顶灯", type=DeviceType.LIGHT, room="卧室",
           status=DeviceStatus.ONLINE, properties={"power": "off", "brightness": 60}),
    Device(id="light_study_01", name="书房台灯", type=DeviceType.LIGHT, room="书房",
           status=DeviceStatus.ONLINE, properties={"power": "on", "brightness": 70, "color_temp": 3500}),
    Device(id="ac_living_01", name="客厅空调", type=DeviceType.AC, room="客厅",
           status=DeviceStatus.ONLINE, properties={"power": "off", "temperature": 24, "mode": "cool"}),
    Device(id="curtain_living_01", name="客厅窗帘", type=DeviceType.CURTAIN, room="客厅",
           status=DeviceStatus.ONLINE, properties={"position": 100}),
    Device(id="fan_bedroom_01", name="卧室风扇", type=DeviceType.FAN, room="卧室",
           status=DeviceStatus.OFFLINE, properties={"power": "off", "speed": 0}),
    Device(id="sensor_temp_01", name="客厅温湿度计", type=DeviceType.SENSOR, room="客厅",
           status=DeviceStatus.ONLINE, properties={"temperature": 26.5, "humidity": 55}),
    Device(id="speaker_living_01", name="客厅小爱音箱", type=DeviceType.SPEAKER, room="客厅",
           status=DeviceStatus.ONLINE, properties={"volume": 40}),
]


class MiOTService:
    """米家 IoT 设备服务"""

    def __init__(self):
        self._http_client: Optional[httpx.AsyncClient] = None
        self._mock_devices: dict[str, Device] = {d.id: d for d in _MOCK_DEVICES}

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=15.0)
        return self._http_client

    # ==================== 设备查询 ====================

    async def list_devices(self, room: Optional[str] = None) -> list[Device]:
        """列出所有设备，可按房间过滤"""
        devices = list(self._mock_devices.values())
        if room:
            devices = [d for d in devices if d.room == room]
        logger.debug(f"列出设备: {len(devices)} 个" + (f" (房间: {room})" if room else ""))
        return devices

    async def get_device(self, device_id: str) -> Optional[Device]:
        """获取单个设备信息"""
        return self._mock_devices.get(device_id)

    async def get_devices_for_ai(self) -> list[dict]:
        """返回 AI 友好的设备列表（简化版）"""
        return [
            {
                "id": d.id,
                "name": d.name,
                "type": d.type.value,
                "room": d.room,
                "properties": d.properties,
            }
            for d in self._mock_devices.values()
            if d.status == DeviceStatus.ONLINE
        ]

    # ==================== 设备控制 ====================

    async def execute_action(self, action: DeviceAction) -> DeviceActionResult:
        """执行单次设备操作"""
        device = self._mock_devices.get(action.device_id)
        if not device:
            return DeviceActionResult(
                device_id=action.device_id,
                success=False,
                message=f"设备 {action.device_id} 未找到",
            )

        action_name = action.action.lower()
        new_state = dict(device.properties)

        try:
            if action_name == "turn_on":
                new_state["power"] = "on"
            elif action_name == "turn_off":
                new_state["power"] = "off"
            elif action_name == "set_brightness":
                brightness = int(action.params.get("brightness", 50))
                new_state["brightness"] = max(0, min(100, brightness))
            elif action_name == "set_temperature":
                temp = float(action.params.get("temperature", 24))
                new_state["temperature"] = temp
            elif action_name == "set_mode":
                new_state["mode"] = action.params.get("mode", "auto")
            elif action_name == "set_color_temp":
                new_state["color_temp"] = int(action.params.get("color_temp", 4000))
            elif action_name == "set_volume":
                vol = int(action.params.get("volume", 30))
                new_state["volume"] = max(0, min(100, vol))
            elif action_name == "set_position":
                pos = int(action.params.get("position", 100))
                new_state["position"] = max(0, min(100, pos))
            elif action_name == "set_speed":
                speed = int(action.params.get("speed", 1))
                new_state["speed"] = max(0, min(5, speed))
            elif action_name == "set_color":
                new_state["color"] = action.params.get("color", "#FFFFFF")
            else:
                # 透传自定义参数
                for k, v in action.params.items():
                    new_state[k] = v

            # 更新模拟设备状态
            device.properties = new_state
            logger.info(f"执行设备操作: {device.name} → {action_name}")

            return DeviceActionResult(
                device_id=action.device_id,
                success=True,
                message=f"{device.name} 操作成功",
                new_state=new_state,
            )
        except Exception as e:
            logger.error(f"设备操作失败: {e}")
            return DeviceActionResult(
                device_id=action.device_id, success=False, message=str(e)
            )

    async def execute_plan(self, actions: list[DeviceAction]) -> list[DeviceActionResult]:
        """执行一系列设备操作"""
        results = []
        for action in actions:
            result = await self.execute_action(action)
            results.append(result)
            await asyncio.sleep(0.2)  # 避免并发冲突
        return results

    # ==================== 传感器读取 ====================

    async def read_sensors(self, room: Optional[str] = None) -> list[dict]:
        """读取传感器数据"""
        sensors = [
            {
                "id": d.id,
                "name": d.name,
                "room": d.room,
                "temperature": d.properties.get("temperature"),
                "humidity": d.properties.get("humidity"),
            }
            for d in self._mock_devices.values()
            if d.type == DeviceType.SENSOR
            and (room is None or d.room == room)
        ]
        return sensors

    async def check_alerts(self) -> list[str]:
        """检查是否需要触发告警（温湿度异常等）"""
        alerts = []
        sensors = await self.read_sensors()
        for s in sensors:
            temp = s.get("temperature")
            humidity = s.get("humidity")
            if temp is not None:
                if temp > settings.temp_high_threshold:
                    alerts.append(f"{s['room']} 温度偏高: {temp}°C")
                elif temp < settings.temp_low_threshold:
                    alerts.append(f"{s['room']} 温度偏低: {temp}°C")
            if humidity is not None and humidity > settings.humidity_high_threshold:
                alerts.append(f"{s['room']} 湿度过高: {humidity}%")
        return alerts


# 全局单例
miot_service = MiOTService()
