"""
TTS 语音播报服务

封装 MiMo-TTS，提供主动播报能力。
支持天气提醒、快递到达、温湿度异常等场景的语音播报。
"""

from typing import Optional

from loguru import logger

from services.mimo_client import mimo_client
from models.schemas import BroadcastEvent


# 场景播报模板
_BROADCAST_TEMPLATES: dict[BroadcastEvent, str] = {
    BroadcastEvent.WEATHER: "今日天气提醒：请根据需要携带雨具，注意出行安全。",
    BroadcastEvent.PACKAGE: "您好，有快递已送达，请及时取件。",
    BroadcastEvent.TEMP_ALERT: "温馨提醒：当前室温偏高，建议开启空调降温。",
    BroadcastEvent.HUMIDITY_ALERT: "温馨提醒：当前湿度较高，建议开启除湿模式。",
    BroadcastEvent.CUSTOM: "",
}


class TTSService:
    """语音合成与播报服务"""

    def __init__(self):
        self._audio_cache: dict[str, str] = {}  # text → base64 cache

    async def synthesize(
        self, text: str, voice: str = "default", speed: float = 1.0
    ) -> Optional[str]:
        """合成语音，返回 Base64 音频"""
        cache_key = f"{text}:{voice}:{speed}"
        if cache_key in self._audio_cache:
            return self._audio_cache[cache_key]

        audio = await mimo_client.text_to_speech(text, voice=voice, speed=speed)
        if audio:
            self._audio_cache[cache_key] = audio
        return audio

    async def broadcast(
        self,
        event: BroadcastEvent,
        message: Optional[str] = None,
        voice: str = "default",
    ) -> Optional[str]:
        """播报指定事件类型的语音"""
        text = message or _BROADCAST_TEMPLATES.get(event, "")
        if not text:
            logger.warning(f"事件 {event} 无播报内容")
            return None

        logger.info(f"播报: [{event.value}] {text[:30]}...")
        return await self.synthesize(text, voice=voice)

    async def broadcast_weather(self) -> Optional[str]:
        """天气提醒播报"""
        return await self.broadcast(BroadcastEvent.WEATHER)

    async def broadcast_package_alert(self) -> Optional[str]:
        """快递到达提醒"""
        return await self.broadcast(BroadcastEvent.PACKAGE)

    async def broadcast_temp_alert(self, temperature: float) -> Optional[str]:
        """温度异常警告"""
        text = f"温馨提示：当前室温 {temperature} 度，请注意调节温度。"
        return await self.broadcast(BroadcastEvent.TEMP_ALERT, message=text)

    async def broadcast_humidity_alert(self, humidity: float) -> Optional[str]:
        """湿度异常警告"""
        text = f"温馨提示：当前湿度 {humidity}%，建议开启除湿。"
        return await self.broadcast(BroadcastEvent.HUMIDITY_ALERT, message=text)

    async def custom_broadcast(self, text: str, voice: str = "default") -> Optional[str]:
        """自定义语音播报"""
        return await self.broadcast(BroadcastEvent.CUSTOM, message=text, voice=voice)


# 全局单例
tts_service = TTSService()
