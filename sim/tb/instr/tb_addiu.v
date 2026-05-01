`timescale 1ns/1ps
`include "vtest.vh"
`include "instr.vh"

module tb_addiu ();
    reg clk, rst;

    cpu_top cpu (
        .clk(clk),
        .rst(rst)
    );

    always #5 clk <= ~clk;

    `VTEST_INIT

    // addiu rt, rs, imm
    function [31:0] addiu_code(input [4:0] rt, input [4:0] rs, input [15:0] imm);
        addiu_code = {`OP_ADDIU, rs, rt, imm};
    endfunction

    initial begin
        $dumpfile("waves/tb_addiu.vcd");
        $dumpvars(0, tb_addiu);

        `VTEST_BOOT

        `TEST(addiu_test)
            clk = 0;
            rst = 1;
            cpu.u_pc.curr_pc = 32'd0;

            cpu.u_regfile.regs[1] = 32'd10;
            cpu.u_regfile.regs[2] = 32'd0;
            cpu.u_regfile.regs[3] = 32'd0;

            cpu.u_instrm.mem[0] = addiu_code(2, 1, 16'd33);
            cpu.u_instrm.mem[1] = addiu_code(3, 0, 16'd33);

            #10;
            rst = 0;
            // 经过两个时钟周期
            @(posedge clk); #1;
            @(posedge clk); #1;

            `EXPECT("R[2]", cpu.u_regfile.regs[2], 32'd43);
            `EXPECT("R[3]", cpu.u_regfile.regs[3], 32'd33);
        `TEST_END

        `VTEST_FINISH
    end
endmodule
