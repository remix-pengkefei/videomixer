#!/bin/bash
# VideoMixer 启动脚本 — 双击即可启动服务
cd "$(dirname "$0")"
echo "=========================================="
echo "  VideoMixer v2.0"
echo "=========================================="
echo ""
echo "启动服务中..."
echo "启动后请在浏览器打开: http://$(ipconfig getifaddr en0 2>/dev/null || echo localhost):8000"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""
./bin/videomixer-server
