`include "rtl/core/defines.v"
`timescale 1ns/1ps

module tb_npc ();
    reg [31:0] curr_pc;
    reg [1:0] npc_op;
    reg cond_jmp;
    reg [25:0] jmp_target;
    reg [15:0] jmp_offset;
    reg [31:0] ra;
    wire [31:0] next_pc, pc_plus4;
    reg test_passed, correct;

    npc dut(.*);

    initial begin
        $dumpfile("waves/tb_npc.vcd");
        $dumpvars(0, tb_npc);

        test_passed = 1;

        npc_op = `NPC_OP_PLUS4;
        curr_pc = 32'b0100_1100;
        #10;
        $display("(plus4) pc=%d npc=%d", curr_pc, next_pc);
        correct = (next_pc == 32'b0100_1100 + 4);
        $display("%s", correct ? "yes" : "no");
        test_passed = test_passed && correct;

        npc_op = `NPC_OP_BRANCH;
        curr_pc = 32'b1101_1111_0000;
        jmp_offset = -4;
        cond_jmp = 1;
        #10;
        $display("(branch 1) offset=-4 pc=%d npc=%d", curr_pc, next_pc);
        correct = (next_pc == 32'b1101_1111_0000 - (4 << 2));
        $display("%s", correct ? "yes" : "no");
        test_passed = test_passed && correct;

        cond_jmp = 0;
        #10;
        $display("(branch 0) offset=-4 pc=%d npc=%d", curr_pc, next_pc);
        correct = (next_pc == 32'b1101_1111_0000 + 4);
        $display("%s", correct ? "yes" : "no");
        test_passed = test_passed && correct;

        npc_op = `NPC_OP_DIRECT;
        curr_pc = 32'hffff_ffff;
        curr_pc[31:28] = 4'b0101;
        curr_pc[27:20] = 8'b1111_1111;
        jmp_target = 26'b1011_1110_1001_1001_1111_0001_01;
        #10;
        $display("(direct) pc=%b target=%b npc=%b", curr_pc, jmp_target, next_pc); 
        correct = (next_pc == 32'b0101_1011_1110_1001_1001_1111_0001_0100);
        $display("%s", correct ? "yes" : "no");
        test_passed = test_passed && correct;

        npc_op = `NPC_OP_RA;
        curr_pc = 32'hffff_ffff;
        ra = 32'b0;
        #10;
        $display("(ra) pc=%d ra=%d npc=%d", curr_pc, ra, next_pc);
        correct = (next_pc == 32'b0);
        $display("%s", correct ? "yes" : "no");
        test_passed = test_passed && correct;

        if (test_passed)
            $display("TEST PASSED");
        else
            $display("TEST FAILED");

        $finish;
    end
endmodule
