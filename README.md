# pm-monitor

基于 PyQt5 的功率计数据监测系统，支持实时采集、显示和导出功率数据。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ 功能特性

- 📊 **实时监测** - 读取功率计数据，实时显示测量值
- 📈 **数据可视化** - 实时功率曲线，显示 Max/Min/RMS 统计值
- 💾 **数据导出** - 支持 CSV 格式导出，便于后续分析
- 🔌 **多种连接方式** - 支持 TCP/IP、USB、串口等 VISA 连接
- 🧪 **Mock 模式** - 无需硬件即可测试所有功能

## 🚀 快速开始

### 安装依赖

```bash
# 完整安装（使用真实功率计）
pip install -r pm-monitor/requirements.txt

# 仅模拟模式（无需硬件）
pip install PyQt5 pyqtgraph numpy
```

### 运行程序

```bash
# GUI 模式
./pm-monitor/start.sh

# 命令行测试 Mock 功能
python3 pm-monitor/test_mock.py
```

## 📖 使用说明

### 1. 连接设备
- 点击 **"刷新设备列表"** 扫描 VISA 设备
- 选择或输入 VISA 资源字符串（如 `TCPIP::192.168.1.100::5025::SOCKET`）
- 点击 **"连接设备"**

> 💡 **提示**：没有硬件时选择 `MOCK::PowerMeter::1` 使用模拟数据

### 2. 开始测量
- 设置采样间隔（10-5000 ms）
- 点击 **"开始测量"**
- 实时查看功率曲线和统计值

### 3. 导出数据
- 点击 **"导出数据 (CSV)"**
- 选择保存位置
- 数据包含时间、功率、平均值、RMS

## 🧪 Mock 模式

无需功率计硬件即可测试所有功能：

```bash
python3 pm-monitor/test_mock.py
```

模拟数据特点：
- 基础功率：约 50W
- 随机噪声、缓慢趋势变化、周期性波动
- 与真实数据行为相似

## 📁 项目结构

```
pm-monitor/
├── README.md           # 详细说明文档
├── requirements.txt    # Python 依赖
├── start.sh           # 启动脚本
├── test_mock.py       # Mock 测试脚本
├── docs/              # 设计文档
│   ├── interface.md   # 界面设计
│   └── protocol.md    # 通信协议
└── src/               # 源代码
    ├── main.py        # 程序入口
    ├── main_window.py # 主窗口 UI
    └── mock_visa.py   # Mock VISA 模块
```

## 🔧 支持的功率计

支持任何符合 NI-VISA 标准的功率计：

- YOKOGAWA (横河) WT 系列
- KEITHLEY (吉时利) 系列仪表
- Chroma (致茂) 负载仪
- Fluke (福禄克) 功率分析仪
- 其他支持 SCPI 命令的仪表

## 🛠️ 技术栈

- **Python 3.x** - 核心语言
- **PyQt5** - GUI 框架
- **pyqtgraph** - 高性能实时绘图
- **pyvisa + pyvisa-py** - NI-VISA 仪器通信

## 📄 详细文档

- [界面设计文档](pm-monitor/docs/interface.md) - UI 布局和配色方案
- [通信协议文档](pm-monitor/docs/protocol.md) - SCPI 命令和 VISA 操作
- [pm-monitor/README.md](pm-monitor/README.md) - 完整使用手册

## 📝 License

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**Made with ❤️ by ash**
