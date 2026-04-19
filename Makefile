RTL_DIR = rtl
SIM_DIR = sim
TB_DIR = sim/tb
BUILD_DIR = build
WAVES_DIR = waves
LOGS_DIR = logs

BUILD_LOG := $(LOGS_DIR)/compile.log
RTL_SRCS := $(shell find $(RTL_DIR) -name "*.v")
TB_FILES := $(wildcard $(TB_DIR)/tb_*.v)
TESTS := $(patsubst $(TB_DIR)/tb_%.v,%,$(TB_FILES))
WAVES := $(wildcard $(WAVES_DIR)/*.vcd)

LINT_FLAGS = --lint-only -Wall --timing --bbox-sys
LINT_LOG := $(LOGS_DIR)/lint.log
V_DIRS := $(shell find . -name "*.v" -exec dirname {} + | sort -u)
INC_PATH := $(addprefix -I,$(V_DIRS))

$(shell mkdir -p $(BUILD_DIR) $(WAVES_DIR) $(LOGS_DIR))

tb_instr_%: $(RTL_SRCS) $(TB_DIR)/instr/tb_%.v
	@echo "Build(tb_$*): $(shell date '+%Y-%m-%d %H:%M:%S')" | tee -a $(BUILD_LOG)
	@iverilog -o $(BUILD_DIR)/$@ $^ >> $(BUILD_LOG) 2>&1 && echo "OK" | tee -a $(BUILD_LOG) || (echo "FAILED"; exit 1)

tb_unit_%: $(RTL_SRCS) $(TB_DIR)/unit/tb_%.v
	@echo "Build(tb_$*): $(shell date '+%Y-%m-%d %H:%M:%S')" | tee -a $(BUILD_LOG)
	@iverilog -o $(BUILD_DIR)/$@ $^ >> $(BUILD_LOG) 2>&1 && echo "OK" | tee -a $(BUILD_LOG) || (echo "FAILED"; exit 1)

run-instr-%: tb_instr_%
	@echo "Run(tb_$*): $(shell date '+%Y-%m-%d %H:%M:%S')"
	@vvp $(BUILD_DIR)/$^ > $(LOGS_DIR)/$^.log && echo "OK" || (echo "FAILED"; exit 1)

run-unit-%: tb_unit_%
	@echo "Run(tb_$*): $(shell date '+%Y-%m-%d %H:%M:%S')"
	@vvp $(BUILD_DIR)/$^ > $(LOGS_DIR)/$^.log && echo "OK" || (echo "FAILED"; exit 1)

all: $(addprefix run-,$(TESTS))

wave-%: $(WAVES_DIR)/tb_%.vcd
	gtkwave $^

clean:
	rm -rf $(BUILD_DIR) $(WAVES_DIR) $(LOGS_DIR) $(LOGS_DIR)

lint:
	@echo "Linting: $(shell date '+%Y-%m-%d %H:%M:%S')" | tee -a $(LINT_LOG)
	@verilator $(LINT_FLAGS) $(RTL_SRCS) >> $(LINT_LOG) 2>&1 | tee -a $(LINT_LOG)

help:
	@echo "Commands:"
	@echo " make tb_[module]   - build specific module testbench (e.g. make tb_alu)"
	@echo " make run-[module]  - run specific module testbench (e.g. make run-alu)"
	@echo " make all           - run all testbenches"
	@echo " make wave-[module] - display wave for specific module (e.g. make wave-alu)"
	@echo " make clean         - clean all generated files"
	@echo " make lint  	       - run linting on all RTL files"

.PHONY: tb_% run-% all wave-% clean lint help