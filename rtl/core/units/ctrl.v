`default_nettype none

module ctrl
    import cpu_pkg::*;
(
    input  logic [5:0] op,
    input  logic [5:0] funct,
    output ctrl_t      ctrl
);

    // 先给所有控制信号一个安全默认值，再按 opcode/funct 覆盖。
    // 未定义的指令保持默认值（不写回、不访存、顺序执行）。
    always_comb begin
        ctrl.npc_op    = NPC_OP_PLUS4;
        ctrl.reg_write = 1'b0;
        ctrl.alu_op    = ALU_OP_ADD;
        ctrl.mem_write = 1'b0;
        ctrl.mem_read  = 1'b0;
        ctrl.cond_type = COND_TYPE_EQ;
        ctrl.ext_type  = EXT_TYPE_SIGN_EXT;
        ctrl.rd_sel    = RD_SEL_RT;
        ctrl.wb_sel    = WB_SEL_ALU_OUT;
        ctrl.src2_sel  = SRC2_SEL_RS2;

        unique case (op)
            OP_R: begin
                unique case (funct)
                    FUNCT_ADDU: begin
                        ctrl.reg_write = 1'b1;
                        ctrl.rd_sel    = RD_SEL_RD;
                        ctrl.wb_sel    = WB_SEL_ALU_OUT;
                        ctrl.alu_op    = ALU_OP_ADD;
                    end
                    FUNCT_JR: begin
                        ctrl.npc_op = NPC_OP_RA;
                    end
                    default: ;  // 未定义的 R 型指令
                endcase
            end

            OP_ADDIU: begin
                ctrl.reg_write = 1'b1;
                ctrl.rd_sel    = RD_SEL_RT;
                ctrl.wb_sel    = WB_SEL_ALU_OUT;
                ctrl.src2_sel  = SRC2_SEL_IMM;
                ctrl.ext_type  = EXT_TYPE_SIGN_EXT;
                ctrl.alu_op    = ALU_OP_ADD;
            end

            OP_BEQ: begin
                ctrl.npc_op    = NPC_OP_BRANCH;
                ctrl.cond_type = COND_TYPE_EQ;
                ctrl.alu_op    = ALU_OP_SUB;
                ctrl.src2_sel  = SRC2_SEL_RS2;
            end

            OP_LW: begin
                ctrl.reg_write = 1'b1;
                ctrl.rd_sel    = RD_SEL_RT;
                ctrl.wb_sel    = WB_SEL_R_DATA;
                ctrl.src2_sel  = SRC2_SEL_IMM;
                ctrl.ext_type  = EXT_TYPE_SIGN_EXT;
                ctrl.alu_op    = ALU_OP_ADD;
                ctrl.mem_read  = 1'b1;
            end

            OP_SW: begin
                ctrl.src2_sel  = SRC2_SEL_IMM;
                ctrl.ext_type  = EXT_TYPE_SIGN_EXT;
                ctrl.alu_op    = ALU_OP_ADD;
                ctrl.mem_write = 1'b1;
            end

            OP_J: begin
                ctrl.npc_op = NPC_OP_DIRECT;
            end

            OP_JAL: begin
                ctrl.npc_op    = NPC_OP_DIRECT;
                ctrl.reg_write = 1'b1;
                ctrl.rd_sel    = RD_SEL_REG_RA;
                ctrl.wb_sel    = WB_SEL_PC_P4;
            end

            default: ;  // 未定义的 opcode
        endcase
    end
endmodule

`default_nettype wire
