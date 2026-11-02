# 常用命令；具体路径、工具和参数在 toolchain.toml 中配置。
UV ?= uv
MYCUP := $(UV) run mycup
CYCLES ?= 8

.PHONY: help init lint test check fmt cov install-verilator prog doctor clean

help:
	@echo "make init                生成 .verilator/verilator.f 和 .slang/slang.f"
	@echo "make lint                Verilator 静态检查"
	@echo "make test                运行 cocotb + pytest"
	@echo "make check               lint + test"
	@echo "make fmt                 用 verible 格式化 RTL（原地修改）"
	@echo "make cov                 用 Verilator 跑测试并生成覆盖率"
	@echo "make install-verilator   安装项目本地 Verilator（覆盖率用）"
	@echo "make prog FILE=<hex>     运行程序；可选 DATA=<hex> CYCLES=8"
	@echo "make doctor              检查 toolchain.toml 和外部工具"
	@echo "make clean               清理生成物"

init:
	$(MYCUP) init

lint:
	$(MYCUP) lint

test:
	$(MYCUP) test

check: lint test

fmt:
	$(MYCUP) fmt

cov:
	$(MYCUP) cov

install-verilator:
	scripts/install_verilator.sh

prog:
	@test -n "$(FILE)" || { echo "usage: make prog FILE=programs/demo.hex [DATA=...] [CYCLES=8]" >&2; exit 1; }
	$(MYCUP) prog "$(FILE)" $(if $(DATA),--data "$(DATA)") --cycles "$(CYCLES)"

doctor:
	$(MYCUP) doctor

clean:
	$(MYCUP) clean
