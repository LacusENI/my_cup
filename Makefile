RTL_DIR = rtl
SIM_DIR = sim
TB_DIR = sim/tb
BUILD_DIR = build
WAVES_DIR = $(BUILD_DIR)/waves
LOGS_DIR = logs

BUILD_LOG = $(LOGS_DIR)/compile.log
RTL_SRCS = $(shell find $(RTL_DIR) -name "*.v")
TB_FILES := $(wildcard $(TB_DIR)/tb_*.v)
TESTS := $(patsubst $(TB_DIR)/tb_%.v,%,$(TB_FILES))
WAVES = $(wildcard $(WAVES_DIR)/*.vcd)

$(shell mkdir -p $(BUILD_DIR) $(WAVES_DIR) $(LOGS_DIR))

tb_%: $(RTL_SRCS) $(TB_DIR)/tb_%.v
	iverilog -o $(BUILD_DIR)/$@ $^ >> $(BUILD_LOG) 2>&1

run-%: tb_%
	vvp $(BUILD_DIR)/$^ > $(LOGS_DIR)/$^.log

all: $(addprefix run-,$(TESTS))

wave: $(WAVES)
	gtkwave $(WAVES)

clean:
	rm -rf $(BUILD_DIR) $(WAVES_DIR) $(LOGS_DIR)

.PHONY: tb_% run-% wave clean 