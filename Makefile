RTL_DIR    = rtl
SIM_DIR    = sim
TB_DIR     = sim/tb
BUILD_DIR  = build
F_DIR      = build/filelists
TARGET_DIR = build/targets
WAVES_DIR  = waves
LOGS_DIR   = logs

# Rtl
RTL_FILES := $(shell find $(RTL_DIR) -name "*.v")

# Build
BUILD_LOG := $(LOGS_DIR)/build.log
BUILD_FLAGS = -g2012
F_FILES := $(shell find $(F_DIR) -name "*.f")
TASKS := $(basename $(notdir $(F_FILES))) 

# Lint
LINT_FLAGS = --lint-only -Wall --timing --bbox-sys
LINT_LOG := $(LOGS_DIR)/lint.log
V_DIRS := $(shell find . -name "*.v" -exec dirname {} + | sort -u)
INC_PATH := $(addprefix -I,$(V_DIRS))

# Dump
DUMP_FILES := $(wildcard $(WAVES_DIR)/*.vcd)

$(shell mkdir -p $(BUILD_DIR) $(WAVES_DIR) $(LOGS_DIR))

.PHONY: init list all clean lint help

init:
	./chore/gen_tb_dep.sh

list:
	$(foreach task,$(TASKS),$(info $(task)))

build-%: $(F_DIR)/%.f
	@echo "Build($*): $(shell date '+%Y-%m-%d %H:%M:%S')" | tee -a $(BUILD_LOG)
	@iverilog $(BUILD_FLAGS) -o $(TARGET_DIR)/$* -f $^ >> $(BUILD_LOG) 2>&1 && echo "OK" | tee -a $(BUILD_LOG) || (echo "FAILED"; exit 1)

run-%: build-%
	@echo "Run($*): $(shell date '+%Y-%m-%d %H:%M:%S')"
	@vvp $(TARGET_DIR)/$* || (echo "FAILED"; exit 1)

all: $(addprefix run-,$(TASKS))
	@echo ""

wave-%: $(WAVES_DIR)/%.vcd
	gtkwave $^

clean:
	rm -rf $(BUILD_DIR) $(WAVES_DIR) $(LOGS_DIR)

lint:
	@echo "Linting: $(shell date '+%Y-%m-%d %H:%M:%S')" | tee -a $(LINT_LOG)
	@verilator $(LINT_FLAGS) $(RTL_FILES) >> $(LINT_LOG) 2>&1 | tee -a $(LINT_LOG)

help:
	@echo "Commands:"
	@echo " make init         - initialize dependencies"
	@echo " make list         - list all build tasks"
	@echo " make build-[name] - build (e.g. build-tb_alu)"
	@echo " make run-[name]   - run (e.g. run-tb_alu)"
	@echo " make all          - run all"
	@echo " make wave-[name]  - display wave (e.g. wave-alu)"
	@echo " make clean        - clean all generated files"
	@echo " make lint  	      - run linting on all RTL files"
