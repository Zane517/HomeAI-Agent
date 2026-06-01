"""
MiMo API 客户端 — 兼容 OpenAI 协议的统一调用层

支持三种模型能力：
- MiMo-V2-Omni   : 多模态视觉理解（图片→文本描述/场景分析）
- MiMo-V2-Pro    : 长上下文推理 + 工具调用（意图解析、设备指令规划）
- MiMo-V2.5-Pro  : 智能体编排（多步骤调度、Agent 工具编排）
- MiMo-V2-TTS    : 语音合成
"""

import base64
import json
from typing import Optional, AsyncIterator

from loguru import logger
from openai import AsyncOpenAI

from config import settings


class MiMoClient:
    """小米 MiMo API 统一客户端（兼容 OpenAI SDK）"""

    def __init__(self):
        self._client = AsyncOpenAI(
            api_key=settings.mimo_api_key,
            base_url=settings.mimo_base_url,
        )

    # ==================== 视觉理解 (Omni) ====================

    async def analyze_image(
        self,
        image_base64: str,
        prompt: str = "请详细描述这张图片中的场景、人物活动、物体状态和光线条件。",
        model: Optional[str] = None,
    ) -> str:
        """分析图片内容，返回场景描述"""
        model = model or settings.mimo_vision_model
        logger.debug(f"[MiMo-Omni] 分析图片, model={model}")

        response = await self._client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high",
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""

    async def detect_scene(
        self,
        image_base64: str,
        model: Optional[str] = None,
    ) -> str:
        """识别场景中的用户行为（读书、睡觉、离家等）"""
        model = model or settings.mimo_vision_model
        prompt = (
            "请分析这张室内画面，识别以下信息并以 JSON 格式返回：\n"
            "1. 用户当前行为（reading/sleeping/cooking/watching_tv/away/none）\n"
            "2. 所在房间\n"
            "3. 光线亮度（0-100）\n"
            "4. 建议触发的智能设备动作\n\n"
            "返回格式示例：\n"
            '{"behavior": "reading", "room": "客厅", "brightness": 45, '
            '"suggestions": ["调暗灯光至30%", "关闭电视"]}'
        )
        return await self.analyze_image(image_base64, prompt, model)

    # ==================== 意图推理 + 工具调用 (Pro) ====================

    async def parse_intent(
        self,
        user_command: str,
        available_devices: list[dict],
        model: Optional[str] = None,
    ) -> dict:
        """自然语言→设备控制计划的意图解析"""
        model = model or settings.mimo_reasoning_model
        logger.debug(f"[MiMo-Pro] 意图解析: '{user_command}'")

        system_prompt = (
            "你是一个智能家居控制助手。用户会用自然语言描述需求，"
            "你需要解析意图并生成设备控制指令列表。\n\n"
            f"当前可用设备：\n{json.dumps(available_devices, ensure_ascii=False, indent=2)}\n\n"
            "请分析用户的指令，返回分步骤的设备控制计划，格式为 JSON：\n"
            '{"intent": "...", "steps": [\n'
            '  {"device_id": "...", "action": "...", "params": {...}}\n'
            "], \"reasoning\": \"...\"}"
        )

        response = await self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_command},
            ],
            response_format={"type": "json_object"},
            max_tokens=2048,
        )

        try:
            return json.loads(response.choices[0].message.content or "{}")
        except json.JSONDecodeError:
            logger.warning("MiMo 返回内容不是有效 JSON，回退到原始文本")
            return {"intent": "unknown", "steps": [], "reasoning": response.choices[0].message.content}

    async def plan_scene_actions(
        self,
        scene_description: str,
        detected_behavior: str,
        available_devices: list[dict],
        model: Optional[str] = None,
    ) -> dict:
        """根据场景分析结果，规划设备联动动作"""
        model = model or settings.mimo_reasoning_model

        system_prompt = (
            "你是一个智能家居自动化编排引擎。根据场景分析结果，"
            "为检测到的用户行为规划合适的设备联动方案。\n\n"
            f"当前可用设备：\n{json.dumps(available_devices, ensure_ascii=False, indent=2)}\n\n"
            "返回 JSON 格式的设备控制指令列表。"
        )

        user_prompt = (
            f"场景描述：{scene_description}\n"
            f"检测到的行为：{detected_behavior}\n"
            "请规划合适的设备联动方案。"
        )

        response = await self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=2048,
        )

        try:
            return json.loads(response.choices[0].message.content or "{}")
        except json.JSONDecodeError:
            return {"steps": []}

    # ==================== Agent 编排 (2.5-Pro) ====================

    async def orchestrate(
        self,
        task: str,
        tools: list[dict],
        model: Optional[str] = None,
    ) -> str:
        """使用 2.5-Pro 进行多步骤 Agent 调度"""
        model = model or settings.mimo_orchestrator_model

        response = await self._client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是 HomeAI Agent 的核心调度器，负责协调视觉理解、"
                        "设备控制和语音播报三个子系统，完成用户的复杂家居自动化任务。"
                    ),
                },
                {"role": "user", "content": task},
            ],
            max_tokens=4096,
        )
        return response.choices[0].message.content or ""

    # ==================== 语音合成 (TTS) ====================

    async def text_to_speech(
        self,
        text: str,
        voice: str = "default",
        speed: float = 1.0,
        model: Optional[str] = None,
    ) -> Optional[str]:
        """文本转语音，返回 Base64 编码的音频"""
        model = model or settings.mimo_tts_model
        logger.debug(f"[MiMo-TTS] 合成语音, text_len={len(text)}")

        try:
            # MiMo TTS API (OpenAI 兼容 speech 接口)
            response = await self._client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                speed=speed,
                response_format="mp3",
            )
            audio_bytes = response.content
            return base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"TTS 合成失败: {e}")
            return None

    # ==================== 通用对话 ====================

    async def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        max_tokens: int = 2048,
    ) -> str:
        """通用对话接口"""
        model = model or settings.mimo_reasoning_model

        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def chat_stream(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """流式对话"""
        model = model or settings.mimo_reasoning_model

        stream = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# 全局单例
mimo_client = MiMoClient()
