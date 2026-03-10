RTL_DIR = rtl
SIM_DIR = sim
BUILD_DIR = build
WAVES_DIR = waves
LOGS_DIR = logs

SOURCES = $(wildcard $(RTL_DIR)/*.v $(wildcard $(SIM_DIR)/*.v))
TARGET = $(BUILD_DIR)/simv
WAVES = $(wildcard waves/*.vcd)
LOG_FILE = $(LOGS_DIR)/compile.log

$(shell mkdir -p $(BUILD_DIR) $(WAVES_DIR) $(LOGS_DIR))

$(TARGET): $(SOURCES)
	iverilog -o $(TARGET) $(SOURCES) > $(LOG_FILE) 2>&1

run: $(TARGET)
	vvp $(TARGET) +vcd=$(WAVES)

wave: $(WAVES)
	gtkwave $(WAVES)

clean:
	rm -rf $(BUILD_DIR) $(WAVES_DIR) $(LOGS_DIR)

.PHONY: run wave clean