`timescale 1ns/1ps
`include "vtest.vh"
`include "instr.vh"

module tb_addu ();
    reg clk, rst;

    cpu_top cpu(
        .clk(clk),
        .rst(rst)
    );

    always #5 clk <= ~clk;

    // addu rd, rs, rt
    function [31:0] addu_code(input [4:0] rd, input [4:0] rs, input [4:0] rt);
        addu_code = {`OP_R, rs, rt, rd, 5'b0, `FUNCT_ADDU};
    endfunction

    `VTEST_INIT

    initial begin
        $dumpfile("waves/tb_addu.vcd");
        $dumpvars(0, tb_addu);

        `VTEST_BOOT

        `TEST(addu_test)
            clk = 0;
            rst = 1;

            cpu.u_pc.curr_pc = 32'd0;
            cpu.u_regfile.regs[1] = 32'd5;
            cpu.u_regfile.regs[2] = 32'd3;
            cpu.u_regfile.regs[3] = 32'd0;

            cpu.u_instrm.mem[0] = addu_code(3, 1, 2); // addu $3, $1, $2
            cpu.u_instrm.mem[1] = addu_code(1, 1, 0); // addu $1, $1, $0
            #10; rst = 0;
            #20;
            `EXPECT("R[1]", cpu.u_regfile.regs[1], 5);
            `EXPECT("R[2]", cpu.u_regfile.regs[2], 3);
            `EXPECT("R[3]", cpu.u_regfile.regs[3], 5 + 3);
        `TEST_END

        `VTEST_FINISH
    end
endmodule
