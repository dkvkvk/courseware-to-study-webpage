#!/usr/bin/env bash
# 用法：bash build.sh <源目录> <输出文件>
# 源目录中按文件名排序拼接所有 .html 分块（00_head → 10_… → 80_svgdefs → 90_core.js）。
set -euo pipefail
SRC="${1:-.}"; OUT="${2:-lesson.html}"
ls "$SRC"/*.html | sort | xargs cat > "$OUT"
echo "built $OUT ($(wc -c < "$OUT") bytes)"
