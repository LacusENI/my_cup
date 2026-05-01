`include "lib/vtest.vh"
`include "rtl/core/defines.v"
`timescale 1ns/1ps

module tb_ctrl ();
    reg [5:0] op;
    reg [5:0] funct;

    wire [1:0] npc_op;
    wire       reg_write;
    wire [3:0] alu_op;
    wire       mem_write;
    wire       mem_read;
    wire [1:0] mem_size;
    wire [1:0] cond_type;
    wire       ext_type;
    wire [1:0] rd_sel;
    wire [1:0] wb_sel;
    wire       src2_sel;

    ctrl dut(.*);

    `VTEST_INIT

    initial begin
        $dumpfile("waves/tb_ctrl.vcd");
        $dumpvars(0, tb_ctrl);

        `VTEST_BOOT

        // 测试1: addu 指令
        `TEST(addu_test)
            op = `OP_R_INSTR;
            funct = `FUNCT_ADDU;
            #10;
            
            `EXPECT("rd_sel", rd_sel, `RD_SEL_RD);
            `EXPECT("wb_sel", wb_sel, `WB_SEL_ALU_OUT);
            `EXPECT("src2_sel", src2_sel, `SRC2_SEL_RS2);
            `EXPECT("npc_op", npc_op, `NPC_OP_PLUS4);
            `EXPECT("alu_op", alu_op, `ALU_OP_ADD);
            `EXPECT("mem_read", mem_read, 1'b0);
            `EXPECT("mem_write", mem_write, 1'b0);
        `TEST_END
        
        // 测试2: lw 指令
        `TEST(lw_test);
            op = `OP_LW;
            #10;

            `EXPECT("mem_read", mem_read, 1'b1);
            `EXPECT("mem_write", mem_write, 1'b0);
        `TEST_END
        
        `VTEST_FINISH
        $finish;
    end
endmodule
