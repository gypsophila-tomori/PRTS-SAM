"""
SAM嵌入向量生成工具 - 界面
"""

import os
from pathlib import Path
from PyQt5 import QtWidgets, QtCore, QtGui

class SAMEmbeddingsTab(QtWidgets.QWidget):
    """SAM嵌入向量生成标签页"""

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

        # ==================== 模型设置 ====================
        model_group = QtWidgets.QGroupBox("模型设置")
        model_layout = QtWidgets.QVBoxLayout()

        # 模型类型选择
        type_layout = QtWidgets.QHBoxLayout()
        type_layout.addWidget(QtWidgets.QLabel("模型类型:"))

        self.model_type_combo = QtWidgets.QComboBox()
        self.model_type_combo.addItems(["default", "vit_h", "vit_l", "vit_b"])
        self.model_type_combo.setCurrentText("default")
        type_layout.addWidget(self.model_type_combo)

        type_layout.addStretch()
        model_layout.addLayout(type_layout)

        # 权重文件选择
        weight_layout = QtWidgets.QHBoxLayout()
        weight_layout.addWidget(QtWidgets.QLabel("权重文件:"))

        self.weight_path_edit = QtWidgets.QLineEdit()
        self.weight_path_edit.setPlaceholderText("选择SAM模型权重文件 (.pth)")
        weight_layout.addWidget(self.weight_path_edit)

        self.browse_weight_btn = QtWidgets.QPushButton("浏览...")
        self.browse_weight_btn.clicked.connect(self.browse_weight_file)
        weight_layout.addWidget(self.browse_weight_btn)

        model_layout.addLayout(weight_layout)

        # 设备选择
        device_layout = QtWidgets.QHBoxLayout()
        device_layout.addWidget(QtWidgets.QLabel("运行设备:"))

        self.device_combo = QtWidgets.QComboBox()
        self.device_combo.addItems(["cuda", "cpu"])
        device_layout.addWidget(self.device_combo)

        device_layout.addStretch()
        model_layout.addLayout(device_layout)

        model_group.setLayout(model_layout)
        content_layout.addWidget(model_group)

        # ==================== 数据集设置 ====================
        dataset_group = QtWidgets.QGroupBox("数据集设置")
        dataset_layout = QtWidgets.QVBoxLayout()

        # 数据集目录选择
        dataset_dir_layout = QtWidgets.QHBoxLayout()
        dataset_dir_layout.addWidget(QtWidgets.QLabel("根目录:"))

        self.dataset_dir_edit = QtWidgets.QLineEdit()
        self.dataset_dir_edit.setPlaceholderText("选择数据集根目录")
        dataset_dir_layout.addWidget(self.dataset_dir_edit)

        self.browse_dataset_btn = QtWidgets.QPushButton("浏览...")
        self.browse_dataset_btn.clicked.connect(self.browse_dataset_dir)
        dataset_dir_layout.addWidget(self.browse_dataset_btn)

        dataset_layout.addLayout(dataset_dir_layout)

        # 扫描模式选择
        mode_layout = QtWidgets.QHBoxLayout()
        mode_layout.addWidget(QtWidgets.QLabel("扫描模式:"))

        self.scan_mode_combo = QtWidgets.QComboBox()
        self.scan_mode_combo.addItems(["传统模式", "分组模式"])
        self.scan_mode_combo.setToolTip("传统模式: 只处理根目录下的images文件夹\n分组模式: 递归扫描所有子文件夹中的images文件夹")
        mode_layout.addWidget(self.scan_mode_combo)

        mode_layout.addStretch()
        dataset_layout.addLayout(mode_layout)

        # 目录结构说明
        dir_structure_label = QtWidgets.QLabel("目录结构说明:")
        dir_structure_label.setStyleSheet("font-weight: bold;")
        dataset_layout.addWidget(dir_structure_label)

        structure_text = """传统模式（处理单个images文件夹）:
根目录/
├── images/          # 图片目录（必需）
│   ├── image1.jpg
│   ├── image2.png
│   └── ...
└── embeddings/      # 输出目录（自动创建）
    ├── image1.npy
    ├── image2.npy
    └── ...

分组模式（处理多个images子文件夹）:
根目录/
├── train_001/
│   ├── images/     # 图片目录
│   │   ├── train_00001.png
│   │   └── ...
│   └── embeddings/ # 输出目录（自动创建）
├── train_002/
│   ├── images/
│   └── embeddings/
└── ..."""

        self.structure_text = QtWidgets.QTextEdit()
        self.structure_text.setPlainText(structure_text)
        self.structure_text.setMaximumHeight(180)
        self.structure_text.setReadOnly(True)
        self.structure_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                font-family: monospace;
                font-size: 10pt;
            }
        """)
        dataset_layout.addWidget(self.structure_text)

        dataset_group.setLayout(dataset_layout)
        content_layout.addWidget(dataset_group)

        # ==================== 处理控制 ====================
        control_group = QtWidgets.QGroupBox("处理控制")
        control_layout = QtWidgets.QVBoxLayout()

        # 进度条
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(True)
        control_layout.addWidget(self.progress_bar)

        # 状态信息
        self.status_label = QtWidgets.QLabel("等待开始处理...")
        self.status_label.setStyleSheet("color: #666;")
        control_layout.addWidget(self.status_label)

        # 控制按钮
        button_layout = QtWidgets.QHBoxLayout()

        self.start_btn = QtWidgets.QPushButton("▶ 开始生成")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.start_btn.clicked.connect(self.start_processing)
        button_layout.addWidget(self.start_btn)

        self.stop_btn = QtWidgets.QPushButton("■ 停止")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_processing)
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

    def browse_weight_file(self):
        """浏览权重文件"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "选择SAM模型权重文件",
            str(Path.home()),
            "PyTorch模型文件 (*.pth);;所有文件 (*.*)"
        )
        if file_path:
            self.weight_path_edit.setText(file_path)

    def browse_dataset_dir(self):
        """浏览数据集目录"""
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "选择数据集根目录",
            str(Path.home())
        )
        if dir_path:
            self.dataset_dir_edit.setText(dir_path)

    def get_config(self):
        """获取当前配置"""
        config = {
            'checkpoint_path': self.weight_path_edit.text(),
            'model_type': self.model_type_combo.currentText(),
            'device': self.device_combo.currentText(),
            'dataset_root': self.dataset_dir_edit.text(),
            'scan_mode': self.scan_mode_combo.currentText(),  # "传统模式" 或 "分组模式"
        }
        return config

    def validate_config(self):
        """验证配置是否有效"""
        config = self.get_config()

        # 检查权重文件
        if not config['checkpoint_path']:
            QtWidgets.QMessageBox.warning(self, "警告", "请选择SAM模型权重文件")
            return False

        if not os.path.exists(config['checkpoint_path']):
            QtWidgets.QMessageBox.warning(self, "警告", "权重文件不存在")
            return False

        # 检查根目录
        if not config['dataset_root']:
            QtWidgets.QMessageBox.warning(self, "警告", "请选择数据集根目录")
            return False

        if not os.path.exists(config['dataset_root']):
            QtWidgets.QMessageBox.warning(self, "警告", "数据集根目录不存在")
            return False

        return True

    def start_processing(self):
        """开始处理"""
        if self.is_processing:
            return

        if not self.validate_config():
            return

        # 禁用开始按钮，启用停止按钮
        self.is_processing = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        # 更新状态
        self.status_label.setText("正在扫描目录结构...")
        self.progress_bar.setValue(0)

        # 创建工作线程
        from utils.sam_embeddings.processor import SAMEmbeddingsProcessorThread

        config = self.get_config()
        self.worker_thread = SAMEmbeddingsProcessorThread(config)
        self.worker_thread.progress_updated.connect(self.progress_updated)
        self.worker_thread.processing_finished.connect(self.processing_finished)
        self.worker_thread.start()

    def stop_processing(self):
        """停止处理"""
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
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        if success:
            self.status_label.setText(f"处理完成: {message}")
            self.progress_bar.setValue(100)
            QtWidgets.QMessageBox.information(self, "完成", "SAM嵌入向量生成完成！")
        else:
            self.status_label.setText(f"处理失败: {message}")
            QtWidgets.QMessageBox.warning(self, "错误", f"处理失败: {message}")

    def save_data(self):
        """保存数据（用于主窗口关闭时调用）"""
        # 这里可以保存当前状态
        pass
