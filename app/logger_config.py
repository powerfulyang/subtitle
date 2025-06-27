"""
日志配置模块

提供统一的控制台日志配置和获取方法，支持不同级别的日志输出。
遵循单例模式，确保整个应用使用统一的日志配置。
仅输出到控制台，不生成日志文件。
"""

import logging
import sys
from typing import Optional, Dict, Any


class LoggerManager:
    """
    日志管理器 - 单例模式
    
    提供统一的日志配置和获取接口，支持：
    - 控制台输出
    - 彩色日志（如果终端支持）
    - 多级别日志
    - 统一格式化
    """
    
    _instance: Optional['LoggerManager'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'LoggerManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_logging()
            LoggerManager._initialized = True
    
    def _setup_logging(self) -> None:
        """初始化日志配置"""
        # 配置根日志器
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(logging.DEBUG)
        
        # 清除现有处理器（避免重复配置）
        self.root_logger.handlers.clear()
        
        # 设置控制台日志格式
        self.console_formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # 仅配置控制台处理器
        self._setup_console_handler()
    
    def _setup_console_handler(self) -> None:
        """设置控制台日志处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.console_formatter)
        
        # 添加颜色支持（如果终端支持）
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            try:
                import colorlog
                color_formatter = colorlog.ColoredFormatter(
                    "%(log_color)s%(asctime)s [%(levelname)s] %(name)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                    log_colors={
                        'DEBUG': 'cyan',
                        'INFO': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'red,bg_white',
                    }
                )
                console_handler.setFormatter(color_formatter)
            except ImportError:
                # 如果没有安装 colorlog，使用默认格式
                pass
        
        self.root_logger.addHandler(console_handler)
    

    
    def get_logger(self, name: str = None, level: str = "INFO") -> logging.Logger:
        """
        获取指定名称的日志器
        
        Args:
            name: 日志器名称，默认使用调用模块的名称
            level: 日志级别，可选：DEBUG, INFO, WARNING, ERROR, CRITICAL
            
        Returns:
            logging.Logger: 配置好的日志器实例
        """
        if name is None:
            # 自动获取调用者的模块名
            import inspect
            frame = inspect.currentframe().f_back
            name = frame.f_globals.get('__name__', 'unknown')
        
        logger = logging.getLogger(name)
        
        # 设置日志器级别
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(numeric_level)
        
        return logger
    
    def set_level(self, level: str) -> None:
        """
        动态设置全局日志级别
        
        Args:
            level: 日志级别字符串
        """
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        self.root_logger.setLevel(numeric_level)
        
        # 同时更新控制台处理器的级别
        for handler in self.root_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                # 控制台处理器
                handler.setLevel(max(numeric_level, logging.INFO))
    
    def add_custom_handler(self, handler: logging.Handler) -> None:
        """
        添加自定义日志处理器
        
        Args:
            handler: 自定义的日志处理器
        """
        self.root_logger.addHandler(handler)
    
    def get_log_stats(self) -> Dict[str, Any]:
        """
        获取日志统计信息
        
        Returns:
            Dict: 包含日志配置信息的字典
        """
        stats = {
            "console_only": True,
            "log_level": logging.getLevelName(self.root_logger.level),
            "handlers_count": len(self.root_logger.handlers),
            "handlers": [
                {
                    "type": type(handler).__name__,
                    "level": logging.getLevelName(handler.level)
                }
                for handler in self.root_logger.handlers
            ]
        }
        
        return stats


# ——— 全局实例和便捷函数 ———

# 全局日志管理器实例
_logger_manager = LoggerManager()


def get_logger(name: str = None, level: str = "INFO") -> logging.Logger:
    """
    获取日志器的便捷函数
    
    Args:
        name: 日志器名称，默认使用调用模块的名称
        level: 日志级别
        
    Returns:
        logging.Logger: 配置好的日志器实例
        
    Example:
        >>> from app.logger_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("这是一条信息日志")
        >>> logger.error("这是一条错误日志")
    """
    return _logger_manager.get_logger(name, level)


def set_log_level(level: str) -> None:
    """
    设置全局日志级别的便捷函数
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    _logger_manager.set_level(level)


def get_log_stats() -> Dict[str, Any]:
    """
    获取日志配置信息的便捷函数
    
    Returns:
        Dict: 日志配置信息
    """
    return _logger_manager.get_log_stats()


def setup_module_logger(module_name: str, level: str = "INFO") -> logging.Logger:
    """
    为特定模块设置日志器的便捷函数
    
    Args:
        module_name: 模块名称
        level: 日志级别
        
    Returns:
        logging.Logger: 模块专用的日志器
    """
    return get_logger(module_name, level)

