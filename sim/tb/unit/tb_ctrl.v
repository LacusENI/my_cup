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
    wire [1:0] cond_type;
    wire       ext_type;
    wire [1:0] rd_sel;
    wire [1:0] wb_sel;
    wire       src2_sel;

    reg        correct;

    ctrl dut(.*);

    initial begin
        $dumpfile("waves/tb_ctrl.v");
        $dumpvars(0, tb_ctrl);

        op = `OP_R_INSTR;
        funct = `FUNCT_ADDU;
        #10;
        $display("instr: addu");

        correct = (rd_sel == `RD_SEL_RD);
        #10;
        $display("rd_sel=%b(%s)", rd_sel, correct ? "yes" : "no");

        correct = (wb_sel == `WB_SEL_ALU_OUT);
        #10;
        $display("wb_sel=%b(%s)", wb_sel, correct ? "yes" : "no");

        correct = (src2_sel == `SRC2_SEL_RS2);
        #10;
        $display("src2_sel=%b(%s)", src2_sel, correct ? "yes" : "no");

        correct = (npc_op == `NPC_OP_PLUS4);
        #10;
        $display("npc_op=%b(%s)", npc_op, correct ? "yes" : "no");

        correct = (alu_op == `ALU_OP_ADD);
        #10;
        $display("alu_op=%b(%s)", alu_op, correct ? "yes" : "no");

        correct = (mem_read == 1'b0);
        #10;
        $display("mem_read=%b(%s)", mem_read, correct ? "yes" : "no");

        $finish;
    end
endmodule
