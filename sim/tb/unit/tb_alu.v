`timescale 1ns/1ps
`include "vtest.vh"
`include "defines.vh"

module tb_alu ();
    reg [31:0] alu_src1, alu_src2;
    reg [3:0] alu_op;
    wire [31:0] alu_out;
    wire zero_f, neg_f, overflow_f, carry_f;

    alu dut (.*);

    `VTEST_INIT

    initial begin
        $dumpfile("waves/tb_alu.vcd");
        $dumpvars(0, tb_alu);
        `VTEST_BOOT

        // 测试1: 测试加法
        `TEST(alu_add_test)
            alu_op = `ALU_OP_ADD;
            alu_src1 = 5; alu_src2 = 3;
            #10;
            `EXPECT("alu_out", alu_out, 8);
            `EXPECT("zero_f", zero_f, 1'b0);
        `TEST_END

        // 测试2: 测试减法
        `TEST(alu_sub_test)
            alu_op = `ALU_OP_SUB;
            alu_src1 = 8; alu_src2 = 8;
            #10;
            `EXPECT("alu_out", alu_out, 0);
            `EXPECT("zero_f", zero_f, 1);
        `TEST_END

        `VTEST_FINISH
    end
endmodule
