"""
图片批量处理工具 - 界面
"""

import os
import sys
import time
from pathlib import Path
from PyQt5 import QtWidgets, QtCore, QtGui

class ImageResizeTab(QtWidgets.QWidget):
    """图片批量处理标签页"""

    # 定义信号
    progress_updated = QtCore.pyqtSignal(int, str)  # 进度，状态消息
    processing_finished = QtCore.pyqtSignal(bool, str)  # 成功与否，消息

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_processing = False
        self.worker_thread = None
        self.total_files = 0  # 添加总文件数跟踪
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

        # ==================== 步骤1：输入设置 ====================
        input_group = QtWidgets.QGroupBox("步骤1：输入设置")
        input_layout = QtWidgets.QVBoxLayout()

        # 图片目录选择
        dir_layout = QtWidgets.QHBoxLayout()
        dir_layout.addWidget(QtWidgets.QLabel("选择图片目录:"))

        self.input_dir_edit = QtWidgets.QLineEdit()
        self.input_dir_edit.setPlaceholderText("请选择包含图片的目录")
        dir_layout.addWidget(self.input_dir_edit)

        self.browse_input_btn = QtWidgets.QPushButton("浏览...")
        self.browse_input_btn.clicked.connect(self.browse_input_dir)
        dir_layout.addWidget(self.browse_input_btn)

        input_layout.addLayout(dir_layout)

        # 文件过滤选项
        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.addWidget(QtWidgets.QLabel("文件过滤:"))

        self.filter_png = QtWidgets.QCheckBox("仅PNG")
        self.filter_jpg = QtWidgets.QCheckBox("仅JPG")
        self.filter_subdir = QtWidgets.QCheckBox("包含子目录")
        self.filter_subdir.setChecked(True)

        filter_layout.addWidget(self.filter_png)
        filter_layout.addWidget(self.filter_jpg)
        filter_layout.addWidget(self.filter_subdir)
        filter_layout.addStretch()

        input_layout.addLayout(filter_layout)

        # 文件统计信息
        self.file_info_label = QtWidgets.QLabel("请选择目录以查看文件信息")
        self.file_info_label.setStyleSheet("color: #666; font-style: italic;")
        input_layout.addWidget(self.file_info_label)

        input_group.setLayout(input_layout)
        content_layout.addWidget(input_group)

        # ==================== 步骤2：缩放设置 ====================
        resize_group = QtWidgets.QGroupBox("步骤2：缩放设置")
        resize_layout = QtWidgets.QVBoxLayout()

        # 缩放模式选择
        mode_layout = QtWidgets.QHBoxLayout()
        mode_layout.addWidget(QtWidgets.QLabel("缩放模式:"))

        self.mode_aspect = QtWidgets.QRadioButton("等比例缩放")
        self.mode_aspect.setChecked(True)
        self.mode_stretch = QtWidgets.QRadioButton("拉伸缩放")
        self.mode_crop = QtWidgets.QRadioButton("裁剪填充")

        mode_layout.addWidget(self.mode_aspect)
        mode_layout.addWidget(self.mode_stretch)
        mode_layout.addWidget(self.mode_crop)
        mode_layout.addStretch()

        resize_layout.addLayout(mode_layout)

        # 目标尺寸设置
        size_layout = QtWidgets.QHBoxLayout()
        size_layout.addWidget(QtWidgets.QLabel("目标尺寸:"))

        size_layout.addWidget(QtWidgets.QLabel("宽度"))
        self.width_spin = QtWidgets.QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(1024)
        size_layout.addWidget(self.width_spin)

        size_layout.addWidget(QtWidgets.QLabel("高度"))
        self.height_spin = QtWidgets.QSpinBox()
        self.height_spin.setRange(1, 10000)
        self.height_spin.setValue(1024)
        size_layout.addWidget(self.height_spin)

        # 锁定宽高比按钮
        self.lock_aspect_btn = QtWidgets.QPushButton("🔒")
        self.lock_aspect_btn.setCheckable(True)
        self.lock_aspect_btn.setChecked(True)
        self.lock_aspect_btn.setMaximumWidth(30)
        self.lock_aspect_btn.setToolTip("锁定宽高比")
        size_layout.addWidget(self.lock_aspect_btn)

        size_layout.addStretch()
        resize_layout.addLayout(size_layout)

        # 格式和质量设置
        format_layout = QtWidgets.QHBoxLayout()
        format_layout.addWidget(QtWidgets.QLabel("输出格式:"))

        self.keep_original = QtWidgets.QRadioButton("保持原始格式")
        self.keep_original.setChecked(True)
        format_layout.addWidget(self.keep_original)

        self.convert_format = QtWidgets.QRadioButton("转换为:")
        format_layout.addWidget(self.convert_format)

        self.format_combo = QtWidgets.QComboBox()
        self.format_combo.addItems(["PNG", "JPEG", "WebP"])
        format_layout.addWidget(self.format_combo)

        format_layout.addStretch()
        resize_layout.addLayout(format_layout)

        # 质量设置（仅JPEG有效）
        quality_layout = QtWidgets.QHBoxLayout()
        quality_layout.addWidget(QtWidgets.QLabel("质量设置:"))

        self.quality_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(90)
        self.quality_slider.setMaximumWidth(150)
        quality_layout.addWidget(self.quality_slider)

        self.quality_label = QtWidgets.QLabel("90% (仅JPEG有效)")
        quality_layout.addWidget(self.quality_label)

        quality_layout.addStretch()
        resize_layout.addLayout(quality_layout)

        resize_group.setLayout(resize_layout)
        content_layout.addWidget(resize_group)

        # ==================== 步骤3：输出设置 ====================
        output_group = QtWidgets.QGroupBox("步骤3：输出设置")
        output_layout = QtWidgets.QVBoxLayout()

        # 输出目录选择
        output_dir_layout = QtWidgets.QHBoxLayout()
        output_dir_layout.addWidget(QtWidgets.QLabel("输出根目录:"))

        self.output_dir_edit = QtWidgets.QLineEdit()
        self.output_dir_edit.setPlaceholderText("选择输出目录")
        output_dir_layout.addWidget(self.output_dir_edit)

        self.browse_output_btn = QtWidgets.QPushButton("浏览...")
        self.browse_output_btn.clicked.connect(self.browse_output_dir)
        output_dir_layout.addWidget(self.browse_output_btn)

        output_layout.addLayout(output_dir_layout)

        # 数据集结构预览
        preview_label = QtWidgets.QLabel("数据集结构预览:")
        preview_label.setStyleSheet("font-weight: bold;")
        output_layout.addWidget(preview_label)

        preview_text = """dataset_name/
├── train/
│   ├── train_001/images/train_00001.png
│   └── ...
└── val/
    ├── val_001/images/val_00001.png
    └── ..."""

        self.preview_text = QtWidgets.QTextEdit()
        self.preview_text.setPlainText(preview_text)
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                font-family: monospace;
            }
        """)
        output_layout.addWidget(self.preview_text)

        # 数据集参数设置
        params_layout = QtWidgets.QGridLayout()

        params_layout.addWidget(QtWidgets.QLabel("数据集名称:"), 0, 0)
        self.dataset_name_edit = QtWidgets.QLineEdit("ieee_apple_dataset")
        params_layout.addWidget(self.dataset_name_edit, 0, 1)

        # 修改这里：将训练集比例改为训练集数量
        params_layout.addWidget(QtWidgets.QLabel("训练集数量:"), 1, 0)
        self.train_count_spin = QtWidgets.QSpinBox()
        self.train_count_spin.setRange(0, 1000000)
        self.train_count_spin.setValue(2000)
        self.train_count_spin.setSuffix("张")
        self.train_count_spin.valueChanged.connect(self.update_val_info)
        params_layout.addWidget(self.train_count_spin, 1, 1)

        params_layout.addWidget(QtWidgets.QLabel("验证集数量:"), 2, 0)
        self.val_count_label = QtWidgets.QLabel("0张")
        params_layout.addWidget(self.val_count_label, 2, 1)

        params_layout.addWidget(QtWidgets.QLabel("每组数量:"), 0, 2)
        self.group_size_spin = QtWidgets.QSpinBox()
        self.group_size_spin.setRange(1, 1000)
        self.group_size_spin.setValue(100)
        self.group_size_spin.setSuffix("张/文件夹")
        params_layout.addWidget(self.group_size_spin, 0, 3)

        params_layout.addWidget(QtWidgets.QLabel("起始编号:"), 1, 2)
        self.start_number_spin = QtWidgets.QSpinBox()
        self.start_number_spin.setRange(1, 99999)
        self.start_number_spin.setValue(1)
        params_layout.addWidget(self.start_number_spin, 1, 3)

        params_layout.addWidget(QtWidgets.QLabel("编号位数:"), 2, 2)
        self.number_digits_spin = QtWidgets.QSpinBox()
        self.number_digits_spin.setRange(1, 10)
        self.number_digits_spin.setValue(5)
        params_layout.addWidget(self.number_digits_spin, 2, 3)

        output_layout.addLayout(params_layout)

        # 选项设置
        options_layout = QtWidgets.QHBoxLayout()

        self.overwrite_checkbox = QtWidgets.QCheckBox("覆盖已有文件")
        options_layout.addWidget(self.overwrite_checkbox)

        self.open_dir_checkbox = QtWidgets.QCheckBox("处理完成后打开输出目录")
        self.open_dir_checkbox.setChecked(True)
        options_layout.addWidget(self.open_dir_checkbox)

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
        self.status_label = QtWidgets.QLabel("等待开始处理...")
        self.status_label.setStyleSheet("color: #666;")
        control_layout.addWidget(self.status_label)

        # 控制按钮
        button_layout = QtWidgets.QHBoxLayout()

        self.start_btn = QtWidgets.QPushButton("▶ 开始处理")
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
        self.start_btn.clicked.connect(self.start_processing)
        button_layout.addWidget(self.start_btn)

        self.stop_btn = QtWidgets.QPushButton("■ 停止")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_processing)
        button_layout.addWidget(self.stop_btn)

        self.save_preset_btn = QtWidgets.QPushButton("✚ 保存预设")
        self.save_preset_btn.clicked.connect(self.save_preset)
        button_layout.addWidget(self.save_preset_btn)

        button_layout.addStretch()
        control_layout.addLayout(button_layout)

        control_group.setLayout(control_layout)
        content_layout.addWidget(control_group)

        # 添加弹性空间
        content_layout.addStretch()

        # 将滚动区域添加到主布局
        main_layout.addWidget(scroll_area)

        # 设置默认值
        self.quality_slider.valueChanged.connect(self.update_quality_label)
        self.width_spin.valueChanged.connect(self.on_width_changed)
        self.height_spin.valueChanged.connect(self.on_height_changed)

    def setup_connections(self):
        """设置信号连接"""
        self.progress_updated.connect(self.update_progress)
        self.processing_finished.connect(self.on_processing_finished)

    def update_quality_label(self, value):
        """更新质量标签"""
        self.quality_label.setText(f"{value}% (仅JPEG有效)")

    def update_val_info(self):
        """更新验证集信息"""
        train_count = self.train_count_spin.value()
        if self.total_files > 0:
            val_count = max(0, self.total_files - train_count)
            self.val_count_label.setText(f"{val_count}张")

            # 如果训练集数量超过总文件数，显示警告
            if train_count > self.total_files:
                self.val_count_label.setStyleSheet("color: #D32F2F; font-weight: bold;")
            else:
                self.val_count_label.setStyleSheet("")

    def on_width_changed(self, value):
        """宽度变化事件"""
        if self.lock_aspect_btn.isChecked() and self.mode_aspect.isChecked():
            # 这里可以根据原始图片的宽高比调整高度，但需要原始图片信息
            # 暂时留空，实际实现时需要获取原始图片信息
            pass

    def on_height_changed(self, value):
        """高度变化事件"""
        if self.lock_aspect_btn.isChecked() and self.mode_aspect.isChecked():
            # 同上
            pass

    def browse_input_dir(self):
        """浏览输入目录"""
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "选择图片目录",
            str(Path.home())
        )
        if dir_path:
            self.input_dir_edit.setText(dir_path)
            self.scan_input_directory(dir_path)

    def browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "选择输出目录",
            str(Path.home())
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)

    def scan_input_directory(self, dir_path):
        """扫描输入目录并统计文件"""
        try:
            from utils.image_resize.utils import scan_image_files

            # 获取过滤选项
            extensions = []
            if self.filter_png.isChecked():
                extensions.append('.png')
            if self.filter_jpg.isChecked():
                extensions.extend(['.jpg', '.jpeg'])

            recursive = self.filter_subdir.isChecked()

            # 扫描文件
            image_files = scan_image_files(dir_path, extensions, recursive)

            # 更新总文件数
            self.total_files = len(image_files)

            # 计算总大小
            total_size = sum(os.path.getsize(f) for f in image_files if os.path.exists(f))
            size_mb = total_size / (1024 * 1024)

            # 更新文件信息
            if image_files:
                self.file_info_label.setText(
                    f"找到 {self.total_files} 张图片 (总计: {size_mb:.2f}MB)"
                )
                self.file_info_label.setStyleSheet("color: #2E7D32; font-weight: bold;")

                # 更新训练集数量最大值
                self.train_count_spin.setMaximum(self.total_files)
                if self.train_count_spin.value() > self.total_files:
                    self.train_count_spin.setValue(self.total_files)

                # 更新验证集信息
                self.update_val_info()
            else:
                self.file_info_label.setText("未找到符合条件的图片文件")
                self.file_info_label.setStyleSheet("color: #D32F2F;")
                self.train_count_spin.setMaximum(0)
                self.val_count_label.setText("0张")

        except Exception as e:
            self.file_info_label.setText(f"扫描目录时出错: {str(e)}")
            self.file_info_label.setStyleSheet("color: #D32F2F;")

    def get_config(self):
        """获取当前配置"""
        config = {
            # 输入设置
            'input_dir': self.input_dir_edit.text(),
            'filter_png': self.filter_png.isChecked(),
            'filter_jpg': self.filter_jpg.isChecked(),
            'recursive': self.filter_subdir.isChecked(),

            # 缩放设置
            'mode': 'aspect' if self.mode_aspect.isChecked() else
                   'stretch' if self.mode_stretch.isChecked() else 'crop',
            'target_width': self.width_spin.value(),
            'target_height': self.height_spin.value(),
            'keep_original_format': self.keep_original.isChecked(),
            'output_format': self.format_combo.currentText().lower(),
            'quality': self.quality_slider.value(),

            # 输出设置
            'output_dir': self.output_dir_edit.text(),
            'dataset_name': self.dataset_name_edit.text(),
            'train_count': self.train_count_spin.value(),  # 改为训练集数量
            'group_size': self.group_size_spin.value(),
            'start_number': self.start_number_spin.value(),
            'number_digits': self.number_digits_spin.value(),
            'overwrite': self.overwrite_checkbox.isChecked(),
            'open_dir_after': self.open_dir_checkbox.isChecked(),
        }
        return config

    def validate_config(self):
        """验证配置是否有效"""
        config = self.get_config()

        # 检查输入目录
        if not config['input_dir'] or not os.path.exists(config['input_dir']):
            QtWidgets.QMessageBox.warning(self, "警告", "请输入有效的输入目录")
            return False

        # 检查输出目录
        if not config['output_dir']:
            QtWidgets.QMessageBox.warning(self, "警告", "请输入输出目录")
            return False

        # 检查至少选择一种图片格式
        if not config['filter_png'] and not config['filter_jpg']:
            QtWidgets.QMessageBox.warning(self, "警告", "请至少选择一种图片格式")
            return False

        # 检查目标尺寸
        if config['target_width'] <= 0 or config['target_height'] <= 0:
            QtWidgets.QMessageBox.warning(self, "警告", "目标尺寸必须大于0")
            return False

        # 检查数据集名称
        if not config['dataset_name']:
            QtWidgets.QMessageBox.warning(self, "警告", "请输入数据集名称")
            return False

        # 检查训练集数量
        if config['train_count'] <= 0:
            QtWidgets.QMessageBox.warning(self, "警告", "训练集数量必须大于0")
            return False

        return True

    def start_processing(self):
        """开始处理"""
        if self.is_processing:
            return

        if not self.validate_config():
            return

        # 检查训练集数量是否超过总文件数
        config = self.get_config()
        if self.total_files > 0 and config['train_count'] > self.total_files:
            QtWidgets.QMessageBox.warning(
                self,
                "警告",
                f"训练集数量({config['train_count']})超过总文件数({self.total_files})"
            )
            return

        # 禁用开始按钮，启用停止按钮
        self.is_processing = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        # 更新状态
        self.status_label.setText("正在处理...")
        self.progress_bar.setValue(0)

        # 创建工作线程
        from utils.image_resize.processor import ImageProcessorThread

        self.worker_thread = ImageProcessorThread(config)
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

            # 如果设置了打开目录，则打开输出目录
            config = self.get_config()
            if config['open_dir_after']:
                output_path = os.path.join(
                    config['output_dir'],
                    config['dataset_name']
                )
                if os.path.exists(output_path):
                    try:
                        if os.name == 'nt':  # Windows
                            os.startfile(output_path)
                        elif os.name == 'posix':  # macOS, Linux
                            import subprocess
                            subprocess.call(['open', output_path] if sys.platform == 'darwin'
                                          else ['xdg-open', output_path])
                    except Exception as e:
                        print(f"无法打开目录: {e}")

            QtWidgets.QMessageBox.information(self, "完成", "图片处理完成！")
        else:
            self.status_label.setText(f"处理失败: {message}")
            QtWidgets.QMessageBox.warning(self, "错误", f"处理失败: {message}")

    def save_preset(self):
        """保存预设"""
        config = self.get_config()

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "保存预设",
            str(Path.home() / "image_resize_preset.json"),
            "JSON文件 (*.json)"
        )

        if file_path:
            try:
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)

                QtWidgets.QMessageBox.information(self, "成功", "预设已保存")
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "错误", f"保存预设失败: {str(e)}")

    def load_preset(self, file_path):
        """加载预设"""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 应用配置到UI
            self.apply_config(config)
            QtWidgets.QMessageBox.information(self, "成功", "预设已加载")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "错误", f"加载预设失败: {str(e)}")

    def apply_config(self, config):
        """应用配置到UI"""
        # 这里需要实现将配置应用到各个UI控件
        # 由于时间关系，这里简化处理
        pass

    def save_data(self):
        """保存数据（用于主窗口关闭时调用）"""
        # 这里可以保存当前状态
        pass
