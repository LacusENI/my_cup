`timescale 1ns/1ps
`include "vtest.vh"
`include "instr.vh"

module tb_jal ();
    reg clk, rst;

    cpu_top cpu (
        .clk(clk),
        .rst(rst)
    );

    always #5 clk <= ~clk;

    `VTEST_INIT

    // addu rd, rs, rt
    function [31:0] addu_code(input [4:0] rd, input [4:0] rs, input [4:0] rt);
        addu_code = {`OP_R, rs, rt, rd, 5'b0, `FUNCT_ADDU};
    endfunction

    // jal target
    function [31:0] jal_code(input [25:0] target);
        jal_code = {`OP_JAL, target};
    endfunction

    initial begin
        $dumpfile("waves/tb_jal.vcd");
        $dumpvars(0, tb_jal);

        `VTEST_BOOT

        `TEST(jal_test)
            clk = 0;
            rst = 1;
            
            cpu.u_pc.curr_pc = 32'd0;
            cpu.u_regfile.regs[31] = 32'd0; // $ra 清零
            cpu.u_regfile.regs[4]  = 32'd0; // 用于验证跳转目标后的结果

            cpu.u_instrm.mem[0] = jal_code(3);         // jal 3
            cpu.u_instrm.mem[1] = addu_code(0, 0, 0);  // addu $0, $0, $0 (nop)
            cpu.u_instrm.mem[3] = addu_code(4, 31, 0); // addu $4, $31, $0 (将 $ra 的值传给 $4)

            #10; rst = 0;

            @(posedge clk); #1; // 周期 1: 取指并执行 jal
            @(posedge clk); #1; // 周期 2: 执行跳转目标的指令

            // 验证逻辑:
            // 1. $31 应该保存了返回地址 4 
            // 2. 第三条指令应当被执行, 因此 R[4] = 4
            `EXPECT("R[4]", cpu.u_regfile.regs[4], 32'd4);
            `EXPECT("R[31]", cpu.u_regfile.regs[31], 32'd4);
        `TEST_END

        `VTEST_FINISH
    end
endmodule
