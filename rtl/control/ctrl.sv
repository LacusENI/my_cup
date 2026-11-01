`default_nettype none

module ctrl
    import cpu_pkg::*;
(
    input  opcode_t opcode,
    input  funct3_t funct3,
    input  funct7_t funct7,
    input  logic    valid_encoding,
    output ctrl_t   ctrl
);

    // funct3/funct7 的合法性已经在 decoder 中检查；ctrl 这里保留端口，
    // 方便以后把更多指令加入控制表。
    logic unused_funct;
    assign unused_funct = &{1'b0, funct3, funct7};

    // 先给所有控制信号一个安全默认值，再按 opcode 覆盖。
    // 非法指令保持这些默认值，同时把 inst_illegal 置 1。
    always_comb begin
        ctrl.npc_op       = NPC_PLUS4;
        ctrl.reg_write    = 1'b0;
        ctrl.alu_op       = ALU_NOP;
        ctrl.mem_read     = 1'b0;
        ctrl.mem_write    = 1'b0;
        ctrl.wb_sel       = WB_SEL_ALU_OUT;
        ctrl.src2_sel     = SRC2_SEL_RS2;
        ctrl.inst_illegal = !valid_encoding;

        if (valid_encoding) begin
            unique case (opcode)
                OP_R: begin
                    ctrl.reg_write = 1'b1;
                    ctrl.alu_op    = ALU_ADD;
                    ctrl.wb_sel    = WB_SEL_ALU_OUT;
                    ctrl.src2_sel  = SRC2_SEL_RS2;
                end

                OP_IMM: begin
                    ctrl.reg_write = 1'b1;
                    ctrl.alu_op    = ALU_ADD;
                    ctrl.wb_sel    = WB_SEL_ALU_OUT;
                    ctrl.src2_sel  = SRC2_SEL_IMM;
                end

                OP_BRANCH: begin
                    ctrl.npc_op   = NPC_BRANCH;
                    ctrl.alu_op   = ALU_EQ;
                    ctrl.src2_sel = SRC2_SEL_RS2;
                end

                OP_LOAD: begin
                    ctrl.reg_write = 1'b1;
                    ctrl.alu_op    = ALU_ADD;
                    ctrl.mem_read  = 1'b1;
                    ctrl.wb_sel    = WB_SEL_R_DATA;
                    ctrl.src2_sel  = SRC2_SEL_IMM;
                end

                OP_STORE: begin
                    ctrl.alu_op    = ALU_ADD;
                    ctrl.mem_write = 1'b1;
                    ctrl.src2_sel  = SRC2_SEL_IMM;
                end

                OP_JAL: begin
                    ctrl.npc_op    = NPC_JAL;
                    ctrl.reg_write = 1'b1;
                    ctrl.alu_op    = ALU_NOP;
                    ctrl.wb_sel    = WB_SEL_PC_PLUS4;
                end

                OP_JALR: begin
                    ctrl.npc_op    = NPC_JALR;
                    ctrl.reg_write = 1'b1;
                    ctrl.alu_op    = ALU_ADD;
                    ctrl.wb_sel    = WB_SEL_PC_PLUS4;
                    ctrl.src2_sel  = SRC2_SEL_IMM;
                end

                default: ;
            endcase
        end
    end

endmodule

`default_nettype wire
