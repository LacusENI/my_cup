`timescale 1ns/1ps
`include "vtest.vh"
`include "instr.vh"

module tb_lw ();
    reg clk, rst;

    cpu_top cpu (
        .clk(clk),
        .rst(rst)
    );

    always #5 clk <= ~clk;

    `VTEST_INIT

    // lw rt, offset(base)
    function [31:0] lw_code(input [4:0] rt, input [15:0] offset, input [4:0] base);
        lw_code = {`OP_LW, base, rt, offset};
    endfunction

    initial begin
        $dumpfile("waves/tb_lw.vcd");
        $dumpvars(0, tb_lw);

        `VTEST_BOOT

        `TEST(lw_test)
            clk = 0; rst = 1;
            cpu.u_pc.curr_pc = 32'd0;

            cpu.u_regfile.regs[1] = 32'd0;  // 存储数据
            cpu.u_regfile.regs[2] = 32'd16; // 存储基址

            cpu.u_datam.mem[8] = 32'd55; // 数据在地址32, 即mem[8]

            cpu.u_instrm.mem[0] = lw_code(1, 16, 2); // lw $1 16($2)

            #10; rst = 0;
            @(posedge clk); #10; // 经过一个时钟周期

            `EXPECT("R[1]", cpu.u_regfile.regs[1], 32'd55);
        `TEST_END
        `VTEST_FINISH
    end
endmodule
