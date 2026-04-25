import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

import os
from dotenv import load_dotenv

'''
    定义通用的日志模块
'''

class ColorFormatter(logging.Formatter):
    '''带颜色的日志格式化器'''
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[34m',  # 蓝色
        'INFO': '\033[32m',  # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',  # 红色
        'CRITICAL': '\033[35m',  # 紫色
    }

    # 重置颜色代码
    RESET = '\033[0m'

    def __init__(self, fmt=None, datefmt=None, use_colors=True):
        """
        Args:
            :param fmt:
            :param datefmt:
            :param use_colors:
        """
        super().__init__(fmt, datefmt)
        self.use_colors = use_colors

    def format(self, record):
        """
        格式化日志记录
        Args:
            :param record:

        :return
            格式化后的日志字符串
        """
        log_message = super().format(record)

        # 如果启用颜色且输出到控制台，则添加颜色
        if self.use_colors and hasattr(record, 'levelname'):
            levelname = record.levelname
            color = self.COLORS.get(levelname, '')
            if color:
                log_message = f'{color}{log_message}{self.RESET}'

        return log_message


def get_log_level_from_env():
    load_dotenv()

    log_level_str = os.environ.get('LOG_LEVEL')

    # 日志级别映射
    log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    return log_levels.get(log_level_str, logging.INFO)


def setup_logging():
    """
    设置日志记录器
    """
    # 创建根日志记录器
    root_logger = logging.getLogger()

    # 避免重复添加处理器
    if root_logger.handlers:
        return

    # 在项目的根目录下创建log文件夹
    current_path = Path(__file__).resolve().parent.parent.parent
    log_dir = current_path / 'log'
    if not os.path.exists(log_dir):
        log_dir.mkdir(exist_ok=True)

    # 创建日志格式
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 创建带颜色的日志格式化器(用于控制台输出)
    color_formatter = ColorFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        use_colors=True
    )

    log_level = get_log_level_from_env()
    root_logger.setLevel(log_level)

    # 添加控制台日志处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(color_formatter)
    root_logger.addHandler(console_handler)

    # 添加按天轮动的文件处理器
    log_file_path = log_dir / 'app.log'
    file_handler = TimedRotatingFileHandler(
        filename=log_file_path,
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8',
        atTime=None
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(log_format)
    root_logger.addHandler(file_handler)

    # 添加专门用于ERROR级别的文件处理器
    error_log_file_path = log_dir / 'app_error.log'
    error_file_handler = TimedRotatingFileHandler(
        filename=error_log_file_path,
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8',
        atTime=None
    )
    error_file_handler.suffix = "%Y-%m-%d"
    error_file_handler.setFormatter(log_format)
    error_file_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_file_handler)

    # 获取日志级别的名称
    log_level_name = logging.getLevelName(log_level)
    logging.info(f'日志记录器已启动，日志级别为：{log_level_name}')
    logging.info(f'常规日志文件路径为：{log_file_path}')
    logging.info(f'错误日志文件路径为：{error_log_file_path}')
