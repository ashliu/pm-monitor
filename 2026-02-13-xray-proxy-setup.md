# OpenClaw 部署代理配置指南

本文档记录在阿里云服务器上部署 OpenClaw 并配置外网代理的完整过程。

## 背景

OpenClaw 部署在阿里云服务器上，无法直接访问外网（Google、OpenAI 等）。需要通过本地 VPN + Xray 代理实现外网访问。

## 完整步骤

### 1. 安装 Xray

#### 1.1 本地开启 VPN + SSH 端口转发

在本地电脑执行（需要先连接好 VPN）：

```bash
# 将本地的 10808 端口转发到服务器的 10808 端口
ssh -N -R 10808:127.0.0.1:10808 ash@47.92.124.238
```

> 注意：本地 VPN 需要开启 SOCKS5 代理并监听在 127.0.0.1:10808

#### 1.2 服务器下载并安装 Xray

```bash
# 下载 xray
curl -o /tmp/xray https://github.com/XTLS/Xray-core/releases/download/v1.8.6/xray-linux-64.zip

# 解压
unzip -o /tmp/xray -d /tmp/

# 赋予执行权限
chmod +x /tmp/xray
```

#### 1.3 配置 Xray

创建配置文件 `/tmp/xray-config.json`：

```json
{
  "inbounds": [
    {
      "tag": "socks",
      "port": 20808,
      "listen": "127.0.0.1",
      "protocol": "socks",
      "settings": {
        "auth": "noauth"
      }
    },
    {
      "tag": "http",
      "port": 20809,
      "listen": "127.0.0.1",
      "protocol": "http",
      "settings": {}
    }
  ],
  "outbounds": [
    {
      "tag": "proxy",
      "protocol": "vless",
      "settings": {
        "vnext": [
          {
            "address": "138.128.220.153",
            "port": 443,
            "users": [
              {
                "id": "9c7d4f2e-3a1b-4c5d-8e6f-0a1b2c3d4e5f",
                "flow": "xtls-rprx-vision"
              }
            ]
          }
        ]
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "serverNames": ["www.speedtest.net"],
          "publicKey": "W7XR6yY7Q1pX8K9zL4mN2pR6tY8vB0cA",
          "shortId": "abcd1234"
        }
      }
    },
    {
      "tag": "direct",
      "protocol": "freedom",
      "settings": {}
    }
  ],
  "routing": {
    "domainStrategy": "IPIfNonMatch",
    "rules": [
      {
        "type": "field",
        "inboundTag": ["socks", "http"],
        "outboundTag": "proxy"
      }
    ]
  }
}
```

> 上述配置通过 VLESS Reality 协议连接到美国 VPN 节点

#### 1.4 启动 Xray

```bash
# 前台运行测试
/tmp/xray run -c /tmp/xray-config.json

# 后台运行
nohup /tmp/xray run -c /tmp/xray-config.json > /tmp/xray.log 2>&1 &

# 验证启动
ps aux | grep xray
tail -f /tmp/xray.log
```

### 2. 命令行临时代理

在命令行中设置代理环境变量（仅当前会话有效）：

```bash
export http_proxy="http://127.0.0.1:20809"
export https_proxy="http://127.0.0.1:20809"
# 或者
export HTTP_PROXY="http://127.0.0.1:20809"
export HTTPS_PROXY="http://127.0.0.1:20809"
```

测试代理是否生效：

```bash
curl -s --max-time 10 https://api.openai.com/v1/models
```

### 3. 配置 systemd 服务（后台运行）

编辑 systemd 服务文件：

```bash
vim ~/.config/systemd/user/openclaw-gateway.service
```

在 `[Service]` 部分添加代理环境变量：

```ini
[Service]
ExecStart="/usr/bin/node" "/home/ash/.npm-global/lib/node_modules/openclaw/dist/index.js" gateway --port 18789
Restart=always
RestartSec=5
KillMode=process
Environment=HTTP_PROXY=http://127.0.0.1:20809
Environment=HTTPS_PROXY=http://127.0.0.1:20809
Environment="HOME=/home/ash"
Environment="PATH=..."
Environment=OPENCLAW_GATEWAY_PORT=18789
Environment=OPENCLAW_GATEWAY_TOKEN=xxx
```

重新加载并重启服务：

```bash
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway
systemctl --user status openclaw-gateway
```

## 常用命令

```bash
# 启动 OpenClaw（后台）
openclaw gateway start

# 停止 OpenClaw
openclaw gateway stop

# 查看状态
openclaw gateway status

# 前台运行（调试用）
openclaw gateway run

# 重启
openclaw gateway restart

# 查看日志
journalctl --user -u openclaw-gateway.service -n 200 --no-pager

# Xray 相关
ps aux | grep xray
tail -f /tmp/xray.log
pkill xray
```

## 代理端口说明

| 端口 | 用途 |
|------|------|
| 10808 | SSH 端口转发入口（本地 → 服务器） |
| 20808 | Xray SOCKS5 代理 |
| 20809 | Xray HTTP 代理 |

## 故障排查

1. **服务启动失败**：检查 `journalctl --user -u openclaw-gateway.service`
2. **网络不通**：确认 Xray 是否正常运行 `ps aux | grep xray`
3. **代理不生效**：确认环境变量配置正确 `env | grep -i proxy`

---

*本文档由 ash-bot 生成于 2026-02-13*
