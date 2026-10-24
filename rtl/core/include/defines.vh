`ifndef DEFINES_V
`define DEFINES_V

`define ALU_OP_ADD 4'b0001
`define ALU_OP_SUB 4'b0010

`define COND_TYPE_EQ  2'b00
`define COND_TYPE_NEQ 2'b01
`define COND_TYPE_LT  2'b10
`define COND_TYPE_LTU 2'b11

`define EXT_TYPE_ZERO_EXT 1'b0
`define EXT_TYPE_SIGN_EXT 1'b1

`define NPC_OP_PLUS4  2'b00
`define NPC_OP_BRANCH 2'b01
`define NPC_OP_DIRECT 2'b10
`define NPC_OP_RA     2'b11

`define RD_SEL_RT      2'b00
`define RD_SEL_RD      2'b01
`define RD_SEL_REG_RA  2'b10
`define WB_SEL_ALU_OUT 2'b00
`define WB_SEL_R_DATA  2'b01
`define WB_SEL_PC_P4   2'b10
`define SRC2_SEL_RS2   1'b0
`define SRC2_SEL_IMM   1'b1

`define OP_R_INSTR 6'b00_0000
`define OP_ADDIU   6'b00_1001
`define OP_BEQ     6'b00_0100
`define OP_LW      6'b10_0011
`define OP_SW      6'b10_1011
`define OP_J       6'b00_0010
`define OP_JAL     6'b00_0011

`define FUNCT_ADDU 6'b10_0001
`define FUNCT_JR   6'b00_1000

`endif // DEFINES_V
