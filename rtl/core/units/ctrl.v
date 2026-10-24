`default_nettype none

module ctrl (
    input  logic [5:0] op,
    input  logic [5:0] funct,
    output logic [1:0] npc_op,
    output logic       reg_write,
    output logic [3:0] alu_op,
    output logic       mem_write,
    output logic       mem_read,
    output logic [1:0] cond_type,
    output logic       ext_type,
    output logic [1:0] rd_sel,
    output logic [1:0] wb_sel,
    output logic       src2_sel
);
    import cpu_pkg::*;

    // 用 always_comb + unique case 写控制逻辑：
    //   - 先给所有输出一个安全默认值（避免 latch / x 传播）；
    //   - 再按 opcode（必要时按 funct）覆盖；
    //   - 未定义的指令保持默认值（相当于“不写回、不访存、顺序执行”）。
    always_comb begin
        npc_op    = NPC_OP_PLUS4;
        reg_write = 1'b0;
        alu_op    = ALU_OP_ADD;
        mem_write = 1'b0;
        mem_read  = 1'b0;
        cond_type = COND_TYPE_EQ;
        ext_type  = EXT_TYPE_SIGN_EXT;
        rd_sel    = RD_SEL_RT;
        wb_sel    = WB_SEL_ALU_OUT;
        src2_sel  = SRC2_SEL_RS2;

        unique case (op)
            OP_R: begin
                unique case (funct)
                    FUNCT_ADDU: begin
                        reg_write = 1'b1;
                        rd_sel    = RD_SEL_RD;
                        wb_sel    = WB_SEL_ALU_OUT;
                        alu_op    = ALU_OP_ADD;
                    end
                    FUNCT_JR: begin
                        npc_op = NPC_OP_RA;
                    end
                    default: ;  // 未定义的 R 型指令
                endcase
            end

            OP_ADDIU: begin
                reg_write = 1'b1;
                rd_sel    = RD_SEL_RT;
                wb_sel    = WB_SEL_ALU_OUT;
                src2_sel  = SRC2_SEL_IMM;
                ext_type  = EXT_TYPE_SIGN_EXT;
                alu_op    = ALU_OP_ADD;
            end

            OP_BEQ: begin
                npc_op    = NPC_OP_BRANCH;
                cond_type = COND_TYPE_EQ;
                alu_op    = ALU_OP_SUB;
                src2_sel  = SRC2_SEL_RS2;
            end

            OP_LW: begin
                reg_write = 1'b1;
                rd_sel    = RD_SEL_RT;
                wb_sel    = WB_SEL_R_DATA;
                src2_sel  = SRC2_SEL_IMM;
                ext_type  = EXT_TYPE_SIGN_EXT;
                alu_op    = ALU_OP_ADD;
                mem_read  = 1'b1;
            end

            OP_SW: begin
                src2_sel  = SRC2_SEL_IMM;
                ext_type  = EXT_TYPE_SIGN_EXT;
                alu_op    = ALU_OP_ADD;
                mem_write = 1'b1;
            end

            OP_J: begin
                npc_op = NPC_OP_DIRECT;
            end

            OP_JAL: begin
                npc_op    = NPC_OP_DIRECT;
                reg_write = 1'b1;
                rd_sel    = RD_SEL_REG_RA;
                wb_sel    = WB_SEL_PC_P4;
            end

            default: ;  // 未定义的 opcode
        endcase
    end
endmodule

`default_nettype wire
