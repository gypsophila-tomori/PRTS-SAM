"""
SAM ONNX模型导出工具 - 界面
"""

import os
from pathlib import Path
from PyQt5 import QtWidgets, QtCore, QtGui


class ONNXExportTab(QtWidgets.QWidget):
    """ONNX模型导出标签页"""

    # 定义信号
    progress_updated = QtCore.pyqtSignal(int, str)  # 进度，状态消息
    processing_finished = QtCore.pyqtSignal(bool, str)  # 成功与否，消息

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_processing = False
        self.worker_thread = None
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """设置UI界面"""
        main_layout = QtWidgets.QVBoxLayout(self)

        # 创建一个滚动区域来容纳所有控件
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        # 创建内容部件
        content_widget = QtWidgets.QWidget()
        scroll_area.setWidget(content_widget)

        content_layout = QtWidgets.QVBoxLayout(content_widget)
        content_layout.setSpacing(15)

        # ==================== 输入设置 ====================
        input_group = QtWidgets.QGroupBox("输入设置")
        input_layout = QtWidgets.QVBoxLayout()

        # PyTorch模型选择
        model_layout = QtWidgets.QHBoxLayout()
        model_layout.addWidget(QtWidgets.QLabel("PyTorch模型:"))

        self.checkpoint_edit = QtWidgets.QLineEdit()
        self.checkpoint_edit.setPlaceholderText("选择SAM PyTorch模型文件 (.pth)")
        model_layout.addWidget(self.checkpoint_edit)

        self.browse_checkpoint_btn = QtWidgets.QPushButton("浏览...")
        self.browse_checkpoint_btn.clicked.connect(self.browse_checkpoint_file)
        model_layout.addWidget(self.browse_checkpoint_btn)

        input_layout.addLayout(model_layout)

        # 模型类型选择
        type_layout = QtWidgets.QHBoxLayout()
        type_layout.addWidget(QtWidgets.QLabel("模型类型:"))

        self.model_type_combo = QtWidgets.QComboBox()
        self.model_type_combo.addItems(["default", "vit_h", "vit_l", "vit_b"])
        self.model_type_combo.setCurrentText("default")
        type_layout.addWidget(self.model_type_combo)

        type_layout.addStretch()
        input_layout.addLayout(type_layout)

        input_group.setLayout(input_layout)
        content_layout.addWidget(input_group)

        # ==================== 输出设置 ====================
        output_group = QtWidgets.QGroupBox("输出设置")
        output_layout = QtWidgets.QVBoxLayout()

        # ONNX模型路径
        onnx_layout = QtWidgets.QHBoxLayout()
        onnx_layout.addWidget(QtWidgets.QLabel("ONNX模型路径:"))

        self.onnx_path_edit = QtWidgets.QLineEdit()
        self.onnx_path_edit.setPlaceholderText("输出ONNX模型文件路径 (.onnx)")
        onnx_layout.addWidget(self.onnx_path_edit)

        self.browse_onnx_btn = QtWidgets.QPushButton("浏览...")
        self.browse_onnx_btn.clicked.connect(self.browse_onnx_file)
        onnx_layout.addWidget(self.browse_onnx_btn)

        output_layout.addLayout(onnx_layout)

        # 原始图像尺寸
        size_layout = QtWidgets.QHBoxLayout()
        size_layout.addWidget(QtWidgets.QLabel("原始图像尺寸:"))

        size_layout.addWidget(QtWidgets.QLabel("高度"))
        self.height_spin = QtWidgets.QSpinBox()
        self.height_spin.setRange(1, 10000)
        self.height_spin.setValue(1080)
        size_layout.addWidget(self.height_spin)

        size_layout.addWidget(QtWidgets.QLabel("宽度"))
        self.width_spin = QtWidgets.QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(1920)
        size_layout.addWidget(self.width_spin)

        size_layout.addStretch()
        output_layout.addLayout(size_layout)

        # ONNX版本和量化选项
        options_layout = QtWidgets.QHBoxLayout()
        options_layout.addWidget(QtWidgets.QLabel("ONNX版本:"))

        self.opset_spin = QtWidgets.QSpinBox()
        self.opset_spin.setRange(7, 17)
        self.opset_spin.setValue(15)
        options_layout.addWidget(self.opset_spin)

        self.quantize_checkbox = QtWidgets.QCheckBox("启用8位量化")
        self.quantize_checkbox.setChecked(True)
        self.quantize_checkbox.setToolTip("减小模型大小，但可能损失少量精度")
        options_layout.addWidget(self.quantize_checkbox)

        options_layout.addStretch()
        output_layout.addLayout(options_layout)

        output_group.setLayout(output_layout)
        content_layout.addWidget(output_group)

        # ==================== 处理控制 ====================
        control_group = QtWidgets.QGroupBox("处理控制")
        control_layout = QtWidgets.QVBoxLayout()

        # 进度条
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(True)
        control_layout.addWidget(self.progress_bar)

        # 状态信息
        self.status_label = QtWidgets.QLabel("等待开始导出...")
        self.status_label.setStyleSheet("color: #666;")
        control_layout.addWidget(self.status_label)

        # 控制按钮
        button_layout = QtWidgets.QHBoxLayout()

        self.export_btn = QtWidgets.QPushButton("▶ 开始导出")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.export_btn.clicked.connect(self.start_export)
        button_layout.addWidget(self.export_btn)

        self.stop_btn = QtWidgets.QPushButton("■ 停止")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_export)
        button_layout.addWidget(self.stop_btn)

        button_layout.addStretch()
        control_layout.addLayout(button_layout)

        control_group.setLayout(control_layout)
        content_layout.addWidget(control_group)

        # 添加弹性空间
        content_layout.addStretch()

        # 将滚动区域添加到主布局
        main_layout.addWidget(scroll_area)

    def setup_connections(self):
        """设置信号连接"""
        self.progress_updated.connect(self.update_progress)
        self.processing_finished.connect(self.on_processing_finished)

    def browse_checkpoint_file(self):
        """浏览PyTorch模型文件"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "选择SAM PyTorch模型文件",
            str(Path.home()),
            "PyTorch模型文件 (*.pth);;所有文件 (*.*)"
        )
        if file_path:
            self.checkpoint_edit.setText(file_path)

            # 根据文件名自动建议ONNX输出路径
            if not self.onnx_path_edit.text():
                base_path = os.path.splitext(file_path)[0] + ".onnx"
                self.onnx_path_edit.setText(base_path)

    def browse_onnx_file(self):
        """浏览ONNX输出文件"""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "选择ONNX输出文件路径",
            str(Path.home()),
            "ONNX模型文件 (*.onnx);;所有文件 (*.*)"
        )
        if file_path:
            # 确保扩展名是.onnx
            if not file_path.lower().endswith('.onnx'):
                file_path += '.onnx'
            self.onnx_path_edit.setText(file_path)

    def get_config(self):
        """获取当前配置"""
        config = {
            'checkpoint_path': self.checkpoint_edit.text(),
            'model_type': self.model_type_combo.currentText(),
            'onnx_model_path': self.onnx_path_edit.text(),
            'orig_im_size': [self.height_spin.value(), self.width_spin.value()],
            'opset_version': self.opset_spin.value(),
            'quantize': self.quantize_checkbox.isChecked(),
        }
        return config

    def validate_config(self):
        """验证配置是否有效"""
        config = self.get_config()

        # 检查PyTorch模型文件
        if not config['checkpoint_path']:
            QtWidgets.QMessageBox.warning(self, "警告", "请选择PyTorch模型文件")
            return False

        if not os.path.exists(config['checkpoint_path']):
            QtWidgets.QMessageBox.warning(self, "警告", "PyTorch模型文件不存在")
            return False

        # 检查输出路径
        if not config['onnx_model_path']:
            QtWidgets.QMessageBox.warning(self, "警告", "请指定ONNX输出路径")
            return False

        # 检查输出目录是否存在
        output_dir = os.path.dirname(config['onnx_model_path'])
        if output_dir and not os.path.exists(output_dir):
            # 询问是否创建目录
            reply = QtWidgets.QMessageBox.question(
                self, '确认',
                f'输出目录不存在:\n{output_dir}\n是否创建该目录？',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.Yes
            )
            if reply == QtWidgets.QMessageBox.Yes:
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except Exception as e:
                    QtWidgets.QMessageBox.warning(self, "错误", f"创建目录失败: {str(e)}")
                    return False
            else:
                return False

        # 检查图像尺寸
        if config['orig_im_size'][0] <= 0 or config['orig_im_size'][1] <= 0:
            QtWidgets.QMessageBox.warning(self, "警告", "图像尺寸必须大于0")
            return False

        return True

    def start_export(self):
        """开始导出"""
        if self.is_processing:
            return

        if not self.validate_config():
            return

        # 禁用开始按钮，启用停止按钮
        self.is_processing = True
        self.export_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        # 更新状态
        self.status_label.setText("正在准备导出...")
        self.progress_bar.setValue(0)

        # 创建工作线程
        from utils.onnx_export.processor import ONNXExportProcessorThread

        config = self.get_config()
        self.worker_thread = ONNXExportProcessorThread(config)
        self.worker_thread.progress_updated.connect(self.progress_updated)
        self.worker_thread.processing_finished.connect(self.processing_finished)
        self.worker_thread.start()

    def stop_export(self):
        """停止导出"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.status_label.setText("正在停止...")

    def update_progress(self, progress, message):
        """更新进度"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)

    def on_processing_finished(self, success, message):
        """处理完成事件"""
        self.is_processing = False
        self.export_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        if success:
            self.status_label.setText(f"导出完成: {message}")
            self.progress_bar.setValue(100)

            # 显示成功消息
            QtWidgets.QMessageBox.information(self, "完成", "ONNX模型导出成功！")

            # 可选：打开输出文件所在目录
            config = self.get_config()
            output_path = config['onnx_model_path']
            if os.path.exists(output_path):
                try:
                    import subprocess
                    output_dir = os.path.dirname(output_path)
                    if os.name == 'nt':  # Windows
                        os.startfile(output_dir)
                    elif os.name == 'posix':  # macOS, Linux
                        subprocess.call(['open', output_dir] if sys.platform == 'darwin'
                                        else ['xdg-open', output_dir])
                except Exception as e:
                    print(f"无法打开目录: {e}")
        else:
            self.status_label.setText(f"导出失败: {message}")
            QtWidgets.QMessageBox.warning(self, "错误", f"导出失败: {message}")

    def save_data(self):
        """保存数据（用于主窗口关闭时调用）"""
        # 这里可以保存当前状态
        pass
