`timescale 1ns/1ps

module tb_load_save();

    reg clk, rst;

    cpu_top cpu (
        .clk(clk),
        .rst(rst)
    );

    always #5 clk <= ~clk;

    initial begin
        $dumpfile("waves/tb_load_save.vcd");
        $dumpvars(0, tb_load_save);

        clk = 0;
        rst = 1;

        // --- 初始化环境 ---
        // $1: 基址寄存器 = 8
        // $3: 数据源 A = 0xAA (用于 sb)
        // $4: 数据源 B = 0xBBCC (用于 sh)
        // $5: 数据源 C = 0x11223344 (用于对比 sw)
        cpu.u_regfile.regs[1] = 32'd8;   
        cpu.u_regfile.regs[3] = 32'h0000_00AA; 
        cpu.u_regfile.regs[4] = 32'h0000_BBCC; 
        cpu.u_regfile.regs[5] = 32'h1122_3344;
        
        // 清空内存地址 8 (即 u_datam.mem[2])
        cpu.u_datam.mem[2] = 32'h0; 

        // --- 写入指令序列 (大端 MIPS 机器码) ---
        cpu.u_pc.curr_pc = 32'd0;
        
        // 1. sb $3, 0($1) -> 往地址 8 存 0xAA。在大端下，Memory[2] 应变为 AA 00 00 00
        cpu.u_instrm.mem[0] = 32'hA0230000; // sb $3, 0($1)
        
        // 2. sb $3, 1($1) -> 往地址 9 存 0xAA。在大端下，Memory[2] 应变为 AA AA 00 00
        cpu.u_instrm.mem[1] = 32'hA0230001; // sb $3, 1($1)

        // 3. sh $4, 2($1) -> 往地址 10 存 0xBBCC。在大端下，Memory[2] 应变为 AA AA BB CC
        cpu.u_instrm.mem[2] = 32'hA4240002; // sh $4, 2($1)

        // 4. lw $2, 0($1) -> 把地址 8 的字读回 $2，验证是否为 0xAAAABBCC
        cpu.u_instrm.mem[3] = 32'h8C220000; // lw $2, 0($1)

        #10;
        rst = 0;

        // 让 CPU 执行 4 条指令 (假设单周期，每条 10ns)
        #40;

        $display("--- sb/sh 大端序综合测试结果 ---");
        $display("寄存器状态:");
        $display("R[3] (src_byte) = %h", cpu.u_regfile.regs[3]);
        $display("R[4] (src_half) = %h", cpu.u_regfile.regs[4]);
        
        $display("\n内存状态 (地址 8):");
        // 注意：mem[2] 对应地址 8, 9, 10, 11
        $display("M[2] (Full Word) = %h", cpu.u_datam.mem[2]);

        $display("\n回读验证:");
        $display("R[2] (Loaded Word) = %h", cpu.u_regfile.regs[2]);

        // 自动校验：如果大端逻辑正确，M[2] 应该是 AAAABBCC
        if (cpu.u_datam.mem[2] == 32'hAAAA_BBCC && cpu.u_regfile.regs[2] == 32'hAAAA_BBCC) begin
            $display("\n[SUCCESS] sb/sh 大端拼接逻辑完全正确！");
        end else begin
            $display("\n[FAILED] 数据不匹配，请检查 mem_sel 或数据移位逻辑。");
            $display("EXPECTED: AAAABBCC");
        end

        $finish;
    end

endmodule