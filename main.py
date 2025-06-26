import os
import shutil
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.logger_config import get_logger
from app.subtitle import generate_detailed_transcription
from utils import format_file_size, get_file_extension

# ——— 获取应用日志器 ———
logger = get_logger(__name__)

# ——— 目录配置 ———
# 确保必要的目录存在
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ——— 生命周期管理 ———
@asynccontextmanager
async def lifespan(_app: FastAPI):
    """应用程序生命周期管理"""
    startup_logger = get_logger("app.startup")
    shutdown_logger = get_logger("app.shutdown")

    # 启动时的操作
    startup_logger.info("🚀 字幕生成服务正在启动...")
    startup_logger.info(f"📁 上传目录: {UPLOAD_DIR}")

    # 这里可以添加模型预加载等初始化操作
    # 例如：预热Whisper模型，初始化音频分离器等

    startup_logger.info("✅ 字幕生成服务启动完成")

    yield  # 这里应用程序运行

    # 关闭时的操作
    shutdown_logger.info("🛑 字幕生成服务正在关闭...")
    shutdown_logger.info("✅ 字幕生成服务已关闭")


# ——— FastAPI 应用初始化 ———
app = FastAPI(
    title="智能字幕生成服务",
    description="基于Whisper的高精度音频转字幕服务，支持词级时间戳和人声分离预处理",
    version="2.0.0",
    docs_url="/docs",
    lifespan=lifespan,
)

# 创建带前缀的路由器
router = APIRouter(prefix="/whisper")

# ——— CORS 配置 ———
# 配置跨域资源共享，支持根据环境动态配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://subtitle.us4ever.com"],
    allow_methods=["*"],
    allow_headers=["*"]
)


class HelloWorld(BaseModel):
    service: str
    status: str
    version: str
    features: List[str]
    timestamp: str


class DetailedTranscriptionResponse(BaseModel):
    """详细转录响应模型"""
    segments: Optional[List[Dict[str, Any]]] = None
    language: Optional[str] = None
    language_probability: Optional[float] = None
    duration: Optional[float] = None
    duration_after_vad: Optional[float] = None
    srt_content: str
    vocal_separation_used: Optional[bool] = None
    processing_info: Optional[Dict[str, Any]] = None


# ——— 健康检查端点 ———
@router.get("/", summary="服务状态检查", response_model=HelloWorld)
async def root():
    """服务根端点，返回基本状态信息"""
    return {
        "service": "智能字幕生成服务",
        "status": "运行中",
        "version": "2.0.0",
        "features": ["SRT字幕生成", "词级时间戳", "人声分离预处理"],
        "timestamp": datetime.now().isoformat()
    }


# ——— API 端点 ———
@router.post(
    "/generate_subtitle",
    summary="生成字幕（支持详细模式和人声分离）",
    description="上传音频或视频文件生成字幕。支持传统SRT格式、包含词级时间戳的详细数据格式，以及可选的人声分离预处理。",
    tags=["Subtitle Generation"],
    response_model=DetailedTranscriptionResponse,
)
async def generate_subtitle_endpoint(
        file: UploadFile = File(description="需要生成字幕的音频或视频文件。"),
        enable_vocal_separation: bool = Form(
            default=False,
            description="是否启用人声与背景音分离预处理。True=先分离人声再转录（推荐），False=直接转录原始音频。"
        )
):
    api_logger = get_logger("api.generate_subtitle")

    # 验证文件
    if not file or not file.filename:
        api_logger.error("❌ 接收到无效的文件上传请求")
        raise HTTPException(status_code=400, detail="未提供有效的文件")

    # 记录请求信息
    file_size_display = format_file_size(file.size) if hasattr(file, 'size') and file.size else '未知'
    mode_desc = "详细模式（含词级时间戳）"
    vocal_sep_desc = "启用人声分离" if enable_vocal_separation else "禁用人声分离"
    api_logger.info(
        f"📥 收到字幕生成请求 - 文件: {file.filename}, 大小: {file_size_display}, {mode_desc}, {vocal_sep_desc}")

    temp_file_path = None

    try:
        start_time = time.time()

        # 生成临时文件名
        file_extension = get_file_extension(file.filename)
        temp_filename = f"subtitle_{uuid.uuid4().hex[:8]}{file_extension}"
        temp_file_path = os.path.join(UPLOAD_DIR, temp_filename)

        # 保存上传的文件
        api_logger.debug(f"保存临时文件: {temp_file_path}")
        with open(temp_file_path, "wb") as temp_file:
            shutil.copyfileobj(file.file, temp_file)

        # 验证保存的文件
        if not os.path.exists(temp_file_path) or os.path.getsize(temp_file_path) == 0:
            raise HTTPException(status_code=500, detail="文件保存失败")

        # 生成字幕
        api_logger.info("🔄 开始生成详细转录数据...")
        result = generate_detailed_transcription(temp_file_path, enable_vocal_separation)

        # 添加处理信息到结果中
        processing_time = time.time() - start_time
        result["processing_info"] = {
            "processing_time_seconds": round(processing_time, 2),
            "mode": "detailed",
            "vocal_separation_enabled": enable_vocal_separation,
            "file_name": file.filename,
            "file_size": file_size_display
        }

        api_logger.info(
            f"✅ 详细转录完成 - 用时: {processing_time:.2f}秒, 段落数: {len(result.get('segments', []))}")
        api_logger.info(
            f"✅ 详细转录完成 - 用时: {processing_time:.2f}秒, {result}")
        return result

    except Exception as e:
        api_logger.error(f"❌ 字幕生成失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"字幕生成过程中发生错误: {str(e)}"
        )

    finally:
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                api_logger.debug(f"已清理临时文件: {temp_file_path}")
            except Exception as e:
                api_logger.warning(f"清理临时文件失败: {temp_file_path} - {e}")


# 将路由器包含到主应用中
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
