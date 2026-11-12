#!/usr/bin/env bash
# One-time setup per session for tools/make_short.py
set -e
pip install -q kokoro-onnx soundfile scipy --break-system-packages 2>/dev/null
D=${KOKORO_DIR:-/home/claude/tts}
mkdir -p "$D"
[ -s "$D/kokoro.onnx" ] || curl -sSL -o "$D/kokoro.onnx" https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx
[ -s "$D/voices.bin" ] || curl -sSL -o "$D/voices.bin" https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
echo "setup ok"
