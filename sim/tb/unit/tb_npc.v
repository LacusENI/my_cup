`timescale 1ns/1ps
`include "vtest.vh"
`include "defines.vh"

module tb_npc ();
    reg [31:0] curr_pc;
    reg [1:0] npc_op;
    reg cond_jmp;
    reg [25:0] jmp_target;
    reg [15:0] jmp_offset;
    reg [31:0] ra;
    wire [31:0] next_pc, pc_plus4;

    npc dut(.*);

    `VTEST_INIT

    initial begin
        $dumpfile("waves/tb_npc.vcd");
        $dumpvars(0, tb_npc);
        `VTEST_BOOT

        `TEST(npc_plus4_test)
            npc_op = `NPC_OP_PLUS4;
            curr_pc = 32'b0100_1100;
            #10;
            `EXPECT("next_pc", next_pc, 32'b0100_1100 + 4)
        `TEST_END

        `TEST(npc_branch_jmp_test)
            npc_op = `NPC_OP_BRANCH;
            curr_pc = 32'b1101_1111_0000;
            jmp_offset = -4;
            cond_jmp = 1;
            #10;
            `EXPECT("next_pc", next_pc, 32'b1101_1111_0000 - (4 << 2));
            cond_jmp = 0;
            #10;
            `EXPECT("next_pc", next_pc, 32'b1101_1111_0000 + 4);
        `TEST_END
        
        `TEST(npc_directly_jmp_test)
            npc_op = `NPC_OP_DIRECT;
            curr_pc = 32'hffff_ffff;
            curr_pc[31:28] = 4'b0101;
            curr_pc[27:20] = 8'b1111_1111;
            jmp_target = 26'b1011_1110_1001_1001_1111_0001_01;
            #10;
            `EXPECT("next_pc", next_pc, 32'b0101_1011_1110_1001_1001_1111_0001_0100);
        `TEST_END
        
        `TEST(npc_jmp_to_ra_test)
            npc_op = `NPC_OP_RA;
            curr_pc = 32'hffff_ffff;
            ra = 32'b1;
            #10;
            `EXPECT("next_pc", next_pc, 32'b1);
        `TEST_END
        
        `VTEST_FINISH
    end
endmodule
