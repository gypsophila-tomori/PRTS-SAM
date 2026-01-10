"""
SAM嵌入向量生成核心逻辑
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
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
            raise ImportError(
                "请安装segment_anything库: pip install git+https://github.com/facebookresearch/segment-anything.git")

        if not HAS_TQDM:
            print("注意: 未安装tqdm库，将使用简单进度显示")

    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback

    def stop(self):
        """停止处理"""
        self.should_stop = True

    def process(self) -> Tuple[bool, str]:
        """执行嵌入向量生成"""
        try:
            # 获取配置参数
            checkpoint_path = self.config['checkpoint_path']
            model_type = self.config['model_type']
            device = self.config['device']
            dataset_folder = self.config['dataset_folder']

            # 设置路径
            images_folder = os.path.join(dataset_folder, "images")
            embeddings_folder = os.path.join(dataset_folder, "embeddings")

            # 创建输出目录
            if not os.path.exists(embeddings_folder):
                os.makedirs(embeddings_folder)

            # 1. 加载SAM模型
            self._update_progress(0, "正在加载SAM模型...")

            try:
                sam = sam_model_registry[model_type](checkpoint=checkpoint_path)
                sam.to(device=device)
                predictor = SamPredictor(sam)
            except Exception as e:
                return False, f"加载SAM模型失败: {str(e)}"

            # 2. 获取图片列表
            image_files = []
            for image_name in os.listdir(images_folder):
                image_path = os.path.join(images_folder, image_name)
                if os.path.isfile(image_path):
                    # 检查是否为图片文件（简单检查扩展名）
                    ext = os.path.splitext(image_name)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']:
                        image_files.append(image_name)

            if not image_files:
                return False, f"未找到图片文件: {images_folder}"

            total_images = len(image_files)
            self._update_progress(5, f"找到 {total_images} 张图片")

            # 3. 处理每张图片
            processed_count = 0

            # 使用tqdm或简单循环
            if HAS_TQDM:
                image_iterator = tqdm(image_files, desc="生成嵌入向量")
            else:
                image_iterator = image_files

            for image_name in image_iterator:
                if self.should_stop:
                    return False, "处理被用户中断"

                # 更新进度
                progress = 5 + int((processed_count / total_images) * 90)
                self._update_progress(progress, f"正在处理: {image_name}")

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

            # 4. 完成
            self._update_progress(100, "处理完成")

            return True, f"成功处理 {processed_count}/{total_images} 张图片"

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
