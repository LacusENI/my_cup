`include "rtl/core/defines.v"
`timescale 1ns/1ps

module tb_npc ();
    reg [31:0] curr_pc;
    reg [1:0] npc_op;
    reg cond_jmp;
    reg [25:0] jmp_target;
    reg [15:0] jmp_offset;
    wire [31:0] next_pc;

    npc dut(.*);

    initial begin
        $dumpfile("waves/tb_npc.vcd");
        $dumpvars(0, tb_npc);

        npc_op = `NPC_OP_PLUS4;
        curr_pc = 32'b0100_1100;
        #10;
        $display("(plus4) pc=%d npc=%d", curr_pc, next_pc);

        npc_op = `NPC_OP_BRANCH;
        curr_pc = 32'b1101_1111_0000;
        jmp_offset = -4;
        cond_jmp = 1;
        #10;
        $display("(branch 1) offset=-4 pc=%d npc=%d", curr_pc, next_pc);

        cond_jmp = 0;
        #10;
        $display("(branch 0) offset=-4 pc=%d npc=%d", curr_pc, next_pc);

        npc_op = `NPC_OP_DIRECT;
        curr_pc[31:28] = 4'b0101;
        curr_pc[27:20] = 8'b1111_1111;
        jmp_target = 26'b1111_0001;
        #10;
        $display("(direct) pc=%b target=%b  npc=%b", curr_pc, jmp_target, next_pc); 

        $finish;
    end
endmodule
