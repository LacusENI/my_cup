#!/usr/bin/env bash
#
# 用 conda-forge 安装项目本地 Verilator。
#
# 为什么不用 apt：Ubuntu 24.04 自带 Verilator 5.020，而 cocotb 2.1 的
# Verilator runner 至少需要 5.036；覆盖率流程当前固定用 5.054。
#
# 为什么用 conda：conda-forge 有现成的 Linux 包，避免源码构建时
# flex/bison/autoconf 等依赖问题。
#
# 结果安装到 .tools/verilator-conda/，不会覆盖系统 Verilator。
# 之后 `mycup cov` 会自动优先使用它。
#
# 用法：
#   scripts/install_verilator.sh
#   VERILATOR_VERSION=5.054 scripts/install_verilator.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${VERILATOR_VERSION:-}"
if [[ -z "$VERSION" ]]; then
    # 默认跟随 toolchain.toml 的 [cov] min_version。
    VERSION="$(python3 - "$ROOT/toolchain.toml" <<'PY' 2>/dev/null || true
import sys
import tomllib

with open(sys.argv[1], "rb") as fh:
    print(tomllib.load(fh)["cov"]["min_version"])
PY
)"
fi
VERSION="${VERSION:-5.054}"
PREFIX="${VERILATOR_PREFIX:-$ROOT/.tools/verilator-conda}"

if [[ -x "$PREFIX/bin/verilator" ]]; then
    installed="$("$PREFIX/bin/verilator" --version | head -1)"
    if [[ "$installed" == *"$VERSION"* ]]; then
        echo "Verilator $VERSION already installed: $PREFIX/bin/verilator"
        exit 0
    fi
fi

if command -v micromamba >/dev/null 2>&1; then
    CONDA=(micromamba)
elif command -v conda >/dev/null 2>&1; then
    CONDA=(conda)
else
    cat >&2 <<EOF
找不到 conda/micromamba。

建议安装 micromamba（不需要 root）：
  "\${SHELL}" <(curl -L micro.mamba.pm/install.sh)

或者使用已有的 conda：
  conda create -p .tools/verilator-conda -c conda-forge verilator=$VERSION -y
EOF
    exit 1
fi

echo "Installing Verilator $VERSION with ${CONDA[0]}..."
"${CONDA[@]}" create -p "$PREFIX" -c conda-forge "verilator=$VERSION" -y

echo
echo "Installed:"
"$PREFIX/bin/verilator" --version | head -1
"$PREFIX/bin/verilator_coverage" --version 2>/dev/null | head -1 || true
echo
echo "Run: make cov"
