`timescale 1ns/1ps
`include "vtest.vh"
`include "instr.vh"

module tb_j ();
    reg clk, rst;

    cpu_top cpu (
        .clk(clk),
        .rst(rst)
    );

    always #5 clk <= ~clk;

    // addu rd, rs, rt
    function [31:0] addu_code(input [4:0] rd, input [4:0] rs, input [4:0] rt);
        addu_code = {`OP_R, rs, rt, rd, 5'b0, `FUNCT_ADDU};
    endfunction

    // j target
    function [31:0] j_code(input [25:0] target);
        j_code = {`OP_J, target};
    endfunction

    `VTEST_INIT

    initial begin
        $dumpfile("waves/tb_j.vcd");
        $dumpvars(0, tb_j);

        `VTEST_BOOT

        `TEST(j_test)
            clk = 0;
            rst = 1;

            cpu.u_pc.curr_pc = 32'd0;
            cpu.u_regfile.regs[1] = 32'd5;
            cpu.u_regfile.regs[2] = 32'd3;
            cpu.u_regfile.regs[3] = 32'd0;
            cpu.u_regfile.regs[4] = 32'd0;

            cpu.u_instrm.mem[0] = j_code(2); // j 2 -> target PC = 8
            cpu.u_instrm.mem[1] = addu_code(3, 1, 2); // addu $3, $1, $2 (跳过，如果跳转成功)
            cpu.u_instrm.mem[2] = addu_code(4, 1, 2); // addu $4, $1, $2

            #10;
            rst = 0;
            
            // 经过三个时钟周期
            @(posedge clk); #1;
            @(posedge clk); #1;
            @(posedge clk); #1;

            // 如果跳转成功, R[3] = 0, R[4] = 8
            `EXPECT("R[3]", cpu.u_regfile.regs[3], 32'd0);
            `EXPECT("R[4]", cpu.u_regfile.regs[4], 32'd8);
        `TEST_END

        `VTEST_FINISH
    end
endmodule
