import asyncio
import logging
import os
import shutil
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
    
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.logger_config import get_logger
from app.subtitle import generate_srt

# ——— 获取应用日志器 ———
logger = get_logger(__name__)


# ——— 工具函数 ———
def format_file_size(size_bytes: int) -> str:
    """
    将字节数转换为人类可读的文件大小格式
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        str: 格式化后的文件大小字符串
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    size_index = 0
    size_value = float(size_bytes)
    
    while size_value >= 1024 and size_index < len(size_names) - 1:
        size_value /= 1024
        size_index += 1
    
    # 根据大小选择合适的小数位数
    if size_index == 0:  # 字节
        return f"{int(size_value)} {size_names[size_index]}"
    elif size_value >= 100:  # 大于100的显示1位小数
        return f"{size_value:.1f} {size_names[size_index]}"
    else:  # 小于100的显示2位小数
        return f"{size_value:.2f} {size_names[size_index]}"


# ——— 全局变量 ———
TEMP_DIR = "temp"  # 临时文件存储目录


# ——— 应用生命周期管理 ———
@asynccontextmanager
async def lifespan(_app: FastAPI):
    """应用生命周期管理器，在应用启动时创建临时目录并启动后台清理任务。"""
    logger.info("🚀 FastAPI 应用正在启动...")

    # 创建临时目录
    try:
        os.makedirs(TEMP_DIR, exist_ok=True)
        logger.info(f"📁 临时目录已创建: {os.path.abspath(TEMP_DIR)}")
    except Exception as e:
        logger.error(f"❌ 创建临时目录失败: {e}")
        raise

    # 启动后台清理任务
    try:
        cleanup_task = asyncio.create_task(cleanup_temp_files())
        logger.info("🧹 后台清理任务已启动，每小时清理一次临时文件")
    except Exception as e:
        logger.error(f"❌ 启动清理任务失败: {e}")
        raise

    logger.info("✅ 应用启动完成，服务已就绪")

    yield

    # 应用关闭时的清理工作
    logger.info("🔄 应用正在关闭，开始清理资源...")

    # 取消后台任务
    cleanup_task.cancel()
    try:
        await cleanup_task
        logger.info("✅ 后台清理任务已成功取消")
    except asyncio.CancelledError:
        logger.info("✅ 后台清理任务已成功取消")
    except Exception as e:
        logger.error(f"❌ 取消后台任务时出错: {e}")

    logger.info("👋 应用已完全关闭")


# ——— FastAPI 应用实例 ———
app = FastAPI(
    lifespan=lifespan,
    title="SRT Subtitle Generation API",
    description="一个通过上传音频或视频文件来自动生成SRT字幕的API。",
    version="1.0.0",
    contact={
        "name": "powerfulyang",
        "email": "i@powerfulyang.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)


# ——— 后台任务 ———
async def cleanup_temp_files():
    """定期清理临时文件夹中的旧文件，防止磁盘空间被占满。"""
    cleanup_logger = get_logger("cleanup_task")

    while True:
        try:
            await asyncio.sleep(3600)  # 每小时执行一次清理
            current_time = time.time()

            cleanup_logger.info("🧹 开始执行临时文件清理任务...")

            if not os.path.exists(TEMP_DIR):
                cleanup_logger.warning(f"⚠️ 临时目录不存在: {TEMP_DIR}")
                continue

            files_cleaned = 0
            total_size_cleaned = 0

            for filename in os.listdir(TEMP_DIR):
                file_path = os.path.join(TEMP_DIR, filename)

                # 只处理文件，跳过目录
                if not os.path.isfile(file_path):
                    continue

                file_age = current_time - os.path.getmtime(file_path)

                # 删除超过30分钟的旧文件
                if file_age > 1800:  # 30分钟 = 1800秒
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        files_cleaned += 1
                        total_size_cleaned += file_size
                        cleanup_logger.debug(f"🗑️ 已删除临时文件: {file_path} (大小: {format_file_size(file_size)})")
                    except Exception as e:
                        cleanup_logger.error(f"❌ 删除文件失败 {file_path}: {e}")

            if files_cleaned > 0:
                cleanup_logger.info(f"✅ 清理完成：删除了 {files_cleaned} 个文件，释放空间 {format_file_size(total_size_cleaned)}")
            else:
                cleanup_logger.debug("📝 无需清理，没有过期的临时文件")

        except asyncio.CancelledError:
            # 捕获取消异常，优雅退出
            cleanup_logger.info("🛑 清理任务收到取消信号，正在退出...")
            break
        except Exception as e:
            cleanup_logger.error(f"❌ 清理任务出错: {e}")
            # 出错后等待5分钟再重试，避免频繁报错
            try:
                await asyncio.sleep(300)
            except asyncio.CancelledError:
                break



class GenerateSubtitleResponse(BaseModel):
    srt_content: str


# ——— API 端点 ———
@app.post(
    "/generate_subtitle",
    summary="生成SRT字幕",
    description="上传一个音频或视频文件，此端点将为其生成SRT格式的字幕文件并返回。",
    tags=["Subtitle Generation"],
    response_model=GenerateSubtitleResponse,
)
async def generate_subtitle_endpoint(
        file: UploadFile = File(description="需要生成字幕的音频或视频文件。")
):
    api_logger = get_logger("api.generate_subtitle")
 
    # 验证文件
    if not file or not file.filename:
        api_logger.error("❌ 接收到无效的文件上传请求")
        raise HTTPException(status_code=400, detail="未提供有效的文件")

    # 记录请求信息
    file_size_display = format_file_size(file.size) if hasattr(file, 'size') and file.size else '未知'
    api_logger.info(f"📥 收到字幕生成请求 - 文件: {file.filename}, "
                    f"大小: {file_size_display}, "
                    f"类型: {file.content_type}")

    # 生成UUID作为临时文件名，保留原始文件扩展名
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
    temp_filename = f"{uuid.uuid4()}{file_extension}"
    temp_file_path = os.path.join(TEMP_DIR, temp_filename)

    try:
        # 将上传的文件保存到临时目录
        api_logger.debug(f"💾 正在保存临时文件: {temp_filename} (原文件: {file.filename})")
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 验证文件保存成功
        saved_size = os.path.getsize(temp_file_path)
        api_logger.debug(f"✅ 临时文件保存成功，大小: {format_file_size(saved_size)}")

        # 调用核心逻辑生成SRT内容
        api_logger.info(f"🔄 开始生成字幕: {file.filename}")
        srt_content = generate_srt(temp_file_path)

        if not srt_content or not srt_content.strip():
            api_logger.warning(f"⚠️ 生成的字幕内容为空: {file.filename}")
            raise HTTPException(status_code=422, detail="未能从音频文件中识别出任何文本内容")

        # 记录成功信息
        api_logger.info(f"✅ 字幕生成成功: {file.filename}")

        return GenerateSubtitleResponse(srt_content=srt_content)

    except HTTPException:
        # 重新抛出HTTP异常，不记录日志（避免重复）
        raise
    except Exception as e:
        # 捕获所有其他异常，记录详细日志并返回HTTP 500错误
        api_logger.error(f"❌ 生成字幕时发生错误: {file.filename} - {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成字幕时发生错误: {str(e)}")

    finally:
        # 确保临时文件在请求结束后被删除
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                api_logger.debug(f"🗑️ 临时文件已清理: {temp_filename}")
            except Exception as e:
                api_logger.error(f"❌ 清理临时文件失败: {temp_filename} - {e}")
        else:
            api_logger.debug(f"📝 临时文件不存在，无需清理: {temp_filename}")


# ——— 自定义日志格式 ———
class MillisecondFormatter(logging.Formatter):
    """自定义日志格式化类，用于在日志时间戳中添加毫秒。"""

    def formatTime(self, record, datefmt=None):
        """重写formatTime方法以支持毫秒级精度。"""
        ct = datetime.fromtimestamp(record.created)
        return ct.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # 截断到毫秒


# ——— 日志配置 ———
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": MillisecondFormatter,
            "format": "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "loggers": {
        "uvicorn.access": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False
        },
        "app": {  # 为应用日志添加配置
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    }
}

# ——— 应用启动 ———
if __name__ == "__main__":
    import uvicorn
    from app.logger_config import set_log_level

    # 设置开发环境的日志级别
    set_log_level("INFO")  # 生产环境可以改为 "WARNING"

    # 使用uvicorn运行FastAPI应用
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        log_config=LOGGING_CONFIG,
        reload=True,
    )
