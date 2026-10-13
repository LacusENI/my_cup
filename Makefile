SHELL      := /bin/bash
RTL_DIR    = rtl
SIM_DIR    = sim
TB_DIR     = sim/tb
BUILD_DIR  = build
F_DIR      = build/filelists
TARGET_DIR = build/targets
WAVES_DIR  = waves
LOGS_DIR   = logs
INC_PATH   = lib rtl/core/include sim/tb/include 

# 仿真期程序装载 (可选)
#   make run-tb_xxx PROG=programs/demo.hex [DATA=programs/data.hex]
PROG ?=
DATA ?=
SIM_ARGS = $(if $(PROG),+instr=$(PROG)) $(if $(DATA),+data=$(DATA))

# Rtl
RTL_FILES := $(shell find $(RTL_DIR) -name "*.v")

# Build
BUILD_LOG := $(LOGS_DIR)/build.log
BUILD_FLAGS = -g2012
F_FILES := $(shell find $(F_DIR) -name "*.f")
TASKS := $(basename $(notdir $(F_FILES))) 

# Lint  (文件清单与参数由 chore/gen_lint_f.sh 统一生成，IDE 亦复用该清单)
LINT_F   := verilator.f
LINT_LOG := $(LOGS_DIR)/lint.log

# Dump
DUMP_FILES := $(wildcard $(WAVES_DIR)/*.vcd)

$(shell mkdir -p $(BUILD_DIR) $(WAVES_DIR) $(LOGS_DIR))

.PHONY: init list all clean lint filelist help

init: filelist
	chore/gen_tb_dep.sh

filelist:
	@chore/gen_lint_f.sh

list:
	$(foreach task,$(TASKS),$(info $(task)))

build-%: $(F_DIR)/%.f
	@echo "Build($*): $(shell date '+%Y-%m-%d %H:%M:%S')" | tee -a $(BUILD_LOG)
	@iverilog $(BUILD_FLAGS) -o $(TARGET_DIR)/$* -f $^ $(addprefix -I,$(INC_PATH)) >> $(BUILD_LOG) 2>&1 && echo "OK" | tee -a $(BUILD_LOG) || (echo "FAILED"; exit 1)

run-%: build-%
	@echo "Run($*): $(shell date '+%Y-%m-%d %H:%M:%S')"
	@vvp $(TARGET_DIR)/$* $(SIM_ARGS) || (echo "FAILED"; exit 1)

all: $(addprefix run-,$(TASKS))
	@echo ""

wave-%: $(WAVES_DIR)/%.vcd
	gtkwave $^

clean:
	rm -rf $(BUILD_DIR) $(WAVES_DIR) $(LOGS_DIR)

lint: filelist
	@echo "Linting: $(shell date '+%Y-%m-%d %H:%M:%S')" | tee -a $(LINT_LOG)
	@set -o pipefail; verilator -f $(LINT_F) 2>&1 | tee -a $(LINT_LOG)

help:
	@echo "Commands:"
	@echo " make init         - initialize dependencies (filelist + testbench deps)"
	@echo " make filelist     - regenerate verilator.f (lint filelist, shared with IDE)"
	@echo " make list         - list all build tasks"
	@echo " make build-[name] - build (e.g. build-tb_alu)"
	@echo " make run-[name]   - run (e.g. run-tb_alu)"
	@echo " make all          - run all"
	@echo " make wave-[name]  - display wave (e.g. wave-alu)"
	@echo " make clean        - clean all generated files"
	@echo " make lint  	      - run linting on all RTL files"
	@echo ""
	@echo "Program loading (simulation only):"
	@echo "   make run-[name] PROG=programs/demo.hex   - load instruction memory (+instr=)"
	@echo "   make run-[name] DATA=programs/data.hex   - load data memory (+data=)"
