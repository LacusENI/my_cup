`ifndef CPU_PKG_SV
`define CPU_PKG_SV

// -----------------------------------------------------------------------------
// cpu_pkg: 全项目共享的类型、常量与纯函数
//
// 说明：
//   - 控制信号用 typedef enum，而不是裸 localparam，获得类型检查；
//   - 指令字段用 struct packed，decoder 直接输出结构体；
//   - 控制信号用 struct packed 打包成 ctrl_t，方便以后做流水线寄存器。
// -----------------------------------------------------------------------------
package cpu_pkg;

    // ---- 基本参数 ----
    localparam int XLEN = 32;
    localparam int IMEM_WORDS = 2048;
    localparam int DMEM_WORDS = 2048;
    localparam int IMEM_ADDR_W = $clog2(IMEM_WORDS);
    localparam int DMEM_ADDR_W = $clog2(DMEM_WORDS);

    typedef logic [XLEN-1:0] word_t;

    // ---- ALU 操作码 ----
    typedef enum logic [3:0] {
        ALU_OP_ADD = 4'b0001,
        ALU_OP_SUB = 4'b0010
    } alu_op_t;

    // ---- 条件比较类型 ----
    typedef enum logic [1:0] {
        COND_TYPE_EQ = 2'b00
    } cond_type_t;

    // ---- 立即数扩展类型 ----
    typedef enum logic {
        EXT_TYPE_ZERO_EXT = 1'b0,
        EXT_TYPE_SIGN_EXT = 1'b1
    } ext_type_t;

    // ---- 下一 PC 的来源 ----
    typedef enum logic [1:0] {
        NPC_OP_PLUS4  = 2'b00,
        NPC_OP_BRANCH = 2'b01,
        NPC_OP_DIRECT = 2'b10,
        NPC_OP_RA     = 2'b11
    } npc_op_t;

    // ---- 写回目标寄存器选择 ----
    typedef enum logic [1:0] {
        RD_SEL_RT     = 2'b00,
        RD_SEL_RD     = 2'b01,
        RD_SEL_REG_RA = 2'b10
    } rd_sel_t;

    // ---- 写回数据选择 ----
    typedef enum logic [1:0] {
        WB_SEL_ALU_OUT = 2'b00,
        WB_SEL_R_DATA  = 2'b01,
        WB_SEL_PC_P4   = 2'b10
    } wb_sel_t;

    // ---- ALU 第二操作数选择 ----
    typedef enum logic {
        SRC2_SEL_RS2 = 1'b0,
        SRC2_SEL_IMM = 1'b1
    } src2_sel_t;

    // ---- opcode / funct（保持 6 位常量，便于和 instr 字段比较）----
    localparam logic [5:0] OP_R     = 6'b000000;
    localparam logic [5:0] OP_ADDIU = 6'b001001;
    localparam logic [5:0] OP_BEQ   = 6'b000100;
    localparam logic [5:0] OP_LW    = 6'b100011;
    localparam logic [5:0] OP_SW    = 6'b101011;
    localparam logic [5:0] OP_J     = 6'b000010;
    localparam logic [5:0] OP_JAL   = 6'b000011;

    localparam logic [5:0] FUNCT_ADDU = 6'b100001;
    localparam logic [5:0] FUNCT_JR   = 6'b001000;

    // ---- 指令字段 ----
    typedef struct packed {
        logic [5:0] op;
        logic [4:0] rs;
        logic [4:0] rt;
        logic [4:0] rd;
        logic [4:0] shamt;
        logic [5:0] funct;
    } instr_t;

    // ---- 控制信号打包 ----
    typedef struct packed {
        npc_op_t    npc_op;
        logic       reg_write;
        alu_op_t    alu_op;
        logic       mem_write;
        logic       mem_read;
        cond_type_t cond_type;
        ext_type_t  ext_type;
        rd_sel_t    rd_sel;
        wb_sel_t    wb_sel;
        src2_sel_t  src2_sel;
    } ctrl_t;

    // ---- 位宽扩展函数 ----
    function automatic word_t s_ext_16_32(input logic [15:0] in);
        return {{16{in[15]}}, in};
    endfunction

    function automatic word_t z_ext_16_32(input logic [15:0] in);
        return {16'b0, in};
    endfunction

endpackage

`endif // CPU_PKG_SV
