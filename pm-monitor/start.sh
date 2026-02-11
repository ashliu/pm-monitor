#!/bin/bash
# PM-Monitor 启动脚本

echo "========================================="
echo "  PM-Monitor 功率监测系统"
echo "========================================="
echo ""

# 检查 Python 版本
python3 --version

# 进入 src 目录
cd "$(dirname "$0")/src"

echo "正在启动程序..."
echo ""

# 启动主程序
python3 main.py

echo ""
echo "程序已退出"
