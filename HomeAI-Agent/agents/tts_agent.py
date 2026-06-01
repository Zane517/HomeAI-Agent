"""
语音合成 Agent (MiMo-V2-TTS)

负责：文字→语音合成，主动播报事件（天气/快递/温湿度）
"""

from typing import Optional

from loguru import logger

from services.tts_service import tts_service
from services.miot_service import miot_service
from models.schemas import BroadcastEvent


class TTSAgent:
    """语音播报 Agent"""

    async def speak(self, text: str, voice: str = "default") -> Optional[str]:
        """合成指定文字的语音"""
        logger.info(f"TTSAgent: 合成语音 '{text[:30]}...'")
        return await tts_service.synthesize(text, voice=voice)

    async def weather_broadcast(self) -> Optional[str]:
        """天气提醒播报"""
        return await tts_service.broadcast_weather()

    async def package_broadcast(self) -> Optional[str]:
        """快递到达播报"""
        return await tts_service.broadcast_package_alert()

    async def sensor_alert_broadcast(self) -> list[str]:
        """检查传感器并播报异常"""
        alerts = await miot_service.check_alerts()
        results = []
        for alert in alerts:
            audio = await tts_service.custom_broadcast(alert)
            if audio:
                results.append(audio)
            logger.info(f"TTSAgent: 传感器告警 → {alert}")
        return results

    async def auto_check_and_broadcast(self) -> dict:
        """定时巡检：检查传感器 + 播报异常"""
        logger.info("TTSAgent: 定时巡检")
        audio_list = await self.sensor_alert_broadcast()
        return {
            "alerts_count": len(audio_list),
            "audio_files": len([a for a in audio_list if a]),
        }


# 全局单例
tts_agent = TTSAgent()
