"""
图片处理核心逻辑
"""

import os
import sys
import time
import threading
from pathlib import Path
from queue import Queue, Empty
from typing import Dict, List, Optional, Tuple
from PyQt5 import QtCore

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("警告: Pillow库未安装，图片处理功能将不可用")

from .utils import (
    scan_image_files, create_groups,
    format_number, get_image_format, safe_delete_file,
    ProgressTracker
)


class ImageProcessor:
    """图片处理器"""

    def __init__(self, config: Dict):
        self.config = config
        self.progress_callback = None
        self.should_stop = False

        # 验证Pillow
        if not HAS_PIL:
            raise ImportError("请安装Pillow库: pip install Pillow")

    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback

    def stop(self):
        """停止处理"""
        self.should_stop = True

    def process(self) -> Tuple[bool, str]:
        """执行图片处理"""
        try:
            # 1. 扫描图片文件
            self._update_progress(0, "正在扫描图片文件...")

            extensions = []
            if self.config.get('filter_png', True):
                extensions.append('.png')
            if self.config.get('filter_jpg', True):
                extensions.extend(['.jpg', '.jpeg'])

            image_files = scan_image_files(
                self.config['input_dir'],
                extensions,
                self.config.get('recursive', True)
            )

            if not image_files:
                return False, "未找到符合条件的图片文件"

            self._update_progress(5, f"找到 {len(image_files)} 张图片")

            # 2. 分割训练集和验证集（根据数量）
            train_count = self.config.get('train_count', 2000)

            # 确保训练集数量不超过总文件数
            if train_count > len(image_files):
                train_count = len(image_files)
                self._update_progress(10, f"训练集数量超过总文件数，已调整为 {train_count}")

            train_files = image_files[:train_count]
            val_files = image_files[train_count:]

            self._update_progress(10, f"分割完成: 训练集 {len(train_files)} 张, 验证集 {len(val_files)} 张")

            # 3. 创建输出目录结构
            dataset_name = self.config.get('dataset_name', 'dataset')
            output_base = Path(self.config['output_dir']) / dataset_name

            train_root = output_base / "train"
            val_root = output_base / "val"

            # 如果目录已存在且不覆盖，则返回错误
            if output_base.exists() and not self.config.get('overwrite', False):
                return False, f"输出目录已存在: {output_base}"

            # 删除现有目录（如果允许覆盖）
            if output_base.exists() and self.config.get('overwrite', False):
                import shutil
                shutil.rmtree(output_base)

            # 4. 处理训练集
            if train_files:
                success, msg = self._process_file_set(
                    train_files, train_root, "train", len(image_files), 15, 60
                )
                if not success:
                    return False, msg

                if self.should_stop:
                    return False, "处理被用户中断"

            # 5. 处理验证集
            if val_files:
                success, msg = self._process_file_set(
                    val_files, val_root, "val", len(image_files), 75, 20
                )
                if not success:
                    return False, msg

                if self.should_stop:
                    return False, "处理被用户中断"

            # 6. 完成
            self._update_progress(100, "处理完成")

            total_processed = len(train_files) + len(val_files)
            return True, f"成功处理 {total_processed} 张图片（训练集: {len(train_files)}张, 验证集: {len(val_files)}张）"

        except Exception as e:
            return False, f"处理过程中出错: {str(e)}"

    def _process_file_set(self, files: List[str], output_root: Path,
                         prefix: str, total_files: int,
                         start_progress: int, progress_range: int) -> Tuple[bool, str]:
        """处理一组文件（训练集或验证集）"""
        group_size = self.config.get('group_size', 100)
        start_number = self.config.get('start_number', 1)
        number_digits = self.config.get('number_digits', 5)

        # 分组
        groups = create_groups(files, group_size)

        # 处理每个组
        file_counter = start_number

        for group_idx, file_group in enumerate(groups):
            if self.should_stop:
                return False, "处理被用户中断"

            # 创建组目录
            group_dir_name = f"{prefix}_{group_idx + 1:03d}"
            group_dir = output_root / group_dir_name / "images"
            group_dir.mkdir(parents=True, exist_ok=True)

            # 处理组内的每张图片
            for file_idx, input_file in enumerate(file_group):
                if self.should_stop:
                    return False, "处理被用户中断"

                # 计算整体进度
                processed_count = file_counter - start_number
                total_count = len(files)
                group_progress = (processed_count / total_count) * progress_range
                overall_progress = start_progress + group_progress

                # 更新进度
                self._update_progress(
                    int(overall_progress),
                    f"正在处理 {prefix} 图片: {processed_count + 1}/{total_count}"
                )

                # 生成输出文件名
                output_filename = f"{prefix}_{format_number(file_counter, number_digits)}"

                # 确定输出格式
                if self.config.get('keep_original_format', True):
                    output_ext = Path(input_file).suffix
                else:
                    output_format = self.config.get('output_format', 'png')
                    output_ext = f".{output_format}"

                output_path = group_dir / f"{output_filename}{output_ext}"

                # 处理图片
                success, msg = self._process_single_image(input_file, output_path)
                if not success:
                    print(f"处理图片失败 {input_file}: {msg}")
                    # 可以选择跳过失败的文件或停止处理
                    # 这里选择跳过

                file_counter += 1

        return True, f"{prefix}处理完成"

    def _process_single_image(self, input_path: str, output_path: Path) -> Tuple[bool, str]:
        """处理单张图片"""
        try:
            # 打开图片
            with Image.open(input_path) as img:
                # 转换模式（如果需要）
                if img.mode not in ['RGB', 'RGBA', 'L', 'P']:
                    img = img.convert('RGB')

                # 获取目标尺寸
                target_width = self.config.get('target_width', 1024)
                target_height = self.config.get('target_height', 1024)
                mode = self.config.get('mode', 'aspect')

                # 应用缩放
                if mode == 'aspect':
                    # 等比例缩放
                    img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
                elif mode == 'stretch':
                    # 拉伸缩放
                    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                elif mode == 'crop':
                    # 裁剪填充（居中裁剪）
                    width_ratio = target_width / img.width
                    height_ratio = target_height / img.height
                    ratio = max(width_ratio, height_ratio)

                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)

                    # 裁剪
                    left = (img.width - target_width) // 2
                    top = (img.height - target_height) // 2
                    right = left + target_width
                    bottom = top + target_height

                    img = img.crop((left, top, right, bottom))

                # 保存图片
                save_kwargs = {}

                # 确定保存格式
                output_ext = output_path.suffix.lower()
                if output_ext in ['.jpg', '.jpeg']:
                    save_format = 'JPEG'
                    save_kwargs['quality'] = self.config.get('quality', 90)
                    # 如果图片有透明通道，转换为RGB
                    if img.mode in ['RGBA', 'LA', 'PA']:
                        img = img.convert('RGB')
                elif output_ext == '.png':
                    save_format = 'PNG'
                    save_kwargs['compress_level'] = 6
                elif output_ext == '.webp':
                    save_format = 'WEBP'
                    save_kwargs['quality'] = self.config.get('quality', 90)
                else:
                    # 默认保存为PNG
                    save_format = 'PNG'
                    output_path = output_path.with_suffix('.png')

                # 确保输出目录存在
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # 保存图片
                img.save(output_path, save_format, **save_kwargs)

                return True, "成功"

        except Exception as e:
            return False, str(e)

    def _update_progress(self, progress: int, message: str):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(progress, message)


class ImageProcessorThread(QtCore.QThread):
    """图片处理线程（用于PyQt）"""

    progress_updated = QtCore.pyqtSignal(int, str)
    processing_finished = QtCore.pyqtSignal(bool, str)

    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        self.processor = None

    def run(self):
        """线程运行函数"""
        try:
            self.processor = ImageProcessor(self.config)
            self.processor.set_progress_callback(
                lambda p, m: self.progress_updated.emit(p, m)
            )

            success, message = self.processor.process()
            self.processing_finished.emit(success, message)

        except Exception as e:
            self.processing_finished.emit(False, f"线程执行出错: {str(e)}")

    def stop(self):
        """停止处理"""
        if self.processor:
            self.processor.stop()
