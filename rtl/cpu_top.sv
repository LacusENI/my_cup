`default_nettype none

module cpu_top
    import cpu_pkg::*;
(
    input  logic        clk,
    input  logic        rst,
    output logic        halt,
    output halt_cause_t halt_cause
);

    word_t inst_addr;
    word_t inst;
    word_t curr_pc, next_pc, pc_plus4, pc_plus_imm;

    inst_t decoded;
    ctrl_t ctrl;

    word_t imm;
    logic  opcode_err;

    logic inst_addr_err;
    logic data_addr_err;
    logic target_addr_err;
    logic load_addr_err;
    logic store_addr_err;

    reg_t rs1, rs2, rd;
    word_t rs1_data, rs2_data;
    word_t wb_data;

    word_t alu_src1, alu_src2, alu_out;
    logic cmp_result;
    logic branch_taken;

    // 复位沿不提交写操作；halt 时停止 PC 和所有写操作。
    logic reg_write_en, mem_write_en, mem_read_en;
    logic pc_stall;

    word_t addr, r_data, w_data;

    instm u_instm (
        .inst_addr(inst_addr),
        .inst(inst),
        .inst_addr_err(inst_addr_err)
    );

    pc u_pc (
        .clk(clk),
        .rst(rst),
        .stall(pc_stall),
        .next_pc(next_pc),
        .curr_pc(curr_pc)
    );

    npc u_npc (
        .inst_pc(curr_pc),
        .npc_op(ctrl.npc_op),
        .branch_taken(branch_taken),
        .pc_offset(imm),
        .jalr_target(alu_out),
        .pc_plus4(pc_plus4),
        .pc_plus_imm(pc_plus_imm),
        .target_addr_err(target_addr_err),
        .next_pc(next_pc)
    );

    decoder u_decoder (
        .inst(inst),
        .decoded(decoded),
        .imm(imm),
        .opcode_err(opcode_err)
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
        .reg_write_en(reg_write_en),
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
        .mem_read_en(mem_read_en),
        .mem_write_en(mem_write_en),
        .addr(addr),
        .w_data(w_data),
        .r_data(r_data),
        .addr_err(data_addr_err)
    );

    ctrl u_ctrl (
        .opcode(decoded.opcode),
        .funct3(decoded.funct3),
        .funct7(decoded.funct7),
        .rd(decoded.rd),
        .rs1(decoded.rs1),
        .funct12(decoded.funct12),
        .opcode_err(opcode_err),
        .ctrl(ctrl)
    );

    assign load_addr_err  = ctrl.mem_read && data_addr_err;
    assign store_addr_err = ctrl.mem_write && data_addr_err;

    halt_unit u_halt_unit (
        .inst_illegal(ctrl.inst_illegal),
        .sys_op(ctrl.sys_op),
        .inst_addr_err(inst_addr_err),
        .load_addr_err(load_addr_err),
        .store_addr_err(store_addr_err),
        .target_addr_err(target_addr_err),
        .halt(halt),
        .halt_cause(halt_cause)
    );

    assign pc_stall     = halt;
    assign reg_write_en = ctrl.reg_write && !rst && !halt;
    assign mem_write_en = ctrl.mem_write && !rst && !halt;
    assign mem_read_en  = ctrl.mem_read && !halt;

    assign branch_taken = cmp_result && (ctrl.npc_op == NPC_BRANCH);
    assign inst_addr = curr_pc;

    assign alu_src1 = rs1_data;
    assign alu_src2 = (ctrl.src2_sel == SRC2_SEL_IMM) ? imm : rs2_data;

    assign addr = alu_out;
    assign w_data = rs2_data;

    // 写回数据：ALU 结果 / 内存读出 / PC+4 / U 型立即数 / PC+imm
    always_comb begin
        unique case (ctrl.wb_sel)
            WB_SEL_ALU_OUT:     wb_data = alu_out;
            WB_SEL_R_DATA:      wb_data = r_data;
            WB_SEL_PC_PLUS4:    wb_data = pc_plus4;
            WB_SEL_IMM:         wb_data = imm;
            WB_SEL_PC_PLUS_IMM: wb_data = pc_plus_imm;
            default:            wb_data = '0;
        endcase
    end

endmodule

`default_nettype wire
