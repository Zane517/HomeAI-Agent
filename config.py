"""
HomeAI Agent 全局配置管理
基于 pydantic-settings，支持 .env 文件和环境变量
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用全局配置"""

    # ---- MiMo API ----
    mimo_api_key: str = "your_mimo_api_key_here"
    mimo_base_url: str = "https://api.mimo.xiaomi.com/v1"

    # ---- Agent 模型 ----
    mimo_vision_model: str = "MiMo-V2-Omni"
    mimo_reasoning_model: str = "MiMo-V2-Pro"
    mimo_orchestrator_model: str = "MiMo-V2.5-Pro"
    mimo_tts_model: str = "MiMo-V2-TTS"

    # ---- 米家 IoT ----
    miot_app_id: str = ""
    miot_app_secret: str = ""
    miot_user_id: str = ""

    # ---- 摄像头 ----
    camera_rtsp_url: str = ""
    camera_capture_interval: int = 10

    # ---- 阈值 ----
    temp_high_threshold: float = 30.0
    temp_low_threshold: float = 10.0
    humidity_high_threshold: float = 80.0

    # ---- 通用 ----
    active_rooms: str = "客厅,卧室,书房"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @property
    def active_room_list(self) -> list[str]:
        return [r.strip() for r in self.active_rooms.split(",") if r.strip()]


# 全局单例
settings = Settings()
