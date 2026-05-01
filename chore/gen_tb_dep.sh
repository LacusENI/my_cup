#!/bin/bash

# 用于搜索 testbench 文件并生成其所需的 .f 和 .d 文件的 Shell 脚本

TB_ROOT="./sim/tb"
RTL_DIR="./rtl"
F_DIR="./build/filelists"
D_DIR="./build/deps"

# 创建输出目录
mkdir -p "$F_DIR" "$D_DIR"

echo "Scanning for testbenches in $TB_ROOT..."

# 找出所有的 tb_*.v 文件
find "$TB_ROOT" -name "tb_*.v" | while read -r tb_path; do
    # 提取文件名 (例如 tb_alu)
    tb_name=$(basename "$tb_path" .v)
    
    # 定义输出文件路径
    f_file="$F_DIR/$tb_name.f"
    d_file="$D_DIR/$tb_name.d"
    
    # --- 1. 生成 .f 文件 (编译器清单) ---
    echo "// Generated for iverilog" > "$f_file"
    echo "+incdir+./include" >> "$f_file"
    # 写入所有 RTL 文件路径
    find "$RTL_DIR" -name "*.v" >> "$f_file"
    # 写入当前的 TB 文件路径
    echo "$tb_path" >> "$f_file"

    # --- 2. 生成 .d 文件 (Makefile 依赖片段) ---
    # 目标是生成类似: build/tb_alu: tb/unit/tb_alu.v rtl/alu.v ...
    # 把所有的 .v 文件都作为依赖项
    echo -n "build/$tb_name: " > "$d_file"
    
    # 整合依赖：当前的 tb 文件 + 所有的 rtl 文件 (转为一行)
    all_deps="$tb_path $(find "$RTL_DIR" -name "*.v" | tr '\n' ' ')"
    echo "$all_deps" >> "$d_file"
    
    echo "  >> Done: $tb_name"
done

echo "All filelists and dependency rules generated in $OUT_DIR."