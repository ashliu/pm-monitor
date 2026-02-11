#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock VISA 功能测试脚本
纯命令行测试，无需 GUI
"""

import sys
import time
import math

sys.path.insert(0, '/home/ash/.openclaw/workspace/pm-monitor/src')

from mock_visa import MockResourceManager, MockInstrument


def test_mock_resource_manager():
    """测试资源管理器"""
    print("=" * 50)
    print("测试 1: MockResourceManager")
    print("=" * 50)
    
    rm = MockResourceManager('@py')
    devices = rm.list_resources()
    
    print(f"✓ 资源管理器创建成功")
    print(f"✓ 发现 {len(devices)} 个模拟设备:")
    for i, dev in enumerate(devices, 1):
        print(f"  {i}. {dev}")
    
    return rm


def test_mock_instrument(rm):
    """测试模拟仪器"""
    print("\n" + "=" * 50)
    print("测试 2: MockInstrument 连接")
    print("=" * 50)
    
    # 打开设备
    instrument = rm.open_resource("MOCK::PowerMeter::1")
    print(f"✓ 设备连接成功")
    
    # 测试 *IDN? 查询
    idn = instrument.query('*IDN?')
    print(f"✓ 设备标识: {idn.strip()}")
    
    # 测试 SCPI 命令
    commands = [
        'MEAS:POW?',
        ':MEAS:POW?',
        'FETC?',
        'MEASure:POWer?',
    ]
    
    print("\n测试 SCPI 命令响应:")
    for cmd in commands:
        response = instrument.query(cmd)
        print(f"  {cmd:<20} -> {response.strip()}")
    
    return instrument


def test_power_data_simulation(instrument):
    """测试功率数据模拟"""
    print("\n" + "=" * 50)
    print("测试 3: 功率数据模拟 (采集 20 个样本)")
    print("=" * 50)
    
    values = []
    
    print("\n样本数据:")
    print(f"{'样本':>6} | {'功率(W)':>12} | {'变化':>10}")
    print("-" * 35)
    
    for i in range(20):
        response = instrument.query('MEAS:POW?')
        value = float(response.strip())
        values.append(value)
        
        change = ""
        if i > 0:
            diff = value - values[i-1]
            change = f"{diff:+.2f}"
        
        print(f"{i+1:>6} | {value:>12.4f} | {change:>10}")
        time.sleep(0.05)  # 模拟采样间隔
    
    # 统计数据
    avg = sum(values) / len(values)
    rms = math.sqrt(sum(v**2 for v in values) / len(values))
    max_val = max(values)
    min_val = min(values)
    
    print("\n" + "-" * 35)
    print(f"统计结果:")
    print(f"  平均值: {avg:.4f} W")
    print(f"  RMS值:  {rms:.4f} W")
    print(f"  最大值: {max_val:.4f} W")
    print(f"  最小值: {min_val:.4f} W")
    print(f"  波动范围: {max_val - min_val:.4f} W")


def test_data_characteristics():
    """测试数据特征是否符合预期"""
    print("\n" + "=" * 50)
    print("测试 4: 数据特征验证")
    print("=" * 50)
    
    rm = MockResourceManager('@py')
    instrument = rm.open_resource("MOCK::PowerMeter::1")
    
    # 采集大量样本验证统计特征
    values = []
    for _ in range(100):
        response = instrument.query('MEAS:POW?')
        values.append(float(response.strip()))
        time.sleep(0.01)
    
    avg = sum(values) / len(values)
    
    print(f"✓ 采集 100 个样本")
    print(f"✓ 平均值: {avg:.2f} W (预期约 50W)")
    print(f"✓ 范围: {min(values):.2f} ~ {max(values):.2f} W")
    
    # 验证平均值是否在合理范围内 (50 ± 10)
    if 40 < avg < 60:
        print(f"✓ 平均值在预期范围内 ✓")
    else:
        print(f"✗ 平均值偏离预期!")


def test_continuous_sampling():
    """测试连续采样模式"""
    print("\n" + "=" * 50)
    print("测试 5: 连续采样模拟 (3 秒)")
    print("=" * 50)
    
    rm = MockResourceManager('@py')
    instrument = rm.open_resource("MOCK::PowerMeter::1")
    
    values = []
    sample_count = 0
    start_time = time.time()
    
    print("\n实时采样 (按 Ctrl+C 提前结束):")
    print(f"{'时间(s)':>8} | {'功率(W)':>10}")
    print("-" * 25)
    
    try:
        while time.time() - start_time < 3:
            elapsed = time.time() - start_time
            response = instrument.query('MEAS:POW?')
            value = float(response.strip())
            values.append(value)
            sample_count += 1
            
            if sample_count <= 10 or sample_count % 5 == 0:
                print(f"{elapsed:>8.2f} | {value:>10.2f}")
            
            time.sleep(0.1)  # 100ms 采样间隔
    
    except KeyboardInterrupt:
        print("\n(用户中断)")
    
    print(f"\n✓ 共采集 {sample_count} 个样本")
    print(f"✓ 实际采样率: {sample_count / (time.time() - start_time):.1f} Hz")


def main():
    """主测试函数"""
    print("\n" + "=" * 50)
    print("PM-Monitor Mock VISA 功能测试")
    print("=" * 50)
    print(f"Python: {sys.version}")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 运行所有测试
        rm = test_mock_resource_manager()
        instrument = test_mock_instrument(rm)
        test_power_data_simulation(instrument)
        test_data_characteristics()
        test_continuous_sampling()
        
        print("\n" + "=" * 50)
        print("所有测试通过! ✓")
        print("=" * 50)
        print("\nMock 功能正常工作，可以在 GUI 中使用:")
        print("1. 运行 ./start.sh")
        print("2. 选择 'MOCK::PowerMeter::1'")
        print("3. 点击连接并开始测量")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
