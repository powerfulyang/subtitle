import threading
from typing import Optional

import torch
import whisperx
import gc

# ——— 导入统一的日志配置 ———
from .logger_config import get_logger

# 获取当前模块的日志器
logger = get_logger(__name__)


def get_device() -> str:
    """
    检查并返回可用的最佳计算设备 (CUDA GPU或CPU)。

    Returns:
        str: "cuda" 如果NVIDIA GPU可用, 否则 "cpu"。
    """
    if torch.cuda.is_available():
        device = "cuda"
        logger.info("CUDA is available, using GPU for inference.")
    else:
        device = "cpu"
        logger.info("CUDA is not available, using CPU for inference.")
    return device

model_size_or_path = "large-v3"

model_instance = None
align_model_instance = None
align_metadata = None

device = get_device()

def get_compute_type() -> str:
    """
    获取最佳的计算类型 (int8或float16)。
    """
    if device == "cuda":
        return "float16"
    else:
        return "int8"
    
compute_type = get_compute_type()

# ——— 便捷函数：保持向后兼容性 ———
def get_whisper_model():
    """
    获取WhisperX模型的便捷函数。
    
    内部使用单例模式管理模型实例，确保资源的高效利用。
    
    Returns:
        WhisperX模型实例
    """
    global model_instance
    if model_instance is None:
        logger.info(f"Loading WhisperX model: {model_size_or_path}, device: {device}, compute_type: {compute_type}")
        model_instance = whisperx.load_model(
            model_size_or_path,
            device,
            compute_type=compute_type,
        )
        logger.info(f"WhisperX model loaded successfully")
    return model_instance


def get_align_model(language_code: str):
    """
    获取WhisperX对齐模型的便捷函数。
    
    Args:
        language_code (str): 语言代码，如 'en', 'zh' 等
        
    Returns:
        tuple: (对齐模型, 元数据)
    """
    global align_model_instance, align_metadata
    if align_model_instance is None:
        logger.info(f"Loading WhisperX alignment model for language: {language_code}")
        align_model_instance, align_metadata = whisperx.load_align_model(
            language_code=language_code, 
            device=device
        )
        logger.info(f"WhisperX alignment model loaded successfully")
    return align_model_instance, align_metadata


def format_timestamp(seconds: float) -> str:
    """
    将总秒数格式化为SRT字幕标准的时间戳字符串 (HH:MM:SS,mmm)。

    Args:
        seconds (float): 需要格式化的时间，单位为秒。

    Returns:
        str: 格式化后的时间戳字符串。
    """
    assert seconds >= 0, "non-negative timestamp expected"
    milliseconds = round(seconds * 1000.0)

    hours = milliseconds // 3_600_000
    milliseconds %= 3_600_000
    minutes = milliseconds // 60_000
    milliseconds %= 60_000
    seconds = milliseconds // 1_000
    milliseconds %= 1_000

    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def convert_to_srt_content(segments) -> str:
    """
    将whisperX识别出的文本段落 (segments) 转换为SRT格式的字符串。

    Args:
        segments: whisperX模型返回的识别结果段落列表。

    Returns:
        str: 完整的SRT格式字幕内容。
    """
    srt_content = ""
    for i, segment in enumerate(segments, 1):
        start_time = format_timestamp(segment['start'])
        end_time = format_timestamp(segment['end'])
        text = segment['text'].strip()
        # SRT格式: 序号\n时间戳 --> 时间戳\n文本\n\n
        srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"
    return srt_content


def generate_srt(audio_path: str, enable_alignment: bool = True) -> str:
    """
    为给定的音频或视频文件生成SRT字幕内容。

    Args:
        audio_path (str): 需要处理的音频或视频文件的绝对路径。
        enable_alignment (bool): 是否启用词级时间戳对齐，默认为True。

    Raises:
        RuntimeError: 如果WhisperX模型加载失败。
        Exception: 如果在转录过程中发生其他错误。

    Returns:
        str: 生成的SRT字幕内容。
    """
    try:
        # 阶段1: 使用WhisperX进行基础转录
        model = get_whisper_model()
        
        logger.info(f"开始转录音频文件: {audio_path}")
        
        # 加载音频文件
        audio = whisperx.load_audio(audio_path)
        
        # 执行转录，使用批量推理提高速度
        batch_size = 16 if device == "cuda" else 4
        result = model.transcribe(audio, batch_size=batch_size)

        logger.info(f"检测到语言 '{result['language']}' (基础转录完成)")

        # 阶段2: 词级时间戳对齐（可选，默认启用）
        if enable_alignment:
            try:
                align_model, metadata = get_align_model(language_code=result["language"])
                result = whisperx.align(
                    result["segments"], 
                    align_model, 
                    metadata, 
                    audio, 
                    device, 
                    return_char_alignments=False
                )
                logger.info("词级时间戳对齐完成")
                
                # 清理对齐模型以节省GPU内存
                if device == "cuda":
                    gc.collect()
                    torch.cuda.empty_cache()
                    
            except Exception as e:
                logger.warning(f"词级对齐失败，使用基础转录结果: {str(e)}")


        # 将转录结果转换为SRT格式
        srt_content = convert_to_srt_content(result["segments"])
        logger.info(f"成功生成SRT字幕内容: {audio_path}")

        return {
            "srt_content": srt_content,
            "language": result["language"],
            "segments": result["segments"],
            "words": result["words"],
        }

    except Exception as e:
        logger.error(f"转录过程中发生错误 {audio_path}: {str(e)}")
        raise
