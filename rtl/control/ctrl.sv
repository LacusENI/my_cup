`default_nettype none

module ctrl
    import cpu_pkg::*;
(
    input  opcode_t opcode,
    input  funct3_t funct3,
    input  funct7_t funct7,
    input  reg_t    rd,
    input  reg_t    rs1,
    input  funct12_t funct12,
    input  logic    opcode_err,
    output ctrl_t   ctrl
);

    // ctrl 是编码合法性的唯一权威：decoder 只负责字段和立即数格式。
    logic legal;

    // 先给所有控制信号一个安全默认值，再按 opcode 覆盖。
    // 非法编码保持这些默认值，同时进入 halt 状态。
    always_comb begin
        ctrl.npc_op       = NPC_PLUS4;
        ctrl.reg_write    = 1'b0;
        ctrl.alu_op       = ALU_NOP;
        ctrl.mem_read     = 1'b0;
        ctrl.mem_write    = 1'b0;
        ctrl.wb_sel       = WB_SEL_ALU_OUT;
        ctrl.src2_sel     = SRC2_SEL_RS2;
        ctrl.halt         = 1'b0;
        ctrl.halt_cause   = HALT_ILLEGAL_INST;
        legal             = 1'b0;

        if (opcode_err) begin
            // decoder 不认识 opcode：ctrl 不再尝试生成正常控制信号。
            ctrl.halt       = 1'b1;
            ctrl.halt_cause = HALT_ILLEGAL_INST;
        end else begin
            unique case (opcode)
                OP_R: begin
                    legal = (funct3 == F3_ADD) && (funct7 == F7_ADD);
                    if (legal) begin
                        ctrl.reg_write = 1'b1;
                        ctrl.alu_op    = ALU_ADD;
                        ctrl.wb_sel    = WB_SEL_ALU_OUT;
                        ctrl.src2_sel  = SRC2_SEL_RS2;
                    end
                end

                OP_IMM: begin
                    legal = (funct3 == F3_ADD);
                    if (legal) begin
                        ctrl.reg_write = 1'b1;
                        ctrl.alu_op    = ALU_ADD;
                        ctrl.wb_sel    = WB_SEL_ALU_OUT;
                        ctrl.src2_sel  = SRC2_SEL_IMM;
                    end
                end

                OP_BRANCH: begin
                    legal = (funct3 == F3_BEQ);
                    if (legal) begin
                        ctrl.npc_op   = NPC_BRANCH;
                        ctrl.alu_op   = ALU_EQ;
                        ctrl.src2_sel = SRC2_SEL_RS2;
                    end
                end

                OP_LOAD: begin
                    legal = (funct3 == F3_LW);
                    if (legal) begin
                        ctrl.reg_write = 1'b1;
                        ctrl.alu_op    = ALU_ADD;
                        ctrl.mem_read  = 1'b1;
                        ctrl.wb_sel    = WB_SEL_R_DATA;
                        ctrl.src2_sel  = SRC2_SEL_IMM;
                    end
                end

                OP_STORE: begin
                    legal = (funct3 == F3_SW);
                    if (legal) begin
                        ctrl.alu_op    = ALU_ADD;
                        ctrl.mem_write = 1'b1;
                        ctrl.src2_sel  = SRC2_SEL_IMM;
                    end
                end

                OP_JAL: begin
                    legal = 1'b1;
                    ctrl.npc_op    = NPC_JAL;
                    ctrl.reg_write = 1'b1;
                    ctrl.alu_op    = ALU_NOP;
                    ctrl.wb_sel    = WB_SEL_PC_PLUS4;
                end

                OP_JALR: begin
                    legal = (funct3 == F3_JALR);
                    if (legal) begin
                        ctrl.npc_op    = NPC_JALR;
                        ctrl.reg_write = 1'b1;
                        ctrl.alu_op    = ALU_ADD;
                        ctrl.wb_sel    = WB_SEL_PC_PLUS4;
                        ctrl.src2_sel  = SRC2_SEL_IMM;
                    end
                end

                OP_LUI: begin
                    legal = 1'b1;
                    ctrl.npc_op    = NPC_PLUS4;
                    ctrl.reg_write = 1'b1;
                    ctrl.alu_op    = ALU_NOP;
                    ctrl.src2_sel  = SRC2_SEL_IMM;
                    ctrl.wb_sel    = WB_SEL_IMM;
                end

                OP_AUIPC: begin
                    legal = 1'b1;
                    ctrl.npc_op    = NPC_PLUS4;
                    ctrl.reg_write = 1'b1;
                    ctrl.alu_op    = ALU_NOP;
                    ctrl.src2_sel  = SRC2_SEL_IMM;
                    ctrl.wb_sel    = WB_SEL_PC_PLUS_IMM;
                end

                OP_MISC_MEM: begin
                    legal = (funct3 == F3_FENCE) && (rd == '0) && (rs1 == '0);
                    // fence / PAUSE 在当前内存模型下是 NOP。
                end

                OP_SYSTEM: begin
                    legal = (funct3 == F3_PRIV) &&
                            (rd == '0) &&
                            (rs1 == '0) &&
                            ((funct12 == F12_ECALL) ||
                             (funct12 == F12_EBREAK));
                    if (legal) begin
                        ctrl.halt       = 1'b1;
                        ctrl.halt_cause = (funct12 == F12_ECALL)
                                          ? HALT_ECALL
                                          : HALT_EBREAK;
                    end
                end

                default: legal = 1'b0;
            endcase

            if (!legal) begin
                ctrl.reg_write  = 1'b0;
                ctrl.mem_read   = 1'b0;
                ctrl.mem_write  = 1'b0;
                ctrl.halt       = 1'b1;
                ctrl.halt_cause = HALT_ILLEGAL_INST;
            end
        end
    end

endmodule

`default_nettype wire
