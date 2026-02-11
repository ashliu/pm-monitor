#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PM-Monitor 主程序入口
"""

import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_window import PMMonitorMainWindow


def main():
    """主函数"""
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用 Fusion 风格

    # 创建并显示主窗口
    window = PMMonitorMainWindow()
    window.show()

    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
