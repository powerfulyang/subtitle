"""
音频分离助手模块

基于 audio_separator 库实现人声与背景音分离功能，
100% 遵循官方推荐用法，专门用于字幕生成前的音频预处理。
"""

import os
import tempfile
import uuid
import traceback
from typing import Optional, Tuple
from audio_separator.separator import Separator

# ——— 导入统一的日志配置 ———
from .logger_config import get_logger
# ——— 导入工具函数 ———
from utils import format_file_size

# 获取当前模块的日志器
logger = get_logger(__name__)

# ——— 全局配置 ———
# 使用官方推荐的最佳人声分离模型
DEFAULT_VOCALS_MODEL = "Kim_Vocal_2.onnx"

# 模型和临时文件目录
MODELS_DIR = "models"
SEPARATION_TEMP_DIR = "temp_separation"

# 单例模式管理 Separator 实例
_separator_instance: Optional[Separator] = None


def get_audio_separator() -> Separator:
    """
    获取音频分离器的单例实例。
    
    内部使用单例模式管理 Separator 实例，确保资源的高效利用。
    
    Returns:
        Separator: audio_separator 实例
    """
    global _separator_instance
    
    if _separator_instance is None:
        try:
            logger.info("初始化音频分离器...")
            
            # 创建必要的目录
            os.makedirs(MODELS_DIR, exist_ok=True)
            os.makedirs(SEPARATION_TEMP_DIR, exist_ok=True)
            
            # 按照官方文档配置 Separator
            _separator_instance = Separator(
                # 输出目录设置为临时分离目录
                output_dir=SEPARATION_TEMP_DIR,
                # 模型文件目录
                model_file_dir=MODELS_DIR,
                # 只输出人声，不输出伴奏
                output_single_stem="Vocals",
            )
            
            # 加载专门的人声分离模型
            logger.info(f"加载人声分离模型: {DEFAULT_VOCALS_MODEL}")
            _separator_instance.load_model(model_filename=DEFAULT_VOCALS_MODEL)
            
            logger.info("音频分离器初始化完成")
            
        except Exception as e:
            # 记录完整的错误栈信息
            error_traceback = traceback.format_exc()
            logger.error("音频分离器初始化失败")
            logger.error(f"错误详情: {str(e)}")
            logger.error(f"完整错误栈:\n{error_traceback}")
            raise
    
    return _separator_instance


def separate_vocals(audio_path: str, cleanup_original: bool = False) -> str:
    """
    从音频文件中分离出人声部分。
    
    使用 audio_separator 库的官方推荐方法，提取高质量的人声音轨，
    去除背景音乐和其他干扰声音，为语音识别提供更清晰的输入。
    
    Args:
        audio_path (str): 输入音频文件的路径
        cleanup_original (bool): 是否在分离完成后删除原始文件，默认为 False
        
    Returns:
        str: 分离出的人声文件路径
        
    Raises:
        FileNotFoundError: 如果输入文件不存在
        RuntimeError: 如果音频分离过程失败
        Exception: 如果发生其他错误
    """
    # 验证输入文件
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"输入音频文件不存在: {audio_path}")
    
    # 获取文件信息
    file_size = os.path.getsize(audio_path)
    logger.info(f"开始人声分离: {audio_path}, 文件大小: {format_file_size(file_size)}")
    
    try:
        # 获取分离器实例
        separator = get_audio_separator()
        
        # 执行人声分离
        logger.info("正在执行人声与背景音分离...")
        output_files = separator.separate(audio_path)
        
        if not output_files:
            raise RuntimeError("音频分离失败：未生成任何输出文件")
        
        # 由于设置了 output_single_stem="Vocals"，应该只有一个输出文件
        vocals_file = output_files[0]
        # preappend vocals_file with SEPARATION_TEMP_DIR
        vocals_file = os.path.join(SEPARATION_TEMP_DIR, vocals_file)

        if not os.path.exists(vocals_file):
            raise RuntimeError(f"人声分离文件未找到: {vocals_file}")
        
        # 验证输出文件
        output_size = os.path.getsize(vocals_file)
        if output_size == 0:
            raise RuntimeError("分离出的人声文件为空")
        
        logger.info(f"人声分离成功: {vocals_file}, 输出大小: {format_file_size(output_size)}")
        
        # 清理原始文件（如果需要）
        if cleanup_original:
            try:
                os.remove(audio_path)
                logger.debug(f"已删除原始文件: {audio_path}")
            except Exception as e:
                logger.warning(f"删除原始文件失败: {audio_path} - {e}")
        
        return vocals_file
        
    except Exception as e:
        # 记录完整的错误栈信息
        error_traceback = traceback.format_exc()
        logger.error(f"人声分离过程中发生错误: {audio_path}")
        logger.error(f"错误详情: {str(e)}")
        logger.error(f"完整错误栈:\n{error_traceback}")
        raise


def separate_vocals_with_cleanup(audio_path: str) -> Tuple[str, callable]:
    """
    分离人声并返回清理函数。
    
    这是一个便捷函数，执行人声分离并返回一个清理函数，
    用于在处理完成后清理临时的分离文件。
    
    Args:
        audio_path (str): 输入音频文件路径
        
    Returns:
        Tuple[str, callable]: (人声文件路径, 清理函数)
    """
    vocals_path = separate_vocals(audio_path)
    
    def cleanup():
        """清理分离产生的临时文件"""
        try:
            if os.path.exists(vocals_path):
                os.remove(vocals_path)
                logger.debug(f"已清理人声分离文件: {vocals_path}")
        except Exception as e:
            logger.warning(f"清理人声分离文件失败: {vocals_path} - {e}")
    
    return vocals_path, cleanup


def cleanup_separation_temp_files(max_age_hours: int = 2):
    """
    清理过期的音频分离临时文件。
    
    Args:
        max_age_hours (int): 文件最大保留时间（小时），默认2小时
    """
    import time
    
    if not os.path.exists(SEPARATION_TEMP_DIR):
        return
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    cleaned_count = 0
    total_size_cleaned = 0
    
    try:
        for filename in os.listdir(SEPARATION_TEMP_DIR):
            file_path = os.path.join(SEPARATION_TEMP_DIR, filename)
            
            if not os.path.isfile(file_path):
                continue
            
            file_age = current_time - os.path.getmtime(file_path)
            
            if file_age > max_age_seconds:
                try:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    cleaned_count += 1
                    total_size_cleaned += file_size
                    logger.debug(f"已清理过期分离文件: {file_path}")
                except Exception as e:
                    logger.warning(f"清理过期分离文件失败: {file_path} - {e}")
        
        if cleaned_count > 0:
            logger.info(f"清理完成：删除了 {cleaned_count} 个过期分离文件，释放空间 {total_size_cleaned} 字节")
    
    except Exception as e:
        logger.error(f"清理分离临时文件时出错: {e}")


def get_separation_status() -> dict:
    """
    获取音频分离模块的状态信息。
    
    Returns:
        dict: 包含模块状态的字典
    """
    status = {
        "separator_initialized": _separator_instance is not None,
        "models_dir": MODELS_DIR,
        "separation_temp_dir": SEPARATION_TEMP_DIR,
        "default_model": DEFAULT_VOCALS_MODEL,
        "models_dir_exists": os.path.exists(MODELS_DIR),
        "temp_dir_exists": os.path.exists(SEPARATION_TEMP_DIR)
    }
    
    if os.path.exists(SEPARATION_TEMP_DIR):
        try:
            temp_files = [f for f in os.listdir(SEPARATION_TEMP_DIR) 
                         if os.path.isfile(os.path.join(SEPARATION_TEMP_DIR, f))]
            status["temp_files_count"] = len(temp_files)
        except:
            status["temp_files_count"] = "unknown"
    else:
        status["temp_files_count"] = 0
    
    return status 