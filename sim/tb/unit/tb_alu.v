`timescale 1ns/1ps
`include "lib/vtest.vh"
`include "rtl/core/defines.v"

module tb_alu ();
    reg [31:0] src_a, src_b;
    reg [3:0] opcode;
    wire [31:0] result;
    wire zero;

    alu dut (
        .alu_src1(src_a),
        .alu_src2(src_b),
        .alu_op(opcode),
        .alu_out(result),
        .zero_f(zero),
        .neg_f(), .overflow_f(), .carry_f()
    );

    `VTEST_INIT

    initial begin
        $dumpfile("waves/tb_alu.vcd");
        $dumpvars(0, tb_alu);

        `VTEST_BOOT

        opcode = `ALU_OP_ADD;
        src_a = 5; src_b = 3;
        #10;
        $display("5 + 3 = %d (zero=%b)", result, zero);

        opcode = `ALU_OP_SUB;
        src_a = 8; src_b = 8;
        #10;
        $display("8 - 8 = %d (zero=%b)", result, zero);

        `VTEST_FINISH
        $finish;
    end
endmodule
