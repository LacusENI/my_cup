`timescale 1ns/1ps

module tb_alu ();
    reg [31:0] src_a, src_b;
    reg [3:0] opcode;
    wire [31:0] result;
    wire zero;

    integer pass_count = 0;
    integer fail_count = 0;
    integer test_id = 0;

    localparam OP_ADD = 4'd0;
    localparam OP_SUB = 4'd1;

    ALU dut (
        .alu_src1(src_a),
        .alu_src2(src_b),
        .alu_op(opcode),
        .alu_out(result),
        .zero_f(zero),
        .neg_f(), .overflow_f(), .carry_f()
    );

    initial begin
        $dumpfile("waves/tb_alu.vcd");
        $dumpvars(0, tb_alu);

        opcode = OP_ADD;
        src_a = 5; src_b = 3;
        #10;
        $display("5 + 3 = %d (zero=%b)", result, zero);

        opcode = OP_SUB;
        src_a = 8; src_b = 8;
        #10;
        $display("8 - 8 = %d (zero=%b)", result, zero);

        $finish;
    end
endmodule