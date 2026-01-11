"""
SAM交互式标注工具 - 界面
"""

import os
from pathlib import Path
from PyQt5 import QtWidgets, QtCore, QtGui

class SAMAnnotatorTab(QtWidgets.QWidget):
    """SAM标注标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.editor = None
        self.annotation_interface = None
        self.is_annotating = False
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """设置UI界面"""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(10)

        # ==================== 配置区域 ====================
        config_group = QtWidgets.QGroupBox("标注配置")
        config_layout = QtWidgets.QVBoxLayout()

        # ONNX模型路径
        onnx_layout = QtWidgets.QHBoxLayout()
        onnx_layout.addWidget(QtWidgets.QLabel("ONNX模型:"))

        self.onnx_path_edit = QtWidgets.QLineEdit()
        self.onnx_path_edit.setPlaceholderText("选择ONNX模型文件 (.onnx)")
        onnx_layout.addWidget(self.onnx_path_edit)

        self.browse_onnx_btn = QtWidgets.QPushButton("浏览...")
        self.browse_onnx_btn.clicked.connect(self.browse_onnx_file)
        onnx_layout.addWidget(self.browse_onnx_btn)

        config_layout.addLayout(onnx_layout)

        # 数据集目录
        dataset_layout = QtWidgets.QHBoxLayout()
        dataset_layout.addWidget(QtWidgets.QLabel("数据集目录:"))

        self.dataset_path_edit = QtWidgets.QLineEdit()
        self.dataset_path_edit.setPlaceholderText("选择包含images文件夹的数据集目录")
        dataset_layout.addWidget(self.dataset_path_edit)

        self.browse_dataset_btn = QtWidgets.QPushButton("浏览...")
        self.browse_dataset_btn.clicked.connect(self.browse_dataset_dir)
        dataset_layout.addWidget(self.browse_dataset_btn)

        config_layout.addLayout(dataset_layout)

        # 类别设置
        categories_layout = QtWidgets.QHBoxLayout()
        categories_layout.addWidget(QtWidgets.QLabel("类别(逗号分隔):"))

        self.categories_edit = QtWidgets.QLineEdit()
        self.categories_edit.setPlaceholderText("例如: good_apple,bad_apple,leaf")
        categories_layout.addWidget(self.categories_edit)

        config_layout.addLayout(categories_layout)

        # 标注文件路径
        annotation_layout = QtWidgets.QHBoxLayout()
        annotation_layout.addWidget(QtWidgets.QLabel("标注文件:"))

        self.annotation_path_edit = QtWidgets.QLineEdit()
        self.annotation_path_edit.setPlaceholderText("COCO格式标注文件路径 (默认: annotations.json)")
        annotation_layout.addWidget(self.annotation_path_edit)

        self.browse_annotation_btn = QtWidgets.QPushButton("浏览...")
        self.browse_annotation_btn.clicked.connect(self.browse_annotation_file)
        annotation_layout.addWidget(self.browse_annotation_btn)

        config_layout.addLayout(annotation_layout)

        # 开始/停止按钮
        control_layout = QtWidgets.QHBoxLayout()

        self.start_btn = QtWidgets.QPushButton("▶ 开始标注")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        control_layout.addWidget(self.start_btn)

        self.stop_btn = QtWidgets.QPushButton("■ 停止标注")
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)

        control_layout.addStretch()
        config_layout.addLayout(control_layout)

        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # ==================== 状态信息 ====================
        status_layout = QtWidgets.QHBoxLayout()
        self.status_label = QtWidgets.QLabel("等待开始标注...")
        self.status_label.setStyleSheet("color: #666;")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()
        main_layout.addLayout(status_layout)

        # ==================== 标注界面容器 ====================
        self.annotation_container = QtWidgets.QWidget()
        self.annotation_container.setVisible(False)
        annotation_layout = QtWidgets.QVBoxLayout(self.annotation_container)
        annotation_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addWidget(self.annotation_container)

        # 添加弹性空间
        main_layout.addStretch()

    def setup_connections(self):
        """设置信号连接"""
        self.start_btn.clicked.connect(self.start_annotation)
        self.stop_btn.clicked.connect(self.stop_annotation)

        # 路径变化时自动更新标注文件路径
        self.dataset_path_edit.textChanged.connect(self.update_annotation_path)

    def browse_onnx_file(self):
        """浏览ONNX模型文件"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "选择ONNX模型文件",
            str(Path.home()),
            "ONNX模型文件 (*.onnx);;所有文件 (*.*)"
        )
        if file_path:
            self.onnx_path_edit.setText(file_path)

    def browse_dataset_dir(self):
        """浏览数据集目录"""
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "选择数据集目录",
            str(Path.home())
        )
        if dir_path:
            self.dataset_path_edit.setText(dir_path)

    def browse_annotation_file(self):
        """浏览标注文件"""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "选择标注文件路径",
            str(Path.home()),
            "JSON文件 (*.json);;所有文件 (*.*)"
        )
        if file_path:
            if not file_path.lower().endswith('.json'):
                file_path += '.json'
            self.annotation_path_edit.setText(file_path)

    def update_annotation_path(self):
        """自动更新标注文件路径"""
        dataset_path = self.dataset_path_edit.text()
        if dataset_path and not self.annotation_path_edit.text():
            default_path = os.path.join(dataset_path, "annotations.json")
            self.annotation_path_edit.setText(default_path)

    def get_config(self):
        """获取当前配置"""
        config = {
            'onnx_model_path': self.onnx_path_edit.text(),
            'dataset_path': self.dataset_path_edit.text(),
            'annotation_path': self.annotation_path_edit.text(),
            'categories': self.categories_edit.text(),
        }
        return config

    def validate_config(self):
        """验证配置是否有效"""
        config = self.get_config()

        # 检查ONNX模型文件
        if not config['onnx_model_path']:
            QtWidgets.QMessageBox.warning(self, "警告", "请选择ONNX模型文件")
            return False

        if not os.path.exists(config['onnx_model_path']):
            QtWidgets.QMessageBox.warning(self, "警告", "ONNX模型文件不存在")
            return False

        # 检查数据集目录
        if not config['dataset_path']:
            QtWidgets.QMessageBox.warning(self, "警告", "请选择数据集目录")
            return False

        if not os.path.exists(config['dataset_path']):
            QtWidgets.QMessageBox.warning(self, "警告", "数据集目录不存在")
            return False

        # 检查images子目录
        images_folder = os.path.join(config['dataset_path'], "images")
        if not os.path.exists(images_folder):
            QtWidgets.QMessageBox.warning(self, "警告", f"数据集目录下没有找到images子目录: {images_folder}")
            return False

        return True

    def start_annotation(self):
        """开始标注"""
        if self.is_annotating:
            return

        if not self.validate_config():
            return

        try:
            # 获取配置
            config = self.get_config()
            onnx_model_path = config['onnx_model_path']
            dataset_path = config['dataset_path']
            annotation_path = config['annotation_path']

            # 处理类别
            categories = None
            if config['categories'].strip():
                categories = [cat.strip() for cat in config['categories'].split(',') if cat.strip()]

            # 创建Editor实例
            from utils.sam_annotator import Editor
            self.editor = Editor(
                onnx_model_path=onnx_model_path,
                dataset_path=dataset_path,
                categories=categories,
                coco_json_path=annotation_path
            )

            # 创建标注界面
            from utils.sam_annotator import ApplicationInterface
            self.annotation_interface = ApplicationInterface(self.annotation_container, self.editor)

            # 清除容器中的旧内容并添加新界面
            layout = self.annotation_container.layout()
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            layout.addWidget(self.annotation_interface)

            # 更新状态
            self.is_annotating = True
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText(f"正在标注: {os.path.basename(dataset_path)}")
            self.annotation_container.setVisible(True)

            # 聚焦到标注界面以便接收键盘事件
            self.annotation_interface.setFocus()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"启动标注失败: {str(e)}")

    def stop_annotation(self):
        """停止标注"""
        if not self.is_annotating:
            return

        # 保存当前标注
        if self.editor:
            try:
                self.editor.save()
                self.status_label.setText("标注已保存")
            except Exception as e:
                self.status_label.setText(f"保存失败: {str(e)}")

        # 清理界面
        self.is_annotating = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.annotation_container.setVisible(False)

        # 清理资源
        self.editor = None
        if self.annotation_interface:
            self.annotation_interface.deleteLater()
            self.annotation_interface = None

    def save_data(self):
        """保存数据（用于主窗口关闭时调用）"""
        if self.is_annotating and self.editor:
            try:
                self.editor.save()
                self.status_label.setText("标注已自动保存")
            except Exception as e:
                self.status_label.setText(f"自动保存失败: {str(e)}")
