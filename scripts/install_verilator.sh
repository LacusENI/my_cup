#!/usr/bin/env bash
#
# 安装项目本地 Verilator。
#
# 为什么不用 apt：Ubuntu 24.04 自带 Verilator 5.020，而 cocotb 2.1 的
# Verilator runner 至少需要 5.036；覆盖率流程当前固定用 5.054。
#
# 结果安装到 .tools/verilator/<version>/，不会覆盖系统 Verilator。
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
PREFIX="${VERILATOR_PREFIX:-$ROOT/.tools/verilator/$VERSION}"
URL="https://github.com/verilator/verilator/archive/refs/tags/v${VERSION}.tar.gz"

if [[ -x "$PREFIX/bin/verilator" ]]; then
    installed="$("$PREFIX/bin/verilator" --version | head -1)"
    if [[ "$installed" == *"$VERSION"* ]]; then
        echo "Verilator $VERSION already installed: $PREFIX/bin/verilator"
        exit 0
    fi
fi

missing=()
for tool in autoconf flex bison make g++ curl; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        missing+=("$tool")
    fi
done
if ((${#missing[@]})); then
    cat >&2 <<EOF
缺少构建依赖：${missing[*]}

Ubuntu/Debian 可以安装：
  sudo apt-get update
  sudo apt-get install -y autoconf flex bison libfl-dev g++ make curl python3
EOF
    exit 1
fi

tmp="$(mktemp -d "${TMPDIR:-/tmp}/verilator.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT

echo "Downloading Verilator $VERSION..."
curl -fL "$URL" -o "$tmp/verilator.tar.gz"
tar -xzf "$tmp/verilator.tar.gz" -C "$tmp"

src="$tmp/verilator-$VERSION"
if [[ ! -d "$src" ]]; then
    echo "unexpected archive layout: $src not found" >&2
    exit 1
fi

echo "Configuring Verilator (prefix: $PREFIX)..."
(
    cd "$src"
    autoconf
    ./configure --prefix="$PREFIX"
    make -j"$(nproc)"
    make install
)

echo
echo "Installed:"
"$PREFIX/bin/verilator" --version | head -1
"$PREFIX/bin/verilator_coverage" --version 2>/dev/null | head -1 || true
echo
echo "Run: make cov"
