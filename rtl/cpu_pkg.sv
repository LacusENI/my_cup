`ifndef CPU_PKG_SV
`define CPU_PKG_SV

// -----------------------------------------------------------------------------
// cpu_pkg: 全项目共享的类型、常量与纯函数
//
// v0.3-rv32i 只保留当前 7 条指令需要的类型：
//   add, addi, beq, lw, sw, jal, jalr
//
// 说明：
//   - 控制信号用 typedef enum，而不是裸 localparam，获得类型检查；
//   - 指令字段用 struct packed，decoder 直接输出结构体；
//   - 控制信号打包成 ctrl_t，方便以后做流水线寄存器。
// -----------------------------------------------------------------------------
package cpu_pkg;

    // ---- 基本参数 ----
    localparam int XLEN = 32;
    localparam int IMEM_WORDS = 2048;
    localparam int DMEM_WORDS = 2048;
    localparam int IMEM_ADDR_W = $clog2(IMEM_WORDS);
    localparam int DMEM_ADDR_W = $clog2(DMEM_WORDS);

    typedef logic [XLEN-1:0] word_t;

    // ---- 指令字段 ----
    typedef logic [4:0] reg_t;
    typedef logic [6:0] funct7_t;
    typedef logic [2:0] funct3_t;
    typedef logic [6:0] opcode_t;

    // ---- ALU 操作码 ----
    // 本批只做加法、相等比较和空操作。
    typedef enum logic [1:0] {
        ALU_NOP = 2'b00,
        ALU_ADD = 2'b01,
        ALU_EQ  = 2'b10
    } alu_op_t;

    // ---- 下一 PC 的来源 ----
    typedef enum logic [1:0] {
        NPC_PLUS4  = 2'b00,
        NPC_BRANCH = 2'b01,
        NPC_JAL    = 2'b10,
        NPC_JALR   = 2'b11
    } npc_op_t;

    // ---- 写回数据选择 ----
    typedef enum logic [1:0] {
        WB_SEL_ALU_OUT = 2'b00,
        WB_SEL_R_DATA  = 2'b01,
        WB_SEL_PC_PLUS4 = 2'b10
    } wb_sel_t;

    // ---- ALU 第二操作数选择 ----
    typedef enum logic {
        SRC2_SEL_RS2 = 1'b0,
        SRC2_SEL_IMM = 1'b1
    } src2_sel_t;

    // ---- RV32I opcode / funct3 / funct7 ----
    localparam opcode_t OP_LOAD   = 7'b0000011;
    localparam opcode_t OP_IMM    = 7'b0010011;
    localparam opcode_t OP_STORE  = 7'b0100011;
    localparam opcode_t OP_R      = 7'b0110011;
    localparam opcode_t OP_BRANCH = 7'b1100011;
    localparam opcode_t OP_JALR   = 7'b1100111;
    localparam opcode_t OP_JAL    = 7'b1101111;

    localparam funct3_t F3_ADD  = 3'b000;
    localparam funct3_t F3_LW   = 3'b010;
    localparam funct3_t F3_SW   = 3'b010;
    localparam funct3_t F3_BEQ  = 3'b000;
    localparam funct3_t F3_JALR = 3'b000;

    localparam funct7_t F7_ADD = 7'b0000000;

    // ---- 指令字段 ----
    // 位序与 RV32I 32 位指令一致：funct7 在最高位，opcode 在最低位。
    typedef struct packed {
        funct7_t funct7;
        reg_t    rs2;
        reg_t    rs1;
        funct3_t funct3;
        reg_t    rd;
        opcode_t opcode;
    } instr_t;

    // ---- 控制信号打包 ----
    typedef struct packed {
        npc_op_t    npc_op;
        logic       reg_write;
        alu_op_t    alu_op;
        logic       mem_read;
        logic       mem_write;
        wb_sel_t    wb_sel;
        src2_sel_t  src2_sel;
        logic       inst_illegal;
    } ctrl_t;

    // ---- 流水线级间数据（本批不上流水线，只保留结构定义）----
    typedef struct packed {
        logic  valid;
        word_t pc;
        word_t pc_plus4;
        word_t instr;
    } if_id_t;

    typedef struct packed {
        logic   valid;
        word_t  pc;
        word_t  pc_plus4;
        instr_t instr;
        word_t  rs1_data;
        word_t  rs2_data;
        word_t  imm32;
        ctrl_t  ctrl;
    } id_ex_t;

    typedef struct packed {
        logic   valid;
        word_t  pc_plus4;
        word_t  alu_out;
        word_t  rs2_data;
        instr_t instr;
        ctrl_t  ctrl;
    } ex_mem_t;

    typedef struct packed {
        logic   valid;
        word_t  pc_plus4;
        word_t  alu_out;
        word_t  r_data;
        instr_t instr;
        ctrl_t  ctrl;
    } mem_wb_t;

endpackage

`endif // CPU_PKG_SV
