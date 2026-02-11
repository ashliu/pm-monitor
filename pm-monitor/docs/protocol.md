# PM-Monitor 通信协议文档

## NI-VISA 通信

### VISA 配置

- 驱动：NI-VISA
- Python 库：pyvisa
- 资源管理器：NI MAX (Measurement & Automation Explorer)

### 连接方式

#### VISA 资源字符串格式

```
TCPIP::{IP}::{PORT}::SOCKET     # TCP/IP 网络连接
USB::{VendorID}::{ProductID}::{SerialNumber}::INSTR  # USB 连接
GPIB::{GPIB_Address}::INSTR   # GPIB 总线连接
ASRL{COM Port}::INSTR         # 串口连接 (ASRL)
```

#### 常见示例

```
# 功率计网络连接
TCPIP::192.168.1.100::5025::SOCKET

# USB 设备
USB0x0x1234::0x5678::INSTR

# 串口 (使用 VISA)
ASRL3::INSTR  # COM3
```

### pyvisa 使用

#### 基本操作

```python
import pyvisa

# 创建资源管理器
rm = pyvisa.ResourceManager('@py')  # 使用 pyvisa-py (纯 Python)
# 或
rm = pyvisa.ResourceManager()      # 使用 NI-VISA (需要安装 NI 驱动)

# 列出所有设备
devices = rm.list_resources()
print(f"可用设备: {devices}")

# 打开设备连接
instrument = rm.open_resource('TCPIP::192.168.1.100::5025::SOCKET')

# 写入命令
instrument.write('*IDN?')  # 查询设备标识

# 读取数据
response = instrument.read()
print(f"设备响应: {response}")

# 查询 (Write + Read)
value = instrument.query('MEAS:VOLT?')
print(f"电压值: {value}")

# 关闭连接
instrument.close()
rm.close()
```

#### 读取功率数据

```python
import time

# 持续读取功率数据
while True:
    try:
        # 查询当前功率值
        power = instrument.query('MEAS:POW?')
        power_value = float(power.strip())
        
        print(f"功率: {power_value} W")
        
        time.sleep(0.1)  # 100ms 采样间隔
        
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"读取错误: {e}")
        break

instrument.close()
```

### 常用 SCPI 命令

功率计通常支持以下 SCPI (Standard Commands for Programmable Instruments) 命令：

| 命令 | 功能 | 示例 |
|--------|------|------|
| `*IDN?` | 查询设备标识 | `YOKOGAWA WT3000` |
| `*RST` | 复位设备 | - |
| `:MEAS:POW?` | 查询功率 (W) | `120.5` |
| `:MEAS:VOLT?` | 查询电压 (V) | `230.0` |
| `:MEAS:CURR?` | 查询电流 (A) | `0.52` |
| `:SENS:RATE?` | 查询采样率 | `1000` |
| `:SENS:RATE <val>` | 设置采样率 | `:SENS:RATE 1000` |
| `:INIT` | 初始化测量 | - |
| `:ABORT` | 停止测量 | - |
| `:FETC?` | 读取当前测量值 | - |

### 错误处理

```python
try:
    instrument = rm.open_resource('TCPIP::192.168.1.100::5025::SOCKET', timeout=10000)
except pyvisa.Error as e:
    print(f"VISA 错误: {e}")
    print(f"错误代码: {e.}")
    print(f"错误描述: {e.description}")
```

常见 VISA 错误码：
- `VI_ERROR_INV_OBJECT` (-1073807343): 无效对象
- `VI_ERROR_INV_RSRC_NAME` (-1073807346): 无效资源名
- `VI_ERROR_INV_SESSION` (-1073807198): 无效会话
- `VI_ERROR_TMO` (-1073807339): 超时错误

### 性能优化

#### 1. 使用查询缓存

```python
# 一次读取多个参数
# 慢：分别查询
volt = instrument.query(':MEAS:VOLT?')
curr = instrument.query(':MEAS:CURR?')
powr = instrument.query(':MEAS:POW?')

# 快：批量查询
values = instrument.query(':MEAS:VOLT?;:MEAS:CURR?;:MEAS:POW?')
```

#### 2. 设置超时时间

```python
instrument.timeout = 5000  # 5秒超时
```

#### 3. 使用异步读取

```python
# 启用异步模式
instrument.read_termination = '\n'
instrument.write_termination = '\n'
```

### 设备发现

#### 扫描可用设备

```python
import pyvisa

rm = pyvisa.ResourceManager()
devices = rm.list_resources()

print("发现的 VISA 设备：")
for i, device in enumerate(devices):
    print(f"{i + 1}. {device}")
    
    # 尝试打开并查询设备信息
    try:
        inst = rm.open_resource(device, timeout=1000)
        idn = inst.query('*IDN?')
        print(f"   → {idn.strip()}")
        inst.close()
    except:
        print(f"   → (无法访问)")
```

### pyvisa-py vs NI-VISA

#### pyvisa-py (推荐用于开发)
- 纯 Python 实现
- 跨平台
- 不需要安装 NI 驱动

```bash
pip install pyvisa-py
```

#### NI-VISA (推荐用于生产)
- 官方 NI 实现
- 性能更好
- 需要安装 NI-VISA 运行时

```bash
# 从 NI 官网下载安装
# https://www.ni.com/zh-cn/support/downloads/drivers/
```

### 连接测试脚本

```python
#!/usr/bin/env python3
import pyvisa

def test_visa_connection():
    print("=" * 50)
    print("NI-VISA 连接测试")
    print("=" * 50)
    
    try:
        # 创建资源管理器
        rm = pyvisa.ResourceManager('@py')
        print("\n✅ 资源管理器创建成功")
        
        # 列出设备
        devices = rm.list_resources()
        print(f"\n📋 发现 {len(devices)} 个设备：")
        
        for i, device in enumerate(devices, 1):
            print(f"  {i}. {device}")
        
        # 如果没有设备
        if not devices:
            print("\n❌ 未发现任何 VISA 设备")
            print("   请检查：")
            print("   1. 设备是否已连接")
            print("   2. NI-VISA 驱动是否已安装")
            print("   3. NI MAX 中是否能看到设备")
            return
        
        # 尝试连接第一个设备
        print(f"\n🔌 尝试连接设备: {devices[0]}")
        inst = rm.open_resource(devices[0], timeout=5000)
        print("✅ 设备连接成功")
        
        # 查询设备信息
        idn = inst.query('*IDN?')
        print(f"\n📝 设备信息: {idn.strip()}")
        
        # 读取一个测试值
        print("\n📊 尝试读取功率值...")
        try:
            power = inst.query('MEAS:POW?')
            print(f"✅ 功率值: {float(power.strip()):.2f} W")
        except:
            print("⚠️  无法读取功率，可能命令不兼容")
        
        inst.close()
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_visa_connection()
```

### 注意事项

1. **确保设备支持 SCPI 命令**
   - 不同厂商可能有不同的命令集
   - 查阅设备手册获取具体命令

2. **连接参数**
   - 根据设备类型选择正确的资源字符串
   - 设置适当的超时时间

3. **错误处理**
   - 所有 VISA 操作都应该在 try-except 中
   - 连接断开时及时清理资源

4. **性能考虑**
   - 避免频繁的 open/close 操作
   - 使用批量查询提高效率
   - 合理设置采样间隔

5. **权限问题**
   - Linux 上可能需要 root 权限访问 USB 设备
   - Windows 上可能需要管理员权限

### 常见功率计型号

#### YOKOGAWA (横河) WT 系列
```python
# 查询功率
power = instrument.query('MEAS:POW?')

# 查询电压/电流/功率
# 格式: "U,I,P"
values = instrument.query('MEAS:ALL?')
```

#### KEITHLEY (吉时利)
```python
# 查询功率
power = instrument.query('MEASure:POWer?')
```

#### Chroma (致茂)
```python
# 查询功率
power = instrument.query(':MEAS:POW?')
```

#### Fluke (福禄克)
```python
# 查询功率
power = instrument.query('MEAS:POW?')
```
