# HomeAI Agent

基于 **小米 MiMo-V2.5 系列模型** 的全模态智能家居管家中控系统。

将 MiMo 模型的视觉理解、智能体推理与语音合成能力，与米家 IoT 生态深度整合，实现从"语音指令"到"主动理解"的智能家居体验升级。

> 🚀 本项目正在申请 [Xiaomi MiMo Orbit 百万亿 Token 创造者激励计划](https://100t.xiaomimimo.com/)。

---

## ✨ 核心功能

| 功能模块 | 描述 | 使用的 MiMo 模型 |
|---------|------|-----------------|
| **智能场景理解** | 连接米家摄像头，定时抓拍室内画面，自动识别用户行为（读书、睡觉、离家等）并触发相应设备联动 | MiMo-V2-Omni（多模态视觉理解） |
| **自然语言设备控制** | 用户用自然语言描述需求（如"看书时调暗灯光"），系统自动进行意图解析、多步骤规划，并映射为米家控制指令 | MiMo-V2-Pro（长上下文推理 + Agent 工具调用） |
| **个性化语音播报** | 主动播报天气提醒、快递到达、温湿度异常等信息，支持自定义音色 | MiMo-V2-TTS（语音合成） |
| **核心调度 Agent** | 统一管理多模态请求的分发、设备指令编排、执行结果反馈，保证复杂场景的健壮性 | MiMo-V2.5-Pro（智能体编排） |

---

## 🧠 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                     HomeAI Agent                        │
├─────────────────────────────────────────────────────────┤
│  FastAPI REST API                                       │
│  /scene/*    /control/*    /tts/*    /chat              │
├──────────┬──────────┬──────────┬───────────────────────┤
│ Vision   │ Control  │ TTS      │ Core Orchestrator     │
│ Agent    │ Agent    │ Agent    │ Agent                 │
│ (Omni)   │ (Pro)    │ (TTS)    │ (2.5-Pro)             │
├──────────┼──────────┼──────────┼───────────────────────┤
│              MiMo API Client (OpenAI SDK)               │
├──────────┼──────────┼──────────┼───────────────────────┤
│ Camera   │ MIoT     │ TTS      │                       │
│ Service  │ Service  │ Service  │                       │
└──────────┴──────────┴──────────┴───────────────────────┘
```

**技术栈**：Python + FastAPI + OpenAI SDK（MiMo 兼容）+ Pydantic + Loguru

---

## 📁 项目结构

```
HomeAI-Agent/
├── main.py                    # FastAPI 入口
├── config.py                  # 全局配置（pydantic-settings）
├── requirements.txt
├── .env.example               # 环境变量模板
├── agents/                    # Agent 层
│   ├── core_agent.py          # 核心调度 Agent（MiMo-V2.5-Pro）
│   ├── vision_agent.py        # 视觉理解 Agent（MiMo-V2-Omni）
│   ├── control_agent.py       # 设备控制 Agent（MiMo-V2-Pro）
│   └── tts_agent.py           # 语音播报 Agent（MiMo-V2-TTS）
├── services/                  # 服务层
│   ├── mimo_client.py         # MiMo API 客户端（OpenAI SDK 兼容）
│   ├── camera_service.py      # 摄像头抓拍服务
│   ├── miot_service.py        # 米家 IoT 设备控制服务
│   └── tts_service.py         # TTS 语音合成服务
├── models/                    # 数据模型
│   └── schemas.py             # Pydantic 请求/响应模型
├── routers/                   # API 路由
│   ├── scene.py               # 场景理解端点
│   ├── control.py             # 设备控制端点
│   └── tts.py                 # 语音播报端点
└── utils/                     # 工具
    └── helpers.py             # 日志、异常处理
```

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- 小米 MiMo API Key（[开放平台申请](https://mimo.xiaomi.com)）
- （可选）米家摄像头 RTSP 地址、米家开放平台凭证

### 安装

```bash
git clone https://github.com/Zane517/HomeAI-Agent.git
cd HomeAI-Agent
pip install -r requirements.txt
```

### 配置

```bash
cp .env.example .env
# 编辑 .env，填入 MiMo API Key 等信息
```

最少只需配置 `MIMO_API_KEY` 即可启动，设备层内置模拟数据供开发测试。

### 启动

```bash
python main.py
# 访问 http://localhost:8000/docs 查看 Swagger API 文档
```

---

## 📡 API 概览

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务信息 |
| `/health` | GET | 健康检查 |
| `/scene/snapshot` | POST | 摄像头抓拍 + 场景分析 |
| `/scene/scene-pipeline` | POST | 完整"看→想→控"闭环 |
| `/scene/analyze` | POST | 传入图片进行场景分析 |
| `/control/command` | POST | 自然语言设备控制 |
| `/control/devices` | GET | 设备列表（可按房间过滤） |
| `/control/devices/{id}` | GET | 单个设备详情 |
| `/control/status` | GET | 全系统状态 |
| `/control/alerts` | GET | 传感器告警检查 |
| `/tts/synthesize` | POST | 文字转语音 |
| `/tts/broadcast` | POST | 事件播报（天气/快递/温湿度） |
| `/tts/patrol` | POST | 定时巡检 + 异常播报 |
| `/chat` | POST | 对话式智能家居问答 |

---

## 🔌 模型接入

MiMo API 兼容 OpenAI 协议，本项目使用 OpenAI Python SDK 统一调用：

```python
from services.mimo_client import mimo_client

# 视觉理解
description = await mimo_client.analyze_image(image_base64)

# 意图解析
plan = await mimo_client.parse_intent("把客厅灯调暗", devices)

# 语音合成
audio = await mimo_client.text_to_speech("您好，欢迎回家")
```

---

## 🏠 模拟设备

无米家硬件时，`miot_service.py` 内置 9 个虚拟设备：

| 设备 | 房间 |
|------|------|
| 客厅主灯、灯带、空调、窗帘、温湿度计、小爱音箱 | 客厅 |
| 卧室吸顶灯、风扇 | 卧室 |
| 书房台灯 | 书房 |

无需任何额外配置即可测试全部 API 功能。

---

## 📄 License

MIT License
