"""
文件相关工具函数

包含文件大小格式化、文件扩展名提取等常用文件操作工具函数。
"""

import os


def format_file_size(size_bytes: int) -> str:
    """
    将字节数转换为人类可读的文件大小格式
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        str: 格式化后的文件大小字符串
        
    Examples:
        >>> format_file_size(0)
        '0 B'
        >>> format_file_size(1024)
        '1.0 KB'
        >>> format_file_size(1048576)
        '1.0 MB'
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    size_index = 0
    size_value = float(size_bytes)
    
    while size_value >= 1024 and size_index < len(size_names) - 1:
        size_value /= 1024
        size_index += 1
    
    return f"{size_value:.1f} {size_names[size_index]}"


def get_file_extension(filename: str) -> str:
    """
    获取文件扩展名
    
    Args:
        filename: 文件名
        
    Returns:
        str: 文件扩展名（包含点号）
        
    Examples:
        >>> get_file_extension("example.txt")
        '.txt'
        >>> get_file_extension("video.mp4")
        '.mp4'
        >>> get_file_extension("document")
        ''
        >>> get_file_extension("")
        ''
    """
    if not filename:
        return ""
    return os.path.splitext(filename)[1] 