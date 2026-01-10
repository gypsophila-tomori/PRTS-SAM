"""
图片处理工具函数
"""

import os
import glob
from pathlib import Path
from typing import List, Tuple
import threading


def scan_image_files(directory: str) -> List[str]:
    """
    扫描目录中的图片文件

    Args:
        directory: 要扫描的目录

    Returns:
        图片文件路径列表
    """
    # 默认支持的图片格式
    extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif']

    image_files = []

    # 总是递归扫描子目录
    for ext in extensions:
        pattern = os.path.join(directory, '**', f'*{ext}')
        image_files.extend(glob.glob(pattern, recursive=True))

    # 过滤掉可能重复的文件（某些扩展名可能有不同的大小写）
    image_files = list(set(image_files))

    return sorted(image_files)


def create_groups(files: List[str], group_size: int) -> List[List[str]]:
    """
    将文件列表分组

    Args:
        files: 文件列表
        group_size: 每组文件数量

    Returns:
        分组后的文件列表
    """
    groups = []
    for i in range(0, len(files), group_size):
        groups.append(files[i:i + group_size])
    return groups


def format_number(number: int, digits: int = 5) -> str:
    """
    格式化数字为指定位数的字符串

    Args:
        number: 数字
        digits: 位数

    Returns:
        格式化后的字符串
    """
    return f"{number:0{digits}d}"


class ProgressTracker:
    """进度跟踪器"""

    def __init__(self, total: int):
        self.total = total
        self.processed = 0
        self.lock = threading.Lock()

    def increment(self, count: int = 1):
        """增加进度"""
        with self.lock:
            self.processed += count

    def get_progress(self) -> float:
        """获取当前进度百分比"""
        if self.total == 0:
            return 0
        return (self.processed / self.total) * 100

    def get_processed(self) -> int:
        """获取已处理数量"""
        return self.processed
