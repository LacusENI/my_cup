# 常用命令；具体路径、工具和参数在 toolchain.toml 中配置。
UV ?= uv
MYCUP := $(UV) run mycup
CYCLES ?= 8

.PHONY: help init code-gen code-gen-check programs asm lint test check fmt prog doctor clean

help:
	@echo "make init                生成 .verilator/verilator.f 和 .slang/slang.f"
	@echo "make code-gen            按 toolchain.toml 运行代码生成器"
	@echo "make code-gen-check      检查生成文件是否最新"
	@echo "make programs            汇编 programs/**/*.S"
	@echo "make asm FILE=<.S>       汇编单个程序"
	@echo "make lint                Verilator 静态检查"
	@echo "make test                运行 cocotb + pytest"
	@echo "make check               lint + test"
	@echo "make fmt                 用 verible 格式化 RTL（原地修改）"
	@echo "make prog FILE=<hex>     运行程序；可选 DATA=<hex> CYCLES=8"
	@echo "make doctor              检查 toolchain.toml 和外部工具"
	@echo "make clean               清理生成物"

init:
	$(MYCUP) init

code-gen:
	$(MYCUP) code-gen

code-gen-check:
	$(MYCUP) code-gen --check

programs:
	$(MYCUP) build-programs

asm:
	@test -n "$(FILE)" || { echo "usage: make asm FILE=programs/demo.S" >&2; exit 1; }
	$(MYCUP) asm "$(FILE)"

lint:
	$(MYCUP) lint

test:
	$(MYCUP) test

check: lint test

fmt:
	$(MYCUP) fmt

prog:
	@test -n "$(FILE)" || { echo "usage: make prog FILE=programs/demo.S [DATA=...] [CYCLES=8]" >&2; exit 1; }
	$(MYCUP) prog "$(FILE)" $(if $(DATA),--data "$(DATA)") --cycles "$(CYCLES)"

doctor:
	$(MYCUP) doctor

clean:
	$(MYCUP) clean
