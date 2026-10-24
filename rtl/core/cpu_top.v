`default_nettype none

module cpu_top (
    input logic clk,
    input logic rst
);
    import cpu_pkg::*;

    logic [31:0] instr_addr;
    logic [31:0] instr;
    logic [31:0] curr_pc, next_pc, pc_plus4, ra;
    logic [1:0]  npc_op;
    logic [25:0] jmp_target;
    logic [15:0] jmp_offset;

    logic [5:0] op, funct;
    logic [4:0] rs, rt, rd;
    /* verilator lint_off UNUSED */
    logic [4:0] shamt;
    logic [15:0] imm16;
    logic [31:0] imm32;
    logic [25:0] instr_index;

    logic [4:0]  reg_src1, reg_src2;
    logic [4:0]  reg_dst;
    logic        reg_write;
    logic [31:0] wb_data;
    logic [31:0] rs1_data, rs2_data;

    logic        ext_type;
    logic [3:0]  alu_op;
    logic [31:0] alu_src1, alu_src2, alu_out;
    logic        zero_f, neg_f, overflow_f, carry_f;
    logic [1:0]  cond_type;
    logic        cond_jmp;

    logic        mem_read, mem_write;
    logic [31:0] addr, r_data, w_data;

    logic [1:0]  rd_sel, wb_sel;
    logic        src2_sel;

    instrm  u_instrm  (.*);
    pc      u_pc      (.*);
    npc     u_npc     (.*);
    decoder u_decoder (.*);
    regfile u_regfile (.*);
    ext     u_ext     (.*);
    alu     u_alu     (.*);
    cond    u_cond    (.*);
    datam   u_datam   (.*);
    ctrl    u_ctrl    (.*);

    assign instr_addr = curr_pc;
    assign jmp_target = instr_index;
    assign jmp_offset = imm16;
    assign ra = rs1_data;

    assign reg_src1 = rs;
    assign reg_src2 = rt;

    // 写回目标寄存器：rd / rt / $ra
    always_comb begin
        unique case (rd_sel)
            RD_SEL_RD:     reg_dst = rd;
            RD_SEL_RT:     reg_dst = rt;
            RD_SEL_REG_RA: reg_dst = 5'd31;
            default:       reg_dst = '0;
        endcase
    end

    // 写回数据：内存读出 / ALU 结果 / PC+4
    always_comb begin
        unique case (wb_sel)
            WB_SEL_R_DATA:  wb_data = r_data;
            WB_SEL_ALU_OUT: wb_data = alu_out;
            WB_SEL_PC_P4:   wb_data = pc_plus4;
            default:        wb_data = '0;
        endcase
    end

    assign alu_src1 = rs1_data;
    assign alu_src2 = src2_sel ? imm32 : rs2_data;

    assign addr = alu_out;
    assign w_data = rs2_data;
endmodule

`default_nettype wire
