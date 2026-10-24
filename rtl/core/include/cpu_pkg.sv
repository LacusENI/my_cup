`ifndef CPU_PKG_SV
`define CPU_PKG_SV

// -----------------------------------------------------------------------------
// cpu_pkg: 全项目共享的常量与纯函数
//
// 说明：
//   - 以前这些定义放在 defines.vh / ext.vh 里，通过 `include 文本拼接；
//   - 现在改成 SystemVerilog package，模块用 `import cpu_pkg::*;` 使用；
//   - 好处：有命名空间、类型安全、不靠文本顺序、IDE/lint 更容易分析。
// -----------------------------------------------------------------------------
package cpu_pkg;

    // ---- ALU 操作码 ----
    localparam logic [3:0] ALU_OP_ADD = 4'b0001;
    localparam logic [3:0] ALU_OP_SUB = 4'b0010;

    // ---- 条件比较类型 ----
    localparam logic [1:0] COND_TYPE_EQ  = 2'b00;

    // ---- 立即数扩展类型 ----
    localparam logic EXT_TYPE_SIGN_EXT = 1'b1;

    // ---- 下一 PC 的来源 ----
    localparam logic [1:0] NPC_OP_PLUS4  = 2'b00;
    localparam logic [1:0] NPC_OP_BRANCH = 2'b01;
    localparam logic [1:0] NPC_OP_DIRECT = 2'b10;
    localparam logic [1:0] NPC_OP_RA     = 2'b11;

    // ---- 写回目标寄存器选择 ----
    localparam logic [1:0] RD_SEL_RT     = 2'b00;
    localparam logic [1:0] RD_SEL_RD     = 2'b01;
    localparam logic [1:0] RD_SEL_REG_RA = 2'b10;

    // ---- 写回数据选择 ----
    localparam logic [1:0] WB_SEL_ALU_OUT = 2'b00;
    localparam logic [1:0] WB_SEL_R_DATA  = 2'b01;
    localparam logic [1:0] WB_SEL_PC_P4   = 2'b10;

    // ---- ALU 第二操作数选择 ----
    localparam logic SRC2_SEL_RS2 = 1'b0;
    localparam logic SRC2_SEL_IMM = 1'b1;

    // ---- opcode ----
    localparam logic [5:0] OP_R       = 6'b000000;
    localparam logic [5:0] OP_ADDIU   = 6'b001001;
    localparam logic [5:0] OP_BEQ     = 6'b000100;
    localparam logic [5:0] OP_LW      = 6'b100011;
    localparam logic [5:0] OP_SW      = 6'b101011;
    localparam logic [5:0] OP_J       = 6'b000010;
    localparam logic [5:0] OP_JAL     = 6'b000011;

    // ---- funct ----
    localparam logic [5:0] FUNCT_ADDU = 6'b100001;
    localparam logic [5:0] FUNCT_JR   = 6'b001000;

    // ---- 位宽扩展函数 ----
    function automatic logic [31:0] s_ext_16_32(input logic [15:0] in);
        return {{16{in[15]}}, in};
    endfunction

    function automatic logic [31:0] z_ext_16_32(input logic [15:0] in);
        return {16'b0, in};
    endfunction

endpackage

`endif // CPU_PKG_SV
