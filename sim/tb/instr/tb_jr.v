`timescale 1ps/1ps

module tb_jr ();
    reg clk, rst;

    cpu_top cpu (
        .clk(clk),
        .rst(rst)
    );

    always #5 clk <= ~clk;

    initial begin
        $dumpfile("waves/tb_jr.vcd");
        $dumpvars(0, tb_jr);

        clk = 0;
        rst = 1;

        cpu.u_pc.curr_pc = 32'd0;
        
        // 把跳转目标地址存入 $31 ($ra)
        // 假设我们要跳到地址 12 (对应 mem[3])
        cpu.u_regfile.regs[31] = 32'd12; 
        
        cpu.u_regfile.regs[1] = 32'd10;
        cpu.u_regfile.regs[2] = 32'd20;
        cpu.u_regfile.regs[3] = 32'd0;

        // 写入指令内存
        // mem[0]: jr $31
        cpu.u_instrm.mem[0] = 32'h03e00008; 
        
        // mem[1]: addu $3, $1, $2 (这行指令应该被跳过)
        cpu.u_instrm.mem[1] = 32'h00221821; 
        
        // mem[2]: addu $0, $0, $0 (nop)
        cpu.u_instrm.mem[2] = 32'h00000021; 
        
        // mem[3]: addu $3, $1, $1 (跳转目标：$3 应变为 20)
        cpu.u_instrm.mem[3] = 32'h00211821; 

        #10;
        rst = 0;

        // 周期1：取指 jr $31
        @(posedge clk); #1;
        $display("Time %0t: Executing JR, Current PC = %d", $time, cpu.instr_addr);

        // 周期2：执行跳转
        @(posedge clk); #1;
        $display("Time %0t: After JR, New PC = %d", $time, cpu.instr_addr);
        $display("Time %0t: R[3] = %d", $time, cpu.u_regfile.regs[3]);

        // 周期3：执行 mem[3] 的指令 addu $3, $1, $1
        @(posedge clk); #1;
        if (cpu.u_regfile.regs[3] == 32'd20)
            $display("TEST PASSED");
        else
            $display("TEST FAILED: R[3] expected 20, got %d", cpu.u_regfile.regs[3]);
        $finish;
    end
endmodule
