"""
ONNX模型导出核心逻辑
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Tuple
from PyQt5 import QtCore

# 尝试导入必要的库
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("警告: torch库未安装")

try:
    from segment_anything import sam_model_registry
    from segment_anything.utils.onnx import SamOnnxModel
    HAS_SAM = True
except ImportError:
    HAS_SAM = False
    print("警告: segment_anything库未安装")

try:
    from onnxruntime.quantization import QuantType
    from onnxruntime.quantization.quantize import quantize_dynamic
    HAS_ONNXRUNTIME = True
except ImportError:
    HAS_ONNXRUNTIME = False
    print("警告: onnxruntime库未安装")


class ONNXExportProcessor:
    """ONNX模型导出处理器"""

    def __init__(self, config: Dict):
        self.config = config
        self.progress_callback = None
        self.should_stop = False

        # 验证依赖
        if not HAS_TORCH:
            raise ImportError("请安装torch库: pip install torch")

        if not HAS_SAM:
            raise ImportError("请安装segment_anything库: pip install git+https://github.com/facebookresearch/segment-anything.git")

    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback

    def stop(self):
        """停止处理"""
        self.should_stop = True

    def process(self) -> Tuple[bool, str]:
        """执行ONNX模型导出"""
        try:
            # 获取配置参数
            checkpoint_path = self.config['checkpoint_path']
            model_type = self.config['model_type']
            onnx_model_path = self.config['onnx_model_path']
            orig_im_size = self.config['orig_im_size']
            opset_version = self.config['opset_version']
            quantize = self.config['quantize']

            # 1. 加载SAM模型
            self._update_progress(10, "正在加载SAM模型...")

            try:
                sam = sam_model_registry[model_type](checkpoint=checkpoint_path)
                self._update_progress(20, "SAM模型加载完成")
            except Exception as e:
                return False, f"加载SAM模型失败: {str(e)}"

            if self.should_stop:
                return False, "导出被用户中断"

            # 2. 准备ONNX模型
            self._update_progress(30, "正在准备ONNX模型...")

            try:
                onnx_model = SamOnnxModel(sam, return_single_mask=True)
                self._update_progress(40, "ONNX模型准备完成")
            except Exception as e:
                return False, f"准备ONNX模型失败: {str(e)}"

            if self.should_stop:
                return False, "导出被用户中断"

            # 3. 导出ONNX模型
            self._update_progress(50, "正在导出ONNX模型...")

            try:
                # 定义动态轴
                dynamic_axes = {
                    "point_coords": {1: "num_points"},
                    "point_labels": {1: "num_points"},
                }

                # 准备虚拟输入
                embed_dim = sam.prompt_encoder.embed_dim
                embed_size = sam.prompt_encoder.image_embedding_size
                mask_input_size = [4 * x for x in embed_size]
                dummy_inputs = {
                    "image_embeddings": torch.randn(1, embed_dim, *embed_size, dtype=torch.float),
                    "point_coords": torch.randint(low=0, high=1024, size=(1, 5, 2), dtype=torch.float),
                    "point_labels": torch.randint(low=0, high=4, size=(1, 5), dtype=torch.float),
                    "mask_input": torch.randn(1, 1, *mask_input_size, dtype=torch.float),
                    "has_mask_input": torch.tensor([1], dtype=torch.float),
                    "orig_im_size": torch.tensor(orig_im_size, dtype=torch.float),
                }
                output_names = ["masks", "iou_predictions", "low_res_masks"]

                # 导出模型
                import warnings
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=torch.jit.TracerWarning)
                    warnings.filterwarnings("ignore", category=UserWarning)
                    with open(onnx_model_path, "wb") as f:
                        torch.onnx.export(
                            onnx_model,
                            tuple(dummy_inputs.values()),
                            f,
                            export_params=True,
                            verbose=False,
                            opset_version=opset_version,
                            do_constant_folding=True,
                            input_names=list(dummy_inputs.keys()),
                            output_names=output_names,
                            dynamic_axes=dynamic_axes,
                        )

                self._update_progress(80, "ONNX模型导出完成")
            except Exception as e:
                return False, f"导出ONNX模型失败: {str(e)}"

            if self.should_stop:
                return False, "导出被用户中断"

            # 4. 量化（如果启用）
            if quantize:
                self._update_progress(85, "正在量化模型...")

                try:
                    # 检查onnxruntime是否可用
                    if not HAS_ONNXRUNTIME:
                        self._update_progress(90, "警告: onnxruntime库未安装，跳过量化步骤")
                        quantize_str = "未量化（缺少onnxruntime库）"
                    else:
                        import shutil
                        temp_model_path = os.path.join(os.path.split(onnx_model_path)[0], "temp.onnx")
                        shutil.copy(onnx_model_path, temp_model_path)

                        # 直接使用原CLI工具的代码，但使用最简单的参数
                        try:
                            # 尝试使用原CLI工具的完整参数
                            quantize_dynamic(
                                model_input=temp_model_path,
                                model_output=onnx_model_path,
                                optimize_model=True,
                                per_channel=False,
                                reduce_range=False,
                                weight_type=QuantType.QUInt8,
                            )
                        except TypeError:
                            # 如果参数错误，尝试不带optimize_model的版本
                            quantize_dynamic(
                                model_input=temp_model_path,
                                model_output=onnx_model_path,
                                per_channel=False,
                                reduce_range=False,
                                weight_type=QuantType.QUInt8,
                            )

                        os.remove(temp_model_path)
                        quantize_str = "已量化"

                        self._update_progress(95, "模型量化完成")
                except Exception as e:
                    # 如果量化失败，但ONNX模型已经成功导出，我们仍然认为导出成功
                    self._update_progress(95, f"警告: 量化失败，但ONNX模型已导出: {str(e)[:100]}...")
                    quantize_str = "量化失败"
            else:
                self._update_progress(95, "跳过量化步骤")
                quantize_str = "未量化"

            if self.should_stop:
                return False, "导出被用户中断"

            # 5. 完成
            self._update_progress(100, "导出完成")

            # 获取文件大小
            file_size_mb = 0
            if os.path.exists(onnx_model_path):
                file_size_mb = os.path.getsize(onnx_model_path) / (1024 * 1024)

            return True, f"ONNX模型导出成功 ({quantize_str}, 大小: {file_size_mb:.2f}MB)"

        except Exception as e:
            return False, f"导出过程中出错: {str(e)}"

    def _update_progress(self, progress: int, message: str):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(progress, message)


class ONNXExportProcessorThread(QtCore.QThread):
    """ONNX模型导出线程（用于PyQt）"""

    progress_updated = QtCore.pyqtSignal(int, str)
    processing_finished = QtCore.pyqtSignal(bool, str)

    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        self.processor = None

    def run(self):
        """线程运行函数"""
        try:
            self.processor = ONNXExportProcessor(self.config)
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
