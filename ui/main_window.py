"""
主窗口模块
"""

import os
import json
from pathlib import Path
from PyQt5 import QtWidgets, QtCore, QtGui

class MainWindow(QtWidgets.QMainWindow):
    """主窗口类"""

    def __init__(self, debug=False, config_path=None, parent=None):
        super().__init__(parent)
        self.debug = debug
        self.config_path = config_path
        self.config = {}

        self.setup_ui()
        self.load_config()
        self.setup_connections()

        if debug:
            print("调试模式已启用")

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("PRTS-SAM 工具套件")
        self.resize(1200, 800)

        # 设置窗口图标
        icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(icon_path)))

        # 创建中心部件和主布局
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QtWidgets.QVBoxLayout(self.central_widget)

        # 创建标签页容器
        self.tab_widget = QtWidgets.QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        # 创建状态栏
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")

        # 创建菜单栏
        self.create_menus()

        # 创建工具栏
        self.create_toolbar()

        # 加载所有标签页
        self.load_tabs()

    def create_menus(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        new_action = QtWidgets.QAction("新建项目", self)
        new_action.setShortcut("Ctrl+N")
        file_menu.addAction(new_action)

        open_action = QtWidgets.QAction("打开项目", self)
        open_action.setShortcut("Ctrl+O")
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QtWidgets.QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 工具菜单
        tools_menu = menubar.addMenu("工具")

        settings_action = QtWidgets.QAction("设置", self)
        settings_action.triggered.connect(self.open_settings)
        tools_menu.addAction(settings_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        about_action = QtWidgets.QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("工具")

        # 添加常用工具
        home_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("go-home"), "主页", self)
        home_action.triggered.connect(self.go_home)
        toolbar.addAction(home_action)

        toolbar.addSeparator()

        refresh_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("view-refresh"), "刷新", self)
        refresh_action.triggered.connect(self.refresh_tabs)
        toolbar.addAction(refresh_action)

    def load_tabs(self):
        """加载所有标签页"""
        # 导入并添加各个标签页
        try:
            from ui.image_resize import ImageResizeTab
            self.image_resize_tab = ImageResizeTab()
            self.tab_widget.addTab(self.image_resize_tab, "📷 图片处理")
        except ImportError as e:
            if self.debug:
                print(f"无法加载图片处理标签页: {e}")

        try:
            from ui.sam_embeddings import SAMEmbeddingsTab
            self.sam_embeddings_tab = SAMEmbeddingsTab()
            self.tab_widget.addTab(self.sam_embeddings_tab, "🧠 SAM嵌入向量")
        except ImportError as e:
            if self.debug:
                print(f"无法加载SAM嵌入向量标签页: {e}")

        try:
            from ui.onnx_export import ONNXExportTab
            self.onnx_export_tab = ONNXExportTab()
            self.tab_widget.addTab(self.onnx_export_tab, "⚡ ONNX导出")
        except ImportError as e:
            if self.debug:
                print(f"无法加载ONNX导出标签页: {e}")

        try:
            # 原有的SAM标注工具
            from ui.sam_annotator import SAMAnnotatorTab
            self.sam_tab = SAMAnnotatorTab()
            self.tab_widget.addTab(self.sam_tab, "🎯 SAM标注")
        except ImportError as e:
            if self.debug:
                print(f"无法加载SAM标注标签页: {e}")

        # 添加更多标签页的占位
        self.tab_widget.addTab(QtWidgets.QWidget(), "📊 批量处理")
        self.tab_widget.addTab(QtWidgets.QWidget(), "⚙️ 设置")

    def refresh_tabs(self):
        """刷新标签页"""
        current_index = self.tab_widget.currentIndex()
        self.tab_widget.clear()
        self.load_tabs()
        self.tab_widget.setCurrentIndex(min(current_index, self.tab_widget.count() - 1))
        self.status_bar.showMessage("标签页已刷新", 2000)

    def load_config(self):
        """加载配置文件"""
        if self.config_path and os.path.exists(self.config_path):
            config_file = self.config_path
        else:
            config_file = Path.home() / ".prts_sam_config.json"

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                if self.debug:
                    print(f"配置文件已加载: {config_file}")
            except Exception as e:
                print(f"加载配置文件失败: {e}")

    def save_config(self):
        """保存配置文件"""
        config_file = Path.home() / ".prts_sam_config.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            if self.debug:
                print(f"配置文件已保存: {config_file}")
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def open_settings(self):
        """打开设置对话框"""
        settings_dialog = QtWidgets.QDialog(self)
        settings_dialog.setWindowTitle("设置")
        settings_dialog.resize(400, 300)

        layout = QtWidgets.QVBoxLayout()

        # 添加设置选项
        debug_checkbox = QtWidgets.QCheckBox("启用调试模式")
        debug_checkbox.setChecked(self.debug)
        layout.addWidget(debug_checkbox)

        # 按钮
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(settings_dialog.accept)
        button_box.rejected.connect(settings_dialog.reject)
        layout.addWidget(button_box)

        settings_dialog.setLayout(layout)

        if settings_dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.debug = debug_checkbox.isChecked()
            self.status_bar.showMessage("设置已更新", 2000)

    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h1>PRTS-SAM 工具套件</h1>
        <p>版本: 1.0.0</p>
        <p>基于 Meta AI 的 Segment Anything Model</p>
        <p>提供图片处理、SAM嵌入向量生成、ONNX模型导出等功能</p>
        <hr>
        <p>© 2024 PRTS 实验室</p>
        """
        QtWidgets.QMessageBox.about(self, "关于 PRTS-SAM", about_text)

    def go_home(self):
        """回到第一个标签页"""
        self.tab_widget.setCurrentIndex(0)

    def closeEvent(self, event):
        """关闭事件"""
        self.save_config()
        # 通知所有标签页保存数据
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if hasattr(tab, 'save_data'):
                tab.save_data()

        if self.debug:
            print("应用程序正在关闭...")

        event.accept()

    def setup_connections(self):
        """设置信号连接"""
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        """标签页切换事件"""
        tab_name = self.tab_widget.tabText(index)
        self.status_bar.showMessage(f"当前标签页: {tab_name}", 2000)
