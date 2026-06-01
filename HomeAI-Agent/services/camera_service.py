"""
摄像头服务 — 抓拍室内画面并转换为 Base64 供 MiMo-Omni 分析

支持：
- RTSP / ONVIF 协议接入米家摄像头
- 定时抓拍 + 按需抓拍
- 图片 Base64 编码
"""

import base64
import io
import asyncio
from typing import Optional

from loguru import logger
from PIL import Image

from config import settings


class CameraService:
    """摄像头管理服务"""

    def __init__(self):
        self.rtsp_url = settings.camera_rtsp_url
        self.capture_interval = settings.camera_capture_interval
        self._last_capture: Optional[bytes] = None
        self._capture_task: Optional[asyncio.Task] = None

    async def capture_snapshot(self) -> Optional[bytes]:
        """
        从摄像头抓拍一帧画面
        
        尝试顺序：RTSP → 本地摄像头(OpenCV) → 回退到模拟图像
        
        Returns:
            图片 JPEG 字节数据，失败返回 None
        """
        # 尝试 OpenCV RTSP 拉流
        try:
            import cv2
            cap = cv2.VideoCapture(self.rtsp_url)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    self._last_capture = buffer.tobytes()
                    logger.debug(f"摄像头抓拍成功, size={len(self._last_capture)} bytes")
                    return self._last_capture
        except ImportError:
            logger.debug("OpenCV 未安装，跳过 RTSP 抓拍")
        except Exception as e:
            logger.warning(f"RTSP 抓拍失败: {e}")

        # 回退：本地摄像头
        try:
            import cv2
            cap = cv2.VideoCapture(0)  # 默认摄像头
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    self._last_capture = buffer.tobytes()
                    logger.debug("本地摄像头抓拍成功")
                    return self._last_capture
        except Exception as e:
            logger.warning(f"本地摄像头抓拍失败: {e}")

        # 最终回退：生成纯色测试图片
        logger.info("无可用摄像头，生成测试图片")
        return self._generate_test_image()

    def _generate_test_image(self, width: int = 640, height: int = 480) -> bytes:
        """生成模拟测试图片（灰色背景 + 时间戳文字）"""
        try:
            from PIL import Image, ImageDraw, ImageFont

            img = Image.new("RGB", (width, height), color=(60, 60, 60))
            draw = ImageDraw.Draw(img)
            draw.text(
                (width // 2 - 100, height // 2 - 10),
                "HomeAI Camera Test",
                fill=(255, 255, 255),
            )
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            return buffer.getvalue()
        except Exception:
            # 最简回退
            img = Image.new("RGB", (width, height), color=(128, 128, 128))
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            return buffer.getvalue()

    def image_to_base64(self, image_bytes: bytes) -> str:
        """将图片字节转换为 Base64 字符串"""
        return base64.b64encode(image_bytes).decode("utf-8")

    async def capture_and_encode(self) -> Optional[str]:
        """抓拍并返回 Base64 编码"""
        img_bytes = await self.capture_snapshot()
        if img_bytes:
            return self.image_to_base64(img_bytes)
        return None

    async def start_periodic_capture(self, interval: Optional[int] = None):
        """启动定时抓拍（后台任务）"""
        if self._capture_task and not self._capture_task.done():
            return

        interval = interval or self.capture_interval
        if interval <= 0:
            return

        async def _capture_loop():
            logger.info(f"启动定时抓拍, interval={interval}s")
            while True:
                try:
                    await self.capture_snapshot()
                    logger.debug("定时抓拍成功")
                except Exception as e:
                    logger.error(f"定时抓拍异常: {e}")
                await asyncio.sleep(interval)

        self._capture_task = asyncio.create_task(_capture_loop())

    def get_last_image_base64(self) -> Optional[str]:
        """获取最近一次抓拍的 Base64"""
        if self._last_capture:
            return self.image_to_base64(self._last_capture)
        return None


# 全局单例
camera_service = CameraService()
