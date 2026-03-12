RTL_DIR = rtl
SIM_DIR = sim
BUILD_DIR = build
WAVES_DIR = waves
LOGS_DIR = logs

RTL_SRCS = $(shell find $(RTL_DIR) -name "*.v")
TB_SRCS = $(wildcard $(SIM_DIR)/tb/*.v)
SOURCES = $(RTL_SRCS) $(TB_SRCS)
TARGET = $(BUILD_DIR)/simv
WAVES = $(wildcard waves/*.vcd)
LOG_FILE = $(LOGS_DIR)/compile.log

$(shell mkdir -p $(BUILD_DIR) $(WAVES_DIR) $(LOGS_DIR))

$(TARGET): $(SOURCES)
	iverilog -o $(TARGET) $(SOURCES) > $(LOG_FILE) 2>&1

run: $(TARGET)
	vvp $(TARGET)

wave: $(WAVES)
	gtkwave $(WAVES)

clean:
	rm -rf $(BUILD_DIR) $(WAVES_DIR) $(LOGS_DIR)

.PHONY: run wave clean