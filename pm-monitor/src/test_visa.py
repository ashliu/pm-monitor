#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PM-Monitor VISA 连接测试脚本
用于验证 NI-VISA/pyvisa 是否正确安装并扫描可用设备
"""

import sys

def check_pyvisa():
    """检查 pyvisa 是否安装"""
    print("=" * 60)
    print("NI-VISA 连接测试")
    print("=" * 60)
    print()

    # 检查 pyvisa
    try:
        import pyvisa
        print("✅ pyvisa 已安装")
        print(f"   版本: {pyvisa.__version__}")
        print()
    except ImportError:
        print("❌ pyvisa 未安装！")
        print()
        print("请运行以下命令安装：")
        print("   pip install pyvisa pyvisa-py")
        print()
        return False

    # 检查 pyvisa-py
    try:
        from pyvisa import ResourceManager
        # 尝试使用 pyvisa-py 后端
        rm = ResourceManager('@py')
        print("✅ pyvisa-py 后端可用（纯 Python 实现）")
        print()
    except:
        print("⚠️  pyvisa-py 后端不可用")
        print()
        print("尝试使用 NI-VISA 后端（需要 NI 驱动）...")

    try:
        # 创建资源管理器
        try:
            rm = pyvisa.ResourceManager('@py')
        except:
            rm = pyvisa.ResourceManager()

        print("✅ VISA 资源管理器创建成功")
        print()

        # 扫描设备
        print("正在扫描 VISA 设备...")
        devices = rm.list_resources()

        print()
        print(f"📋 发现 {len(devices)} 个设备：")
        print("-" * 60)

        if not devices:
            print("❌ 未发现任何 VISA 设备")
            print()
            print("请检查：")
            print("  1. 设备是否已正确连接")
            print("  2. NI-VISA 驱动是否已安装")
            print("  3. NI MAX (Measurement & Automation Explorer) 中是否能看到设备")
            print()
            print("下载 NI-VISA: https://www.ni.com/zh-cn/support/downloads/drivers/")
            print()
            return False

        # 列出设备
        connected_devices = []
        for i, device in enumerate(devices, 1):
            print(f"  {i}. {device}")

            # 尝试连接
            try:
                inst = rm.open_resource(device, timeout=2000)
                idn = inst.query('*IDN?')
                print(f"     └─> {idn.strip()}")
                inst.close()
                connected_devices.append((device, idn.strip()))
            except Exception as e:
                print(f"     └─> (无法访问: {type(e).__name__})")

        print("-" * 60)
        print()

        # 测试读取功率值
        if connected_devices:
            print("📊 尝试读取功率值...")
            print("-" * 60)

            for resource_str, idn in connected_devices[:1]:  # 只测试第一个设备
                try:
                    print(f"连接设备: {resource_str}")
                    inst = rm.open_resource(resource_str, timeout=5000)

                    # 设置终止符
                    inst.read_termination = '\n'
                    inst.write_termination = '\n'

                    # 尝试不同命令
                    commands_to_try = [
                        'MEAS:POW?',
                        ':MEAS:POW?',
                        'FETC?',
                        'MEASure:POWer?',
                        'MEAS:WATT?',
                    ]

                    power_read = False
                    for cmd in commands_to_try:
                        try:
                            print(f"  尝试命令: {cmd}")
                            response = inst.query(cmd)
                            value = float(response.strip())
                            print(f"  ✅ 成功! 功率值: {value:.2f} W")
                            power_read = True
                            break
                        except:
                            continue

                    if not power_read:
                        print("  ⚠️  所有命令都失败，请参考设备手册")

                    inst.close()
                    print()

                except pyvisa.Error as e:
                    print(f"  ❌ VISA 错误: {e.abbreviation}")
                    print(f"      {e.description}")
                except Exception as e:
                    print(f"  ❌ 错误: {type(e).__name__}: {e}")

            print("-" * 60)

        # 测试结果
        print()
        print("=" * 60)
        if connected_devices:
            print("✅ 测试完成！VISA 工作正常")
            print()
            print("你现在可以运行主程序：")
            print("  cd src")
            print("  python3 main.py")
        else:
            print("❌ 未发现可连接的设备")
        print("=" * 60)

        rm.close()
        return True

    except Exception as e:
        print(f"❌ 初始化 VISA 资源管理器失败:")
        print(f"   {type(e).__name__}: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = check_pyvisa()
    sys.exit(0 if success else 1)
