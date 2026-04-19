`timescale 1ns/1ps

module tb_jal ();
    reg clk, rst;

    cpu_top cpu (
        .clk(clk),
        .rst(rst)
    );

    always #5 clk <= ~clk;

    initial begin
        $dumpfile("waves/tb_jal.vcd");
        $dumpvars(0, tb_jal);

        clk = 0;
        rst = 1;
        
        cpu.u_pc.curr_pc = 32'd0;
        cpu.u_regfile.regs[31] = 32'd0; // $ra 清零
        cpu.u_regfile.regs[4]  = 32'd0; // 用于验证跳转目标后的结果

        cpu.u_instrm.mem[0] = 32'h0C000003; // jal 3 (opcode = 0x0C, target = 3)
        cpu.u_instrm.mem[1] = 32'h00000000; // nop
        cpu.u_instrm.mem[3] = 32'h03E02021; // addu $4, $31, $0 -> 将 $ra 的值传给 $4

        #10;
        rst = 0;

        // 周期 1: 取指并执行 jal
        @(posedge clk); #1;
        $display("Execute jal: Current PC = %d, Target PC = %d", 0, cpu.instr_addr);

        // 周期 2: 执行跳转目标的指令
        @(posedge clk); #1;
        $display("After Jump: instr_addr = %d", cpu.instr_addr);
        $display("Return Address ($31) = %d", cpu.u_regfile.regs[31]);

        // 验证逻辑:
        // 1. PC 应该跳转到了 12
        // 2. $31 应该保存了返回地址 4 (假设没有延迟槽)
        // 3. $4 应该拿到了 $31 的值，也就是 4
        if (cpu.u_regfile.regs[31] == 32'd4 && cpu.u_regfile.regs[4] == 32'd4) begin
            $display("TEST PASSED");
            $display("Successfully jumped to PC 12 and saved RA=4 in $31");
        end else begin
            $display("TEST FAILED");
            $display("Expected: RA=4, R[4]=4; Actual: RA=%d, R[4]=%d", 
                      cpu.u_regfile.regs[31], cpu.u_regfile.regs[4]);
        end

        $finish;
    end
endmodule
