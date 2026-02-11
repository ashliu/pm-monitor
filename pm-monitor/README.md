# PM-Monitor 功率监测系统

基于 PyQt5 的功率计数据监测系统。

## 功能特性

- 读取功率计数据（通过 NI-VISA 驱动）
- 实时显示测量值
- 记录测量期间的最大值、最小值、RMS值
- 实时曲线显示
- 支持 TCP/IP、USB、串口等多种连接方式
- 数据导出（CSV 格式）

## 界面布局

```
┌─────────────────────────────────────────────┐
│  操作区                │    数据显示区   │
│                      │  ┌──────────┐  │
│  - VISA 连接           │  │ Max:      │  │
│  - 开始测量             │  │ Min:      │  │
│  - 停止测量             │  │ RMS:      │  │
│  - 重置数据             │  │ Current:  │  │
│  - 采样间隔             │  └──────────┘  │
│                      │                │
│                      │   曲线显示区   │
│                      │  ┌──────────┐  │
│                      │  │          │  │
│                      │  │  曲线   │  │
│                      │  │          │  │
│                      │  └──────────┘  │
└─────────────────────────────────────────────┘
```

## 技术栈

- Python 3.x
- PyQt5
- pyqtgraph (用于高性能绘图)
- pyvisa + pyvisa-py (用于 NI-VISA 仪器通信)

## 安装依赖

### 使用 pip 安装

```bash
pip install -r requirements.txt
```

或单独安装：

```bash
pip install PyQt5 pyqtgraph pyvisa pyvisa-py numpy
```

### 可选：安装 NI-VISA 运行时

如果需要使用 NI 官方驱动（性能更好），请从 NI 官网下载：

https://www.ni.com/zh-cn/support/downloads/drivers/

推荐使用 NI-VISA 21.0 或更高版本。

## 运行

```bash
cd pm-monitor

# 方式 1：使用启动脚本
./start.sh

# 方式 2：直接运行
cd src
python3 main.py
```

## 使用说明

1. **连接设备**
   - 点击"刷新设备列表"扫描 VISA 设备
   - 选择或输入 VISA 资源字符串（如 `TCPIP::192.168.1.100::5025::SOCKET`）
   - 点击"连接设备"

2. **配置命令**
   - 设置功率查询命令（默认为 `MEAS:POW?`）
   - 根据功率计型号调整命令

3. **开始测量**
   - 设置采样间隔（10-5000 ms）
   - 点击"开始测量"
   - 实时查看功率曲线和统计值

4. **停止测量**
   - 点击"停止测量"
   - 数据保留在缓冲区中

5. **导出数据**
   - 点击"导出数据 (CSV)"
   - 选择保存位置
   - 数据包含时间、功率、平均值、RMS

## 支持的功率计

支持任何符合 NI-VISA 标准的功率计，包括：

- YOKOGAWA (横河) WT 系列
- KEITHLEY (吉时利) 系列仪表
- Chroma (致茂) 负载仪
- Fluke (福禄克) 功率分析仪
- 以及其他支持 SCPI 命令的仪表

## 文件结构

```
pm-monitor/
├── README.md              # 项目说明文档
├── requirements.txt        # Python 依赖包
├── start.sh             # 快速启动脚本
├── .gitignore           # Git 忽略文件
├── docs/
│   ├── interface.md      # 界面设计文档（详细布局和配色）
│   └── protocol.md      # NI-VISA 通信协议文档（SCPI 命令和 VISA 操作）
└── src/
    ├── main.py          # 主程序入口
    └── main_window.py  # 主窗口实现（完整 UI 代码 + VISA 通信）
```
