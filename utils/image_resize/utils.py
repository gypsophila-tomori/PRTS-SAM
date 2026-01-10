"""
图片处理工具函数
"""

import os
import glob
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
import threading
from queue import Queue


def scan_image_files(directory: str,
                    extensions: List[str] = None,
                    recursive: bool = True) -> List[str]:
    """
    扫描目录中的图片文件

    Args:
        directory: 要扫描的目录
        extensions: 扩展名列表，如 ['.jpg', '.png']
        recursive: 是否递归扫描子目录

    Returns:
        图片文件路径列表
    """
    if extensions is None:
        extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']

    image_files = []

    if recursive:
        for ext in extensions:
            pattern = os.path.join(directory, '**', f'*{ext}')
            image_files.extend(glob.glob(pattern, recursive=True))
    else:
        for ext in extensions:
            pattern = os.path.join(directory, f'*{ext}')
            image_files.extend(glob.glob(pattern, recursive=False))

    # 过滤掉可能重复的文件（某些扩展名可能有不同的大小写）
    image_files = list(set(image_files))

    return sorted(image_files)


def create_directory_structure(base_dir: str,
                              dataset_name: str,
                              group_size: int = 100) -> Tuple[dict, int]:
    """
    创建数据集目录结构

    Args:
        base_dir: 基础目录
        dataset_name: 数据集名称
        group_size: 每组图片数量

    Returns:
        (目录路径字典, 总组数)
    """
    dataset_root = Path(base_dir) / dataset_name
    train_root = dataset_root / "train"
    val_root = dataset_root / "val"

    # 计算需要多少组
    # 这里假设调用者知道总图片数，实际在processor中会计算

    paths = {
        'dataset_root': str(dataset_root),
        'train_root': str(train_root),
        'val_root': str(val_root),
    }

    return paths, 0  # 组数将在processor中计算


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


def get_image_format(file_path: str) -> str:
    """
    获取图片格式

    Args:
        file_path: 图片文件路径

    Returns:
        图片格式（小写）
    """
    ext = Path(file_path).suffix.lower()
    if ext in ['.jpg', '.jpeg']:
        return 'jpeg'
    elif ext == '.png':
        return 'png'
    elif ext == '.webp':
        return 'webp'
    else:
        return ext[1:] if ext else 'unknown'


def safe_delete_file(file_path: str):
    """
    安全删除文件（如果存在）

    Args:
        file_path: 文件路径
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"删除文件失败 {file_path}: {e}")


def get_file_size_mb(file_path: str) -> float:
    """
    获取文件大小（MB）

    Args:
        file_path: 文件路径

    Returns:
        文件大小（MB）
    """
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except:
        return 0


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
