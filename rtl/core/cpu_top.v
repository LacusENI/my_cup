`include "rtl/core/defines.v"

module cpu_top (
    input clk,
    input rst
);
    wire [31:0] instr_addr;
    wire [31:0] instr;
    wire [31:0] curr_pc, next_pc, pc_plus4, ra;
    wire [1:0] npc_op;
    wire [25:0] jmp_target;
    wire [15:0] jmp_offset;

    wire [5:0] op, funct;
    wire [4:0] rs, rt, rd;
    /* verilator lint_off UNUSED */
    wire [4:0] shamt;
    wire [15:0] imm16;
    wire [31:0] imm32;
    wire [25:0] instr_index;

    wire [4:0] reg_src1, reg_src2;
    wire [4:0] reg_dst;
    wire reg_write;
    wire [31:0] wb_data;
    wire [31:0] rs1_data, rs2_data;
    
    wire ext_type;
    wire [3:0] alu_op;
    wire [31:0] alu_src1, alu_src2, alu_out;
    wire zero_f, neg_f, overflow_f, carry_f;
    wire [1:0] cond_type;
    wire cond_jmp;

    wire mem_read, mem_write;
    wire [31:0] addr, r_data, w_data;

    wire [1:0] rd_sel, wb_sel;
    wire src2_sel;

    instrm u_instrm (.*);
    pc u_pc (.*);
    npc u_npc (.*);
    decoder u_decoder (.*);
    regfile u_regfile (.*);
    ext u_ext (.*);
    alu u_alu (.*);
    cond u_cond (.*);
    datam u_datam (.*);
    ctrl u_ctrl(.*);
    
    assign instr_addr = curr_pc;
    assign jmp_target = instr_index;
    assign jmp_offset = imm16;
    assign ra = rs1_data;

    assign reg_src1 = rs;
    assign reg_src2 = rt;
    assign reg_dst = rd_sel == `RD_SEL_RD ? rd : 
                     rd_sel == `RD_SEL_RT ? rt : 
                     rd_sel == `RD_SEL_REG_RA ? 5'd31 : 
                     5'd0;
    assign wb_data = wb_sel == `WB_SEL_R_DATA ? r_data : 
                     wb_sel == `WB_SEL_ALU_OUT ? alu_out : 
                     wb_sel == `WB_SEL_PC_P4 ? pc_plus4 :
                     32'dx;

    assign alu_src1 = rs1_data;
    assign alu_src2 = src2_sel ? imm32 : rs2_data;

    assign addr = alu_out;
    assign w_data = rs2_data;
endmodule
