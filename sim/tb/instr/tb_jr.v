`timescale 1ns/1ps
`include "vtest.vh"
`include "instr.vh"

module tb_jr ();
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

    // jr rs
    function [31:0] jr_code(input [4:0] rs);
        jr_code = {`OP_R, rs, 10'b0, 5'b0, `FUNCT_JR};
    endfunction

    initial begin
        $dumpfile("waves/tb_jr.vcd");
        $dumpvars(0, tb_jr);

        `VTEST_BOOT

        `TEST(jr_test)
            clk = 0;
            rst = 1;
            cpu.u_pc.curr_pc = 32'd0;
            
            // 把跳转目标地址存入 $31 ($ra)
            // 假设我们要跳到地址 12 (对应 mem[3])
            cpu.u_regfile.regs[31] = 32'd12;

            cpu.u_regfile.regs[1] = 32'd10;
            cpu.u_regfile.regs[2] = 32'd20;
            cpu.u_regfile.regs[3] = 32'd0;

            cpu.u_instrm.mem[0] = jr_code(31);        // jr $31
            cpu.u_instrm.mem[1] = addu_code(3, 1, 2); // addu $3, $1, $2 (跳过)
            cpu.u_instrm.mem[2] = addu_code(0, 0, 0); // addu $0, $0, $0 (跳过)
            cpu.u_instrm.mem[3] = addu_code(3, 1, 1); // addu $3, $1, $1 (执行)

            #10;
            rst = 0;

            // 周期1：执行jr, 并跳转
            @(posedge clk); #1;
            // 周期2：执行指令3
            @(posedge clk); #1;
            
            `EXPECT("R[3]", cpu.u_regfile.regs[3], 32'd20);
        `TEST_END

        `VTEST_FINISH
    end
endmodule
