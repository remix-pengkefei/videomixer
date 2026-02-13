# VideoMixer 部署指南

本文件供目标 Mac 上的 Claude Code 自动执行。请按顺序执行以下所有步骤。

## 1. 安装 Homebrew（如果未安装）

```bash
which brew || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

安装完成后确保 brew 在 PATH 中：
```bash
eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || eval "$(/usr/local/bin/brew shellenv)" 2>/dev/null
```

## 2. 安装 ffmpeg

```bash
brew install ffmpeg
```

验证：
```bash
ffmpeg -version | head -1
```

## 3. 设置可执行权限

```bash
chmod +x ~/Desktop/videomixer-deploy/bin/videomixer-server
chmod +x ~/Desktop/videomixer-deploy/bin/videomixer-processor
chmod +x ~/Desktop/videomixer-deploy/start.command
```

## 4. 解除 macOS 安全限制

macOS 会阻止未签名的二进制。需要移除隔离属性：

```bash
xattr -cr ~/Desktop/videomixer-deploy/
```

## 5. 启动服务测试

```bash
cd ~/Desktop/videomixer-deploy && ./bin/videomixer-server
```

服务应该在 http://0.0.0.0:8000 启动。用浏览器访问验证页面正常加载。

## 6. 获取局域网 IP

```bash
ipconfig getifaddr en0
```

输出的 IP（如 192.168.1.x）就是其他员工要访问的地址：`http://192.168.1.x:8000`

## 7. 设置开机自启（可选）

创建 launchd 服务，开机自动启动 VideoMixer：

```bash
cat > ~/Library/LaunchAgents/com.videomixer.server.plist << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.videomixer.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>DEPLOY_PATH/bin/videomixer-server</string>
    </array>
    <key>WorkingDirectory</key>
    <string>DEPLOY_PATH</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>DEPLOY_PATH/workspace/logs/server.log</string>
    <key>StandardErrorPath</key>
    <string>DEPLOY_PATH/workspace/logs/server_error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
PLIST
```

**注意**：执行前需要把上面的 `DEPLOY_PATH` 替换为 videomixer-deploy 的实际绝对路径（如 `/Users/xxx/Desktop/videomixer-deploy`）。

然后加载服务：
```bash
launchctl load ~/Library/LaunchAgents/com.videomixer.server.plist
```

停止服务：
```bash
launchctl unload ~/Library/LaunchAgents/com.videomixer.server.plist
```

## 目录结构

```
videomixer-deploy/
├── bin/                      ← 编译后的二进制（不可逆向）
│   ├── videomixer-server     ← Web 服务
│   ├── videomixer-processor  ← 混剪处理引擎
│   └── _internal/            ← 运行时依赖
├── assets/                   ← 素材（贴纸、闪光、填充视频）
├── web/frontend/dist/        ← 前端页面
├── workspace/                ← 运行时数据（上传、输出、日志）
├── data/                     ← 配置和计数器
├── start.command             ← 双击启动
└── INSTALL.md                ← 本文件
```

## 故障排查

- **"无法打开，因为无法验证开发者"**：执行步骤 4 的 xattr 命令
- **ffmpeg 未找到**：确认 `which ffmpeg` 有输出，没有就重新 `brew install ffmpeg`
- **端口被占用**：`lsof -i :8000` 查看占用进程，`kill` 掉后重试
- **素材缺失**：确认 assets/ 目录完整拷贝（应有 stickers、sparkles、filler_videos 子目录）
