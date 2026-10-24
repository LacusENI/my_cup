`default_nettype none

module cpu_top (
    input logic clk,
    input logic rst
);
    import cpu_pkg::*;

    word_t instr_addr;
    word_t instr;
    word_t curr_pc, next_pc, pc_plus4, jmp_reg;
    logic [25:0] jmp_target;
    logic [15:0] jmp_offset;

    instr_t decoded;
    ctrl_t  ctrl;

    // 当前 ISA 没有移位指令；shamt 先保留在 instr_t 里，未来使用。
    // 名字含 unused，Verilator 不会告警。
    logic [4:0] unused_shamt;
    assign unused_shamt = decoded.shamt;

    logic [15:0] imm16;
    word_t imm32;
    logic [25:0] instr_index;

    logic [4:0]  reg_dst;
    word_t wb_data;
    word_t rs1_data, rs2_data;

    word_t alu_src1, alu_src2, alu_out;
    logic        zero_f, neg_f, overflow_f, carry_f;
    logic        cond_jmp;

    word_t addr, r_data, w_data;

    instrm u_instrm (
        .instr_addr(instr_addr),
        .instr(instr)
    );

    pc u_pc (
        .clk(clk),
        .rst(rst),
        .next_pc(next_pc),
        .curr_pc(curr_pc)
    );

    npc u_npc (
        .curr_pc(curr_pc),
        .npc_op(ctrl.npc_op),
        .cond_jmp(cond_jmp),
        .jmp_target(jmp_target),
        .jmp_offset(jmp_offset),
        .jmp_reg(jmp_reg),
        .pc_plus4(pc_plus4),
        .next_pc(next_pc)
    );

    decoder u_decoder (
        .instr(instr),
        .decoded(decoded),
        .imm16(imm16),
        .instr_index(instr_index)
    );

    regfile u_regfile (
        .clk(clk),
        .reg_src1(decoded.rs),
        .reg_src2(decoded.rt),
        .reg_dst(reg_dst),
        .wb_data(wb_data),
        .reg_write(ctrl.reg_write),
        .rs1_data(rs1_data),
        .rs2_data(rs2_data)
    );

    ext u_ext (
        .imm16(imm16),
        .ext_type(ctrl.ext_type),
        .imm32(imm32)
    );

    alu u_alu (
        .alu_src1(alu_src1),
        .alu_src2(alu_src2),
        .alu_op(ctrl.alu_op),
        .alu_out(alu_out),
        .zero_f(zero_f),
        .neg_f(neg_f),
        .overflow_f(overflow_f),
        .carry_f(carry_f)
    );

    cond u_cond (
        .zero_f(zero_f),
        .neg_f(neg_f),
        .overflow_f(overflow_f),
        .carry_f(carry_f),
        .cond_type(ctrl.cond_type),
        .cond_jmp(cond_jmp)
    );

    datam u_datam (
        .clk(clk),
        .mem_read(ctrl.mem_read),
        .mem_write(ctrl.mem_write),
        .addr(addr),
        .w_data(w_data),
        .r_data(r_data)
    );

    ctrl u_ctrl (
        .op(decoded.op),
        .funct(decoded.funct),
        .ctrl(ctrl)
    );

    assign instr_addr = curr_pc;
    assign jmp_target = instr_index;
    assign jmp_offset = imm16;
    assign jmp_reg = rs1_data;

    // 写回目标寄存器：rd / rt / $ra
    always_comb begin
        unique case (ctrl.rd_sel)
            RD_SEL_RD:     reg_dst = decoded.rd;
            RD_SEL_RT:     reg_dst = decoded.rt;
            RD_SEL_REG_RA: reg_dst = 5'd31;
            default:       reg_dst = '0;
        endcase
    end

    // 写回数据：内存读出 / ALU 结果 / PC+4
    always_comb begin
        unique case (ctrl.wb_sel)
            WB_SEL_R_DATA:  wb_data = r_data;
            WB_SEL_ALU_OUT: wb_data = alu_out;
            WB_SEL_PC_P4:   wb_data = pc_plus4;
            default:        wb_data = '0;
        endcase
    end

    assign alu_src1 = rs1_data;
    assign alu_src2 = (ctrl.src2_sel == SRC2_SEL_IMM) ? imm32 : rs2_data;

    assign addr = alu_out;
    assign w_data = rs2_data;
endmodule

`default_nettype wire
