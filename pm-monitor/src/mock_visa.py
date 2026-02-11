#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock VISA 设备模拟器
用于在没有实际硬件的情况下测试 PM-Monitor
"""

import random
import math
import time


class MockInstrument:
    """模拟 VISA 仪器"""
    
    def __init__(self, resource_name="MOCK::DEVICE"):
        self.resource_name = resource_name
        self.timeout = 5000
        self.read_termination = '\n'
        self.write_termination = '\n'
        self._connected = True
        self._idn = "MOCK,PowerMeter,PM-001,1.0"
        
        # 模拟参数
        self._base_power = 50.0  # 基础功率值 (W)
        self._noise_level = 2.0   # 噪声幅度
        self._trend = 0.0         # 趋势变化
        self._sample_count = 0
        
    def query(self, command):
        """模拟查询命令"""
        command = command.strip().upper()
        
        if command in ["*IDN?", "*IDN"]:
            return self._idn + self.read_termination
            
        elif command in ["MEAS:POW?", ":MEAS:POW?", "FETC?", "MEASURE:POW?", "MEASURE:POWER?"]:
            # 生成模拟功率值
            self._sample_count += 1
            
            # 添加随机噪声
            noise = random.uniform(-self._noise_level, self._noise_level)
            
            # 添加缓慢的趋势变化（模拟设备预热/负载变化）
            self._trend += random.uniform(-0.1, 0.1)
            self._trend = max(-5, min(5, self._trend))  # 限制趋势范围
            
            # 添加周期性波动（模拟交流电频率）
            cycle = 2.0 * math.sin(self._sample_count * 0.1)
            
            power = self._base_power + self._trend + noise + cycle
            power = max(0, power)  # 功率不能为负
            
            return f"{power:.4f}" + self.read_termination
            
        else:
            return "0" + self.read_termination
    
    def write(self, command):
        """模拟写入命令"""
        pass
    
    def read(self):
        """模拟读取"""
        return "0" + self.read_termination
    
    def close(self):
        """关闭连接"""
        self._connected = False


class MockResourceManager:
    """模拟 VISA 资源管理器"""
    
    def __init__(self, backend='@py'):
        self.backend = backend
        self._mock_devices = [
            "MOCK::PowerMeter::1",
            "TCPIP::192.168.1.100::5025::SOCKET",
            "USB0::0x1234::0x5678::PM001::INSTR",
        ]
    
    def list_resources(self):
        """列出可用资源"""
        return self._mock_devices
    
    def open_resource(self, resource_name, **kwargs):
        """打开资源"""
        return MockInstrument(resource_name)
    
    def close(self):
        """关闭资源管理器"""
        pass


# 兼容性：模拟 pyvisa 模块
class MockPyVISA:
    """模拟 pyvisa 模块"""
    
    ResourceManager = MockResourceManager
    
    class Error(Exception):
        """VISA 错误"""
        def __init__(self, description, abbreviation="ERR"):
            self.description = description
            self.abbreviation = abbreviation
            super().__init__(description)


# 导出
ResourceManager = MockResourceManager
Error = MockPyVISA.Error
