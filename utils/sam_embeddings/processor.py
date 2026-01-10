"""
SAM嵌入向量生成核心逻辑
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Generator
from PyQt5 import QtCore

# 尝试导入SAM库
try:
    from segment_anything import sam_model_registry, SamPredictor
    HAS_SAM = True
except ImportError:
    HAS_SAM = False
    print("警告: segment_anything库未安装，SAM功能将不可用")

# 尝试导入tqdm
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("警告: tqdm库未安装，进度显示功能将受限")


class SAMEmbeddingsProcessor:
    """SAM嵌入向量处理器"""

    def __init__(self, config: Dict):
        self.config = config
        self.progress_callback = None
        self.should_stop = False

        # 验证依赖
        if not HAS_SAM:
            raise ImportError("请安装segment_anything库: pip install git+https://github.com/facebookresearch/segment-anything.git")

        if not HAS_TQDM:
            print("注意: 未安装tqdm库，将使用简单进度显示")

    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback

    def stop(self):
        """停止处理"""
        self.should_stop = True

    def find_images_folders(self, root_dir: str, mode: str) -> List[Tuple[str, str]]:
        """
        查找所有包含图片的images文件夹

        Args:
            root_dir: 根目录
            mode: "传统模式" 或 "分组模式"

        Returns:
            List[(images_folder_path, embeddings_folder_path)]
        """
        images_folders = []

        if mode == "传统模式":
            # 传统模式：只查找根目录下的images文件夹
            images_folder = os.path.join(root_dir, "images")
            if os.path.exists(images_folder) and os.path.isdir(images_folder):
                embeddings_folder = os.path.join(root_dir, "embeddings")
                images_folders.append((images_folder, embeddings_folder))
                self._update_progress(0, f"找到images文件夹: {images_folder}")
        else:
            # 分组模式：递归查找所有子目录中的images文件夹
            for dirpath, dirnames, filenames in os.walk(root_dir):
                # 检查当前目录是否包含images子目录
                if "images" in dirnames:
                    images_folder = os.path.join(dirpath, "images")
                    embeddings_folder = os.path.join(dirpath, "embeddings")
                    images_folders.append((images_folder, embeddings_folder))
                    self._update_progress(0, f"找到images文件夹: {images_folder}")

        return images_folders

    def count_total_images(self, images_folders: List[Tuple[str, str]]) -> int:
        """统计总图片数量"""
        total = 0
        for images_folder, _ in images_folders:
            for image_name in os.listdir(images_folder):
                image_path = os.path.join(images_folder, image_name)
                if os.path.isfile(image_path):
                    ext = os.path.splitext(image_name)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']:
                        total += 1
        return total

    def process_images_folder(self, images_folder: str, embeddings_folder: str,
                            predictor, processed_count: int, total_images: int) -> Tuple[int, bool]:
        """
        处理单个images文件夹

        Returns:
            (新的processed_count, 是否被中断)
        """
        # 创建输出目录
        if not os.path.exists(embeddings_folder):
            os.makedirs(embeddings_folder)

        # 获取当前images文件夹中的图片
        image_files = []
        for image_name in os.listdir(images_folder):
            image_path = os.path.join(images_folder, image_name)
            if os.path.isfile(image_path):
                ext = os.path.splitext(image_name)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']:
                    image_files.append(image_name)

        # 处理当前文件夹中的每张图片
        folder_name = os.path.basename(os.path.dirname(images_folder))
        for image_name in image_files:
            if self.should_stop:
                return processed_count, True

            # 更新进度
            progress = 5 + int((processed_count / total_images) * 90)
            folder_display = folder_name if folder_name != "" else "根目录"
            self._update_progress(progress, f"正在处理 [{folder_display}]: {image_name}")

            try:
                # 读取图片
                image_path = os.path.join(images_folder, image_name)
                image = cv2.imread(image_path)

                if image is None:
                    print(f"警告: 无法读取图片 {image_path}")
                    processed_count += 1
                    continue

                # 转换为RGB
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                # 设置图片并获取嵌入向量
                predictor.set_image(image)
                image_embedding = predictor.get_image_embedding().cpu().numpy()

                # 保存嵌入向量
                out_name = os.path.splitext(image_name)[0] + ".npy"
                out_path = os.path.join(embeddings_folder, out_name)
                np.save(out_path, image_embedding)

                processed_count += 1

            except Exception as e:
                print(f"处理图片 {image_name} 时出错: {str(e)}")
                processed_count += 1
                continue

        return processed_count, False

    def process(self) -> Tuple[bool, str]:
        """执行嵌入向量生成"""
        try:
            # 获取配置参数
            checkpoint_path = self.config['checkpoint_path']
            model_type = self.config['model_type']
            device = self.config['device']
            dataset_root = self.config['dataset_root']
            scan_mode = self.config['scan_mode']  # "传统模式" 或 "分组模式"

            # 1. 查找所有images文件夹
            self._update_progress(0, f"正在扫描目录结构 ({scan_mode})...")
            images_folders = self.find_images_folders(dataset_root, scan_mode)

            if not images_folders:
                return False, f"未找到images文件夹: {dataset_root}"

            # 2. 统计总图片数量
            self._update_progress(1, "正在统计图片数量...")
            total_images = self.count_total_images(images_folders)

            if total_images == 0:
                return False, f"未找到图片文件"

            self._update_progress(2, f"找到 {len(images_folders)} 个images文件夹，共 {total_images} 张图片")

            # 3. 加载SAM模型
            self._update_progress(3, "正在加载SAM模型...")

            try:
                sam = sam_model_registry[model_type](checkpoint=checkpoint_path)
                sam.to(device=device)
                predictor = SamPredictor(sam)
            except Exception as e:
                return False, f"加载SAM模型失败: {str(e)}"

            # 4. 处理每个images文件夹
            processed_count = 0
            folders_processed = 0

            for images_folder, embeddings_folder in images_folders:
                if self.should_stop:
                    return False, "处理被用户中断"

                folders_processed += 1
                folder_name = os.path.basename(os.path.dirname(images_folder))
                folder_name = folder_name if folder_name != "" else "根目录"
                self._update_progress(
                    5 + int((folders_processed / len(images_folders)) * 5),
                    f"正在处理第 {folders_processed}/{len(images_folders)} 个文件夹: {folder_name}"
                )

                # 处理当前文件夹
                processed_count, stopped = self.process_images_folder(
                    images_folder, embeddings_folder, predictor, processed_count, total_images
                )

                if stopped:
                    return False, "处理被用户中断"

            # 5. 完成
            self._update_progress(100, "处理完成")

            return True, f"成功处理 {processed_count}/{total_images} 张图片，来自 {len(images_folders)} 个文件夹"

        except Exception as e:
            return False, f"处理过程中出错: {str(e)}"

    def _update_progress(self, progress: int, message: str):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(progress, message)


class SAMEmbeddingsProcessorThread(QtCore.QThread):
    """SAM嵌入向量生成线程（用于PyQt）"""

    progress_updated = QtCore.pyqtSignal(int, str)
    processing_finished = QtCore.pyqtSignal(bool, str)

    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        self.processor = None

    def run(self):
        """线程运行函数"""
        try:
            self.processor = SAMEmbeddingsProcessor(self.config)
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
