import threading
from typing import Optional, Dict, List, Any, Union

import torch
from faster_whisper import WhisperModel

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

model_size_or_path = "large-v2"

model_instance = None

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
def get_whisper_model() -> WhisperModel:
    """
    获取Whisper模型的便捷函数。
    
    内部使用单例模式管理模型实例，确保资源的高效利用。
    
    Returns:
        WhisperModel: Whisper模型实例
    """
    global model_instance
    if model_instance is None:
        logger.info(f"Loading Whisper model: {model_size_or_path}, device: {device}, compute_type: {compute_type}")
        model_instance = WhisperModel(
            model_size_or_path=model_size_or_path,
            device=device,
            compute_type=compute_type,
        )
        logger.info(f"Whisper model loaded successfully")
    return model_instance


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
    将faster-whisper识别出的文本段落 (segments) 转换为SRT格式的字符串。

    Args:
        segments: faster-whisper模型返回的可迭代的识别结果段落。

    Returns:
        str: 完整的SRT格式字幕内容。
    """
    srt_content = ""
    for i, segment in enumerate(segments, 1):
        start_time = format_timestamp(segment.start)
        end_time = format_timestamp(segment.end)
        # SRT格式: 序号\n时间戳 --> 时间戳\n文本\n\n
        srt_content += f"{i}\n{start_time} --> {end_time}\n{segment.text.strip()}\n\n"
    return srt_content


def extract_detailed_segments(segments, info) -> Dict[str, Any]:
    """
    提取包含词级时间戳的详细转录数据。
    
    Args:
        segments: faster-whisper模型返回的segment迭代器
        info: 转录信息对象
        
    Returns:
        Dict[str, Any]: 包含详细转录数据的字典
    """
    detailed_segments = []
    srt_segments = []  # 用于生成SRT内容
    
    for segment in segments:
        segment_data = {
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip(),
            "words": []
        }
        
        # 提取词级时间戳（如果可用）
        if hasattr(segment, 'words') and segment.words:
            for word in segment.words:
                word_data = {
                    "word": word.word,
                    "start": word.start,
                    "end": word.end,
                    "probability": word.probability
                }
                segment_data["words"].append(word_data)
        
        detailed_segments.append(segment_data)
        srt_segments.append(segment)  # 保存原始segment用于SRT转换
    
    # 生成SRT内容
    srt_content = convert_to_srt_content(srt_segments)
    
    return {
        "segments": detailed_segments,
        "language": info.language,
        "language_probability": info.language_probability,
        "duration": info.duration,
        "duration_after_vad": info.duration_after_vad,
        "all_language_probs": info.all_language_probs,
        "srt_content": srt_content
    }


def generate_detailed_transcription(audio_path: str) -> Dict[str, Any]:
    """
    为给定的音频或视频文件生成包含词级时间戳的详细转录数据。

    Args:
        audio_path (str): 需要处理的音频或视频文件的绝对路径。

    Raises:
        RuntimeError: 如果Whisper模型加载失败。
        Exception: 如果在转录过程中发生其他错误。

    Returns:
        Dict[str, Any]: 包含详细转录数据的字典，包括：
            - segments: 段落列表，每个段落包含文本、时间戳和词级数据
            - language: 检测到的语言
            - language_probability: 语言检测置信度
            - duration: 音频总时长
            - duration_after_vad: VAD处理后的时长
            - all_language_probs: 所有语言的概率分布
            - srt_content: 传统SRT格式的字幕内容
    """
    try:
        # 使用懒加载单例获取模型
        model = get_whisper_model()
        
        logger.info(f"开始转录音频文件: {audio_path}")
        # 使用VAD（Voice Activity Detection）滤波器来移除无声片段，提高识别准确性。
        segments, info = model.transcribe(
            audio_path,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
            initial_prompt="这是一段普通话的音频，请用简体中文转录。",
            language="zh",
            word_timestamps=True
        )

        logger.info(f"转录结果信息: 语言={info.language}, 置信度={info.language_probability}, 时长={info.duration}s")

        # 提取详细的转录数据
        detailed_result = extract_detailed_segments(segments, info)
        
        logger.info(f"成功生成详细转录数据: {audio_path}, 共 {len(detailed_result['segments'])} 个段落")

        return detailed_result

    except Exception as e:
        logger.error(f"转录过程中发生错误 {audio_path}: {str(e)}")
        raise


def generate_srt(audio_path: str) -> str:
    """
    为给定的音频或视频文件生成SRT字幕内容。
    
    【向后兼容性函数】
    此函数保持原有接口不变，内部调用新的详细转录功能。

    Args:
        audio_path (str): 需要处理的音频或视频文件的绝对路径。

    Raises:
        RuntimeError: 如果Whisper模型加载失败。
        Exception: 如果在转录过程中发生其他错误。

    Returns:
        str: 生成的SRT字幕内容。
    """
    try:
        detailed_result = generate_detailed_transcription(audio_path)
        return detailed_result["srt_content"]
    except Exception as e:
        logger.error(f"SRT生成过程中发生错误 {audio_path}: {str(e)}")
        raise
