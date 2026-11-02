`default_nettype none

module cpu_top (
    input  logic clk,
    input  logic rst,
    output logic inst_illegal
);
    import cpu_pkg::*;

    word_t inst_addr;
    word_t inst;
    word_t curr_pc, next_pc, pc_plus4;

    inst_t decoded;
    ctrl_t ctrl;

    word_t imm;
    logic  valid_encoding;

    reg_t rs1, rs2, rd;
    word_t rs1_data, rs2_data;
    word_t wb_data;

    word_t alu_src1, alu_src2, alu_out;
    logic cmp_result;
    logic branch_taken;

    // 复位沿不提交写操作；regfile / datam 的接口保持不动。
    logic reg_write_en, mem_write_en;

    word_t addr, r_data, w_data;

    instm u_instm (
        .inst_addr(inst_addr),
        .inst(inst)
    );

    pc u_pc (
        .clk(clk),
        .rst(rst),
        .next_pc(next_pc),
        .curr_pc(curr_pc)
    );

    npc u_npc (
        .inst_pc(curr_pc),
        .npc_op(ctrl.npc_op),
        .branch_taken(branch_taken),
        .pc_offset(imm),
        .jalr_target(alu_out),
        .inst_illegal(ctrl.inst_illegal),
        .pc_plus4(pc_plus4),
        .next_pc(next_pc)
    );

    decoder u_decoder (
        .inst(inst),
        .decoded(decoded),
        .imm(imm),
        .valid_encoding(valid_encoding)
    );

    assign rs1 = decoded.rs1;
    assign rs2 = decoded.rs2;
    assign rd  = decoded.rd;

    regfile u_regfile (
        .clk(clk),
        .rs1(rs1),
        .rs2(rs2),
        .rd(rd),
        .wb_data(wb_data),
        .reg_write(reg_write_en),
        .rs1_data(rs1_data),
        .rs2_data(rs2_data)
    );

    alu u_alu (
        .alu_src1(alu_src1),
        .alu_src2(alu_src2),
        .alu_op(ctrl.alu_op),
        .alu_out(alu_out),
        .cmp_result(cmp_result)
    );

    datam u_datam (
        .clk(clk),
        .mem_read(ctrl.mem_read),
        .mem_write(mem_write_en),
        .addr(addr),
        .w_data(w_data),
        .r_data(r_data)
    );

    ctrl u_ctrl (
        .opcode(decoded.opcode),
        .funct3(decoded.funct3),
        .funct7(decoded.funct7),
        .valid_encoding(valid_encoding),
        .ctrl(ctrl)
    );

    assign reg_write_en = ctrl.reg_write && !rst;
    assign mem_write_en = ctrl.mem_write && !rst;

    assign branch_taken = cmp_result && (ctrl.npc_op == NPC_BRANCH);
    assign inst_illegal = ctrl.inst_illegal;
    assign inst_addr = curr_pc;

    assign alu_src1 = rs1_data;
    assign alu_src2 = (ctrl.src2_sel == SRC2_SEL_IMM) ? imm : rs2_data;

    assign addr = alu_out;
    assign w_data = rs2_data;

    // 写回数据：ALU 结果 / 内存读出 / PC+4
    always_comb begin
        unique case (ctrl.wb_sel)
            WB_SEL_ALU_OUT:  wb_data = alu_out;
            WB_SEL_R_DATA:   wb_data = r_data;
            WB_SEL_PC_PLUS4: wb_data = pc_plus4;
            default:         wb_data = '0;
        endcase
    end

endmodule

`default_nettype wire
