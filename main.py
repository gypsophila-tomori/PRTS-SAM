#!/usr/bin/env python3
"""
PRTS-SAM: SAM标注与图像处理工具
主程序入口
"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='PRTS-SAM')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--config', type=str, default=None, help='配置文件路径')
    return parser.parse_args()


def check_dependencies():
    """检查依赖"""
    try:
        from PyQt5 import QtWidgets
        return True
    except ImportError as e:
        print(f"错误: 缺少依赖 - {e}")
        print("请安装依赖: pip install PyQt5")
        return False


def main():
    """主函数"""
    args = parse_args()

    if not check_dependencies():
        sys.exit(1)

    # 设置应用
    from PyQt5 import QtWidgets, QtGui
    from ui.main_window import MainWindow

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("PRTS-SAM")
    app.setOrganizationName("PRTS")

    # 设置样式
    app.setStyle('Fusion')

    # 创建主窗口
    window = MainWindow(debug=args.debug, config_path=args.config)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
