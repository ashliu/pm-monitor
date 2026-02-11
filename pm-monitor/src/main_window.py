#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PM-Monitor 主窗口模块
主界面布局和交互逻辑
使用 NI-VISA 驱动与功率计通信
"""

import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QSpinBox,
    QGroupBox, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

import pyqtgraph as pg

try:
    import pyvisa
    HAS_PYVISA = True
except ImportError:
    HAS_PYVISA = False

# 导入 Mock VISA（用于测试）
try:
    from mock_visa import MockResourceManager, MockPyVISA
    HAS_MOCK = True
except ImportError:
    HAS_MOCK = False


class PMMonitorMainWindow(QMainWindow):
    """功率监测主窗口"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_data()
        self.init_visa()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("PM-Monitor 功率监测系统")
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumSize(1000, 600)

        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 左侧操作区 (30%)
        left_panel = self.create_control_panel()
        main_layout.addWidget(left_panel, 3)

        # 右侧显示区 (70%)
        right_panel = self.create_display_panel()
        main_layout.addWidget(right_panel, 7)

        # 状态栏
        self.statusBar().showMessage("就绪")

    def init_data(self):
        """初始化数据"""
        self.is_measuring = False
        self.current_value = 0.0
        self.max_value = 0.0
        self.min_value = 0.0
        self.rms_value = 0.0
        self.peak_value = 0.0
        self.avg_value = 0.0
        self.sample_count = 0

        # 数据缓冲区
        self.data_buffer = []
        self.time_buffer = []
        self.max_buffer_size = 1000

        # 定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.start_time = None

    def init_visa(self):
        """初始化 VISA"""
        self.use_mock = False
        
        if not HAS_PYVISA and not HAS_MOCK:
            QMessageBox.warning(
                self,
                "缺少依赖",
                "未安装 pyvisa 库！\n\n请运行:\npip install pyvisa pyvisa-py\n\n或者使用 Mock 模式测试。"
            )
            self.btn_start.setEnabled(False)
            self.btn_connect.setEnabled(False)
            return

        try:
            if HAS_PYVISA:
                self.rm = pyvisa.ResourceManager('@py')
                self.statusBar().showMessage("VISA 资源管理器已加载 (真实模式)")
            elif HAS_MOCK:
                self.rm = MockResourceManager('@py')
                self.use_mock = True
                self.statusBar().showMessage("VISA 资源管理器已加载 (模拟模式)")
        except Exception as e:
            QMessageBox.critical(
                self,
                "VISA 初始化失败",
                f"无法初始化 VISA 资源管理器:\n{str(e)}"
            )
            self.btn_start.setEnabled(False)
            self.btn_connect.setEnabled(False)

        self.instrument = None

    def create_control_panel(self):
        """创建左侧控制面板"""
        panel = QFrame()
        panel.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)

        # 1. VISA 设备连接组
        conn_group = QGroupBox("设备连接 (VISA)")
        conn_layout = QVBoxLayout()

        # VISA 资源字符串输入
        self.combo_visa_resources = QComboBox()
        self.combo_visa_resources.setEditable(True)
        self.combo_visa_resources.setPlaceholderText("TCPIP::192.168.1.100::5025::SOCKET")
        conn_layout.addWidget(QLabel("VISA 资源："))
        conn_layout.addWidget(self.combo_visa_resources)

        # 刷新设备列表
        self.btn_refresh = QPushButton("刷新设备列表")
        self.btn_refresh.clicked.connect(self.refresh_devices)
        conn_layout.addWidget(self.btn_refresh)

        self.btn_connect = QPushButton("连接设备")
        self.btn_connect.clicked.connect(self.connect_visa_device)
        conn_layout.addWidget(self.btn_connect)

        # SCPI 命令配置
        conn_layout.addWidget(QLabel("功率查询命令："))
        self.combo_command = QComboBox()
        self.combo_command.setEditable(True)
        self.combo_command.addItems([
            'MEAS:POW?',           # 常用
            ':MEAS:POW?',          # 带 :
            'FETC?',              # Fetch
            'MEASure:POWer?',     # Measure
        ])
        self.combo_command.setCurrentIndex(0)
        conn_layout.addWidget(self.combo_command)

        # 采样率设置
        conn_layout.addWidget(QLabel("采样间隔："))
        self.spin_sample_rate = QSpinBox()
        self.spin_sample_rate.setRange(10, 5000)
        self.spin_sample_rate.setValue(100)
        self.spin_sample_rate.setSuffix(" ms")
        conn_layout.addWidget(self.spin_sample_rate)

        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)

        # 2. 测量控制组
        measure_group = QGroupBox("测量控制")
        measure_layout = QVBoxLayout()

        self.btn_start = QPushButton("开始测量")
        self.btn_start.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.btn_start.clicked.connect(self.start_measurement)
        self.btn_start.setEnabled(False)
        measure_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton("停止测量")
        self.btn_stop.setStyleSheet("background-color: #F44336; color: white; font-weight: bold; padding: 8px;")
        self.btn_stop.clicked.connect(self.stop_measurement)
        self.btn_stop.setEnabled(False)
        measure_layout.addWidget(self.btn_stop)

        self.btn_reset = QPushButton("重置数据")
        self.btn_reset.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 8px;")
        self.btn_reset.clicked.connect(self.reset_data)
        measure_layout.addWidget(self.btn_reset)

        measure_group.setLayout(measure_layout)
        layout.addWidget(measure_group)

        # 3. 数据导出组
        export_group = QGroupBox("数据导出")
        export_layout = QVBoxLayout()

        self.btn_export = QPushButton("导出数据 (CSV)")
        self.btn_export.clicked.connect(self.export_data)
        export_layout.addWidget(self.btn_export)

        export_group.setLayout(export_layout)
        layout.addWidget(export_group)

        # 4. 设备信息组
        info_group = QGroupBox("设备信息")
        info_layout = QVBoxLayout()

        self.lbl_device_info = QLabel("未连接")
        self.lbl_device_info.setStyleSheet("color: #666; font-style: italic;")
        self.lbl_device_info.setWordWrap(True)
        info_layout.addWidget(self.lbl_device_info)

        self.lbl_connection_status = QLabel("状态: 未连接")
        self.lbl_connection_status.setStyleSheet("color: #F44336; font-weight: bold;")
        info_layout.addWidget(self.lbl_connection_status)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        layout.addStretch()
        return panel

    def create_display_panel(self):
        """创建右侧显示面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        # 上方：数值显示区 (30%)
        values_group = QGroupBox("测量数据")
        values_layout = QVBoxLayout()
        values_layout.setSpacing(10)

        # 创建字体
        font_large_label = QFont("Arial", 14)
        font_current = QFont("Arial", 48, QFont.Bold)  # 当前值用大字体
        font_value = QFont("Arial", 20, QFont.Bold)    # 其他值用中等字体
        font_small_label = QFont("Arial", 11)
        font_stat = QFont("Arial", 16, QFont.Bold)

        # ========== 当前值（单独一行，大字体）==========
        current_frame = QFrame()
        current_frame.setStyleSheet("background-color: #E8F5E9; border-radius: 8px; padding: 10px;")
        current_layout = QVBoxLayout(current_frame)
        current_layout.setSpacing(5)

        self.lbl_current_label = QLabel("当前功率")
        self.lbl_current_label.setFont(font_large_label)
        self.lbl_current_label.setStyleSheet("color: #2E7D32;")
        self.lbl_current_label.setAlignment(Qt.AlignCenter)
        current_layout.addWidget(self.lbl_current_label)

        self.lbl_current_value = QLabel("0.00 W")
        self.lbl_current_value.setFont(font_current)
        self.lbl_current_value.setStyleSheet("color: #4CAF50;")
        self.lbl_current_value.setAlignment(Qt.AlignCenter)
        current_layout.addWidget(self.lbl_current_value)

        values_layout.addWidget(current_frame)

        # ========== 其他统计值（网格布局）==========
        stats_layout = QGridLayout()
        stats_layout.setSpacing(10)

        # 最大值
        self.lbl_max_label = QLabel("最大值")
        self.lbl_max_value = QLabel("0.00 W")
        self.lbl_max_value.setFont(font_value)
        self.lbl_max_value.setStyleSheet("color: #FF9800; background-color: #FFF3E0; padding: 8px; border-radius: 5px;")
        self.lbl_max_value.setAlignment(Qt.AlignCenter)
        self.lbl_max_label.setFont(font_small_label)
        self.lbl_max_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(self.lbl_max_label, 0, 0)
        stats_layout.addWidget(self.lbl_max_value, 1, 0)

        # 最小值
        self.lbl_min_label = QLabel("最小值")
        self.lbl_min_value = QLabel("0.00 W")
        self.lbl_min_value.setFont(font_value)
        self.lbl_min_value.setStyleSheet("color: #2196F3; background-color: #E3F2FD; padding: 8px; border-radius: 5px;")
        self.lbl_min_value.setAlignment(Qt.AlignCenter)
        self.lbl_min_label.setFont(font_small_label)
        self.lbl_min_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(self.lbl_min_label, 0, 1)
        stats_layout.addWidget(self.lbl_min_value, 1, 1)

        # RMS值
        self.lbl_rms_label = QLabel("RMS值")
        self.lbl_rms_value = QLabel("0.00 W")
        self.lbl_rms_value.setFont(font_value)
        self.lbl_rms_value.setStyleSheet("color: #9C27B0; background-color: #F3E5F5; padding: 8px; border-radius: 5px;")
        self.lbl_rms_value.setAlignment(Qt.AlignCenter)
        self.lbl_rms_label.setFont(font_small_label)
        self.lbl_rms_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(self.lbl_rms_label, 0, 2)
        stats_layout.addWidget(self.lbl_rms_value, 1, 2)

        values_layout.addLayout(stats_layout)

        # ========== 采样统计（底部）==========
        time_layout = QHBoxLayout()

        time_frame = QFrame()
        time_frame.setStyleSheet("background-color: #F5F5F5; border-radius: 5px; padding: 5px;")
        time_inner = QVBoxLayout(time_frame)
        self.lbl_time_label = QLabel("测量时间")
        self.lbl_time_label.setFont(font_small_label)
        self.lbl_time_label.setAlignment(Qt.AlignCenter)
        self.lbl_time_value = QLabel("00:00:00")
        self.lbl_time_value.setFont(font_stat)
        self.lbl_time_value.setStyleSheet("color: #333;")
        self.lbl_time_value.setAlignment(Qt.AlignCenter)
        time_inner.addWidget(self.lbl_time_label)
        time_inner.addWidget(self.lbl_time_value)
        time_layout.addWidget(time_frame)

        count_frame = QFrame()
        count_frame.setStyleSheet("background-color: #F5F5F5; border-radius: 5px; padding: 5px;")
        count_inner = QVBoxLayout(count_frame)
        self.lbl_count_label = QLabel("采样次数")
        self.lbl_count_label.setFont(font_small_label)
        self.lbl_count_label.setAlignment(Qt.AlignCenter)
        self.lbl_count_value = QLabel("0")
        self.lbl_count_value.setFont(font_stat)
        self.lbl_count_value.setStyleSheet("color: #333;")
        self.lbl_count_value.setAlignment(Qt.AlignCenter)
        count_inner.addWidget(self.lbl_count_label)
        count_inner.addWidget(self.lbl_count_value)
        time_layout.addWidget(count_frame)

        values_layout.addLayout(time_layout)

        values_group.setLayout(values_layout)
        layout.addWidget(values_group, 3)

        # 下方：曲线显示区 (70%)
        plot_group = QGroupBox("功率曲线")
        plot_layout = QVBoxLayout()

        # 创建曲线控件
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setTitle("实时功率监测曲线")
        self.plot_widget.setLabel('left', '功率', units='W')
        self.plot_widget.setLabel('bottom', '时间', units='s')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setBackground('#F5F5F5')

        # 添加多条曲线
        self.curve_current = self.plot_widget.plot(pen=pg.mkPen('#2196F3', width=2), name='当前值')
        self.curve_avg = self.plot_widget.plot(pen=pg.mkPen('#FF5722', width=1, style=Qt.DashLine), name='平均值')

        self.plot_widget.addLegend()

        plot_layout.addWidget(self.plot_widget)
        plot_group.setLayout(plot_layout)
        layout.addWidget(plot_group, 7)

        return panel

    def refresh_devices(self):
        """刷新 VISA 设备列表"""
        try:
            devices = self.rm.list_resources()
            self.combo_visa_resources.clear()

            # 始终添加 Mock 设备（用于测试）
            if "MOCK::PowerMeter::1" not in devices:
                devices = ["MOCK::PowerMeter::1 (模拟设备 - 无需硬件)"] + list(devices)

            if not devices:
                QMessageBox.information(
                    self,
                    "未发现设备",
                    "未发现任何 VISA 设备！\n\n请检查：\n1. 设备是否已连接\n2. NI-VISA 驱动是否已安装\n3. NI MAX 中是否能看到设备\n\n提示：可以使用 MOCK::PowerMeter::1 进行模拟测试"
                )
                return

            self.combo_visa_resources.addItems(devices)
            
            # 默认选择 Mock 设备（方便测试）
            for i, dev in enumerate(devices):
                if "MOCK" in dev.upper():
                    self.combo_visa_resources.setCurrentIndex(i)
                    break
            else:
                self.combo_visa_resources.setCurrentIndex(0)
                
            self.statusBar().showMessage(f"发现 {len(devices)} 个设备 (包含模拟设备)")

        except Exception as e:
            QMessageBox.critical(
                self,
                "设备扫描失败",
                f"无法扫描设备:\n{str(e)}"
            )

    def connect_visa_device(self):
        """连接 VISA 设备"""
        resource_str = self.combo_visa_resources.currentText().strip()

        if not resource_str:
            QMessageBox.warning(self, "警告", "请输入或选择 VISA 资源字符串！")
            return

        try:
            # 关闭现有连接
            if self.instrument:
                self.instrument.close()

            # 打开新连接
            self.statusBar().showMessage("正在连接设备...")
            QApplication.processEvents()  # 更新界面

            # 检测是否为 Mock 设备
            is_mock = "MOCK" in resource_str.upper()
            
            if is_mock and HAS_MOCK:
                from mock_visa import MockResourceManager
                self.rm = MockResourceManager('@py')
                self.use_mock = True
            elif not HAS_PYVISA:
                QMessageBox.warning(
                    self,
                    "缺少依赖",
                    "未安装 pyvisa！\n请使用 MOCK::PowerMeter 进行模拟测试。"
                )
                return

            self.instrument = self.rm.open_resource(resource_str, timeout=5000)

            # 设置超时和终止符
            self.instrument.timeout = 5000
            self.instrument.read_termination = '\n'
            self.instrument.write_termination = '\n'

            # 查询设备信息
            idn = self.instrument.query('*IDN?')
            self.lbl_device_info.setText(idn.strip())

            self.btn_connect.setEnabled(False)
            self.btn_connect.setText("已连接")
            self.btn_start.setEnabled(True)
            self.lbl_connection_status.setText("状态: 已连接" + (" [模拟]" if is_mock else ""))
            self.lbl_connection_status.setStyleSheet("color: #4CAF50; font-weight: bold;")

            if is_mock:
                self.statusBar().showMessage("模拟设备已连接 (生成虚拟数据)")
                QMessageBox.information(
                    self,
                    "模拟模式",
                    "已连接到模拟设备！\n\n将生成虚拟功率数据用于测试：\n- 基础功率：约 50W\n- 随机噪声、趋势变化、周期性波动"
                )
            else:
                self.statusBar().showMessage("设备已连接")

        except Exception as e:
            if HAS_PYVISA:
                import pyvisa
                if isinstance(e, pyvisa.Error):
                    error_msg = f"VISA 错误 ({e.abbreviation}): {e.description}"
                else:
                    error_msg = f"未知错误:\n{str(e)}"
            else:
                error_msg = f"连接失败:\n{str(e)}"
            QMessageBox.critical(self, "连接失败", error_msg)
            self.statusBar().showMessage("连接失败")

    def start_measurement(self):
        """开始测量"""
        if not self.instrument:
            QMessageBox.warning(self, "警告", "请先连接设备！")
            return

        self.is_measuring = True
        self.start_time = time.time()
        
        self.btn_start.setEnabled(False)
        self.btn_connect.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_refresh.setEnabled(False)
        self.combo_visa_resources.setEnabled(False)
        self.combo_command.setEnabled(False)
        self.spin_sample_rate.setEnabled(False)
        
        self.statusBar().showMessage("测量中...")

        # 启动更新定时器
        interval = self.spin_sample_rate.value()
        self.update_timer.start(interval)

    def stop_measurement(self):
        """停止测量"""
        self.is_measuring = False
        
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_connect.setEnabled(False)
        self.btn_refresh.setEnabled(True)
        self.combo_visa_resources.setEnabled(True)
        self.combo_command.setEnabled(True)
        self.spin_sample_rate.setEnabled(True)
        
        self.update_timer.stop()
        self.statusBar().showMessage("测量已停止")

    def reset_data(self):
        """重置数据"""
        self.data_buffer = []
        self.time_buffer = []
        self.max_value = 0.0
        self.min_value = 0.0
        self.rms_value = 0.0
        self.peak_value = 0.0
        self.avg_value = 0.0
        self.sample_count = 0
        self.start_time = None

        self.update_display()
        self.curve_current.setData([], [])
        self.curve_avg.setData([], [])
        
        self.statusBar().showMessage("数据已重置")

    def update_display(self):
        """更新显示"""
        if not self.instrument or not self.is_measuring:
            return

        try:
            # 获取功率查询命令
            command = self.combo_command.currentText().strip()

            # 读取功率值
            response = self.instrument.query(command)
            new_value = float(response.strip())

            # 更新计数
            self.sample_count += 1
            elapsed_time = time.time() - self.start_time if self.start_time else 0

            # 更新当前值
            self.current_value = new_value

            # 更新最大/最小值
            if len(self.data_buffer) == 0:
                self.max_value = new_value
                self.min_value = new_value
            else:
                if new_value > self.max_value:
                    self.max_value = new_value
                if new_value < self.min_value:
                    self.min_value = new_value

            # 更新数据缓冲区
            self.data_buffer.append(new_value)
            self.time_buffer.append(elapsed_time)

            # 限制缓冲区大小
            if len(self.data_buffer) > self.max_buffer_size:
                self.data_buffer.pop(0)
                self.time_buffer.pop(0)

            # 计算统计数据
            import math
            avg = sum(self.data_buffer) / len(self.data_buffer) if self.data_buffer else 0.0
            rms = math.sqrt(sum(x**2 for x in self.data_buffer) / len(self.data_buffer)) if self.data_buffer else 0.0

            self.avg_value = avg
            self.rms_value = rms

            # 更新曲线
            self.curve_current.setData(self.time_buffer, self.data_buffer)
            self.curve_avg.setData(self.time_buffer, [avg] * len(self.time_buffer))

            # 更新数值显示
            self.lbl_current_value.setText(f"{self.current_value:.2f} W")
            self.lbl_max_value.setText(f"{self.max_value:.2f} W")
            self.lbl_min_value.setText(f"{self.min_value:.2f} W")
            self.lbl_rms_value.setText(f"{self.rms_value:.2f} W")
            self.lbl_count_value.setText(str(self.sample_count))

            # 更新时间显示
            hours = int(elapsed_time // 3600)
            minutes = int((elapsed_time % 3600) // 60)
            seconds = int(elapsed_time % 60)
            self.lbl_time_value.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        except Exception as e:
            # 处理 VISA 错误（如果安装了 pyvisa）
            if HAS_PYVISA:
                import pyvisa
                if isinstance(e, pyvisa.Error):
                    print(f"VISA 读取错误: {e}")
                    self.statusBar().showMessage(f"读取错误: {e.abbreviation}")
                    return
            # 重新抛出其他异常

        except ValueError as e:
            print(f"数据解析错误: {e}")
            self.statusBar().showMessage("数据格式错误")

        except Exception as e:
            print(f"更新显示错误: {e}")
            import traceback
            traceback.print_exc()

    def export_data(self):
        """导出数据到 CSV"""
        if not self.data_buffer:
            QMessageBox.information(self, "提示", "没有数据可导出！")
            return

        try:
            from PyQt5.QtWidgets import QFileDialog
            import datetime

            # 选择保存文件
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "导出数据",
                f"power_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV 文件 (*.csv)"
            )

            if filename:
                # 写入 CSV
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("Time(s),Power(W),Avg(W),RMS(W)\n")
                    for i, (t, p) in enumerate(zip(self.time_buffer, self.data_buffer)):
                        avg = sum(self.data_buffer[:i+1]) / (i+1)
                        rms = (sum(x**2 for x in self.data_buffer[:i+1]) / (i+1))**0.5
                        f.write(f"{t:.3f},{p:.4f},{avg:.4f},{rms:.4f}\n")

                self.statusBar().showMessage(f"数据已导出到: {filename}")
                QMessageBox.information(self, "导出成功", f"数据已导出:\n{filename}")

        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出数据时出错:\n{str(e)}")

    def closeEvent(self, event):
        """关闭事件"""
        if self.is_measuring:
            self.stop_measurement()

        # 关闭 VISA 连接
        if self.instrument:
            try:
                self.instrument.close()
            except:
                pass

        # 关闭资源管理器
        if hasattr(self, 'rm'):
            try:
                self.rm.close()
            except:
                pass

        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PMMonitorMainWindow()
    window.show()
    sys.exit(app.exec_())
